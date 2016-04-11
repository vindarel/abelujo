# -*- coding: utf-8 -*-
# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

import csv
import datetime
import json
import logging
import traceback
import urllib
import urlparse

from unidecode import unidecode

import datasources.all.discogs.discogsScraper as discogs
# The datasources imports must have the name as their self.SOURCE_NAME
import datasources.deDE.buchwagner.buchWagnerScraper as buchWagner
import datasources.esES.casadellibro.casadellibroScraper as casadellibro
import datasources.frFR.chapitre.chapitreScraper as chapitre  # same name as module's SOURCE_NAME
import datasources.frFR.decitre.decitreScraper as decitre
import datasources.frFR.librairiedeparis.librairiedeparisScraper as librairiedeparis
import models
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from models import Basket
from models import Bill
from models import Card
from models import CardType
from models import Deposit
from models import DepositState
from models import Distributor
from models import Inventory
from models import Place
from models import Preferences
from models import Publisher
from models import Sell
from models import Shelf
from models import Stats
from search.models import Entry
from search.models import EntryCopies
from search.models.utils import is_isbn
from search.models.utils import list_from_coma_separated_ints
from search.models.utils import list_to_pairs
from search.models.utils import ppcard
from search.models.utils import truncate
from xhtml2pdf import pisa

log = logging.getLogger(__name__)

MAX_COPIES_ADDITIONS = 10000  # maximum of copies to add at once
DEFAULT_NB_COPIES = 1         # default nb of copies to add.

# scraper names are the name of the imported module.
SCRAPER_CHOICES = [
    ("Book shops", (
        ("decitre", "decitre.fr"),
        ("librairiedeparis", "librairie de Paris"),
        ("chapitre", "chapitre.com - fr"),
        ("buchWagner", "buchWagner Munchen - de"),
        ("casadellibro", "casa del libro, Madrid - es"),
    )
 ),
    ("CDs", (
        ("discogs", "discogs.com"),
    )
 )
]

def get_places_choices():
    return [(0, _("All"))] + [(it.id, it.name)
                               for it in Place.objects.all()]

class MyNumberInput(TextInput):
    # render an IntegerField with a "number" html5 widget, not text.
    input_type = 'number'


def get_distributor_choices():
    dists = [(dist.id, dist.name) for dist in Distributor.objects.all()]
    pubs = [(pub.id, pub.name) for pub in Publisher.objects.all()]
    choices = [(_(u"Distributors"),
                dists),
               (_(u"Publishers"),
                pubs)]
    return choices


class AddForm(forms.Form):
    """The form populated when the user clicks on "add this card"."""
    # The search is saved to the session so we need to get the element we want: hence the for counter.
    # We couldn't find how to populate its value (which is {{ forloop.counter0 }})
    # without not writting it explicitely in the template.
    forloop_counter0 = forms.IntegerField(min_value=0,
                                          widget=forms.HiddenInput())

def get_places_choices():
    not_stands = Place.objects.filter(is_stand=False)
    default_place = Preferences.objects.first().default_place
    ret = [ (default_place.id, default_place.name) ] + [ (p.id, p.name) for p in not_stands \
                                                         if not p.id == default_place.id]
    return ret

class DepositForm(forms.ModelForm):
    """Create a new deposit.
    """
    copies = forms.ModelMultipleChoiceField(Card.objects.all(),
                                            cache_choices=True,
                                            required=False)
    class Meta:
        model = Deposit
        fields = "__all__"
        # exclude = ["copies",]

class DepositAddCopiesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        pk = kwargs.pop('pk')
        super(self.__class__, self).__init__(*args, **kwargs)

        # Build fields depending on the deposit existing cards.
        dep = Deposit.objects.get(id=pk)
        cards = dep.copies.all()
        for card in cards:
            self.fields[str(card.id)] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min':0, 'max':MAX_COPIES_ADDITIONS,
                       'step':1, 'value': 0,
                       'style': 'width: 70px'}),
                                                           label=card.title)


def get_deposits_choices():
    choices = [(depo.name, depo.name) for depo in Deposit.objects.all()]
    return choices

class AddToDepositForm(forms.Form):
    """When we view our stock, choose to add the card to a deposit.
    """
    deposit = forms.ChoiceField(choices=get_deposits_choices(),
                                 label=_(u"Add to the deposit:"),
                                 required=False)

def get_bills_choices():
    bills = Bill.objects.all()
    ret = [(0, "---")] + [ (it.id, it.long_name) for it in bills]
    return ret

