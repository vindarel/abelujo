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

import clize
import distance
import json
import logging
import os
import sys
import time
from datetime import datetime
from pprint import pprint
from sigtools.modifiers import kwoargs

# Relative imports inside a package using __main__ don't work. Need
# a sys.path trick or a setup.py entrypoint for the script.
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
sys.path.append(cdp)

import ods2csv2py
from frFR.chapitre.chapitreScraper import Scraper
from frFR.chapitre.chapitreScraper import postSearch


"""Workflow is as follow:
- get the list of rows from the ods file (with ods2csv2py)
- fire a search on a datasource for each card
- find a good matching result inside the result list
- we return:
  - a list of matches
  - a list of matches but with ean not found
  - a list of cards not found

The price is the one from the ods sheet. TODO:

"""
# Observations: fnac.com is better than chapitre or decitre. These two
# won't find nothing with a long title and sub-title like "nanterre 68
# vers le mouvement du 22 mars acratie".


logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

TIMEOUT = 0.2

def filterResults(cards, odsrow):
    """

    :param list_of_dicts cards: list of dicts with cards informations
    (list of authors, title, list of publishers, ean, etc.). See the
    scrapers documentation.

    returns one card.
    """
    card_not_found = None
    card_no_ean    = None
    card_found     = None
    for card in cards:
        if not cards:
            card_not_found = card
            continue
        # check the publisher, the price, etc
        if cardCorresponds(card, odsrow):
            post_search = postSearch(card["details_url"])
            for key in post_search.keys():
                card[key] = post_search[key]
            if not card.get("ean") and not card.get("isbn"):
                card_no_ean = card
            else:
                card_found = card
            break

    return (card_found, card_no_ean, card_not_found)

def cardCorresponds(card, odsrow):
    """check if the card found with a scraper corresponds to what was in the user's ods file.
    """
    return True

    #: list of important rows of the user file to check. Typically,
    # the title and the publisher. The price is questionnable because the
    # bookshop may sell it cheaper for some reasons.
    rows_to_check = [
        "title",
        "authors",  # on the ods side, they are comma-separated.
        "publisher",
        ]

    check_price = False
    #: messages of warnings, successes or errors: list of dicts with
    # "level":warning, "message": "foo", "field": field
    messages = []
    status = True
    for row in rows_to_check:
        if row == "authors":
            log.debug("warning: ensure rows are named the same (both authors with an s for instance).")
            res, msg = check_authors(card["authors"], odsrow["authors"])
            if msg:
                messages.append(msg)
            status = status and res
        elif row == "title":
            res, msg = check_title(card["title"], odsrow["title"])

    return status, messages

def check_title(from_search, from_ods):
    """check the titles look the same.
    Returns a tuple (status, messages).
    """
    return True, None

def check_authors(from_search, from_ods):
    """check if the two authors/list of authors are the same.
    Returns a tupel (status, message dict).
    """
    # from_s = ", ".join([aut.lower() for aut  in from_card])
    # print "caution: authors not checked."
    return True, None

def search_on_scraper(search_terms):
    """Fire the search.

    This method is easy to monkeypatch in unit tests.
    """
    return Scraper(search_terms).search()

