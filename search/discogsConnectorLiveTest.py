#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest


common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
scraper = os.path.join(cdpp, 'decitreScraper')

# from ... import decitreScraper
sys.path.append(cdpp)
from discogsConnector import Scraper as scraper

"""Test that our scraper still works fine with the real discogs website
"""

class TestDiscogsE2E(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testEan(self):
        ean = "7559618112"
        search = scraper(ean=ean)
        res = search.search()
        self.assertTrue(res)
        for key in ["artist", "title", "uri", "format", "tracklist", "year"]:
            self.assertTrue(res[key])
        self.assertEqual(res["artist"], u"Kyuss")

    def testArtistSearch(self):
        search = scraper(artist=["kyuss",])
        res = search.search()
        print res["results"][0]["title"]
        self.assertTrue(res)
        self.assertEqual(res["results"][0]["title"], u"Kyuss")
        # TODO: finish thinking about the format of returned results
        # (all discogs json ? our own object ?), and finish the test.

    def testKeyWordsSearch(self):
        kw = ["kyuss", "circus"]
        self.s = scraper(*kw)
        res = self.s.search()
        self.assertTrue(res)
        self.assertEqual(res["results"][0]["title"], u'Kyuss - ...And The Circus Leaves Town')
        # TODO: check all object keys and values

if __name__ == '__main__':
    unittest.main()