def get_reverse_url(cleaned_data, url_name="card_search"):
    """Get the reverse url with the query parameters taken from the
    form's cleaned data.

    query parameters:
    - source
    - q

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_reverse_url({"source": "chapitre", "q": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre

    """

    qparam = {}
    qparam['source'] = cleaned_data.get("source")
    if "q" in cleaned_data.keys():
        qparam['q'] = cleaned_data["q"]
    log.debug("on recherche: ", qparam)
    # construct the query parameters of the form
    # q=query+param&source=discogs
    params = urllib.urlencode(qparam)
    rev_url = reverse(url_name) + "?" + params
    return rev_url

def search_on_data_source(data_source, search_terms, PAGE=1):
    """search with the appropriate scraper.

    data_source is the name of an imported module.
    search_terms: list of strings.

    return: a couple (search results, stacktraces). Search result is a
    list of dicts.
    """
    # get the imported module by name.
    # They all must have a class Scraper.
    scraper = getattr(globals()[data_source], "Scraper")
    # res, traces = scraper(*search_terms).search()
    res, traces = scraper(search_terms, PAGE=PAGE).search()
    return res, traces

def postSearch(data_source, details_url):
    """Call the postSearch function of the module imported with the name
    of data_source.

    data_source: a scraper name, containing a function postSearch
    details_url: url of the card's details.

    return: a dict of results (for books, must have the isbn/ean).
    """
    try:
        # Allow a scraper not to have the postSearch method.
        res =  getattr(globals()[data_source], "postSearch")(details_url)
    except Exception as e:
        log.warning(e)
        res = {}
    return res

def _session_result_set(request, key, val):
    """Set request.session['search_result'][key] to val.

    Needed to mock for unit tests. Otherwise, during a test, the
    session remains a void list and we have a key error in the code below.
    """
    request.session['search_result'][key] = val

@login_required
def search(request):
    template = "search/searchresults.jade"
    return render(request, template)

@login_required
def card_show(request, pk):
    template = "search/card_show.jade"
    card = None
    sells = []
    total_sold = "---"
    if request.method == 'GET':
        card = Card.objects.get(id=pk)

        # Last time we entered this item
        last_entry = EntryCopies.last_entry(card)

        # Sells since the last entry
        if last_entry:
            sells = Sell.search(card.id, date_min=last_entry.created).order_by("-created")
            if sells and card:
                total_sold = Sell.nb_card_sold_in_sells(sells, card)

    return render(request, template, {
        "object": card,
        "sells": sells,
        "last_entry": last_entry,
        "total_sold": total_sold,
        })


class CardMoveForm(forms.Form):
    """We want to create a field for each Place and Basket object

    This approch is too much work to create a simple form. We want to
    write our form directly in a template instead, using angularjs
    calls to an api to fetch the places and baskets.
    """
    #XXX: replace these forms with a template and api calls.
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        model = "Place"
        query = models.__dict__[model].objects.all()
        for obj in query:
            self.fields[obj.name] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min':0, 'max':MAX_COPIES_ADDITIONS,
                       'step':1, 'value': 1,
                       'style': 'width: 70px'}))

class CardMove2BasketForm(forms.Form):
    # needs refacto etc… too complicating and unecessary.
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        model = "Basket"
        query = models.__dict__[model].objects.all()
        for obj in query:
            self.fields[obj.name] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min':0, 'max':MAX_COPIES_ADDITIONS,
                       'step':1, 'value': 0,
                       'style': 'width: 70px'}))

class CardMoveTypeForm(forms.Form):
    choices = [(1, "Pay these cards"),
               (2, "Add to a deposit"),
               (3, "Internal movement"),
               ]
    typ = forms.ChoiceField(choices=choices)
PAYMENT_MEANS = [
    (1, "cash"),
    (2, "credit card"),
    (3, "cheque"),
    (4, "gift"),
    (5, "lost"),
    ]

class BuyForm(forms.Form):
    payment = forms.ChoiceField(choices=PAYMENT_MEANS, label=_("Payment"))
    bill = forms.ChoiceField(choices=get_bills_choices(), label=_("Bill"))
    quantity = forms.FloatField(label=_("Quantity"))
    place  = forms.ChoiceField(choices=get_places_choices(), label=_("Place"))

class MoveDepositForm(forms.Form):
    choices = forms.ChoiceField(choices=get_deposits_choices())

class MoveInternalForm(forms.Form):
    origin = forms.ChoiceField(choices=get_places_choices())
    destination  = forms.ChoiceField(choices=get_places_choices())
    nb = forms.IntegerField()

