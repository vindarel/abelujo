#!/usr/bin/env python
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
import string
import sys
import time

from datetime import datetime
from pprint import pprint
from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs
from tqdm import tqdm

# Relative imports inside a package using __main__ don't work. Need
# a sys.path trick or a setup.py entrypoint for the script.
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
sys.path.append(cdp)

import ods2csv2py
from odsutils import toInt
from odsutils import replaceAccentsInStr
from frFR.decitre.decitreScraper import Scraper
from frFR.decitre.decitreScraper import postSearch

"""Workflow is as follow:
- get the list of rows from the ods file (with ods2csv2py). The row titles must not contain non-utf8 characters.
- fire a search on a datasource for each card
- find a good matching result inside the result list (because we may have falso positives)
    - i.e., we have to check that the titles are /similar/. That takes time and is computational heavy.
      They can differ by details. See method "cardCorresponds".
- we return:
  - a list of matches
  - a list of matches but with isbn not found
  - a list of cards not found on the data source.
- to add cards to abelujo, use scripts/odsimport.py

Because of the remote search and checking similarities, this will take like 15min for 400 cards.

The price is the one from the ods sheet. TODO:

"""
# Observations: fnac.com is better than chapitre or decitre. These two
# won't find nothing with a long title and sub-title like "nanterre 68
# vers le mouvement du 22 mars acratie".


logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

#: Timeout for searc queries
TIMEOUT = 0.2
#: levenstein's normalized distance to consider two strings corresponding.
#: the smaller the nearer.
DISTANCE_ACCEPTED = 0.4

def filterResults(cards, odsrow):
    """Filter a list of candidates against the ods row.
    Check that a card correponds to a row and look for its isbn with the
    postSearch scraper method.

    :param list_of_dicts cards: list of dicts with cards informations
    (list of authors, title, list of publishers, isbn, etc.). See the
    scrapers documentation.

    returns one card.

    """
    card_not_found = None
    card_no_isbn    = None
    card_found     = None
    accepted = False
    # idea: remove very similar candidates to spare computational time.
    for card in cards:
        if not cards:
            card_not_found = card
            continue
        # Check the titles, the publishers, authors if available, etc.
        if cardCorresponds(card, odsrow):
            accepted = True
            card = postSearch(card)
            if not card.get("ean") and not card.get("isbn"):
                card_no_isbn = card
            else:
                card_found = card
            break

    if not accepted:
        card_not_found = odsrow

    return (card_found, card_no_isbn, card_not_found)

def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and is_substr(data[0][i:i+j], data):
                    substr = data[0][i:i+j]
    return substr

def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True

def rmPunctuation(it):
    """Remove all punctuation from the string.

    return: str
    """
    # https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    # ret = it.translate(None, string.punctuation) # faster, not with unicode
    if not it:
        return it
    exclude = set(string.punctuation)
    st = ''.join(ch for ch in it if ch not in exclude)
    return st


def cardCorresponds(card, odsrow):
    """Check if the card found with a scraper corresponds to what was in
    the user's ods file.  Some titles are totally eronous.

    - odsrow must have: a title
    - to avoid a lot of false positive, odsrow should have a publisher.

    - card: dictionnary coming from a scraper. See its type there.
      - title: uicode str
      - publishers: list of strings

    False negatives are also possible (see comments).

    return: Boolean

    """
    # Check isbn first.
    if card.get('isbn') == odsrow.get('ISBN'):
        return True

    # BUG card['isbn'] égal 'poche' !!! TODO:
    if not odsrow.get('title'):
        log.warning("odsrow has no title. This shouldn't happen. {}".format(odsrow))
        return False

    t1 = rmPunctuation(card.get('title'))
    t1 = replaceAccentsInStr(t1)
    t1 = t1.upper()
    t2 = rmPunctuation(odsrow.get('title')) # already unidecoded.
    t2 = t2.upper()
    if card.get('publishers'):
        p1 = rmPunctuation(card.get('publishers')[0])
        p2 = rmPunctuation(odsrow.get('publishers'))
        if not p2 in p1:
            pdist = distance.levenshtein(p1, p2, normalized=True)
            accept = pdist < DISTANCE_ACCEPTED
            if not accept:
                log.info(u"Rejecting two titles because of too different publishers: {} VS {}".format(p1, p2))
                return accept

    # Publishers seem quite similar. Our only option left (depending
    # on the ods input though) is to check the titles' similarity.

    dist = distance.levenshtein(t1, t2, normalized=True)
    accept = dist < DISTANCE_ACCEPTED
    if not accept:
        # Here we can have a title that includes the sub-title, thus
        # the two strings will be very different. False negative. We
        # will find the longest common substring and check its
        # distance with the odsrow title.
        log.info(u"Titles are very different. Check the common substring of '{}' and '{}'".format(
            card.get('title'), odsrow.get('title')))
        # Of course the common substring can match well but the two
        # titles be totally different. Normally the cards will
        # mismatch by their publisher.

        # check authors, if available in ods.
        # idea: remove everything in ( ) and [ ], we sometimes see "title (the)".
        # idea: remove vol.x, t.x
        sub = long_substr([t1, t2])
        dist = distance.levenshtein(sub, t2, normalized=True)
        accept = dist < DISTANCE_ACCEPTED
        if not accept:
            log.info(u"Rejecting two title with distance {}: common substring {} VS {}".format(
                dist, sub, t2))
        else:
            log.info(u"Accepting two titles with distance {}: common substring '{}' VS '{}'.".format(
                dist, sub, t2))

    return accept

