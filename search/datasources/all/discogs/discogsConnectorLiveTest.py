#!/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import requests_cache
import sys
import unittest

# requests_cache.install_cache("memory")  # default is sqlite. I want to see API changes.
# Activate sqlite in dev mode ?
requests_cache.install_cache()

common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
scraper = os.path.join(cdpp, 'decitreScraper')

sys.path.append(cdpp)
from discogsConnector import Scraper as scraper

"""
Test that our scraper still works fine with the real discogs website.

We only look for releases (not artists or labels).
"""

class TestDiscogsE2E(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testEan(self):
        ean = "7559618112"
        search = scraper(ean=ean)
        res, traces = search.search()
        self.assertTrue(res)
        self.assertEqual(traces, [])
        for key in ["authors", "title", "details_url", "format", "tracklist", "year"]:
            self.assertTrue(res[key])
        self.assertEqual(res["authors"], u"Kyuss")

    # We are not interested in artist search, but in releases.
    # def testArtistSearch(self):
        # search = scraper(artist=["kyuss",])
        # res = search.search()
        # print res[0]["title"]
        # self.assertTrue(res)
        # self.assertEqual(res[0]["title"], u"Kyuss")

        # TODO: get the artist image ?
        # check we have access to the image
        # img = res[0]['img']
        # self.assertTrue(img, "the first result doesn't have an 'img' attr: can not carry on the tests.")
        # req = requests.get(img)
        # self.assertEqual(req.status_code, requests.codes.ok,
                         # "the image is not accessible: %s with %s " % (req.reason, img))

    def testKeyWordsSearch(self):
        kw = ["kyuss", "circus"]
        self.s = scraper(*kw)
        res, stacktraces = self.s.search()
        self.assertTrue(res)
        self.assertEqual(stacktraces, [], "the search threw the following exceptions:\n%s" % (stacktraces,))
        self.assertEqual(res[0]["title"], u'Kyuss - ...And The Circus Leaves Town')

        # Check we have access to the image:
        img = res[0]['img']
        self.assertTrue(img, "the first result doesn't have an 'img' attr: can not carry on the tests.")
        req = requests.get(img)
        self.assertEqual(req.status_code, requests.codes.ok,
                         "the image is not accessible: %s with %s " % (req.reason, img))
        # TODO: check all object keys and values

if __name__ == '__main__':
    unittest.main()
