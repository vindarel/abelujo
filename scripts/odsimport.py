#!/bin/env python
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

import glob
import json
import os

import search.datasources.odslookup.odslookup as odslookup
from search.models.models import Card
from search.models.models import Category
from search.models.models import Distributor
from search.models.models import Place
from search.models.models import Preferences
from search.models.models import Publisher
from tqdm import tqdm


def getAllKeys(cards, key):
    """From the list of dicts "cards", get all the values of "key".

    return: a list
    """
    its = []
    for _, val in cards.iteritems():
        if val:
            for dic in val:
                if dic.get(key) not in its:
                    its.append(dic.get(key))
    its = filter(lambda it: it is not None, its)
    return its

def import_file(odsfile):
    """Import the cards (as dicts) from within this csv file.

    Read the csv and lookup for the cards on the remote data source.

    Take the data from the .json if any.

    Then create all the publishers, the distributors and their
    discount (if any), the default place, and add the cards to the
    default place.

    """
    ADD_NO_EAN = True
    ADD_NOT_FOUND = True
    if not os.path.exists(odsfile):
        print "Error: file '%s' doesn't exist. Give it as argument with odsfile=..." % (odsfile,)
        return 1
    datasource = "chapitre"

    ### Get the json data, if any.
    basename, ext = os.path.splitext(odsfile)
    jsonfile = basename + ".json"
    cards = []
    jsonfile = os.path.join(os.path.abspath("./"), jsonfile)
    if os.path.isfile(jsonfile):
        with open(jsonfile, "r") as f:
            data = f.read()
        try:
            print "Reading cards data from the saved json file…"
            cards = json.loads(data)
        except Exception as e:
            print "json error. Will read the ods file instead. {}".format(e)
            cards = []

    ### Run: lookup cards from the ods.
    if not cards:
        cards = odslookup.run(odsfile, datasource)

    ### Get all publishers and create them OR do it in Card.from_dict ?
    pubs = []
    for key, val in cards.iteritems():
        if val:
            for dic in val:
                if dic.get('publisher') not in pubs:
                    pubs.append(dic.get('publishers'))
    pubs = filter(lambda it: it is not None, pubs)

    print "Creating publishers..."
    for pub in tqdm(pubs):
        _, _ = Publisher.objects.get_or_create(name=pub)
    print "...done."

    ### Get all distributors and their discount
    dists = []
    seen = []
    for key, val in cards.iteritems():
        if val:
            for dic in val:
                dist = dic.get('distributor')
                if dist and dist not in seen:
                   discount = dic.get('discount', 0)
                   seen.append(dist)
                   dists.append((dist, discount))

    print "Creating distributors..."
    for tup in tqdm(dists):
        try:
            obj, _ = Distributor.objects.get_or_create(name=tup[0])
            obj.discount = tup[1]
            obj.save()
        except Exception as e:
            print e
    print "...done."

    ### Get and create all categories
    print "Creating categories..."
    cats = []
    cats = getAllKeys(cards, "category")
    for it in tqdm(cats):
        Category.objects.get_or_create(name=it)
    print "...done."

    import ipdb; ipdb.set_trace()
    ### Create a default place if needed.
    pref = Preferences.objects.first()
    if pref and pref.default_place:
        place = pref.default_place
    else:
        if not Place.objects.count() == 0:
            place = Place.objects.first()
        else:
            place = Place(name="default place")
            place.save()

    ### Add cards
    # Add the cards with all info.
    print "Adding cards to the database..."
    print "Adding cards with ean..."
    for card in tqdm(cards["cards_found"]): # tqdm: progress bar
        qty = card.get('quantity')
        card_obj, msgs = Card.from_dict(card)
        place.add_copy(card_obj, nb=qty)
    print "...done."

    # Add all other cards (even with uncomplete info).
    if ADD_NO_EAN:
        print "Adding cards without ean..."
        for card in tqdm(cards["cards_no_isbn"]):
            #XXX the logs will thrash stdout.
            card_obj, msgs = Card.from_dict(card)
            if card.get('title'):
                place.add_copy(card_obj, nb=qty)
        print "...done."

    if ADD_NOT_FOUND:
        print "Adding cards not found, without much info..."
        for card in tqdm(cards["cards_not_found"]):
            try:
                card_obj, msgs = Card.from_dict(card)
                place.add_copy(card_obj, nb=qty)
            except Exception as e:
                print "Error adding card {}: {}".format(card.get('title'), e)

    print "All done."

def run(*args):
    """This method is needed by the runscript command. We can pass
    arguments from the command line by passing a comma-separated list
    of values with --script-args.

    Usage:
    : python manage.py runscript odsimport

    So with a Makefile target:
    : make odsimport odsfile=myfile.ods

    You can also give a directory as argument. We'll look for all csv files in there:
    : make odsimport odsfile=mydir/

    documentation of runscript: http://django-extensions.readthedocs.org/en/latest/runscript.html
    """
    print "script args:", args
    files = args
    if os.path.isdir(args[0]):
        files = glob.glob('{}*csv'.format(args[0]))

    for i, afile in enumerate(files):
        print "---------------"
        print "Importing file {}/{}: {}".format(i + 1, len(files) + 1, afile)
        print "---------------"
        import_file(afile)

    print "All files imported."
