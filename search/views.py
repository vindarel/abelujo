# Create your views here.
# -*- coding: utf-8 -*-

import urllib

from django import forms
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from chapitreScraper import scraper
from chapitreScraper import getEan
from discogsConnector import Scraper as discogs

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
    current_scraper = forms.ChoiceField(choices=SCRAPER_CHOICES,
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

    >>> get_rev_url({"current_scraper": "chapitre", "title": u"emma goldman"})
    /search?q=emma+goldman&source=chapitre
    """

    qparam = {}
    qparam['q'] = cleaned_data["title"]
    print "on recherche: ", qparam
    qparam['source'] = cleaned_data["current_scraper"]
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
    current_scraper = SCRAPER_CHOICES[0][0][0]
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("title") and request.POST["title"]:
                current_scraper = form.cleaned_data['current_scraper']
                rev_url = get_rev_url(form.cleaned_data)
                # forward to search?q=query+parameters
                return HttpResponseRedirect(rev_url)

    return render(request, "search/search_result.jade", {
            "form": form,
            "result_list": retlist,
            "data_source": current_scraper,
            "page_title": page_title,
            })


def search(request):
    form = SearchForm()
    retlist = []
    page_title = ""
    current_scraper = SCRAPER_CHOICES[0][0][0]
    if request.method == 'GET':
        current_scraper = request.GET['source']
        query = request.GET['q']
        page_title = query[:50]
        search_terms = [q for q in query.split()]

        if current_scraper == u'chapitre':
            query = scraper(*search_terms)
        elif current_scraper == u'discogs':
            query = discogs(*search_terms)

        retlist = query.search() # list of dicts
        print "--- search results:", retlist

    return render(request, "search/search_result.jade", {
            "form": form,
            "result_list": retlist,
            "data_source": current_scraper,
            "page_title": page_title,
            })

def add(request):

    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    req = request.POST.copy()

    if not req['ean'] and 'data_source' in req:
        data_source = req['data_source'] # scraper
        # use the data_source generically

        # fire a new http request to get the ean (or other missing informations):
        ean = getEan(req['details_url']) # TODO: généraliser
        print "---- found ean: ", ean
        req['ean'] = ean

    if not 'img' in req:
        req['img'] = ""
    book = {'title': req['title'],
            'authors': req['authors'],
            'price': req['price'],
            'location': 'maison',
            'ean': req['ean'],
            'img': req['img'] ,
            'quantity': int(req['quantity']), # needs validation -> use ModelForm
            }
    # Connection to Ruche's DB ! => later…
    Card.from_dict(book)

    messages.add_message(request, messages.SUCCESS, u'«%s» a été ajouté avec succès' % (req['title'],))

    return render(request, 'search/index.jade', {
                  'form': SearchForm()
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

    # obliged not to have unicode decode errors…
    for card in cards:
        retlist.append({
                "title": card.title,
                "authors": card.authors,
                "price": card.price,
                "ean": card.ean,
                "id": card.id,
                "img": card.img,
                "quantity": card.quantity,
                # "description": card.description,
                })


    return render(request, "search/collection.jade", {
            "form": form,
            "book_list": retlist # obliged to give a dict rather than an objet for accent pbs
            })

def sell(request):
    req = request.POST
    ret = Card.sell(ean=req['ean'])

    form = SearchForm()
    message = u"La vente de %s est bien enregistrée" % (req['title'],)
    messages.add_message(request, messages.SUCCESS, message)
    return render(request, 'search/index.jade', {
                  'form': form
                  })
