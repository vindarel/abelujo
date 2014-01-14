#!/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

class Scraper:

    def __init__(self, *args, **kwargs):
        """
        Constructs the query url to the discogs API.
        doc: http://www.discogs.com/developers/resources/database/release.html
        """
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
                    jrel = json.loads(rel.text)
                    # Do we return the json object or rather an object with
                    # a predefined format ?
                    card["artist"] = jrel["artists"][0]["name"]
                    card["title"] = jrel["title"]
                    card["uri"] = jrel["uri"]
                    card["format"] = jrel["formats"][0]["name"]
                    card["tracklist"] = jrel["tracklist"]
                    card["year"] = jrel["year"]
                    # images, genre,…
                    print "found album %s by %s" % (card["title"], card["artist"])
                    return card

                except Exception, e:
                    print "Error on getting release informations of %s " % (release_url,)
                    print e
                    return card

        else:
            # usual case
            res = requests.get(self.url)
            json_res = json.loads(res.text)
            results = []
            for val in json_res['results']:
                card = {}
                card['authors'] = val['title']
                card['title'] = val['title']
                card['price'] = 10
                card['ean'] = 'one ean'
                if 'label' in val: card['editor'] = val['label']
                card['details_url'] = val['uri']
                results.append(card)
                # import ipdb; ipdb.set_trace()
            # return json_res
            return results

if __name__ == '__main__':
    scrap = Scraper("kyuss")
    scrap.search()
    scrap = Scraper("kyuss", "blues")
    scrap = Scraper(ean="7559618112")
    scrap.search()

    # exit(main(sys.argv[1:]))
