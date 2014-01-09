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
# from ... import decitreScraper
sys.path.append(cdpp)
from chapitreScraper import scraper
from chapitreScraper import Book

"""
Test that our scraper still works fine with the real decitre website
"""

class testChapitreFromEan(unittest.TestCase):

    def setUp(self):
        ean = '9782035834256'
        self.s = scraper(ean=[ean,])
        self.bk_list = self.s.search()
        self.book = self.bk_list[0]

    def tearDown(self):
        pass

    def test_nbr_results(self):
        print self.bk_list
        print self.book.__print__()
        self.assertEqual(u"1", self.s._nbr_results())

    def test_product_list(self):
        self.assertEqual(1, len(self.s._product_list()), "one ean should give one book !")

    def test_search(self):
        self.assertTrue(self.bk_list)
        self.assertEqual(1, len(self.bk_list))
        self.assertTrue(self.book)

    def test_title(self):
        self.assertEqual(u"Les Miserables", self.book.title)

    def test_authors(self):
        auths = ["Victor Hugo",]
        self.assertEqual(auths, self.book.authors)

    def test_price(self):
        self.assertEqual(u'3,50', self.book.price)

    def test_book_details(self):
        b = Book(isbn="978-2-03-583425-6", ean="9782035834256",
                 editor="Larousse")
        self.assertEqual("Larousse", b.editor)
        self.assertEqual("978-2-03-583425-6", b.isbn)



if __name__ == '__main__':
    unittest.main()
