#!/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys

DISCOGS_IMG_URL = "http://s.pixogs.com/image/"
DEFAULT_IMG_SIZE = "150"  # "90" or "150"
TYPE_CD = "cd"
TYPE_VINYL = "vinyl"

class Scraper:

    def __init__(self, *args, **kwargs):
        """
        Constructs the query url to the discogs API.
        doc: http://www.discogs.com/developers/resources/database/release.html
        """
        self.discogs_url = "http://discogs.com"
        self.api_url = "http://api.discogs.com"
        self.db_search = self.api_url + "/database/search?q="
        self.url = ""
        self.ean = None

        if not args and not kwargs:
            print "give some search keywords"

        if args:
            query = "+".join(arg for arg in args)
            self.url = self.db_search + query
            print "we'll search: " + self.url

        if kwargs:
            if "ean" in kwargs:
                self.ean = kwargs["ean"]
                self.url = self.db_search + self.ean
                print "ean search: " + self.url

            elif "artist" in kwargs:
                query = "+".join(arg for arg in kwargs["artist"])
                self.url = self.db_search + query + "&type=" + "artist"
                print "on cherche: " + self.url

    def _construct_img_url(self, thumb_url, search_type="R", size=DEFAULT_IMG_SIZE):
        """As of beginning of march 2014, it appears the thumbnail url we were
        getting through the api search requires an Oauth
        authentication. We don't want to do that (yet?), so here's a
        way to go to the thumbnail we see with a manual search on the
        website.

        search_type: release -> R, artist -> A ??
        size: str, "90" or "150"
        return type: str

        Example:
        >>> _construct_img_url(http://api.discogs.com/image/R-90-1768971-1242146278.jpeg)
        http://s.pixogs.com/image/R-150-1768971-1242146278.jpeg

        """
        try:
            split = thumb_url.split("-")
            assert len(split) > 2
            pixogs_url = DISCOGS_IMG_URL + search_type
            myimg = "-".join([pixogs_url, size] + split[-2:])
            return myimg
        except Exception, e:
            # It doesn t work in some cases
            # print "--- error getting the image url: ", e
            return ""

    def search(self):
        """
        if ean search, returns a dict with all the info
        """
        if self.ean:
            card = {}
            res = requests.get(self.url)
            json_res = json.loads(res.text)
            try:
                uri = json_res["results"][0]["uri"]
                print "uri: ", uri
            except Exception, e:
                print "Error searching ean %s: " % (self.ean,)
                print e
                return None

            # now getting the release id
            release = uri.split("/")[-1]
            print "release: ", release
            if release:
                release_url = self.api_url + "/releases/" + release
                print "release_url: ", release_url
                rel = requests.get(release_url)

                try:
                    val = json.loads(rel.text)
                    # Do we return the json object or rather an object with
                    # a predefined format ?
                    card["authors"] = val["artists"][0]["name"]
                    card["title"] = val["title"]
                    card["details_url"] = self.discogs_url + val["uri"]
                    card["format"] = val["formats"][0]["name"]
                    if 'label' in val: card['editor'] = val['label']
                    card["tracklist"] = val["tracklist"]
                    card["year"] = val["year"]
                    card["card_type"] = TYPE_CD  # or vinyl
                    # images, genre,…
                    print "found album %s by %s" % (card["title"], card["authors"])
                    return card

                except Exception, e:
                    print "Error on getting release informations of %s " % (release_url,)
                    print e
                    return card

        else:
            # usual case
            res = requests.get(self.url)
            json_res = json.loads(res.text)
            to_ret = []
            ean_list = []
            for val in json_res["results"]:
                mycard = {}
                if 'title' in val:
                    mycard["authors"] = [val['title'].split('-')[0]]  # what if the band name contains a - ?
                if 'title' in val:
                    mycard["title"] = val["title"]
                if 'uri' in val: mycard["details_url"] = self.discogs_url + val["uri"]
                if 'format' in val: mycard["format"] = val["format"][0]
                if 'label' in val: mycard['editor'] = val['label']
                if 'barcode' in val: mycard['ean'] = val['barcode'][0]
                if 'thumb' in val:
                    # that link appears not to be available without Oauth registration any more.
                    # Construct the link we see with a search via the website.
                    # following works for albums, not artists or sthg else.TODO: artist search
                    mycard['img'] = self._construct_img_url(val['thumb'])
                # mycard["year"] = val["year"]
                if 'genre' in val: mycard['genre'] = val['genre']
                mycard['card_type'] = TYPE_CD  # to finish

                # append if ean not already present, if title ?
                to_ret.append(mycard)
                print "got a card: ", mycard
            return to_ret

if __name__ == '__main__':
    scrap = Scraper("kyuss")
    scrap.search()
    scrap = Scraper("kyuss", "blues")
    scrap = Scraper(ean="7559618112")
    scrap.search()

    exit(Scraper(*sys.argv[1:]).search())
