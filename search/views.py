# -*- coding: utf-8 -*-
# Copyright 2014 - 2017 The Abelujo Developers
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

import datetime
import urllib

import unicodecsv
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.views.generic import ListView
from weasyprint import HTML

#
# The datasources imports must have the name as their self.SOURCE_NAME
# Also add the search engine in the client side controller.
#
from search.datasources.bookshops.all.discogs import discogsScraper as discogs  # noqa: F401
from search.datasources.bookshops.all.momox import momox  # noqa: F401
from search.datasources.bookshops.deDE.buchlentner import buchlentnerScraper as buchlentner  # noqa: F401
from search.datasources.bookshops.esES.casadellibro import casadellibroScraper as casadellibro  # noqa: F401
from search.datasources.bookshops.frFR.decitre import decitreScraper as decitre  # noqa: F401
from search.datasources.bookshops.frFR.librairiedeparis import librairiedeparisScraper as librairiedeparis  # noqa: F401


import models
from search.models import Barcode64
from search.models import Basket
from search.models import Bill
from search.models import Card
from search.models import Command
from search.models import Deposit
from search.models import Distributor
from search.models import Inventory
from search.models import InventoryCommand
from search.models import Place
from search.models import Preferences
from search.models import Publisher
from search.models import Sell
from search.models import Stats
from search.models import Entry
from search.models import EntryCopies
from search.models.api import _get_command_or_return
from search.models.utils import _is_truthy
from search.models.utils import get_logger
from search.models.utils import is_isbn
from search.models.utils import ppcard
from search.models.utils import truncate

from views_utils import Echo
from views_utils import cards2csv

log = get_logger()

MAX_COPIES_ADDITIONS = 10000  # maximum of copies to add at once
DEFAULT_NB_COPIES = 1         # default nb of copies to add.


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
    preferences = Preferences.objects.first()
    ret = []
    if preferences:
        default_place = preferences.default_place
        ret = [(default_place.id, default_place.name)] + [(p.id, p.name) for p in not_stands
                                                          if not p.id == default_place.id]
    return ret

def get_suppliers_choices():
    res = Distributor.objects.order_by("-name").all()
    res = [(it.id, it.__repr__()) for it in res]
    return res

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
        cards = dep.copies()
        for card in cards:
            self.fields[str(card.id)] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 0,
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
    ret = [(0, "---")] + [(it.id, it.long_name) for it in bills]
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
    # construct the query parameters of the form
    # q=query+param&source=discogs
    params = urllib.urlencode(qparam)
    rev_url = reverse(url_name) + "?" + params
    return rev_url

@login_required
def preferences(request):
    """
    """
    template = "search/preferences.jade"
    return render(request, template)

def postSearch(data_source, details_url):
    """Call the postSearch function of the module imported with the name
    of data_source.

    data_source: a scraper name, containing a function postSearch
    details_url: url of the card's details.

    return: a dict of results (for books, must have the isbn/ean).
    """
    try:
        # Allow a scraper not to have the postSearch method.
        res = getattr(globals()[data_source], "postSearch")(details_url)
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
    places = Place.objects.order_by("id").all()
    places_quantities = []
    total_sold = "0"
    if request.method == 'GET':
        card = get_object_or_404(Card, id=pk)

        # Ongoing commands.
        pending_commands = card.commands_pending()

        # Last time we entered this item
        last_entry = EntryCopies.last_entry(card)

        # Quantity per place.
        for place in places:
            places_quantities.append((place.name,
                                      place.quantity_of(card)))

        # Sells since the last entry
        if last_entry:
            res = Sell.search(card.id, date_min=last_entry.created)
            total_sold = res['nb_cards_sold']

    return render(request, template, {
        "object": card,
        "sells": sells,
        "places_quantities": places_quantities,
        "last_entry": last_entry,
        "total_sold": total_sold,
        "pending_commands": pending_commands,
        "page_title": u"Abelujo - " + card.title[:50],
    })

