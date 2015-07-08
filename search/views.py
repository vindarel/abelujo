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

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.detail import DetailView

import datasources.all.discogs.discogsConnector as discogs
import datasources.frFR.chapitre.chapitreScraper as chapitre # same name as module's SOURCE_NAME
import datasources.deDE.buchwagner.buchWagnerScraper as buchWagner
import datasources.esES.casadellibro.casadellibroScraper as casadellibro

from models import Basket
from models import Card
from models import CardType
from models import Deposit
from models import DepositState
from models import Distributor
from models import Inventory
from models import Place

from search.models.utils import ppcard

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
                                        label='Data source',
                                        # help_text='choose the data source for your query',
                                        )
    q = forms.CharField(max_length=100, required=False,
                        min_length=4,
                        label="key words",
                        help_text="Partie du titre, nom de l'auteur, etc.",
                    )
    ean = forms.CharField(required=False)

def get_card_type_choices():
    return [(0, "Tout")] + [(typ.id, typ.name)
                           for typ in CardType.objects.all()]

class CollectionSearchForm(forms.Form):
    card_type = forms.ChoiceField(get_card_type_choices(),
                                  label="Type de notice",
                                  required=False)
    q = forms.CharField(max_length=100,
                        required=False,
                        min_length=3,
                        label="Mots-clefs")

    ean = forms.CharField(required=False)


class MyNumberInput(TextInput):
    # render an IntegerField with a "number" html5 widget, not text.
    input_type = 'number'


def get_basket_choices():
    # TODO: make list dynamic + query in class.
    return [(0, "Aucun panier")] + [(basket.id, basket.name)
                                    for basket in Basket.objects.all()]


class AddForm(forms.Form):
    """The form populated when the user clicks on "add this card"."""
    # The search is saved to the session so we need to get the element we want: hence the for counter.
    # We couldn't find how to populate its value (which is {{ forloop.counter0 }})
    # without not writting it explicitely in the template.
    forloop_counter0 = forms.IntegerField(min_value=0,
                                          widget=forms.HiddenInput())
    # How many copies ?
    quantity = forms.IntegerField(widget = MyNumberInput(attrs={'min':0, 'max':MAX_COPIES_ADDITIONS,
                                                                'step':1, 'value':DEFAULT_NB_COPIES,
                                                                'style':"width: 70px"}))
    basket = forms.ChoiceField(choices=get_basket_choices(),
                               label="Ajouter la notice au panier (optionnel)",
                               required=False)


def get_places_choices():
    not_stands = Place.objects.filter(is_stand=False)
    ret = [ (p.name, p.name) for p in not_stands]
    return ret

def get_distributor_choices():
    choices = [(dist.id, dist.name) for dist in Distributor.get_from_kw()]
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
                                 label=u"Ajouter au depot:",
                                 required=False)