def lookupCards(odsdata, datasource=None, timeout=0.2, search_on_datasource=search_on_scraper,
                level="DEBUG", debugfile=None):
    """
    Look for the desired cards on remote datasources.

    "Authors" are optionnal.

    :param list_of_dict data: list of dict with names of columns, generally author, title, etc.
    :parama str datasource: the scraper to use ("chapitre", "discogs", etc).

    return a tuple (cards found, cards without ean, cards not found on remote sources).
    """
    log.setLevel(level.upper())
    cards_not_found = []
    cards_no_ean    = []
    cards_found     = []
    #: catch the names of the ods columns.
    ODS_AUTHORS = "authors"
    ODS_PUBLISHER = "publisher"

    start = datetime.now()

    if os.path.isfile(debugfile):
        with open(debugfile, "r") as f:
            data = f.read()
        if data:
            cards = json.loads(data)
            return cards['cards_found'], cards['cards_no_ean'], cards['cards_not_found']

    for i, row in enumerate(odsdata):
        search_terms = row["title"] + " " + row.get(ODS_AUTHORS, "") + row[ODS_PUBLISHER]
        log.debug("item %d/%d: Searching %s for '%s'..." % (
            i, len(odsdata), datasource, search_terms))

        # Fire the search:
        try:
            cards, stacktraces = search_on_datasource(search_terms)
        except Exception as e:
            log.error(e)
            return 1

        log.debug("found %s cards.\n" % len(cards))
        if stacktraces:
            log.debug("warning: found errors:", stacktraces)
        if cards:
            found, no_ean, not_found = filterResults(cards, row)
        else:
            cards_not_found.append(row)
        if found:
            log.debug("found a valid result: {}".format(found))
            cards_found.append(found)
        if no_ean:
            cards_no_ean.append(no_ean)
        if not_found:  # TODO: useless
            cards_not_found.append(not_found)
        time.sleep(timeout)              # be gentle with the remote server...

    ended = datetime.now()
    print "Search on {} lasted: {}".format(datasource, ended - start)
    return (cards_found, cards_no_ean, cards_not_found)

def run(odsfile, datasource, timeout=TIMEOUT, debugfile=None):
    cards_found = cards_no_ean = cards_not_found = None
    to_ret = {"found": cards_found, "no_ean": None, "not_found": None,
              "odsdata": None,
              "messages": None,
              "status": 0}
    odsdata = {}
    if not debugfile:
        odsdata = ods2csv2py.run(odsfile)
    if not odsdata and not debugfile:
        log.error("No data. See previous logs. Do nothing.")
        return 1
    if odsdata.get("status") == 1:
        # TODO: propagate the error
        return odsdata
    if odsdata:
        print "\n".join(res['title'] for res in odsdata.get("data"))
        log.debug("ods sheet data: %i results\n" % (len(odsdata.get("data")),))

    # Look up for cards on our datasource
    cards_found, cards_no_ean, cards_not_found = lookupCards(odsdata.get("data"),
                                                             datasource=datasource, timeout=timeout,
                                                             debugfile=debugfile)

    # TODO: check that the total corresponds.
    if not sum([len(cards_found), len(cards_not_found), len(cards_no_ean)]) == len(odsdata):
        log.warning("The sum of everything doesn't match ;)")
    # TODO: make a list to confront the result to the ods value.
    log.debug("\nThe following cards will be added to the database: %i results\n" % (len(cards_found),))

    with open("testdata.json", "wb") as f:
        towrite = {"cards_found": cards_found,
                   "cards_no_ean": cards_no_ean,
                   "cards_not_found": cards_not_found}
        f.write(json.dumps(towrite))

    print "\nCards found, complete: "
    pprint(cards_found)
    print "\nCards without ean: %i results\n" % (len(cards_no_ean),)
    pprint(cards_no_ean)
    print "\nCards not found: %i results\n" % (len(cards_not_found,))
    pprint(cards_not_found)
    print "\nResults: %i cards found, %i without ean, %i not found" % (len(cards_found),
                                                                       len(cards_no_ean),
                                                                       len(cards_not_found))
    to_ret["found"]     = cards_found
    to_ret["no_ean"]    = cards_no_ean
    to_ret["not_found"] = cards_not_found
    to_ret["odsdata"]   = odsdata
    return to_ret

@kwoargs("ods", "json")
def main(ods=None, json=None):
    """
    ods: the ods file

    json: a json file (debug only)
    """
    datasource = "chapitre"
    odsdata = run(ods, datasource, timeout=TIMEOUT, debugfile=json)
    if odsdata["messages"]:
        log.debug("\n".join(msg["message"] for msg in odsdata["messages"]))
    return odsdata["status"]

if __name__ == '__main__':
    clize.run(main)