def card_history(request, pk):
    """Show the card's sells, entries and commands history."""
    MAX = 50
    card = None
    template = "search/card_history.jade"

    if request.method == 'GET':
        card = get_object_or_404(Card, pk=pk)

        # Sells
        sells = Sell.search(card.id)

        # OutMovements
        # TODO: get all out movements
        # outmovement_set: direct link
        # outmovementcopies_set: linked from baskets
        outs = card.outmovementcopies_set.order_by("-created").all()[:MAX]

        # Commands
        pending_commands = card.commands_pending()
        commands = card.commands_received()

    return render(request, template, {
        "card": card,
        "sells": sells,
        "outs": outs,
        "pending_commands": pending_commands,
        "commands": commands,
        "page_title": u"Abelujo - {} - {}".format(_("History"), card.title),
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
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 1,
                       'style': 'width: 70px'}))


class CardMove2BasketForm(forms.Form):
    # needs refacto etc… too complicating and unecessary.
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        model = "Basket"
        query = models.__dict__[model].objects.all()
        for obj in query:
            self.fields[obj.name] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 0,
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
    place = forms.ChoiceField(choices=get_places_choices(), label=_("Place"))


class MoveDepositForm(forms.Form):
    choices = forms.ChoiceField(choices=get_deposits_choices())