def search_on_scraper(search_terms):
    """Fire the search.

    This method is easy to monkeypatch in unit tests.
    """
    return Scraper(search_terms).search()

def search_post_results(card, isbn=None):
    return postSearch(card, isbn=isbn)

def addRowInfo(card, row):
    """Add some info to the card coming from the ods row.

    - the quantity,
    - the discount of the publisher
    - the distributor (warning, specific use case).

    return: the card (dict).
    """
    if not card:
        print "card is None. that shouldn't happen."
        return card
    if row.get('quantity'): # TODO: to check
        card['quantity'] = toInt(row.get('quantity'))

    if row.get('discount') and not card.get('discount'):
        card['discount'] = row.get('discount')

    # Warning, this is a specific use case:
    # if the column "distributor" is blank, we say it's the publisher.
    # It may not be the case in someone else's ods file.
    if not card.get('distributor'):
        if row.get('distributor'):
            card['distributor'] = row.get('distributor')
        else:
            card['distributor'] = row.get('publisher')

    if row.get('category'):
        card['category'] = row.get('category')

    return card

def lookupCards(odsdata, datasource=None, timeout=0.2, search_on_datasource=search_on_scraper,
                level="DEBUG", odsfile=""):
    """
    Look for the desired cards on remote datasources.

    Use the "cached" json if any. Create it at the first run.

    "Authors" are optionnal.

    :param list_of_dict data: list of dict with names of columns, generally author, title, etc.
    :parama str datasource: the scraper to use ("chapitre", "discogs", etc).

    return a tuple (cards found, cards without isbn, cards not found on remote sources).
    """
    log.setLevel(level.upper())
    cards = []
    stacktraces = []
    cards_not_found = []
    cards_no_isbn    = []
    cards_found     = []
    #: catch the names of the ods columns.
    ODS_AUTHORS = "authors"
    ODS_PUBLISHER = "publishers"

    start = datetime.now()

    # Get the json "cache", if any.
    basename, ext = os.path.splitext(os.path.basename(odsfile))
    debugfile = basename + ".json"
    if os.path.isfile(debugfile):
        with open(debugfile, "r") as f:
            log.info("Reading the json cache file...")
            data = f.read()
        if data:
            cards = json.loads(data)
            # cards = cards.get('cards_found') + cards.get('cards_no_isbn') + cards.get('cards_not_found')
            return cards['cards_found'], cards['cards_no_isbn'], cards['cards_not_found']

    for i, row in tqdm(enumerate(odsdata)):
        if "ISBN" in row:
            search_terms = row['ISBN']
            row['isbn_search'] = True
        else:
            search_terms = "{} {} {}".format(row["title"], row.get(ODS_AUTHORS, ""), row[ODS_PUBLISHER])

        row['search_terms'] = search_terms
        # log.debug("item %d/%d: Searching %s for '%s'..." % (i, len(odsdata), datasource, search_terms))

        # Fire the search:
        try:
            cards, stacktraces = search_on_datasource(search_terms)
            if row.get('isbn_search'):
                log.debug("Looking postSearch of {}".format(row.get('isbn')))
                cards[0] = search_post_results(cards[0], isbn=row.get('isbn'))

        except Exception as e:
            log.error("odslookup: Error while searching cards: {}".format(e))


        # log.debug("found %s cards.\n" % len(cards))
        if stacktraces:
            log.debug("warning: found errors:", stacktraces)
        if cards:
            found, no_isbn, not_found = filterResults(cards, row)
            if found:
                # log.debug("found a valid result: {}".format(found))
                found = addRowInfo(found, row)
                cards_found.append(found)
            if no_isbn:
                no_isbn = addRowInfo(no_isbn, row)
                cards_no_isbn.append(no_isbn)
            if not_found:
                not_found = addRowInfo(not_found, row)
                not_found['publishers'] = [not_found['publishers']]
                cards_not_found.append(not_found)

        else:
            cards_not_found.append(row)
        time.sleep(timeout)              # be gentle with the remote server...

    ended = datetime.now()
    print "Search on {} lasted: {}".format(datasource, ended - start)
    return (cards_found, cards_no_isbn, cards_not_found)

