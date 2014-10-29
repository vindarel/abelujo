#! /usr/bin/python
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

import unittest
from discogsConnector import Scraper

class TestDiscogs(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInitKwargs(self):
        kw = ["kyuss", "circus"]
        disc = Scraper(*kw)
        witness = "http://api.discogs.com/database/search?q=kyuss+circus"
        self.assertEqual(disc.url, witness)

    def testInitArgsEan(self):
        ean = "7559618112"
        disc = Scraper(ean=ean)
        self.assertEqual(disc.url, "http://api.discogs.com/database/search?q=7559618112")

    def testInitArtist(self):
        artist = ["kyuss"]
        disc = Scraper(artist=artist)
        self.assertEqual(disc.url, "http://api.discogs.com/database/search?q=kyuss&type=artist")

    def testInitVoid(self):
        disc = Scraper()
        self.assertEqual(disc.url, '')

    def testConstructImgUrl(self):
        discogs = Scraper('foo')
        api_url = "http://api.discogs.com/image/R-90-1768971-1242146278.jpeg"
        accessible_url = "http://s.pixogs.com/image/R-150-1768971-1242146278.jpeg"
        test_uri = discogs._construct_img_url(api_url, size="150")
        self.assertEqual(test_uri, accessible_url)

    def testNoJSON(self): # TODO: simulate a 403 error.
        pass


if __name__ == '__main__':
    unittest.main()
