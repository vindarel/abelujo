# Create your views here.
# -*- coding: utf-8 -*-

import urllib

from django import forms
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from datasources.frFR.chapitre.chapitreScraper import scraper
from datasources.frFR.chapitre.chapitreScraper import getEan
from datasources.all.discogs.discogsConnector import Scraper as discogs

from models import Card

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
    data_source = forms.ChoiceField(choices=SCRAPER_CHOICES,
                                        label='Data source',
                                        # help_text='choose the data source for your query',
                                        )
    title = forms.CharField(max_length=100, required=False,
                            min_length=4,
                            )
    ean = forms.CharField(required=False)


def get_rev_url(cleaned_data):
    """ Get the reverse url with the query parameters taken from the form's cleaned data.

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_rev_url({"data_source": "chapitre", "title": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre
    """

    qparam = {}
    qparam['q'] = cleaned_data["title"]
    print "on recherche: ", qparam
    qparam['source'] = cleaned_data["data_source"]
    # construct the query parameters of the form
    # q=query+param&source=discogs
    params = urllib.urlencode(qparam)
    rev_url = reverse("card_search") + "?" + params
    return rev_url

def index(request):
    bk1 = {"title": u"Les Misérables tome 6",
           "authors": "Victor Hugo",
           "price": 7,
           "ean": 6,
           "img": "",
           }
    bk2 = {"title": "Living my life",
           "authors": "Emma Goldman",
           "price": 7.5,
           "ean": 6969,
           "img": "",
           }
    bk3 = {"title": "Sans patrie ni frontières",
           "authors": "Jan Valtin",
           "price": 8,
           "ean": 3945,
           "img": "",
           }

    retlist = [bk1, bk2, bk3]

    form = SearchForm()
    page_title = ""
    data_source = SCRAPER_CHOICES[0][0][0]
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("title") and request.POST["title"]:
                data_source = form.cleaned_data['data_source']
                rev_url = get_rev_url(form.cleaned_data)
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
    form = SearchForm()
    retlist = []
    page_title = ""
    data_source = SCRAPER_CHOICES[0][0][0]
    if "search_result" in request.session:
        retlist = request.session["search_result"]
    if request.method == 'GET' and 'source' in request.GET.keys():
        data_source = request.GET['source']
        query = request.GET['q']
        page_title = query[:50]
        search_terms = [q for q in query.split()]

        retlist = search_on_data_source(data_source, search_terms)
        request.session["search_result"] = retlist
        print "--- search results:", retlist

    return render(request, "search/search_result.jade", {
            "form": form,
            "result_list": retlist,
            "data_source": data_source,
            "page_title": page_title,
            })

def add(request):

    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    req = request.POST.copy()
    forloop_counter0 = int(req["forloop_counter0"])
    cur_search_result = request.session["search_result"]
    card = cur_search_result[forloop_counter0]
    card['quantity'] = request.POST['quantity']

    if not card['ean']:
        if not 'data_source' in req:
            print "Error: the data source is unknown."
            # return an error page
        else:
            data_source = req['data_source']
            # fire a new http request to get the ean (or other missing informations):
            ean = getEan(card['details_url']) # TODO: généraliser
            print "---- looked for and found ean: ", ean
            card['ean'] = ean

    # Connection to Ruche's DB ! => later…
    Card.from_dict(card)

    messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (card['title'],))

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
                # "description": card.description,
                })


    return render(request, "search/collection.jade", {
            "form": form,
            "book_list": retlist
            })

def sell(request):
    form = SearchForm()
    req = request.POST
    if not req["ean"]:
        msg = u"Erreur: cette notice n'a pas d'ean et ne peut être vendue."
        messages.add_message(request, messages.ERROR, msg)
    else:
        ret = Card.sell(ean=req['ean'])
        message = u"La vente de %s est bien enregistrée" % (req['title'],)
        messages.add_message(request, messages.SUCCESS, message)

    return render(request, 'search/index.jade', {
                  'form': form
                  })
