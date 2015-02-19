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
import yaml

from buchWagnerScraper import Scraper
from buchWagnerScraper import postSearch

def filterAttribute(attr, dataresult, fdata):
    """Filter out elements from fdata.
    """
    return filter(lambda it: it.get(attr) == dataresult.get(attr),
                  fdata)

class testBuchWagner(unittest.TestCase):
    """Test the results of search() and postSearch() from a list of
    expected results stored in a yaml file.
    """

    def setUp(self):
        tfile = "test_buchwagner.yaml"
        with open(tfile, "rb") as f:
            self.datatest = yaml.load(f.read())

    def tearDown(self):
        pass


    def testSearch(self):
        for bktest in self.datatest:
            if bktest.get("search"):
                # Get real results (from cache)
                scrap = Scraper(*bktest["search"]["search_keywords"].split())
                bklist, errors = scrap.search()
                # Get the real results that matches the one we described in the yaml.
                dataresults = bktest["search"]["results"]
                filtered_res = filterAttribute("title", dataresults, bklist)
                filtered_res = filterAttribute("ean", dataresults, filtered_res)
                filtered_res = filterAttribute("price", dataresults, filtered_res)

                # Test the attributes.
                self.assertEqual(len(filtered_res), 1)
                for attr in ["title",
                             "ean",  # may be None
                             "price",
                             "publishers",
                             "authors",
                             "img",
                             "details_url"]:
                    # Better: use nose's test generators to test all attributes at once.
                    self.assertEqual(filtered_res[0].get(attr), dataresults.get(attr))

    def testPostSearch(self):
        for bktest in self.datatest:
            if bktest.get("postSearch"):
                postresult = postSearch(bktest["postSearch"]["url"])
                for attr in bktest["postSearch"]["results"]:
                    self.assertEqual(postresult[attr],
                                     bktest["postSearch"]["results"][attr])

if __name__ == '__main__':
    unittest.main()
