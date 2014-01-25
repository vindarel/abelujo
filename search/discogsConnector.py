#!/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys

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
                # mycard["authors"] = val["artists"][0]["name"]
                if 'title' in val: mycard["title"] = val["title"]
                if 'uri' in val: mycard["details_url"] = self.discogs_url + val["uri"]
                if 'format' in val: mycard["format"] = val["format"][0]
                if 'label' in val: mycard['editor'] = val['label']
                if 'barcode' in val: mycard['ean'] = val['barcode'][0]
                if 'thumb' in val: mycard['img'] = val['thumb']
                # mycard["year"] = val["year"]
                if 'genre' in val: mycard['genre'] = val['genre']
                #TODO: append if ean not already present
                to_ret.append(mycard)
                print "got a card: ", mycard
            # return json_res
            return to_ret

if __name__ == '__main__':
    scrap = Scraper("kyuss")
    scrap.search()
    scrap = Scraper("kyuss", "blues")
    scrap = Scraper(ean="7559618112")
    scrap.search()

    exit(Scraper(*sys.argv[1:]).search())