def run(odsfile, datasource, timeout=TIMEOUT, nofieldsrow=False):
    cards_found = cards_no_isbn = cards_not_found = None
    to_ret = {"found": cards_found, "no_isbn": None, "not_found": None,
              "odsdata": None,
              "messages": None,
              "status": 0}
    odsdata = {}

    # Read the data.
    odsdata = ods2csv2py.run(odsfile, nofieldsrow=nofieldsrow)

    if not odsdata:
        exit(1)
    if odsdata.get("status") == 1:
        # TODO: propagate the error
        return odsdata
    if odsdata:
        log.debug("ods sheet data: %i results\n" % (len(odsdata.get("data")),))

    # Look up for cards on our datasource
    cards_found, cards_no_isbn, cards_not_found = lookupCards(odsdata.get("data"),
                                                             datasource=datasource, timeout=timeout,
                                                             odsfile=odsfile)

    if not sum([len(cards_found), len(cards_not_found), len(cards_no_isbn)]) == len(odsdata):
        log.warning("The sum of everything doesn't match ;)")
    # TODO: make a list to confront the result to the ods value.
    log.debug("\nThe following cards will be added to the database: %i results\n" % (len(cards_found),))

    basename, ext = os.path.splitext(os.path.basename(odsfile))
    jsonfile = basename + ".json"
    with open(jsonfile, "wb") as f:
        towrite = {"cards_found": cards_found,
                   "cards_no_isbn": cards_no_isbn,
                   "cards_not_found": cards_not_found}
        f.write(json.dumps(towrite))

    print "\nCards found, complete: "
    pprint(cards_found)
    print "\nCards without isbn: %i results\n" % (len(cards_no_isbn),)
    pprint(cards_no_isbn)
    print "\nCards not found: %i results\n" % (len(cards_not_found,))
    pprint(cards_not_found)
    print "\nResults: %i cards found, %i without isbn, %i not found" % (len(cards_found),
                                                                       len(cards_no_isbn),
                                                                       len(cards_not_found))
    to_ret["found"]     = cards_found
    to_ret["no_isbn"]   = cards_no_isbn
    to_ret["not_found"] = cards_not_found
    to_ret["odsdata"]   = odsdata
    return to_ret

@annotate(sourcefiles=clize.Parameter.REQUIRED)
@autokwoargs
def main(nofieldsrow=False, *sourcefiles):
    """

    sourcefile: the ods/csv file

    If we find a file with the same basename and ending in json, we'll
    use that data to replace the remote search of the ods file (debug
    purposes). If we don't find one we'll create one.

    """
    datasource = "decitre"
    odsdata = []
    status = 1
    ll = len(sourcefiles)
    for i, sourcefile in enumerate(sourcefiles):
        log.info("Loading file {}/{}: {}…".format(sourcefile, i, ll))
        odsdata = run(sourcefile, datasource, timeout=TIMEOUT, nofieldsrow=nofieldsrow)

        if odsdata.get("messages"):
            log.debug("\n".join(msg["message"] for msg in odsdata["messages"]))

        status = status or odsdata['status']

    return status

if __name__ == '__main__':
    clize.run(main)