@login_required
def card_buy(request, pk=None):
    form = BuyForm()
    template = "search/card_buy.jade"
    card = Card.objects.get(id=pk)
    form = BuyForm(initial={"quantity": 1})
    if request.method == 'GET':
        try:
            buying_price = card.price - (card.price * card.distributor.discount / 100)
        except Exception as e:
            buying_price = card.price

        return render(request, template, {
            "form": form,
            "card": card,
            "buying_price": buying_price,
            })

    if request.method == 'POST':
        # buying the card
        form = BuyForm(request.POST)
        if form.is_valid():
            place = form.cleaned_data['place']
            nb = form.cleaned_data['quantity']
            bill = form.cleaned_data['bill']
            payment = form.cleaned_data['payment']
            place_obj = Place.objects.get(id=place)
            if bill and bill != "0":
                bill_obj = Bill.objects.get(id=bill)
                # Link to the bill:
                try:
                    bill_obj.add_copy(card,nb=nb)
                except Exception as e:
                    log.error(e)

            # Add to the place
            try:
                place_obj.add_copy(card, nb=nb)
            except Exception as e:
                log.error("couldn't add copies to {}: {}".format(place, e))

            # Log in History:
            try:
                entry, created = Entry.new([card], payment=payment)
            except Exception as e:
                log.error("couldn't add Entry in history: {}".format(e))


            return HttpResponseRedirect(reverse("card_search"))

    return render(request, template, {
            "form": form,
            "card": card,
            "buying_price": buying_price,
            })

@login_required
def card_move(request, pk=None):
    template = "search/card_move.jade"
    BasketsForm = CardMove2BasketForm()
    internalForm = MoveInternalForm()
    params = request.GET

    if request.method == 'POST':
        placeForm = MoveInternalForm(request.POST)
        basketForm = CardMove2BasketForm(request.POST)

        if placeForm.is_valid() and basketForm.is_valid():
            card_obj = Card.objects.get(pk=pk)
            data = placeForm.cleaned_data
            if data['nb']:
                orig_obj = Place.objects.get(id=data['origin'])
                dest_obj = Place.objects.get(id=data['destination'])
                try:
                    orig_obj.move(dest_obj, card_obj, data['nb'])
                except Exception as e:
                    log.error("couldn't move copies from {} to {}: {}".format(data['origin'], data['destination'], e))

            for (basket, nb) in basketForm.cleaned_data.iteritems():
                if nb:
                    basket_obj = Basket.objects.get(name=basket)
                    try:
                        basket_obj.add_copy(card_obj, nb=nb)
                    except Exception as e:
                        log.error("couldn't add copies to {}: {}".format(basket, e))

            messages.add_message(request, messages.SUCCESS, _(u'The card "{}" was added successfully.'.format(card_obj.title)))
            # We can also retrieve the query parameters from the url:
            # url = request.META['HTTP_REFERER']
            # qparams = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            qparams = {'q': request.POST.get('q')}
            back_to = request.session.get("back_to", reverse("card_search"))
            # back_to += "?" + urlparse.urlsplit(url).query
            back_to += "?" + urllib.urlencode(qparams)
            # XXX back_to should be set more than once, per-search.
            if request.session.get("back_to"):
                del request.session["back_to"]
            return HttpResponseRedirect(back_to)

        else:
            # form not valid
            internalForm = MoveInternalForm(request.POST)

    # method: GET
    return render(request, template, {
        "BasketsForm": BasketsForm,
        "internalForm": internalForm,
        "pk": pk,
        "q": request.GET.get('q'),
        "type": params.get('type'),
        })


@login_required
def collection(request):
    """Search our own collection and take actions.

    - return: a list (of card dicts)
    """

    return render(request, "search/collection.jade")

@login_required
def sell(request):
    return render(request, "search/sell_create.jade")

@login_required
def sell_details(request, pk):
    template = "search/sell_details.jade"
    sell = None
    soldcards = []
    total_sell = None
    total_price_init = None

    if request.method == 'GET':
        try:
            sell = Sell.objects.get(id=pk)
        except Exception as e:
            log.error(e)
            #XXX return a 404

        if sell:
            soldcards = sell.soldcards_set.all()
            total_sell = sum([it.price_sold for it in soldcards])
            total_price_init = sum([it.price_init for it in soldcards])

    return render(request, template, {
        "sell": sell,
        "soldcards": soldcards,
        "total_sell": total_sell,
        "total_price_init": total_price_init,
        })

