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
import sys
import unittest

common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
sys.path.append(cdpp)

from odslookup.odslookup import lookupCards
from odslookup.odslookup import cardCorresponds
from odslookup.odslookup import DISTANCE_ACCEPTED

card_bourgeois = {'authors': [u'Daniel Gu\xe9rin'],
  'card_type': 'book',
  'data_source': 'Chapitre.com',
  'description': u'',
  'details_url': 'http://www.chapitre.com/CHAPITRE/fr/BOOK/guerin-daniel/bourgeois-et-bras-nus-guerre-sociale-durant-le-revolution-francaise-1793-1795,54748482.aspx',
  'isbn': u'',
  'img': 'http://www.images-chapitre.com/ima1/newnormal/482/54748482_10852487.jpg',
  'isbn': u'',
  'price': 'produit indisponible',
  'publishers': [u'Libertalia'],
  'title': u'Bourgeois et bras nus ; guerre sociale durant le R\xe9volution fran\xe7aise (1793-1795)'}

card_crack = {'authors': [u'John Holloway'],
  'card_type': 'book',
  'data_source': 'Chapitre.com',
  'description': u'',
  'details_url': 'http://www.chapitre.com/CHAPITRE/fr/BOOK/holloway-john/crack-capitalism-33-theses-contre-le-capital,41626741.aspx',
  'isbn': u'',
  'img': 'http://www.images-chapitre.com/indispo/newnormal.png',
  'isbn': u'',
  'price': 'produit indisponible',
  'publishers': [u'Libertalia'],
  'title': u'Crack Capitalism - 33 Theses Contre Le Capital'}

def search_on_datasource_fixture(search_terms):
    """Return a tuple (card, stacktraces).
    """
    if "bourgeois" in search_terms.lower():
        return [card_bourgeois,], []
    elif "crack" in search_terms.lower():
        return [card_crack,], []
    else:
        print "search_on_datasource_fixture: error."

def fixtfn(*args):
    return "yo"

class testOdsUtils(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.odsdata = [{'NB VENDUS': '',
                         'PRIX DU': '0',
                         'PRIX TOTAL': '0',
                         'REMISE': '40%',
                         'STOCK': '3',
                         'authors': '',
                         'price': '18',
                         'publisher': 'libertalia',
                         'title': u'Bourgeois et bras nus ; guerre sociale durant le R\xe9volution fran\xe7aise (1793-1795)'},
                        {'NB VENDUS': '',
                         'PRIX DU': '0',
                         'PRIX TOTAL': '0',
                         'REMISE': '40%',
                         'STOCK': '3',
                         'authors': '',
                         'price': '20',
                         'publisher': 'libertalia',
                         'title': u'Crack Capitalism - 33 Theses Contre Le Capital'}]

        self.card = {"title": "title test"}
        self.odsrow = {"title": "title test 1"}

    def tearDown(self):
        pass

    def testLookupCards(self):
        # Augment the tests when module is stabilized.
        found, no_isbn, not_found = lookupCards(self.odsdata, datasource="chapitre", level="ERROR",
                                               search_on_datasource=search_on_datasource_fixture)
        self.assertEqual(len(found), 2)
        self.assertTrue(found[0].has_key("title"))
        self.assertFalse(no_isbn)

    def testPubsCorrespond(self):
        self.card['publisher'] = "aael"
        self.odsrow['publisher'] = "aaaa"
        self.assertFalse(cardCorresponds(self.card, self.odsrow))
        #TODO: tester les 3 faux positifs ONGOING:

    def testTitlesCorrespond(self):
        self.assertTrue(cardCorresponds(self.card, self.odsrow))

        self.card['title'] = u"""Introduction \u00e0\u00a0l'histoire\u00a0moderne, g\u00e9n\u00e9rale
et\u00a0politique de\u00a0l'univers.\u00a0Empire d'Alexandre. Histoire
des\u00a0peuples\u00a0orientaux. Histoire
des\u00a0Croisades.\u00a0Empire ottoman. Asie / commenc\u00e9e
par\u00a0le\u00a0baron\u00a0de\u00a0Pufendorff,\u00a0augment\u00e9e
par\u00a0M.\u00a0Bruzen de\u00a0La\u00a0Martini\u00e8re. Nouvelle
\u00e9dition continu\u00e9e jusqu'en mil sept cent cinquante,
par\u00a0M.\u00a0de\u00a0Grace [Edition de 1753-1759]"""
        self.odsrow['title'] = u"introduction a qq chose d'autre"
        # with different publishers, it's easy to reject:
        self.card['publishers'] = ["aael",]
        self.odsrow['publisher'] = "aaaa"
        self.assertFalse(cardCorresponds(self.card, self.odsrow))

        # other false positive example
        self.card['title'] = u"Recueil d'instructions et\u00a0m\u00e9moires diplomatiques. I-III \u00ab Histoire politique de\u00a0ce\u00a0qui s'est pass\u00e9 l'an mil six cens vingt-sept \u00bb jusqu'en 1633 [Edition de 1601-1700]"
        self.odsrow['title'] = u"Le MIL, une histoire politique"
        # these are quite similar : Accepting two titles with distance
        # 0.344827586207: common substring ' HISTOIRE POLITIQUE' VS
        # 'LE MIL UNE HISTOIRE POLITIQUE'.
        self.card['publishers'] = ["chapitre",]
        self.odsrow['publisher'] = "acratie"
        # without different publishers they would be similar enough.
        self.assertFalse(cardCorresponds(self.card, self.odsrow))

        # Now with same publishers, check titles
        self.card['publishers'] = ["aael",]
        self.odsrow['publisher'] = "aael"

        self.card['title'] = u"Petit Parisien Sixieme Derniere (Le) N°23009 du 28/02/1940"
        self.odsrow['title'] = u"La sueur du burnous"
        self.assertFalse(cardCorresponds(self.card, self.odsrow))

        # Titles included in a longer title + subtitle must pass.
        self.card['title'] = u"Sexe, opium et charleston t.1 ; les vies surréalistes des prémices à 1920"
        self.odsrow['title'] = u"Sexe, opium et charleston, 3"
        self.assertTrue(cardCorresponds(self.card, self.odsrow))

        self.card['title'] = u"Anthologie Vol.1 De La Connerie Militariste D'Expression Francaise"
        self.odsrow['title'] = u'Anthologie de la connerie militariste, 1'
        self.assertTrue(cardCorresponds(self.card, self.odsrow))
        #Results: 297 cards found, 73 without isbn, 62 not found

    def testAccents(self):
        self.card['title'] = u"De mémoire t.1 ; les jours du début : un automne 1970 à toulouse"
        self.odsrow['title'] = u"De memoire, 1"
        self.assertTrue(cardCorresponds(self.card, self.odsrow))

    def testParenthesisUppercase(self):
        self.card['title'] = u"Chair A Canon...(De La)"
        self.odsrow['title'] = u"La chair a canon"
        self.assertTrue(cardCorresponds(self.card, self.odsrow))

        # accept: explsions de liberte, guerre au vivant, putain d'usine, etc
if __name__ == '__main__':
    unittest.main()
