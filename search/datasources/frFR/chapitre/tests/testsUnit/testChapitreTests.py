#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

# We could import with search.datasources.frFR.chapitre, but let's
# keep that module independant from the Django project.
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
sys.path.append(cdpp)

from chapitreScraper import scraper

class testChapitre(unittest.TestCase):
    """
    """

    def setUp(self):
        self.detailed_search_base_url = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam="
        self.search_keywords = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&quicksearch="

    def tearDown(self):
        pass

    def test_ean_search_url(self):
        ean = '9782035834256'
        req = scraper(ean=[ean,])
        ean_url = self.detailed_search_base_url + "&reference=" + ean
        self.assertTrue(req.url, ean_url)

    def test_keywords_search_url(self):
        req = scraper('victor', 'hugo')
        res_url = self.search_keywords + "victor+hugo"
        self.assertEqual(req.url, res_url)

    def test_many_authors(self):
        """The same as e2e test… but keep the cache.
        """
        ean = "9782756030067"  # a comic book with 3 authors
        scrap = scraper(ean=[ean,])
        bkl, traces = scrap.search()
        bk = bkl[0]
        self.assertEqual(len(bk["authors"]), 3)


if __name__ == '__main__':
    unittest.main()