class InventoriesListView(ListView):
    model = Inventory
    template_name = "search/inventories.jade"
    context_object_name = "inventories"

class DepositsListView(ListView):
    model = Deposit
    template_name = "search/deposits.jade"
    context_object_name = "deposits"

    def get_context_data(self, **kwargs):
        """Give more context objects to the template.
        """
        context = super(DepositsListView, self).get_context_data(**kwargs)
        pubtype = Deposit.objects.filter(deposit_type="publisher").all()
        context["depo_pubtype"] = pubtype
        fixtype = Deposit.objects.filter(deposit_type="fix").all()
        context["depo_fix"] = fixtype
        context["total_price_fix"] = sum([it.total_init_price for it in fixtype])
        return context

#  # for a comparison:
# def deposits(request):
    # deposits = Deposit.objects.all()
    # return render(request, "search/deposits.jade", {
        # "deposits": deposits})

@login_required
def deposits_new(request):
    return render(request, "search/deposits_create.jade", {
        "DepositForm": DepositForm(),
        })

@login_required
def deposits_create(request):
    results = 200
    if request.method == "POST":
        req = request.POST.copy()
        form = DepositForm(req)
        if form.is_valid():
            deposit = form.cleaned_data
            try:
                msgs = Deposit.from_dict(deposit)
                for msg in msgs:
                    messages.add_message(request, msg["level"],
                                         msg["message"])
            except Exception as e:
                log.error("Error when creating the deposit: %s" % e)
                messages.add_message(request, messages.ERROR,
                                     _(u"Error when adding the deposit"))

        else:
            return render(request, "search/deposits_create.jade", {
                "DepositForm": form,
                })

    return redirect("/deposits/")  # should make status follow

@login_required
def deposits_add_card(request):
    """Add the given card (post) to the given deposit (in the form).
    """
    resp_status = 200
    req = request.POST.copy()
    form = AddToDepositForm(req)
    if request.method == "POST":
        if not form.is_valid():
            log.debug("deposits_add_card: form is not valid")
            resp_status = 500
        else:
            card_isbn = req["isbn"]
            if not card_isbn:
                log.debug("deposits_add_card: the isbn is null. That should not happen !")
                resp_status = 400
                messages.add_message(request, messages.ERROR,
                                     _(u"We could not add the card to the deposit: the given isbn is null."))
            else:
                deposit_id = form.cleaned_data["deposit"]
                # TODO: do the logic !
                messages.add_message(request, messages.SUCCESS,
                                     _(u'The card were successfully added to the deposit.'))

    retlist = request.session.get("collection_search")
    redirect_to = req.get('redirect_to')
    return redirect(redirect_to, status=resp_status)


@login_required
def deposits_view(request, pk):
    """Display the given deposit."""
    deposit = None
    copies = []
    template = "search/deposits_view.jade"
    try:
        deposit = Deposit.objects.get(pk=pk)
        copies = deposit.copies.all()

        deposit = Deposit.objects.get(id=pk)
        checkout, msgs = deposit.checkout_create()
        if not checkout:
            # Could do in a "get or create" method.
            checkout = deposit.last_checkout()

        if checkout and not checkout.closed:
            checkout.update()
        balance = checkout.balance()

    except Deposit.DoesNotExist as e:
        messages.add_message(request, messages.ERROR, _(u"This deposit doesn't exist !"))
        log.error("le depot demande (%s) n'existe pas: %s" % (pk, e))
        return HttpResponseRedirect(reverse("deposits"))

    return render(request, template, {
        "deposit": deposit,
        "copies": copies,
        "cards_balance": balance["cards"],
        "total": balance["total"],
        "created": checkout.created,
        "distributor": checkout.deposit.distributor,
    })

@login_required
def deposits_checkout(request, pk):
    """
    """
    template = "search/deposits_view.jade"
    deposit = Deposit.objects.get(pk=pk)
    msgs = []
    try:
        status, msgs = deposit.checkout_close()
        for msg in msgs:
            messages.add_message(request, messages.INFO, msg)
    except Exception as e:
        log.error("Error while closing deposing state: {}".format(e))
        messages.add_message(request, messages.ERROR,
                             _(u"Woops, there was an error :S we can't close this deposit state."))
        return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

    return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

@login_required
def deposit_delete(request, pk):
    """
    """
    pass

