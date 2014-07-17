# Create your views here.
# -*- coding: utf-8 -*-

import urllib

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponseRedirect
from django.shortcuts import render

import datasources.all.discogs.discogsConnector as discogs
import datasources.frFR.chapitre.chapitreScraper as chapitre

from models import Basket
from models import Card
from models import Place

MAX_COPIES_ADDITIONS = 10000  # maximum of copies to add at once
DEFAULT_NB_COPIES = 1         # default nb of copies to add.

# scraper names are the name of the imported module.
SCRAPER_CHOICES = [
    ("Book shops", (
            ("chapitre", "chapitre.com - fr"),
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


class MyNumberInput(TextInput):
    # render an IntegerField with a "number" html5 widget, not text.
    input_type = 'number'


def get_basket_choices():
    # TODO: make list dynamic + query in class.
    return [(0, "Aucun panier")] + [(basket.id, basket.name) for basket in Basket.objects.all()]

basket_choices = get_basket_choices()

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
    basket = forms.ChoiceField(choices=basket_choices,  #TODO en cours
                               label="Ajouter la notice au panier (optionnel)",
                               required=False)

def get_places_choices():
    not_stands = Place.objects.filter(is_stand=False)
    ret = [ (p.name, p.name) for p in not_stands]
    return ret


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
    print "on recherche: ", qparam
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
    scraper = getattr(globals()[data_source], "postSearch")
    return scraper.postSearch(details_url)

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
            print "--- search results:", retlist
        else:
            # uncomplete form (specify we need ean or q).
            print "--- form not complete"
            pass

    else:
        # POST or form not valid.
        form = SearchForm()
        # Re-display results of previous search.
        if "search_result" in request.session:
            retlist = request.session["search_result"]

    return render(request, "search/search_result.jade", {
            "searchForm": form,
            "addForm": AddForm(initial={"basket": basket_choices[0]}),
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
        print "debug: add view: form is not valid."
        resp_status = 400
    else:
        # get the last search results of the session:
        cur_search_result = _request_session_get(request, "search_result")
        if not cur_search_result:
            print "Error: the session has no search_result."
            pass
        card = cur_search_result[form.cleaned_data["forloop_counter0"]]

        card['quantity'] = form.cleaned_data["quantity"]
        data_source = card["data_source"]

        if not card.get('ean') and "chapitre" in data_source:  # have to call postSearch of the right module.
            if not data_source:
                print "Error: the data source is unknown."
                resp_status = 500
                # return an error page
            else:
                # fire a new http request to get the ean (or other missing informations):
                complements = postSearch(data_source, card['details_url'])
                if not complements.get("ean"):
                    print "--- warning: postSearch couldnt get the ean."
                for k, v in complements.iteritems():
                    print "--- postSearch: found %s: %s" % (k,v)
                    card[k] = v

        try:
            # Add the card to the DB.
            card_obj = Card.from_dict(card)

            # Add a copy to a basket or to the default place ?
            basket_id = form.cleaned_data.get("basket")
            if basket_id and int(basket_id):
                # add to the basket
                basket_id = int(basket_id)
                print "adding card %s to basket %i" % (card['title'], basket_id)
                basket = Basket.objects.get(id=basket_id)
                basket.add_copy(card_obj)
            else:
                # add to the default place.
                print "adding card %s to default place" % (card['title'],)
                Place.card_to_default_place(card_obj)

            messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (card['title'],))
        except Basket.DoesNotExist as e:
            messages.add_message(request, messages.ERROR,
                                 u"The basket n° %s was not found. The card could not be registered." % (form.cleaned_data["basket"],))
            print "Error when fetching basket %s: %s" % (form.cleaned_data["basket"], e)
            resp_status = 500
        except Exception, e:
            messages.add_message(request, messages.ERROR, u'"%s" could not be registered.' % (card['title'],))
            print "Error when trying to add card ", e
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
    form = SearchForm()
    retlist = []
    cards = []

    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("q"):
                words = form.cleaned_data["q"].split()
                #TODO: better query, include all authors
                cards = Card.get_from_kw(words)

            elif request.POST.has_key("ean"):
                messages.add_message(request, messages.INFO,
                                     "La recherche par ean n'est pas encore implémentée.")
                print "TODO: search on ean"

    else:
        cards = Card.first_cards(5)

    for card in cards:
        retlist.append({
            "title": card.title,
            "authors": ", ".join([ca.name for ca in card.authors.all()]),
            "price": card.price,
            "ean": card.ean,
            "id": card.id,
            "img": card.img,
            "quantity": card.quantity,
            "publishers": ", ".join([p.name.capitalize() for p in card.publishers.all()]),
            "collection": card.collection.name.capitalize() if card.collection else None,
            "details_url": card.details_url,
            "data_source": card.data_source,
            "places": ", ".join([p.name for p in card.places.all()]),
        })


    return render(request, "search/collection.jade", {
            "searchForm": form,
            "book_list": retlist
            })

def sell(request):
    form = SearchForm()
    req = request.POST

    if not req.get("ean"):
        message = u"Erreur: cette notice n'a pas d'ean et ne peut être vendue."
        level = messages.ERROR
    else:
        ret, msg = Card.sell(ean=req['ean'])
        if ret:
            message = u"La vente de %s est bien enregistrée." % (req.get('title'),)
            level = messages.SUCCESS
        else:
            message = u"La vente a échoué. %s" % msg
            level = messages.ERROR

    messages.add_message(request, level, message)
    return render(request, 'search/index.jade', {
                  'searchForm': form
                  })
