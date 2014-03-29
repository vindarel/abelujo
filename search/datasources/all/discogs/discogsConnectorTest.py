#! /usr/bin/python
# -*- coding: utf-8 -*-

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


if __name__ == '__main__':
    unittest.main()