class CardPlacesAddForm(forms.Form):
    """
    Add exemplaries to some Places, from the Card view.
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        for place in Place.objects.order_by("id").all():
            self.fields[place.id] = forms.IntegerField(required=False, label=place.name)


class MoveInternalForm(forms.Form):
    nb = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields['origin'] = forms.ChoiceField(choices=get_places_choices())
        self.fields['destination'] = forms.ChoiceField(choices=get_places_choices())


class SetSupplierForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields['supplier'] = forms.ChoiceField(choices=get_suppliers_choices())


class NewSupplierForm(forms.Form):
    name = forms.CharField()
    discount = forms.IntegerField(label=_("discount"))


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
                    bill_obj.add_copy(card, nb=nb)
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
def card_places_add(request, pk=None):
    """
    Add the given card to Places.
    """
    template = "search/card_places_add.jade"
    params = request.GET

    if request.method == 'GET':
        form = CardPlacesAddForm()
        return render(request, template, {
            "form": form,
            "pk": pk,
            "type": params.get('type'),
        })

    else:
        back_to = reverse("card_show", args=(pk,))
        form = CardPlacesAddForm(request.POST)
        if form.is_valid():
            for (id, nb) in form.data.iteritems():  # cleaned_data won't have nothing...
                if nb:
                    place = Place.objects.get(id=id)
                    if place:
                        card = Card.objects.get(id=pk)
                        try:
                            place.add_copy(card, nb=int(nb))
                        except Exception as e:
                            log.error("Adding Card {} to Place {}: if this happens, that's because of lacking form validation ! {}".format(pk, id, e))

        return HttpResponseRedirect(back_to)


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
            back_to = request.session.get("back_to")
            if not back_to:
                back_to = reverse("card_show", args=(pk,))
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
def cards_set_supplier(request, **kwargs):
    template = 'search/set_supplier.jade'
    form = SetSupplierForm()
    newsupplier_form = NewSupplierForm()
    cards_ids = request.session.get('set_supplier_cards_ids')
    if not cards_ids:
        return HttpResponseRedirect(reverse('card_collection'))
    cards_ids = cards_ids.split(',')
    response_dict = {
        'form': form,
        'newsupplier_form': newsupplier_form,
        'nb_cards': len(cards_ids),
    }

    if request.method == 'GET':
        return render(request, template, response_dict)

    elif request.method == 'POST':
        dist_id = None
        dist_obj = None
        req = request.POST.copy()

        # The user chose an existing distributor.
        if 'supplier' in req.keys():
            form = SetSupplierForm(req)
            if form.is_valid():
                dist_id = form.cleaned_data['supplier']
                dist_obj = Distributor.objects.get(id=dist_id)

        # Create distributor.
        elif 'discount' in req.keys():
            form = NewSupplierForm(req)
            if form.is_valid():
                data = form.cleaned_data

                # Check existing name.
                existing = Distributor.objects.filter(name=data['name'])
                if existing:
                    messages.add_message(request, messages.ERROR, _("A supplier with the same name already exists."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

                try:
                    dist_obj = Distributor(name=data['name'], discount=data['discount'])
                    dist_obj.save()
                except Exception as e:
                    log.error(u"Could not create new distributor: {}".format(e))
                    messages.add_message(request, messages.ERROR, _("An internal error occured, we have been notified."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

            else:
                messages.add_message(request, messages.ERROR, _("The form is invalid."))
                return render(request, template, response_dict)

        else:
            log.error(u"Error in the form setting the supplier for many cards")
            return render(request, template, response_dict)

        # Set supplier for all cards.
        for id in cards_ids:
            try:
                card = Card.objects.get(id=id)
                card.distributor = dist_obj
                card.save()
            except Exception as e:
                log.error(u"Error batch-setting the distributor: {}".format(e))
                messages.add_message(request, messages.ERROR, _("Internal error :("))
                response_dict['messages'] = messages.get_messages(request)
                return render(request, template, response_dict)

        messages.add_message(request, messages.SUCCESS, _("The supplier was correctly set for those {} cards.".format(len(cards_ids))))

        return HttpResponseRedirect(reverse('card_collection'))


@login_required
def collection_export(request, **kwargs):
    """Export a search of our stock or all of it.

    - format: text, csv.
    - select: all, selection.
    """
    if request.method == 'GET':
        formatt = request.GET.get('format')
        select = request.GET.get('select')
        query = request.GET.get('query')
        distributor = request.GET.get("distributor")
        distributor_id = request.GET.get("distributor_id")
        card_type_id = request.GET.get("card_type_id")
        publisher_id = request.GET.get("publisher_id")
        place_id = request.GET.get("place_id")
        shelf_id = request.GET.get("shelf_id")
        order_by = request.GET.get("order_by")
        # bought = request.GET.get("in_stock")

        # Export all the stock or a custom search ?
        # would rather validate request.GET and **
        # or call api's cards search and get the json.
        if select == "selection":
            query_list = query.split(" ")
            res, meta = Card.search(query_list, to_list=True,
                                    distributor=distributor,
                                    distributor_id=distributor_id,
                                    publisher_id=publisher_id,
                                    card_type_id=card_type_id,
                                    place_id=place_id,
                                    shelf_id=shelf_id,
                                    order_by=order_by,
                                    in_deposits=True)

        elif select == "all":
            # res = Card.objects.filter(in_stock=True).all()
            res = Card.cards_in_stock()

        # Which format ?
        if formatt == 'txt':
            content_type = "text/raw"
            content = ppcard(res)

        elif formatt == "csv":
            content_type = "text/csv"
            cards = [it.to_list() for it in res]
            content = cards2csv(cards)

        else:
            content = "This format isn't supported."

        # Build the response.
        response = HttpResponse(content, content_type=content_type)
        filename = u"Abelujo stock search"
        if query:
            filename += " - {}".format(query)

        response['Content-Disposition'] = u'attachment; filename="{}.{}"'.format(filename, formatt)
        return response

    else:
        content = "no search query"

    return HttpResponse(content, content_type=content_type)

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
        # context["total_price_fix"] = sum([it.total_init_price for it in fixtype])
        context["total_price_fix"] = -1
        context["page_title"] = "Abelujo - " + _("Deposits")
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
    # results = 200
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
                deposit_id = form.cleaned_data["deposit"]  # noqa: F841
                # TODO: do the logic !
                messages.add_message(request, messages.SUCCESS,
                                     _(u'The card were successfully added to the deposit.'))

    retlist = request.session.get("collection_search")  # noqa: F841
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
        cards_balance = deposit.checkout_balance()

    except Deposit.DoesNotExist as e:
        messages.add_message(request, messages.ERROR, _(u"This deposit doesn't exist !"))
        log.error("le depot demande (%s) n'existe pas: %s" % (pk, e))
        return HttpResponseRedirect(reverse("deposits"))

    return render(request, template, {
        "page_title": "Abelujo - " + deposit.name,
        "deposit": deposit,
        "cards_balance": cards_balance,
    })

@login_required
def deposits_checkout(request, pk):
    """
    """
    # template = "search/deposits_view.jade"
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
    template = "search/to_command.jade"
    if request.method == "GET":
        return render(request, template)

@login_required
def baskets(request):
    template = "search/baskets.jade"
    if request.method == "GET":
        return render(request, template)

@login_required
def basket_list(request):
    """
    Simple list of baskets. Vue stuff only on a basket page.
    """
    template = 'search/basket_list.html'
    if request.method == "GET":
        baskets = Basket.objects.all()[1:]  # not the auto_command
        return render(request, template, {
            'baskets': baskets,
        })

@login_required
def basket_view(request, pk):
    template = 'search/basket_view.html'
    if request.method == "GET":
        basket = Basket.objects.get(pk=pk)
        return render(request, template, {
            'basket': basket,
        })

@login_required
def basket_export(request, pk):
    """Export the given basket to txt, csv or pdf, with or without barcodes.

    Possible GET parameters:
    - report: bill, listing, simplelisting
    - format: txt, pdf, csv
    - distributor_id: a distributor id (see To Command basket)

    Return: an HttpResponse with the right content type.
    """
    response = HttpResponse()

    try:
        basket = Basket.objects.get(id=pk)
    except Exception as e:
        log.error(u"Error trying to export basket{}: {}".format(pk, e))
        return response

    copies_set = basket.basketcopies_set.all()

    report = request.GET.get('report')
    format = request.GET.get('format')
    distributor_id = request.GET.get('distributor_id')
    # Export of all cards: distributor_id is None.
    # Export of cards with no distributor_id:
    if distributor_id == 'undefined' or distributor_id in ["", u""]:
        distributor_id = -1
    elif distributor_id:
        distributor_id = int(distributor_id)

    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))

    if copies_set and report and format:
        response = _export_response(copies_set, report=report, format=format,
                                    distributor_id=distributor_id,
                                    barcodes=barcodes,
                                    covers=covers,
                                    name=basket.name)

    return response

def _export_response(copies_set, report="", format="", inv=None, name="", distributor_id=None,
                     covers=False,
                     barcodes=False):
    """Build the response with the right data (a bill ? just a list ?).

    - copies_set: list of objects, like basketcopies_set: has attributes card and quantity.
    - inv: inventory object (necessary to get the diff and the sold cards).

    Return: formatted HttpResponse
    """
    response = HttpResponse()
    quantity_header = _("Quantity")
    rows = None

    if distributor_id == -1:
        # get the ones without dist
        copies_set = filter(lambda it: it.card.has_no_distributor(), copies_set)

    elif distributor_id is not None and distributor_id not in ["", u""]:
        copies_set = filter(lambda it: it.card.has_distributor(distributor_id), copies_set)

    if report == 'bill':
        # The cards of the inventory alongside their quantities.
        if inv:
            header = (_("Title"), _("Quantity sold"))
            diff = inv.diff()[0]  # that should be cached XXX. A json row in the db ?
            rows = []
            for k in diff.itervalues():
                if k.get('diff', 0) < 0:
                    qtysold = - k.get('diff')
                else:
                    qtysold = 0
                rows.append((k['card'], qtysold))

            # Sort quantities first, then by title.
            rows = sorted(rows)
            rows = sorted(rows, key = lambda it: it[1] > 0, reverse=True)  # with quantities first

        else:
            log.eror("Implementation error: if you want a bill, that's certainely from an inventory, but we don't have the 'inv' object.")

    elif report == 'listing':
        # inv_cards = inv.inventorycopies_set.all()
        header = (_("Title"), _("Authors"), _("Publishers"), _("Shelf"), _("Price"), _("Quantity"))
        rows = [
            (ic.card.title,
             ic.card.authors_repr,
             ic.card.pubs_repr,
             ic.card.shelf.name if ic.card.shelf else "",
             ic.card.price,
             ic.quantity)
            for ic in copies_set]
        rows = sorted(rows)

    elif report == 'simplelisting':
        header = None
        rows = copies_set
        rows = [
            (ic.card.isbn,
             ic.quantity)
            for ic in rows]
        rows = sorted(rows)

    # From here we have rows: list of tuples with the card obj and the quantity.
    if rows is None:
        log.error("No rows when exporting to file. Shouldn't happen !")

    if format in ['csv']:
        pseudo_buffer = Echo()
        writer = unicodecsv.writer(pseudo_buffer, delimiter=';')
        content = writer.writerow("")

        if report in ['bill']:
            rows = [(it[0].title, it[1]) for it in rows]
        if header:
            rows.insert(0, header)
        content = "".join([writer.writerow(row) for row in rows])

        response = StreamingHttpResponse(content, content_type="text/csv")
        response['Content-Disposition'] = u'attachment; filename="{}.csv"'.format(name)

    elif format in ['txt']:
        # 63 = MAX_CELL + 3 because of trailing "..."
        rows = [u"{:63} {:20} {}".format(truncate(it.card.title),
                                         it.card.pubs_repr,
                                         it.quantity) for it in copies_set]
        rows = sorted(rows)
        content = "\n".join(rows)
        response = HttpResponse(content, content_type="text/raw")

    elif format in ['pdf']:
        date = datetime.date.today()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = u'attachment; filename="{}.pdf"'.format(name)

        template = get_template('pdftemplates/pdf-barcode.jade')
        if report == "listing":
            cards_qties = [(it.card, it.quantity) for it in copies_set]
        elif report == "bill":
            quantity_header = _("Quantity sold")
            for it in rows:
                if not is_isbn(it[0].isbn):
                    it[0].isbn = "0000000000000"

            cards_qties = rows

        total = sum(map(lambda it: it[1] * it[0].price if it[0].price else 0, cards_qties))
        total_qty = sum([it[1] for it in cards_qties])

        # barcode
        import time
        start = time.time()
        if barcodes:
            for card, __ in cards_qties:
                # Find or create the base64 barcode.
                search = Barcode64.objects.filter(ean=card.ean)
                if not search:
                    eanbase64 = Barcode64.ean2barcode(card.ean)
                    try:
                        if eanbase64:
                            log.info("---- saving a base64 for ean {}".format(card.ean))
                            Barcode64(ean=card.ean, barcodebase64=eanbase64).save()
                    except Exception as e:
                        log.error(u'Error saving barcode of ean {}: {}'.format(card.ean, e))
                else:
                    eanbase64 = search[0].barcodebase64

                card.eanbase64 = eanbase64

        sourceHtml = template.render({'cards_qties': cards_qties,
                                      'list_name': name,
                                      'total': total,
                                      'total_qty': total_qty,
                                      'barcode': barcodes,
                                      'covers': covers,
                                      'quantity_header': quantity_header,
                                      'date': date})

        genstart = time.time()
        outhtml = HTML(string=sourceHtml).write_pdf()
        genend = time.time()
        log.info("------ html generation is taking {}".format(genend - genstart))

        response = HttpResponse(outhtml, content_type='application/pdf')
        end = time.time()
        log.info("-------- generating barcodes for {} cards took {}".format(len(cards_qties), end - start))
        response['Content-Disposition'] = u'attachment; filename="{}.pdf"'.format(name)

    return response

def history_sells_exports(request, **kwargs):
    """Export a list of Sells in csv or txt.
    If no date nor distributor is given, export the first 50 results.

    - month: int (starting at 1 for python, when it starts at 0 in js)
    - year: int
    - distributor_id: int

    Return: a StreamingHttpResponse with the right content_type.
    """
    params = request.GET.copy()
    outformat = params.get('format')
    params.pop('format')
    month = params.get('month', timezone.now().month)
    year = params.get('year', timezone.now().year)
    distributor_id = params.get('distributor_id')
    filename = _(u"Sells history")
    if year:
        filename += " - {}".format(year)
    if month:
        filename += "-{}".format(month)

    response = None
    res = Sell.search(to_list=True,
                      distributor_id=distributor_id,
                      month=month,
                      year=year)
    # total = res.get('total')
    res = res['data']

    if outformat in ['csv']:
        pseudo_buffer = Echo()
        writer = unicodecsv.writer(pseudo_buffer, delimiter=';')
        content = writer.writerow("")

        rows = [(it['created'],
                 it['sell_id'],
                 it['price_sold'],
                 it['card']['title'],
                 it['card']['distributor']['name'] if it['card']['distributor'] else "",
                )
                for it in res]
        header = (_("date sold"),
                  _("sell id"),
                  _("price sold"),
                  _("title"),
                  _("supplier"),
        )
        rows.insert(0, header)
        content = "".join([writer.writerow(row) for row in rows])

        response = StreamingHttpResponse(content, content_type="text/csv")
        response['Content-Disposition'] = u'attachment; filename="{}.csv"'.format(filename)

    elif outformat in ['txt']:
        rows = [u"{}-+-{}-+-{}-+-{}-+-{}".format(
            _("date sold"),
            _("sell id"),
            _("price sold"),
            _("title"),
            _("supplier"),
        )]
        # format: {:min width.truncate}
        # https://pyformat.info/
        rows += sorted([u"{:10.10} {} {:5} {:30} {}".format(
            it['created'],
            it['sell_id'],
            it.get('price_sold', 0),
            truncate(it['card']['title']),  # truncate long titles
            it['card']['distributor']['name'] if it['card']['distributor'] else "",
        )
                        for it in res])
        content = "\n".join(rows)
        response = HttpResponse(content, content_type="text/raw")
        response['Content-Disposition'] = u'attachment; filename="{}.txt"'.format(filename)

    return response

@login_required
def inventory_export(request, pk):
    try:
        inv = Inventory.objects.get(id=pk)
    except Exception as e:
        log.error(u"Error trying to export inventory of pk {}: {}".format(pk, e))

    copies_set = inv.inventorycopies_set.all()

    report = request.GET.get('report')
    format = request.GET.get('format')
    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))

    response = _export_response(copies_set, report=report, format=format,
                                inv=inv,
                                barcodes=barcodes,
                                covers=covers,
                                name=inv.name)

    return response

@login_required
def inventories(request):
    """Get all inventories.
    """
    template = "search/inventories.jade"
    if request.method == 'GET':
        return render(request, template)

@login_required
def inventory(request, pk):
    template = "search/inventory_view.jade"
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)  # noqa: F841
            except Exception as e:
                log.error(e)
            # state = inv.state()
            return render(request, template)

@login_required
def inventory_delete(request, pk):
    #XXX should be a post
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
    stock = Stats.stock()
    return render(request, template, {
        "stats_stock": stock,
    })


class CommandDetailView(DetailView):
    model = Command
    template_name = "search/commands_view.jade"


@login_required
def command_receive(request, pk):
    """
    GET: get the inventory state for this command.
    POST: create a new one.
    """
    template = "search/command_receive.jade"
    cmd = None

    try:
        cmd = Command.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        log.warning(e)
        messages.add_message(request, messages.ERROR,
                             u"Internal erorr: the command you requested does not exist.")
        return HttpResponseRedirect(reverse("commands_view", args=(pk,)))

    if not cmd.inventory:
        inv = InventoryCommand()
        inv.save()
        cmd.inv = inv
        cmd.save()

    return render(request, template)


@login_required
def command_receive_terminate(request, pk):
    """
    """
    template = "search/inventory_terminate.jade"
    return render(request, template)


@login_required
def command_receive_export(request, pk):
    cmd = _get_command_or_return(pk)
    inv = cmd.get_inventory()
    copies_set = inv.copies_set.all()
    inv_name = inv.name or inv.command.title

    report = request.GET.get('report')
    format = request.GET.get('format')
    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))

    response = _export_response(copies_set, report=report, format=format,
                                inv=inv,
                                barcodes=barcodes,
                                covers=covers,
                                name=inv_name)

    return response
