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

import logging
import traceback
import urllib
import urlparse

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from djangular.forms import NgModelFormMixin
from unidecode import unidecode

# import datasources.all.discogs.discogsConnector as discogs
import datasources.all.discogs.discogsScraper as discogs
import datasources.deDE.buchwagner.buchWagnerScraper as buchWagner
import datasources.esES.casadellibro.casadellibroScraper as casadellibro
import datasources.frFR.chapitre.chapitreScraper as chapitre  # same name as module's SOURCE_NAME
import models
from models import Basket
from models import Card
from models import CardType
from models import Deposit
from models import DepositState
from models import Distributor
from models import Inventory
from models import Place
from models import Publisher
from models import Sell
from search.models.utils import ppcard
from search.models import EntryCopies

log = logging.getLogger(__name__)

MAX_COPIES_ADDITIONS = 10000  # maximum of copies to add at once
DEFAULT_NB_COPIES = 1         # default nb of copies to add.

# scraper names are the name of the imported module.
SCRAPER_CHOICES = [
    ("Book shops", (
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

class SearchForm(forms.Form):
    source = forms.ChoiceField(choices=SCRAPER_CHOICES,
                                        label=_(u'Data source'),
                                        # help_text='choose the data source for your query',
                                        )
    q = forms.CharField(max_length=100, required=False,
                        min_length=4,
                        label=_("Key words"),
                        help_text=_("Part of title, of author's name, etc."),
                    )
    ean = forms.CharField(required=False)

def get_card_type_choices():
    return [(0, _(u"All cards"))] + [(typ.id, typ.name)
                               for typ in CardType.objects.all()]

def get_publisher_choices():
    return [(0, _("All"))] + [(pub.id, pub.name)
                              for pub in Publisher.objects.all()]

class CollectionSearchForm(forms.Form):
    card_type = forms.ChoiceField(get_card_type_choices(),
                                  label=_("Type of card"),
                                  required=False)
    publisher = forms.ChoiceField(get_publisher_choices(),
                                  label=_("Publisher"),
                                  required=False)

    q = forms.CharField(max_length=100,
                        required=False,
                        min_length=3,
                        label=_(u"Search on title and authors."))

    ean = forms.CharField(required=False)


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
    distributor = forms.ChoiceField(choices=get_distributor_choices(),
                                    label=_(u"Distributor"),
                                    required=True)

def get_places_choices():
    not_stands = Place.objects.filter(is_stand=False)
    ret = [ (p.name, p.name) for p in not_stands]
    return ret

def get_distributor_choices():
    choices = [(dist.id, dist.name) for dist in Distributor.get_all()]
    return choices

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

def get_deposits_choices():
    choices = [(depo.name, depo.name) for depo in Deposit.objects.all()]
    return choices

class AddToDepositForm(forms.Form):
    """When we view our stock, choose to add the card to a deposit.
    """
    deposit = forms.ChoiceField(choices=get_deposits_choices(),
                                 label=_(u"Add to the deposit:"),
                                 required=False)


def get_reverse_url(cleaned_data, url_name="card_search"):
    """Get the reverse url with the query parameters taken from the
    form's cleaned data.

    query parameters:
    - source
    - q
    - ean

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_reverse_url({"source": "chapitre", "q": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre

    """

    qparam = {}
    qparam['source'] = cleaned_data.get("source")
    if "q" in cleaned_data.keys():
        qparam['q'] = cleaned_data["q"]
    if ("ean" in cleaned_data.keys()) and cleaned_data.get('ean'):
        qparam['ean'] = cleaned_data["ean"]
    log.debug("on recherche: ", qparam)
    # construct the query parameters of the form
    # q=query+param&source=discogs
    params = urllib.urlencode(qparam)
    rev_url = reverse(url_name) + "?" + params
    return rev_url

def search_on_data_source(data_source, search_terms):
    """search with the appropriate scraper.

    data_source is the name of an imported module.
    search_terms: list of strings.

    return: a couple (search results, stacktraces). Search result is a
    list of dicts.
    """
    # get the imported module by name.
    # They all must have a class Scraper.
    scraper = getattr(globals()[data_source], "Scraper")
    res, traces = scraper(*search_terms).search()
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

def index(request):
    form = SearchForm()
    page_title = ""
    data_source = SCRAPER_CHOICES[0][1][0][0]
    retlist = []
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("q") and request.POST["q"]:
                data_source = form.cleaned_data['source']
                rev_url = get_reverse_url(form.cleaned_data)
                page_title = "search index"
                # forward to search?q=query+parameters
                return HttpResponseRedirect(rev_url)

    return render(request, "search/search_result.jade", {
            "searchForm": form,
            "result_list": retlist,
            "data_source": data_source,
            "page_title": page_title,
            })

def _session_result_set(request, key, val):
    """Set request.session['search_result'][key] to val.

    Needed to mock for unit tests. Otherwise, during a test, the
    session remains a void list and we have a key error in the code below.
    """
    request.session['search_result'][key] = val

def search(request):
    retlist = []
    page_title = ""
    data_source = SCRAPER_CHOICES[0][1][0][0]
    query = ""
    ean_param = ""

    req = request.GET.copy()
    if not req.get('data_source'):
        req['data_source'] = data_source
    form = SearchForm(req)

    if request.method == 'GET' and form.is_valid():
        data_source = form.cleaned_data['source']
        query = form.cleaned_data.get('q')
        ean_param = form.cleaned_data.get('ean')
        if ean_param or query:
            if ean_param:
                search_terms = {"ean": ean_param}
                page_title = "search for %s on %s" % (ean_param, data_source)
            elif query:
                page_title = query[:50]
                search_terms = [q for q in query.split()]

            retlist, traces = search_on_data_source(data_source, search_terms)
            if not retlist:
                messages.add_message(request, messages.INFO, "Sorry, we didn't find anything with '%s'" % (query,))
            # if not request.session.get("search_result"):
            if not _request_session_get(request, "search_result"):
                request.session["search_result"] = {}
            # unidecode: transliteration from unicode to ascii (query will be in url)
            _session_result_set(request, unidecode(query), retlist)
            # request.session["search_result"][unidecode(query)] = retlist
            # This too, otherwise it doesn't stick in session["search_result"].
            request.session[unidecode(query)] = retlist
            _session_result_set(request, unidecode(query), retlist)
        else:
            # Uncomplete form (specify we need ean or q).
            log.error("form not complete")

    else:
        # POST or form not valid
        form = SearchForm()
        query = None
        ean_param = None
        # Re-display results of previous search.
        if "search_result" in request.session:
            url = request.META['HTTP_REFERER']
            qparams = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            query = qparams['q']
            # Get the last query of this page (case of parallell searches)
            retlist = request.session["search_result"][qparams['q']]

    return render(request, "search/search_result.jade", {
        "searchForm": form,
        "addForm": AddForm(),
        "result_list": retlist,
        "data_source": data_source,
        "page_title": page_title,
        "q": query,
        "ean": ean_param,
    })

def _request_session_get(request, key):
    """Gets the session's key.

    A function is needed to mock this call in unit tests (Django
    doesn't provide anything to use the session in tests).
    """
    return request.session.get(key)

def card_show(request, pk):
    template = "search/card_show.jade"
    card = None
    sells = []
    if request.method == 'GET':
        card = Card.objects.get(id=pk)
        sells = Sell.search(card.id, date_min=card.modified).order_by("-created")

        # Last time we entered this item
        last_entry = EntryCopies.last_entry(card)

    return render(request, template, {
        "object": card,
        "sells": sells,
        "last_entry": last_entry,
        })


def add(request):
    """Add the requested Card to the DB.

    Before adding it, we need to get the last information about the
    Card, the ones we couldn't get at the first scraping. We call the
    `postSearch` method of the scraper module. Sometimes it is the
    only way to get the ean (with only two http requests).

    The list of cards is stored in the session. The template only returns the list's indice.

    """
    card = {}
    resp_status = 200
    cur_search_result = _request_session_get(request, "search_result")
    req = request.POST.copy()
    form = AddForm(req)

    if not form.is_valid():
        resp_status = 400
        log.error("Addform isn't valid.")
        return HttpResponse(status=resp_status)

    else:
        # Get the last search results of the session:
        cur_search_result = _request_session_get(request, "search_result")
        # Get the results of the corresponding search.
        if req.get('q'):
            cur_search_result = cur_search_result.get(unidecode(req.get('q')))
        elif req.get('ean'):
            cur_search_result = cur_search_result.get(req.get('ean'))
        else:
            # The "q" should be following along, hidden in template or as url param.
            cur_search_result = cur_search_result.get(cur_search_result.keys()[-1])
        if not cur_search_result:
            log.debug("Error: the session has no search_result.")

        card = cur_search_result[form.cleaned_data["forloop_counter0"]]
        data_source = card["data_source"]

        # Call the postSearch method of the datasource module.
        if not card.get('ean') and not card.get('isbn'):
            if not data_source:
                log.debug("Error: the data source is unknown.")
                resp_status = 500
                # XXX return an error page
            else:
                # fire a new http request to get the ean (or other missing informations):
                complements = postSearch(data_source, card['details_url'])
                if not complements.get("isbn"):
                    log.warning("warning: postSearch couldnt get the isbn.")
                for k, v in complements.iteritems():
                    log.debug("postSearch: found %s: %s" % (k,v))
                    card[k] = v

        try:
            # Create the card. No quantity yet.
            card["distributor"] = form.cleaned_data.get("distributor")
            card_obj, msgs = Card.from_dict(card)
            for msg in msgs:
                messages.add_message(request, messages.INFO, msg)

            messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (card['title'],))

        except Exception, e:
            messages.add_message(request, messages.ERROR, u'"%s" could not be registered.' % (card['title'],))
            log.error("Error when trying to add card: {}".format(e))
            log.error(traceback.format_exc())
            resp_status = 500

        # the card_move view is used by two other views. Go back to the right one.
        request.session["back_to"] = reverse("card_search")
        url = reverse("card_move", args=(card_obj.id,))
        # Doesn't Django have an automatic way, really ?
        # see also our get_reverse_url(qparams, url=)
        # unidecode: transliterate unicode to ascii (unicode protection).
        qparams = {"q": unidecode(req.get('q')),
                   "ean": req.get('ean') }
        url = url + "?" + urllib.urlencode(qparams)

        return HttpResponseRedirect(url)

class CardMoveForm(forms.Form):
    """We want to create a field for each Place and Basket object

    This approch is too much work to create a simple form. We want to
    write our form directly in a template instead, using angularjs
    calls to an api to fetch the places and baskets.
    """
    #TODO: replace these forms with a template and api calls.
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

class BuyForm(forms.Form):
    buy = forms.BooleanField(required=False)

def card_move(request, pk=None):
    template = "search/card_move.jade"
    PlacesForm = CardMoveForm()
    BasketsForm = CardMove2BasketForm()
    buyForm = BuyForm()

    if request.method == 'GET':
        return render(request, template, {
            "PlacesForm": PlacesForm,
            "BasketsForm": BasketsForm,
            "BuyForm": buyForm,
            "pk": pk,
            "q": request.GET.get('q'),
            "ean": request.GET.get('ean'),
            })

    if request.method == 'POST':
        placeForm = CardMoveForm(request.POST)
        basketForm = CardMove2BasketForm(request.POST)
        # buyForm = BuyForm(request.POST)

        if placeForm.is_valid() and basketForm.is_valid():
            card_obj = Card.objects.get(pk=pk)
            for (place, nb) in placeForm.cleaned_data.iteritems():
                if nb:
                    place_obj = Place.objects.get(name=place)
                    try:
                        place_obj.add_copy(card_obj, nb=nb)
                    except Exception as e:
                        log.error("couldn't add copies to {}: {}".format(place, e))

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

def collection(request):
    """Search our own collection and take actions.
    """
    form = CollectionSearchForm()
    retlist = []
    cards = []

    if request.method == "POST":
        form = CollectionSearchForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("ean") and \
               form.cleaned_data.get("ean"):
                messages.add_message(request, messages.INFO,
                                     _(u"The search by ean isn't implemented yet."))
                log.debug("TODO: search on ean")

            else:
                card_type_id = form.cleaned_data.get("card_type")
                if card_type_id:
                    card_type_id = int(card_type_id)
                publisher_id = form.cleaned_data.get("publisher")
                if publisher_id:
                    publisher_id = int(publisher_id)
                words = form.cleaned_data.get("q").split()
                cards = Card.search(words,
                                    card_type_id=card_type_id,
                                    publisher_id=publisher_id,
                                    to_list=True)
                # store results in session for later re-use
                request.session["collection_search"] = cards


    else:
        # GET
        # Get the last new cards of the database.
        cards = Card.first_cards(50)
        cards = Card.obj_to_list(cards)

        if request.GET.get("format") == "text":
            response = HttpResponse(ppcard(cards),
                                    content_type="text/plain;charset=utf-8")
            return response

    return render(request, "search/collection.jade", {
            "searchForm": form,
            "nb_results": len(cards),
            "total_results": Card.objects.count(),
            "book_list": cards,
            "AddToDepositForm": AddToDepositForm,
            })

# def sell(request):
#     form = CollectionSearchForm()
#     req = request.POST
#     if not req.get("id"):
#         message = u"Erreur: cette notice n'existe pas."
#         level = messages.ERROR
#     else:
#         ret, msg = Card.sell(id=req['id'])
#         if ret:
#             message = u"La vente de %s est bien enregistrée." % (req.get('title'),)
#             level = messages.SUCCESS
#         else:
#             message = u"La vente a échoué. %s" % msg
#             level = messages.ERROR

#     messages.add_message(request, level, message)
#     return render(request, 'search/index.jade', {
#                   'searchForm': form
#                   })

def sell(request):
    return render(request, "search/sell_create.jade")

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

def deposits_new(request):
    return render(request, "search/deposits_create.jade", {
        "DepositForm": DepositForm(),
        })

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
            card_ean = req["ean"]
            if not card_ean:
                log.debug("deposits_add_card: the ean is null. That should not happen !")
                resp_status = 400
                messages.add_message(request, messages.ERROR,
                                     _(u"We could not add the card to the deposit: the given ean is null."))
            else:
                deposit_id = form.cleaned_data["deposit"]
                # TODO: do the logic !
                messages.add_message(request, messages.SUCCESS,
                                     _(u'The card were successfully added to the deposit.'))

    retlist = request.session.get("collection_search")
    redirect_to = req.get('redirect_to')
    return redirect(redirect_to, status=resp_status)


def deposits_view(request, depo_name):
    """Display the given deposit."""
    deposit = None
    copies = []
    template = "search/deposits_view.jade"
    try:
        deposit = Deposit.objects.get(pk=depo_name)
        copies = deposit.copies.all()
    except Deposit.DoesNotExist as e:
        messages.add_message(request, messages.ERROR, _(u"This deposit doesn't exist !"))
        log.error("le depot demande (%s) n'existe pas: %s" % (depo_name, e))

    return render(request, template, {
        "deposit": deposit,
        "copies": copies,
    })

def deposits_checkout(request, pk):
    """Create a DepositState for the given deposit (of id "pk).
    """
    template = "search/deposits_checkout.jade"
    checkout = None

    if request.method == 'GET':
        deposit = Deposit.objects.get(id=pk)
        checkout, msgs = deposit.checkout_create()
        if not checkout:
            # Could do in a "get or create" method.
            checkout = deposit.last_checkout()
        if not checkout.closed:
            checkout.update()
        balance = checkout.balance()
    return render(request, "search/deposit_checkout.jade", {
        "cards_balance": balance["cards"],
        "total": balance["total"],
        "created": checkout.created,
        "distributor": checkout.deposit.distributor,
        })

def basket_auto_command(request):
    template = "search/basket_auto_command.jade"
    auto_command_nb = Basket.auto_command_nb()
    if request.method == "GET":
        basket = Basket.objects.get(name="auto_command")
        cards = basket.copies.all()
        return render(request, template, {
            "basket": basket,
            "cards": cards,
            "auto_command_nb": auto_command_nb,
        })

def inventory_list(request):
    """Display all the ongoing inventories.

    An inventory can happen for a place or for a shelf.
    """
    pass
