#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
sys.path.append(cdpp)

from odslookup.ods2csv2py import fieldNames
from odslookup.ods2csv2py import extractCardData

class testOdsUtils(unittest.TestCase):

    def setUp(self):
        data_csvfile = [{'': 'attention les cases suivantes sont lues',
                         'authors': 'emma goldman',
                         'price': '',
                         'publisher': 'versaille',
                         'title': "de l'amour et des bombes"},
                        {'': '',
                         'authors': 'ernest hemingway',
                         'price': '5,6',
                         'publisher': 'gallimard',
                         'title': 'le vieil homme et la mer'}]
        self.csvfiles = [
            # simple (french column names)
            # warning: path depends on who runs the test.
            ("csvfile.csv", {"fieldnames": ['AUTHORS', 'TITLE', 'PUBLISHER', 'PRICE', '', ''],
                                   "data": data_csvfile,
                                   "messages": []}),
            # more real (from libertalia.csv)
            ("csvreal.csv", {"fieldnames": ['TITLE', 'AUTHORS', 'STOCK', 'PRICE',
                                                  'NB VENDUS', 'PRIX TOTAL', 'REMISE', 'PRIX DU', 'PUBLISHER'],
                                   "data":
                                   [{'NB VENDUS': '',
                                     'PRIX DU': '0',
                                     'PRIX TOTAL': '0',
                                     'REMISE': '40%',
                                     'STOCK': '3',
                                     'authors': '',
                                     'price': '10',
                                     'publisher': 'libertalia',
                                     'title': 'Apprendre \xc3\xa0 d\xc3\xa9sob\xc3\xa9ir'},
                                    {'NB VENDUS': '',
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
                                     'title': 'Crack capitalism                                 '}]

                                   ,
                                   "messages": []}),
            # No title nor publisher columns.
            ("nofieldnames.csv", {"fieldnames": [],
                                   "data": None,
                                   "messages": []}),
            ("voidfile.csv", {"fieldnames": [],
                                   "data": None,
                                   "messages": []}),  # void file
            # Same as first with english column names.
            ("english.csv", {"fieldnames": ['AUTHORS', 'TITLE', 'PUBLISHER', 'PRICE', '', ''],
                                   "data": data_csvfile,
                                   "messages": []}),
            ]

        self.maxDiff = None  # Show diff of big lists.

    def tearDown(self):
        pass

    def testFieldNames(self):
        # should test better translations and variations (lower/upper case, plurial, accents)
        for csvfile in self.csvfiles:
            orig, fieldnames = fieldNames(csvfile[0])
            self.assertEqual(fieldnames, csvfile[1]["fieldnames"])

    def testExtractCardData(self):
        for csvfile in self.csvfiles:
            print "test on " + csvfile[0]
            self.assertEqual(extractCardData(csvfile[0])["data"], csvfile[1]["data"])

if __name__ == '__main__':
    unittest.main()
