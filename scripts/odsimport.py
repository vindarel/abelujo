#!/bin/env python
# -*- coding: utf-8 -*-

import os
from search.models.models import Card
import search.datasources.odslookup.odslookup as odslookup

def run(*args):
    """This method is needed by the runscript command. We can pass
    arguments from the command line by passing a comma-separated list
    of values with --script-args.

    documentation of runscript: http://django-extensions.readthedocs.org/en/latest/runscript.html
    """
    print "script args:", args
    ADD_NO_EAN = True
    odsfile = args[0]
    if not os.path.exists(odsfile):
        print "error: file %s doesn't exist." % (odsfile,)
        return 1
    datasource = "chapitre"
    cards = odslookup.run(odsfile, datasource)
    if cards["status"] == 1:
        print "Error - todo"
        return 1
    if len(cards["odsdata"]) != cards["found"]:
        cont = raw_input("Nb of cards found VS rows in ods file differ. Continue ? ([y]/n) ")
        if cont.lower().startswith("n"):
            return 0
    print "Adding cards to the database..."
    for card in cards["found"]:
        card_obj = Card.from_dict(card)
    print "...done."
    if ADD_NO_EAN:
        print "Adding cards without ean..."
        for card in cards["no_ean"]:
            obj = Card.from_dict(card)
        print "...done."
