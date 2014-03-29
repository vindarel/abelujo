#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest


common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
scraper = os.path.join(cdpp, 'decitreScraper')

# http://stackoverflow.com/questions/714063/python-importing-modules-from-parent-folder
# from ... import chapitreScraper
sys.path.append(cdpp)
from chapitreScraper import scraper

class testChapitre(unittest.TestCase):
    """
    """

    def setUp(self):
        self.detailed_search_base_url = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam="
        self.search_keywords = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&quicksearch="
        pass

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

if __name__ == '__main__':
    unittest.main()
