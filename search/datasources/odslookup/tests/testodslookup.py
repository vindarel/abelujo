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

card_bourgeois = {'authors': [u'Daniel Gu\xe9rin'],
  'card_type': 'book',
  'data_source': 'Chapitre.com',
  'description': u'',
  'details_url': 'http://www.chapitre.com/CHAPITRE/fr/BOOK/guerin-daniel/bourgeois-et-bras-nus-guerre-sociale-durant-le-revolution-francaise-1793-1795,54748482.aspx',
  'ean': u'',
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
  'ean': u'',
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
                         'title': 'Bourgeois et bras nus'},
                        {'NB VENDUS': '',
                         'PRIX DU': '0',
                         'PRIX TOTAL': '0',
                         'REMISE': '40%',
                         'STOCK': '3',
                         'authors': '',
                         'price': '20',
                         'publisher': 'libertalia',
                         'title': 'Crack capitalism'}]

    def tearDown(self):
        pass

    def testLookupCards(self):
        # Augment the tests when module is stabilized.
        found, no_ean, not_found = lookupCards(self.odsdata, datasource="chapitre", level="ERROR",
                                               search_on_datasource=search_on_datasource_fixture)
        self.assertEqual(len(found), 2)
        self.assertTrue(found[0].has_key("title"))
        self.assertFalse(no_ean)

if __name__ == '__main__':
    unittest.main()
