
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

"""
Spanish book scraper for la casadellibro.com
http://www.casadellibro.com
"""

from bs4 import BeautifulSoup
import logging
import os
import requests
import requests_cache
import sys

# Add "datasources" to sys.path (independant from Django project,
# to clean up for own module).
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
cdppp, _ = os.path.split(cdpp)
sys.path.append(cdppp)
from datasources.utils.baseScraper import Scraper as baseScraper
from datasources.utils.baseScraper import postSearch
from datasources.utils.scraperUtils import isbn_cleanup
from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float
from datasources.utils.decorators import catch_errors

requests_cache.install_cache()
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

class Scraper(baseScraper):
    """
    """

    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "casadellibro"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"http://www.casadellibro.com"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"http://www.casadellibro.com/busqueda-generica?busqueda="
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.TYPE_BOOK = "book"
        self.URL_END = u"&idtipoproducto=-1&tipoproducto=1&nivel=5"


    query = ""

    def __init__(self, *args, **kwargs):
        """
        """
        self.set_constants()
        super(Scraper, self).__init__(*args, **kwargs)

    def _product_list(self):
        items = self.soup.find_all(class_="mod-list-item")
        return items

    @catch_errors
    def _title(self, product):
        return product.find(class_="title-link").text.strip()

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="title-link")["href"].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _price(self, product):
        price = product.find(class_="currentPrice").text
        price = price.replace(u"\u20ac", "").strip()  # remove euro sign.
        price = priceStr2Float(price)
        return price

    @catch_errors
    def _authors(self, product):
        authors = []
        authors.append(product.find(class_="mod-libros-author").text.strip())
        return authors

    @catch_errors
    def _description(self, product):
        """No description in the result page.
        There is a summup in the details page. See postSearch.
        """
        desc = product.find(class_="pb15")
        return desc.text.strip() if desc else None

    @catch_errors
    def _img(self, product):
        img = product.find(class_="img-shadow")["src"]
        return img

    @catch_errors
    def _publisher(self, product):
        publisher = product.find(class_="mod-libros-editorial").text.strip()
        split = publisher.split(",")
        if split:
            publisher = split[0] # split out the date.
        return [publisher]

    @catch_errors
    def _date(self, product):
        date = product.find(class_="mod-libros-editorial").text.strip()
        split = date.split(",")
        if len(split) > 1:
            date = split[1] # split out the publisher.
        return date

    @catch_errors
    def _isbn(self, product):
        pass

def postSearch(card):
    """Get the ean/isbn."""
    url = card.get('details_url') or card.get('url')
    if not url:
        log.error("postSearch error: url is False ! ({}).".format(url))
        return None

    to_ret = {"isbn": None}
    req = requests.get(url)
    soup = BeautifulSoup(req.text)

    try:
        isbn = soup.find(class_="book-header-2-subtitle-isbn").text
        isbn = isbn.replace("ISBN", "").strip()
        isbn = isbn_cleanup(isbn)
        card["isbn"] = isbn
        log.debug("postSearch of {}: we got isbn {}.".format(url, isbn))
    except Exception as e:
        log.debug("postSearch: error while getting the isbn of {}: {}".format(url, e))

    return card

if __name__=="__main__":
    import pprint
    scrap = Scraper("emma", "goldman")
    bklist, errors = scrap.search()
    map(pprint.pprint, bklist)
    print "Nb results: {}".format(len(bklist))
    print "1st book postSearch:"
    post = postSearch(bklist[0]["details_url"])
    print post
