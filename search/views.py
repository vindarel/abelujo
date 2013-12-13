# Create your views here.
# -*- coding: utf-8 -*-

import json

from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
# from django.views.decorators.csrf import csrf_protect

from decitreScraper import decitreScraper as scraper

# from models import Location, Author, Book
import models

class ContactForm(forms.Form):
    title = forms.CharField(max_length=100, required=False)
    ean = forms.CharField(required=False)


def index(request):
    bk1 = {"title": "Les Miserables tome deux",
           "authors": "Victor Hugo",
           "price": 7
           }
    bk2 = {"title": "Living my life",
           "authors": "Emma Goldman",
           "price": 7.5
           }
    bk3 = {"title": "Sans patrie ni frontières",
           "authors": "Jan Valtin",
           "price": 8
           }

    bkl = [bk1, bk2, bk3]

    form = ContactForm()
    retlist = [bk1, ]
    if request.method == "POST":
        print "----- method is POST"
        form = ContactForm(request.POST)
        if request.POST.has_key("title") and request.POST["title"]:
            s = request.POST["title"].split()
            print "on recherche: ", s
            query = scraper(*s)
            bkl = query.search() #on a une list d'objets decitreScraper.Book
            print "found: ", bkl
            retlist = []
            from models import Book

            # import ipdb; ipdb.set_trace()
            # form.cleaned_data["title"]
            # passer dans un simple dict marche bien, on crée l'objet dans «add»
            #TODO: use the __json__ method that I implemented for that !
            for b in bkl:
                nb = {}
                nb["title"] = b.title
                nb["authors"] = b.authors
                # pb avec acents quelque part
                # nb = Book()
                # nb.title = b.title
                # retlist.append(
                    # {"title": b.title,
                     # "authors": str(b.authors),
                     # "price": b.price
                     # })
                retlist.append(nb)

        if form.is_valid():
            if request.POST.has_key("ean"):
                print "--------- recherche ean"
                ean = form.cleaned_data["ean"]
                print "on a l ean: ", ean
                query = scraper(ean=ean)
                l = query.search()
                print "livre-ean: ", l

    print "------- let's return"
    return render(request, "search/index.jade", {
            "form": form,
            # "book_list": bkl #return un objet book de decitreScraper: non
            "book_list": retlist
            })

def add(request):

    print "our ruequest: ", request.POST
    if request.method == "POST":
        print "our post: ", request.POST

    print "request.pots[book]: ", request.POST["book"]
    req = request.POST["book"]
    print "notre r: ", req
    print "r.title ?", req.title
    print "type r: ", type(req)
    # I dont know why but book is a str instead of an object
    req = req.replace("'", '"')
    # import ipdb; ipdb.set_trace()
    book = json.loads(req) #pb with accents
    print "my book to add to model: ", book

    # Connection to Ruche's DB ! => later…
    models.Book.from_dict({'title': book['title'],
                      # 'authors': [book['authors']],
                      'authors': book['authors'][0],
                      'location': 'maison',
                      # 'sortkey': book['authors'],
                      # 'origkey': book['ean']
                      })


    return render(request, 'search/add_book.jade', {
                  'book': book
                  })



#         if not bkl or bkl is []:
#             return HttpResponse('no result')

#     return render_to_response('search/index.jade', bkl,
#                               context_instance=RequestContext(request))
#     # return render('search/index.jade', bk_list) #forces use of RequestContext
#     # return HttpResponse("Hello, world. You're at the search result index.")
