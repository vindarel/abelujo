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

from models import Card

class ContactForm(forms.Form):
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
                # s = request.POST["title"].split()
                s = form.cleaned_data["title"].split()
                # print "+++++++form.cleaned_data: ", form.cleaned_data['title'].split()
                # .POST.get('title', 'backup value')
                print "on recherche: ", s
                query = scraper(*s)
                bkl = query.search() #on a une list d'objets decitreScraper.Book
                print "found: ", bkl
                retlist = []

                # import ipdb; ipdb.set_trace()
                # form.cleaned_data["title"]
                # passer dans un simple dict marche bien, on crée l'objet dans «add»
                #TODO: use the __json__ method that I implemented for that !
                for b in bkl:
                    nb = {}
                    nb["title"] = b.title
                    nb["authors"] = ", ".join([aut for aut in b.authors])  # working
                    nb["description"] = b.description
                    nb["price"] = b.price
                    nb['ean'] = b.ean
                    nb['details_url'] = b.details_url
                    nb['editor'] = b.editor


                    # pb avec acents quelque part
                    # nb = Book()
                    # nb.title = b.title
                    # retlist.append(
                        # {"title": b.title,
                         # "authors": str(b.authors),
                         # "price": b.price
                         # })
                    retlist.append(nb)

            elif request.POST.has_key("ean"):
                print "--------- recherche ean"
                ean = form.cleaned_data["ean"]
                print "on a l ean: ", ean
                query = scraper(ean=ean)
                l = query.search()
                print "livre-ean: ", l

    print "------- let's return"
    return render(request, "search/search_result.jade", {
            "form": form,
            "result_form": result_form,
            "result_list": retlist,
            # "book_list": bkl #return un objet book de decitreScraper: non
            "book_list": retlist
            })

def add(request):

    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    req = request.POST.copy()

    if not req['ean']:
        # fire a new http request to get the ean:
        ean = getEan(req['details_url'])
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
