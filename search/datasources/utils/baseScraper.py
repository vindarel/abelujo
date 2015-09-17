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
Base scraper to build new ones.
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
from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float
from datasources.utils.decorators import catch_errors

requests_cache.install_cache()
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


"""Some fields are not available directly in the search results page
but in the book's details page, which needs another GET
request. We don't request it for every book, this would be too
long. We will fetch those complementary informations when the user
recquires it (when it clicks to add a book or to get more
informations about one). We call the postSearch method, defined
above, which gets those complementary fields, if any.

Shall we use xpath ?
---

Using xpath expressions would allow to further factorize code.  We
prefer not to use them as of today since many elements need
post-processing (cleanup, transformation to list, etc).
"""


class baseScraper(object):
    """Base class to build scrapers. Mostly used for the __init__ and
    postSearch methods. A subclass will redefine the methods used to
    really extract the data.

    Must have:

    - an init to construct the url

    - a search() method to fire the query, which must return a tuple
      (list of search results/stacktraces). A search result is a dict.

    """

    query = ""

    def set_constants(self):
        self.SOURCE_NAME = "name"
        self.SOURCE_URL_BASE = u"http//url-base"
        self.SOURCE_URL_SEARCH = u"url-search"
        ERR_OUTOFSTOCK = u"product out of stock"
        self.TYPE_BOOK = "book"
        self.TYPE_DVD = "dvd"
        # there is no comic type.
        self.TYPE_DEFAULT = TYPE_BOOK


    def __init__(self, *args, **kwargs):
        """Constructs the query url with the given parameters, retrieves the
        page and parses it through BeautifulSoup. Then we can call
        search() to get a list of results, or specific methods (_ean,
        _authors, _title, …).

        parameters: either a list of words (fires a global search) or
        keywords arguments (key/values pairs, values being lists).

        Keys can be: label (for title), author_names,publisher, ean, …
        the same as decitre (without the dctr_ prefix).

        """

        self.set_constants()

        if not args and not kwargs:
            print 'Error: give args to the query'

        # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',
                   # 'Host':'www.decitre.fr',
                   # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

        if kwargs:
            if 'ean' in kwargs:
                # the name of ean for the search is "reference"
                kwargs['reference'] = kwargs['ean']
                kwargs.pop('ean')
            self.url = self.SOURCE_URL_SEARCH  # ready to add query+args+parameters
            q = ""
            for k, v in kwargs.iteritems():
                urlend = "+".join(val for val in v)
                q += "&%s=%s" % (k, urlend)

            self.url += q

        else:
            self.query = "+".join(args)
            self.url = self.SOURCE_URL_SEARCH + self.query

        log.debug('search url: %s' % self.url)
        self.url += self.URL_END
        self.r = requests.get(self.url)
        #TODO: to be continued
        self.soup = BeautifulSoup(self.r.text)

    def _product_list(self):
        """The css class that every block of book has in common.

        returns: a list of type soup that contain each the information
        about a single book.
        """
        items = self.soup.find_all(class_="categorySummary")
        return items

    @catch_errors
    def _title(self, product):
        title = product.find(class_="prodTitle").h3.a.text.strip()
        return title

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="prodTitle").h3.a.attrs["href"].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _price(self, product):
        """return a float."""
        price = product.find(class_="bookPrise").text
        price = price.replace("EUR", "").strip()
        price = priceStr2Float(price)
        return price

    @catch_errors
    def _authors(self, product):
        """return a list of strings."""
        authors = []
        authors.append(product.find(class_="prodSubTitle").h3.a.text.strip())
        return authors

    @catch_errors
    def _description(self, product):
        """No description in the result page.
        There is a summup in the details page. See postSearch.
        """
        pass

    @catch_errors
    def _img(self, product):
        """return the full url to the cover."""
        img = product.find(class_="icoBook").img.attrs["src"]
        img = "http:" + img
        return img

    @catch_errors
    def _publisher(self, product):
        """return a list of strings."""
        publisher = product.find(class_="year").text.strip()
        publisher = publisher.split("-")[1].strip()
        return [publisher]

    @catch_errors
    def _date(self, product):
        """return a string."""
        date = product.find(class_="year").text.strip()
        date = date.split("-")[0].split(":")[1].strip()
        return date

    @catch_errors
    def _ean(self, product):
        pass

    def search(self, *args, **kwargs):
        """Searches books.

        Returns: a couple list of books / stacktraces.
        """
        bk_list = []
        stacktraces = []
        product_list = self._product_list()
        for product in product_list:
            b = {}
            b["data_source"] = self.SOURCE_NAME
            b["ean"] = self._ean(product) # missing
            b["title"] = self._title(product)
            b["details_url"] = self._details_url(product)
            b["search_url"] = self.url
            b["search_terms"] = self.query
            b["authors"] = self._authors(product)
            b["price"] = self._price(product)
            b["description"] = self._description(product)
            b["img"] = self._img(product)
            b["publishers"] = self._publisher(product)
            b["date"] = self._date(product)
            b["card_type"] = self.TYPE_BOOK
            bk_list.append(b)

        return (bk_list, stacktraces)

def postSearch(url):
    """Complementary informations to fetch on a details' page.

    - ean (compulsory)
    - description
    """
    if not url:
        log.error("postSearch error: url is {} !".format(url))
        return None

    req = requests.get(url)
    soup = BeautifulSoup(req.text)
    details = soup.find_all(class_="productDetails-items-content")
    # The complementary information we need to return. Ean is compulsory.
    to_ret = {"ean": None}

    try:
        ean = soup.find(class_="floatRight")
        ean = ean.find_all("p")[2].text.strip().split(":")[1].strip()
        to_ret["ean"] = ean
        to_ret["isbn-13"] = ean
        log.debug("postSearch of {}: we got ean {}.".format(url, ean))

    except Exception, e:
        log.debug("Error while getting the ean of {} : {}".format(url, e))
        log.debug(e)

    try:
        description = soup.find(class_="alt_content").p.text.strip()
        to_ret["description"] = description
    except Exception as e:
        log.debug("Error while getting the description of {}: {}".format(url, e))

    return to_ret


if __name__=="__main__":
    import pprint
    scrap = Scraper("emma", "goldman")
    bklist, errors = scrap.search()
    map(pprint.pprint, bklist)
    print "Nb results: {}".format(len(bklist))
    print "1st book postSearch:"
    post = postSearch(bklist[0]["details_url"])
    print post