def get_reverse_url(cleaned_data, url_name="card_search"):
    """ Get the reverse url with the query parameters taken from the form's cleaned data.

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_reverse_url({"source": "chapitre", "q": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre
    """

    qparam = {}
    qparam['source'] = cleaned_data.get("source")
    if "q" in cleaned_data.keys():
        qparam['q'] = cleaned_data["q"]
    if "ean" in cleaned_data.keys():
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
    """
    return getattr(globals()[data_source], "postSearch")(details_url)

def index(request):
    form = SearchForm()
    page_title = ""
    data_source = SCRAPER_CHOICES[0][0][0]
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




def search(request):
    retlist = []
    page_title = ""
    data_source = SCRAPER_CHOICES[0][0][0]

    form = SearchForm(request.GET)
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
            request.session["search_result"] = retlist
            log.debug("--- search results: %s" % retlist)
        else:
            # uncomplete form (specify we need ean or q).
            log.debug("--- form not complete")
            pass

    else:
        # POST or form not valid.
        form = SearchForm()
        # Re-display results of previous search.
        if "search_result" in request.session:
            retlist = request.session["search_result"]

    return render(request, "search/search_result.jade", {
            "searchForm": form,
            "addForm": AddForm(initial={"basket": get_basket_choices()[0]}),
            "result_list": retlist,
            "data_source": data_source,
            "page_title": page_title,
            })

def _request_session_get(request, key):
    """Gets the session's key.

    A function is needed to mock this call in unit tests (Django
    doesn't provide anything to use the session in tests).
    """
    return request.session.get(key)

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
        log.debug("debug: add view: form is not valid.")
        resp_status = 400
    else:
        # get the last search results of the session:
        cur_search_result = _request_session_get(request, "search_result")
        if not cur_search_result:
            log.debug("Error: the session has no search_result.")
            pass
        card = cur_search_result[form.cleaned_data["forloop_counter0"]]

        card['quantity'] = form.cleaned_data["quantity"]
        data_source = card["data_source"]

        # Call the postSearch method of the datasource module.
        if not card.get('ean'):
            if not data_source:
                log.debug("Error: the data source is unknown.")
                resp_status = 500
                # return an error page
            else:
                # fire a new http request to get the ean (or other missing informations):
                complements = postSearch(data_source, card['details_url'])
                if not complements.get("isbn"):
                    log.warning("warning: postSearch couldnt get the isbn.")
                for k, v in complements.iteritems():
                    log.debug("postSearch: found %s: %s" % (k,v))
                    card[k] = v

        try:
            # Add the card to the DB.
            card_obj = Card.from_dict(card)

            # Add a copy to a basket or to the default place ?
            basket_id = form.cleaned_data.get("basket")
            if basket_id and int(basket_id):
                # add to the basket
                basket_id = int(basket_id)
                log.debug("adding card %s to basket %i" % (card['title'], basket_id))
                basket = Basket.objects.get(id=basket_id)
                basket.add_copy(card_obj)
            else:
                # add to the default place.
                log.debug("adding card %s to default place" % (card['title'],))
                Place.card_to_default_place(card_obj)

            messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (card['title'],))
        except Basket.DoesNotExist as e:
            messages.add_message(request, messages.ERROR,
                                 u"The basket n° %s was not found. The card could not be registered." % (form.cleaned_data["basket"],))
            log.error("Error when fetching basket %s: %s" % (form.cleaned_data["basket"], e))
            resp_status = 500
        except Exception, e:
            messages.add_message(request, messages.ERROR, u'"%s" could not be registered.' % (card['title'],))
            log.error("Error when trying to add card ", e)
            log.error(traceback.format_exc())
            resp_status = 500

    return render(request, 'search/search_result.jade',
                  {
                  'searchForm': SearchForm(),
                  'addForm': AddForm(),
                  'result_list': cur_search_result,
                  },
                  status=resp_status,
                  )

def collection(request):
    """Search our own collection and take actions
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
                                     "La recherche par ean n'est pas encore implémentée.")
                log.debug("TODO: search on ean")

            else:
                card_type_id = form.cleaned_data.get("card_type")
                if card_type_id:
                    card_type_id = int(card_type_id)
                words = form.cleaned_data.get("q").split()
                cards = Card.search(words,
                                    card_type_id=card_type_id,
                                    to_list=True)
                # store results in session for later re-use
                request.session["collection_search"] = cards


    else:
        # GET
        # Get the last new cards of the database.
        cards = Card.first_cards(5)
        cards = Card.obj_to_list(cards)

        if request.GET.get("format") == "text":
            response = HttpResponse(ppcard(cards),
                                    content_type="text/plain;charset=utf-8")
            return response

    return render(request, "search/collection.jade", {
            "searchForm": form,
            "nb_results": len(cards),
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

class inventoriesListView(ListView):
    model = Inventory
    template_name = "search/inventories.jade"
    context_object_name = "inventories"

class depositsListView(ListView):
    model = Deposit
    template_name = "search/deposits.jade"
    context_object_name = "deposits"

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
                                     "Error when adding the deposit")

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
                                     u"We could not add the card to the deposit: the given ean is null.")
            else:
                deposit_id = form.cleaned_data["deposit"]
                # TODO: do the logic !
                messages.add_message(request, messages.SUCCESS,
                                     u'La notice a été ajoutée au dépôt.')

    retlist = request.session.get("collection_search")
    redirect_to = req.get('redirect_to')
    return redirect(redirect_to, status=resp_status)


def deposits_view(request, depo_name):
    """Display the given deposit."""
    deposit = None
    copies = []
    template = "search/deposits_view.jade"
    try:
        deposit = Deposit.objects.get(name=depo_name)
        copies = deposit.copies.all()
    except Deposit.DoesNotExist as e:
        messages.add_message(request, messages.ERROR, "Le dépôt demandé n'existe pas !")
        log.error("le depot demande (%s) n'existe pas: %s" % (depo_name, e))

    return render(request, template, {
        "deposit": deposit,
        "copies": copies,
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
            "pagetitle": "hello basket",
        })

def inventory_list(request):
    """Display all the ongoing inventories.

    An inventory can happen for a place or for a shelf.
    """
    pass
