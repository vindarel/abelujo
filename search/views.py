# Create your views here.
# -*- coding: utf-8 -*-

import json

from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.contrib import messages
# from django.views.decorators.csrf import csrf_protect

# from decitreScraper import decitreScraper as scraper
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

class ContactForm(forms.Form):
    current_scraper = forms.ChoiceField(choices=SCRAPER_CHOICES,
                                        label='Data source',
                                        # help_text='choose the data source for your query',
                                        )
    title = forms.CharField(max_length=100, required=False)
    ean = forms.CharField(required=False)

class BookForm(ContactForm):
    authors = forms.CharField()
    description = forms.IntegerField()
    price = forms.IntegerField()


def index(request):
    bk1 = {"title": u"Les Misérables tome 6",
    # bk1 = {"title": "Les Miserables tome deux",
           "authors": "Victor Hugo",
           "price": 7,
           "ean": 6,
           }
    bk2 = {"title": "Living my life",
           "authors": "Emma Goldman",
           "price": 7.5,
           "ean": 6969,
           }
    bk3 = {"title": "Sans patrie ni frontières",
           "authors": "Jan Valtin",
           "price": 8,
           "ean": 3945,
           }

    retlist = [bk1, bk2, bk3]

    form = ContactForm()
    result_form = BookForm()
    if request.method == "POST":
        print "----- method is POST"
        form = ContactForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("title") and request.POST["title"]:
                search_terms = form.cleaned_data["title"].split()
                # print "+++++++form.cleaned_data: ", form.cleaned_data['title'].split()
                print "on recherche: ", search_terms
                current_scraper = form.data['current_scraper']
                if current_scraper == u'chapitre':
                    query = scraper(*search_terms)
                elif current_scraper == u'discogs':
                    query = discogs(*search_terms)

                retlist = query.search() # list of dicts

    return render(request, "search/search_result.jade", {
            "form": form,
            "result_form": result_form,
            "result_list": retlist,
            "book_list": retlist,
            "data_source": current_scraper,
            })

def add(request):

    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    req = request.POST.copy()

    if not req['ean']:
        data_source = req['data_source'] # scraper
        # use the data_source generically

        # fire a new http request to get the ean:
        ean = getEan(req['details_url']) # TODO: généraliser
        print "---- found ean: ", ean
        req['ean'] = ean

    book = {'title': req['title'],
            'authors': req['authors'],
            # 'authors': book['authors'][0], #todo [0] temp
            'price': req['price'],
            'location': 'maison',
            'ean': req['ean'],
            # 'sortkey': book['authors'],
            # 'origkey': book['ean']
            }
    # Connection to Ruche's DB ! => later…
    Card.from_dict(book)

    messages.add_message(request, messages.SUCCESS, u'Le livre «%s», de %s, a été ajouté avec succès' % (req['title'], req['authors']))

    # return render(request, 'search/add_book.jade', {
    return render(request, 'search/index.jade', {
                  # 'book': book,
                  'form': ContactForm()
                  })



#         if not bkl or bkl is []:
#             return HttpResponse('no result')

#     return render_to_response('search/index.jade', bkl,
#                               context_instance=RequestContext(request))
#     # return render('search/index.jade', bk_list) #forces use of RequestContext
#     # return HttpResponse("Hello, world. You're at the search result index.")

def collection(request):
    """Search our own collection and take actions

    TODO: function identical to index, except the search function: factorize
    Arguments:
    - `self`:
    """
    form = ContactForm()
    retlist = []

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if request.POST.has_key("title") and request.POST["title"]:
                words = request.POST["title"].split()
                #TODO: better query !
                cards = Card.get_from_kw(words)

            elif request.POST.has_key("ean"):
                print "todo"


    else:
        cards = Card.first_cards(5)

    # obliged not to have unicode decode errors…
    for card in cards:
        print "=========== card: ", card
        retlist.append({
                "title": card.title,
                "authors": card.authors,
                "price": card.price,
                "ean": card.ean,
                # "description": card.description,
                })


    return render(request, "search/collection.jade", {
            "form": form,
            "book_list": retlist # obliged to give a dict rather than an objet for accent pbs
            })

def sell(request):
    req = request.POST
    book = {'title': req['title'],
            'authors': req['authors'],
            'price': req['price'],
            'location': 'maison',
            'ean': req['ean']
            }
    ret = Card.sell(ean=req['ean'])

    form = ContactForm()
    message = u"La vente de %s est bien enregistrée" % (req['title'],)
    messages.add_message(request, messages.SUCCESS, message)
    return render(request, 'search/index.jade', {
                  'form': form
                  })
