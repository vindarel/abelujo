# Create your views here.
# -*- coding: utf-8 -*-

from datasources.frFR.chapitre.chapitreScraper import scraper
from datasources.frFR.chapitre.chapitreScraper import postSearch
from datasources.all.discogs.discogsConnector import Scraper as discogs

from models import Card

from django import forms
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import urllib


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


def get_reverse_url(cleaned_data, url_name="card_search"):
    """ Get the reverse url with the query parameters taken from the form's cleaned data.

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_reverse_url({"source": "chapitre", "q": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre
    """

    qparam = {}
    qparam['source'] = cleaned_data["source"]
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
            "form": form,
            "result_list": retlist,
            "data_source": data_source,
            "page_title": page_title,
            })


def search_on_data_source(data_source, search_terms):
    if data_source == u'chapitre':
        print "--- search on chapitre"
        query = scraper(*search_terms)
    elif data_source == u'discogs':
        query = discogs(*search_terms)

    retlist = query.search() # list of dicts
    return retlist

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

            retlist = search_on_data_source(data_source, search_terms)
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
            "form": form,
            "result_list": retlist,
            "data_source": data_source,
            "page_title": page_title,
            })

def add(request):

    card = {}
    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    req = request.POST.copy()
    # get the last search results of the session:
    forloop_counter0 = int(req.get("forloop_counter0"))
    cur_search_result = request.session.get("search_result")
    card = cur_search_result[forloop_counter0]

    card['quantity'] = int(request.POST.get('quantity'))

    if not 'card_type' in card:
        print "card has no type."
        card['card_type'] = ""

    if not card.get('ean'):
        if not 'data_source' in req:
            print "Error: the data source is unknown."
            # return an error page
        else:
            data_source = req['data_source']
            # fire a new http request to get the ean (or other missing informations):
            complements = postSearch(card['details_url']) # TODO: généraliser
            if not complements.get("ean"):
                print "--- warning: postSearch couldnt get the ean."
            for k, v in complements.iteritems():
                # import ipdb; ipdb.set_trace()
                print "--- postSearch: found %s: %s" % (k,v)
                card[k] = v

    # Add it to the DB.
    try:
        Card.from_dict(card)
        messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (card['title'],))
    except Exception, e:
        messages.add_message(request, messages.ERROR, u'"%s" could not be registered.' % (card['title'],))
        print "Error when trying to add card ", e

    return render(request, 'search/search_result.jade', {
                  'form': SearchForm(),
                  'result_list': cur_search_result,
                  })

def collection(request):
    """Search our own collection and take actions

    TODO: function identical to index, except the search function: factorize
    Arguments:
    - `self`:
    """
    form = SearchForm()
    retlist = []
    cards = []

    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("title") and request.POST["title"]:
                words = request.POST["title"].split()
                #TODO: better query, include all authors
                cards = Card.get_from_kw(words)

            elif request.POST.has_key("ean"):
                print "todo: search on ean"

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
            "publisher": card.publisher.name.capitalize(),
            "collection": card.collection.name.capitalize(),
            # "description": card.description,
                })


    return render(request, "search/collection.jade", {
            "form": form,
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
                  'form': form
                  })