@login_required
def deposit_add_copies(request, pk):
    """Add copies to this deposit. (only ones that already exist)
    """
    template = "search/deposit_add_copies.jade"
    form = DepositAddCopiesForm(pk=pk)
    if request.method == "GET":
        pass

    if request.method == "POST":
        form = DepositAddCopiesForm(request.POST, pk=pk)
        if form.is_valid():
            data = form.cleaned_data
            dep = Deposit.objects.get(id=pk)
            for id, qty in data.iteritems():
                dep.add_copies([id], quantities=[qty])

            return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

    return render(request, template, {
        "form": form,
        "pk": pk,
        })

@login_required
def basket_auto_command(request):
    template = "search/basket_auto_command.jade"
    if request.method == "GET":
        return render(request, template)

class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    # taken from Django docs
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

@login_required
def baskets(request):
    template = "search/baskets.jade"
    if request.method == "GET":
        return render(request, template)

@login_required
def baskets_export(request):
    """Export as the required format: csv, pdf, pdf with barcode (todo),...

    - POST parameter: str of coma-separated ints. They represent
    tuples of a card id and its quantity. (use api.list_to_pairs and
    api.list_from_coma_separated_ints to get a list of tuples back)

    - layout: 'simple': only show isbns and quantities. 'complete':
      with title, authors, publishers etc; 'pdf': pdf with barcodes and quantity.

    Return: it returns raw data, either csv or pdf. The client side must handle its download.

    """

    params = request.body
    params = json.loads(params)
    layout = params.get('layout')
    ids_qties = params.get('ids_qties')
    list_name = params.get('list_name')
    tups = list_to_pairs(list_from_coma_separated_ints(ids_qties))
    tups = filter(lambda it: it is not None, tups)

    response = HttpResponse()

    try:
        template = get_template('pdftemplates/pdf-barcode.jade')

        cards_qties = [(Card.objects.get(id=tup[0]), tup[1]) for tup in tups]
        isbns_qties = [(tup[0].isbn, tup[1]) for tup in cards_qties]
        # Should warn about no isbn, also on client side.
        # Booklets, newspapers or even books can be without isbn in a normal situation.
        isbns_qties = filter(lambda it: it[0] is not None, isbns_qties)

        if layout == 'simple':
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer, delimiter=';')
            content = [writer.writerow(row) for row in isbns_qties]
            response = StreamingHttpResponse(content, content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        elif layout == 'txt':
            rows = [ u"{} {}".format( truncate(card.title), qty) for (card, qty) in cards_qties]
            content = "\n".join(rows)
            response = HttpResponse(content, content_type="text/raw")

        elif layout == 'pdf':
            # How to test that easily ?
            with open("pdfexport.pdf", "w+b") as resultFile:

                date = datetime.date.today()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

                cards = [it[0] for it in cards_qties]
                # the barcode generator doesn't accept None isbn.
                for card in cards:
                    if not is_isbn(card.isbn):
                        # XXX should return a message
                        card.isbn = "0000000000000"

                total = sum(map(lambda it: it[1] * it[0].price, cards_qties))
                total_qty = sum([it[1] for it in cards_qties])
                sourceHtml = template.render({'cards_qties': cards_qties,
                                              'list_name': list_name,
                                              'total': total,
                                              'total_qty': total_qty,
                                              'date': date})
                # convert to a pdf file
                # pisaStatus = pisa.CreatePDF(
                        # sourceHtml,                # the HTML to convert
                        # dest=response)           # file handle to recieve result

                pisaStatus = pisa.CreatePDF(
                        sourceHtml,
                        # outsource,                # the HTML to convert
                        # dest=resultFile)           # file handle to recieve result
                        dest=response)


    except Exception as e:
        log.error("Error while constructing {}: {}".format(layout, e))
        response.status_code = 500

    return response

@login_required
def inventory_list(request):
    """Display all the ongoing inventories.

    An inventory can happen for a place or for a shelf.
    """
    pass

@login_required
def inventories(request, pk):
    template = "search/inventory_view.jade"
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)
            except Exception as e:
                log.error(e)
            # state = inv.state()
            return render(request, template)

@login_required
def inventory_delete(request, pk):
    #XXX should be a post, but we're doing it from a button...
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)
                inv.delete()
            except Exception as e:
                log.error(e)

    return HttpResponseRedirect(reverse("inventories"))

@login_required
def inventory_terminate(request, pk):
    """
    """
    template = "search/inventory_terminate.jade"
    return render(request, template)

@login_required
def dashboard(request):
    template = "search/dashboard.jade"
    stats = Stats()
    stock = stats.stock()
    return render(request, template, {
        "stats_stock": stock,
        })
