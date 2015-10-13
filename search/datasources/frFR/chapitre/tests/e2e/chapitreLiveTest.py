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
scraper = os.path.join(cdpp, 'decitreScraper')

sys.path.append(cdpp)
from chapitreScraper import Scraper
from chapitreScraper import postSearch
from chapitreScraper import Book

"""
Test that our scraper still works fine with the real decitre website
"""

class testChapitreFromEan(unittest.TestCase):

    def setUp(self):
        ean = '9782035834256'
        self.s = Scraper(ean=[ean,])  #TODO: we must disable the cache.
        self.bk_list = self.s.search()[0]  # the books, not the stacktraces
        self.book = self.bk_list[0]

    def tearDown(self):
        pass

    def test_nbr_results(self):
        self.assertEqual(u"1", self.s._nbr_results())

    def test_product_list(self):
        self.assertEqual(1, len(self.s._product_list()), "one ean should give one book !")

    def test_search(self):
        self.assertTrue(self.bk_list)
        self.assertEqual(1, len(self.bk_list))
        self.assertTrue(self.book)

    def test_title(self):
        self.assertTrue(u"Les Mis" in self.book["title"])  #XXX: the accent is inconsistent.

    def test_authors(self):
        auths = [u"Victor Hugo",]
        self.assertEqual(auths, self.book["authors"])

    def test_many_authors(self):
        """The cache is enabled in the scraper. Find how to disable it for end to end tests.
        """
        ean = "9782756030067"  # a comic book with 3 authors
        scrap = Scraper(ean=[ean,])
        bkl = scrap.search()
        bk = bkl[0][0]
        self.assertEqual(len(bk["authors"]), 3)

    def test_price(self):
        self.assertTrue(self.book["price"])
        # chapitre.com has undefined prices, but they should be rendered as Floats anyway.
        self.assertTrue(type(self.book["price"]) == type(0.5))

    def test_book_details(self):
        b = Book(isbn="978-2-03-583425-6", ean="9782035834256",
                 publisher="Larousse")
        self.assertEqual("Larousse", b.publisher)
        self.assertEqual("978-2-03-583425-6", b.isbn)


class TestChapitrePostSearch(unittest.TestCase):
    """Tests the postSearch method of the scraper, which gets complementary
    information from the book's product page.
    """

    def setUp(self):
        self.details_url = "http://www.chapitre.com/CHAPITRE/fr/BOOK/hugo-victor/les-miserables,962572.aspx"

    def test_postSearch(self):
        complements = postSearch(self.details_url)
        self.assertTrue("un couvert de plus" in complements['summary'])


if __name__ == '__main__':
    unittest.main()
