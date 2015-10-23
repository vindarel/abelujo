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

import json
import os

import search.datasources.odslookup.odslookup as odslookup
from tqdm import tqdm
from search.models.models import Card
from search.models.models import Place
from search.models.models import Preferences


def run(*args):
    """This method is needed by the runscript command. We can pass
    arguments from the command line by passing a comma-separated list
    of values with --script-args.

    Usage:
    : python manage.py runscript odsimport

    So with a Makefile target:
    : make odsimport odsfile=myfile.ods

    documentation of runscript: http://django-extensions.readthedocs.org/en/latest/runscript.html
    """
    print "script args:", args
    ADD_NO_EAN = True
    ADD_NOT_FOUND = True
    odsfile = args[0]
    if not os.path.exists(odsfile):
        print "Error: file '%s' doesn't exist. Give it as argument with odsfile=..." % (odsfile,)
        return 1
    datasource = "chapitre"

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

    if not cards:
        import ipdb; ipdb.set_trace()
        cards = odslookup.run(odsfile, datasource)

    if cards.get("status") == 1: # XXX deprecated
        print "Error - todo"
        return 1
    # if len(cards["odsdata"]) != cards["found"]: # and no_ean etc
        # cont = raw_input("Nb of cards found VS rows in ods file differ. Continue ? ([y]/n) ")
        # if cont.lower().startswith("n"):
            # return 0
    print "Adding cards to the database..."

    # Create a place if needed.
    pref = Preferences.objects.first()
    if pref and pref.default_place:
        place = pref.default_place
    else:
        if not Place.objects.count() == 0:
            place = Place.objects.first()
        else:
            place = Place(name="default place")
            place.save()

    # Add the cards with all info.
    print "Adding cards with ean..."
    for card in tqdm(cards["cards_found"]): # tqdm: progress bar
        qty = card.get('quantity')
        card_obj, msgs = Card.from_dict(card)
        place.add_copy(card_obj, nb=qty)
    print "...done."

    # Add all other cards (even with uncomplete info).
    if ADD_NO_EAN:
        print "Adding cards without ean..."
        for card in tqdm(cards["cards_no_ean"]):
            #XXX the logs will thrash stdout.
            card_obj, msgs = Card.from_dict(card)
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
