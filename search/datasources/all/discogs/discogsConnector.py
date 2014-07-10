#!/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import traceback

import requests

DATA_SOURCE_NAME = "Discogs.com"
DISCOGS_IMG_URL = "http://s.pixogs.com/image/"
DEFAULT_IMG_SIZE = "150"  # "90" or "150"
TYPE_CD = "cd"
TYPE_VINYL = "vinyl"

class Scraper:
    """Search releases on discogs, by keyword or ean.

    Limitations: see discogs doc.

    == Exceptions handling ==

    if an exception occurs, we want it to be catched early and not to
    be blocking, but we still want to tell the outside world that an
    exception occured. For example, the unit tests should exit on
    exception and the UI could say that an error occured.

    Consequently, the search() method returns the result AND a list of
    stacktraces.

    """

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

        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0"}

        self.stacktraces = []  # store stacktraces

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

        returns: a couple results / stacktraces.

        - publishers: a list of labels (str)
        """
        self.stacktraces = []
        if self.ean:
            card = {}
            card["data_source"] = DATA_SOURCE_NAME
            res = requests.get(self.url, headers=self.headers)
            try:
                json_res = json.loads(res.text)
                uri = json_res["results"][0]["uri"]
                print "uri: ", uri
            except Exception, e:
                print "Error searching ean %s: " % (self.ean,)
                print e
                return None, traceback.format_exc()

            # now getting the release id
            release = uri.split("/")[-1]
            print "release: ", release
            if release:
                release_url = self.api_url + "/releases/" + release
                print "release_url: ", release_url
                rel = requests.get(release_url, headers=self.headers)

                try:
                    val = json.loads(rel.text)
                    card["authors"] = val["artists"][0]["name"]
                    card["title"] = val["title"]
                    card["details_url"] = self.discogs_url + val["uri"]
                    card["format"] = val["formats"][0]["name"]
                    if 'label' in val:
                        # sometimes str, we need list
                        label = val['label']
                        if type(label) == str:
                            label = [label]
                        card['publishers'] = list(set(label))  # rm duplicates
                    card["tracklist"] = val["tracklist"]
                    card["year"] = val["year"]
                    card["card_type"] = TYPE_CD  # or vinyl
                    # images, genre,…
                    print "found album %s by %s" % (card["title"], card["authors"])

                except Exception, e:
                    print "Error on getting release informations of %s " % (release_url,)
                    print e
                    print "Traceback: %s" % (traceback.format_exc())
                    self.stacktraces.append(traceback.format_exc())

                return card, self.stacktraces

        else:
            # usual case: a search by keywords
            try:
                to_ret = []
                res = requests.get(self.url, headers=self.headers)
                if res.status_code == 403:
                    return to_ret, ["Discogs: 403 Error", traceback.format_exc()]
                json_res = json.loads(res.text)
                # ean_list = []  # don't return more than an entry by ean ? but some info and thumbnails can vary.
                for val in json_res["results"]:
                    # discogs' results can be a release, an artist, a label… we want releases.
                    if val["type"] == "release":
                        mycard = {}
                        mycard["data_source"] = DATA_SOURCE_NAME
                        # if type in val and type == release : filter on releases ?
                        if 'title' in val:
                            mycard["authors"] = [val['title'].split('-')[0]]  # what if the band name contains a - ?
                        if 'title' in val:
                            mycard["title"] = val["title"]
                        if 'uri' in val: mycard["details_url"] = self.discogs_url + val["uri"]
                        if 'format' in val: mycard["format"] = val["format"][0]
                        if 'label' in val:
                            # releases have often many labels (2 or 3).
                            # label is sometimes a str, sometimes a list.
                            label = val['label']
                            if type(label) == str:
                                label = [label]
                            # remove duplicates
                            mycard['publishers'] = list(set(label))

                        if 'barcode' in val:
                            if val["barcode"] != []:
                                mycard['ean'] = val['barcode'][0]
                            else:
                                # discogs now includes mp3 to the search results.
                                # Some vinyls don't have a barcode too.
                                # print "debug: following entry has no barcode: %s" % (val,)
                                pass
                        if 'thumb' in val:
                            # that link appears not to be available without Oauth registration any more.
                            # Construct the link we see with a search via the website.
                            # following works for albums, not artists or sthg else.TODO: artist search
                            mycard['img'] = self._construct_img_url(val['thumb'])
                        if 'genre' in val: mycard['genre'] = val['genre']
                        mycard['card_type'] = TYPE_CD  # to finish
                        # mycard["year"] = val["year"]

                        # append if ean not already present, if title ?
                        to_ret.append(mycard)
                        print "got a card: ", mycard

            except IndexError as e:
                print "IndexError with val %s" % (val,)
                print "Traceback: %s" % (traceback.format_exc())
                self.stacktraces.append(traceback.format_exc())
            except Exception as e:
                print "discogs search: unknown exception: %s" % (e,)
                self.stacktraces.append(traceback.format_exc())

            return to_ret, self.stacktraces

    def postSearch(self):
        """Return the info we could not get at the first time/connection.
        """
        return []

if __name__ == '__main__':
    # Testing data:
    scrap = Scraper("kyuss")
    scrap.search()
    scrap = Scraper("kyuss", "blues")
    scrap = Scraper(ean="7559618112")
    scrap.search()

    if len(sys.argv) > 1:
        exit(Scraper(*sys.argv[1:]).search())
