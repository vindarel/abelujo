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

import os
from search.models.models import Card
from search.models.models import Place
from search.models.models import Preferences
import search.datasources.odslookup.odslookup as odslookup

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
        print "error: file %s doesn't exist." % (odsfile,)
        return 1
    datasource = "chapitre"
    cards = odslookup.run(odsfile, datasource)
    if cards["status"] == 1:
        print "Error - todo"
        return 1
    # if len(cards["odsdata"]) != cards["found"]: # and no_ean etc
        # cont = raw_input("Nb of cards found VS rows in ods file differ. Continue ? ([y]/n) ")
        # if cont.lower().startswith("n"):
            # return 0
    print "Adding cards to the database..."
    pref = Preferences.object.first()
    if pref and pref.default_place:
        place = pref.default_place
    else:
        if not Place.objects.count() == 0:
            place = Place.objects.first()
        else:
            place = Place(name="default place")
            place.save()

    import ipdb; ipdb.set_trace()
    qty = 1 #TODO: get quantity from ods
    for card in cards["found"]:
        card_obj = Card.from_dict(card)
        place.add_copy(card_obj, nb=qty)
    print "...done."

    if ADD_NO_EAN:
        print "Adding cards without ean..."
        for card in cards["no_ean"]:
            obj = Card.from_dict(card)
            place.add_copy(card_obj, nb=qty)
        print "...done."

    if ADD_NOT_FOUND:
        print "Adding cards not found, without much info..."
        for card in cards["not_found"]:
            try:
                obj = Card.from_dict(card)
                place.add_copy(card_obj, nb=qty)
            except Exception as e:
                print "Error adding card {}: {}".format(card.get('title'), e)
        print "...done"
