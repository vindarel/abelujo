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
German Buch Wagner bookshop scraper.
http://www.buch-wagner.de
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
from datasources.utils.scraperUtils import isbn_cleanup
from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float
from datasources.utils.decorators import catch_errors

requests_cache.install_cache()
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

SOURCE_NAME = "buchWagner"
SOURCE_URL_BASE = u"http://www.buch-wagner.de"
SOURCE_URL_SEARCH = u"http://www.buch-wagner.de/SearchCmd?storeId=55250&catalogId=4099276460822233274&langId=-3&knv_header=yes&pageSize=12&beginIndex=0&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&pageView=image&searchBtn=Search&searchFld=CATEGORY&searchFldName=Bücher&searchFldCount=29&searchFldId=4099276460822241224&searchTerm="
ERR_OUTOFSTOCK = u"product out of stock"
TYPE_BOOK = "book"
TYPE_DVD = "dvd"
# there is no comic type.
TYPE_DEFAULT = TYPE_BOOK

"""
Some fields are not available directly in the search results page
but in the book's details page, which needs another GET
request. We don't request it for every book, this would be too
long. We will fetch those complementary informations when the user
recquires it (when it clicks to add a book or to get more
informations about one). We call the postSearch method, defined
above, which gets those complementary fields, if any.
"""




class Scraper:
    """Must have:

    - an init to construct the url

    - a search() method to fire the query, which must return a tuple
      search results/stacktraces.
    """

    query = ""

    def __init__(self, *args, **kwargs):
        """Constructs the query url with the given parameters, retrieves the
        page and parses it through BeautifulSoup. Then we can call
        search() to get a list of results, or specific methods (_isbn,
        _authors, _title, …).

        parameters: either a list of words (fires a global search) or
        keywords arguments (key/values pairs, values being lists).

        Keys can be: label (for title), author_names,publisher, isbn, …
        the same as decitre (without the dctr_ prefix).

        """

        if not args and not kwargs:
            print 'Error: give args to the query'

        # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',
                   # 'Host':'www.decitre.fr',
                   # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

        if kwargs:
            if 'isbn' in kwargs:
                # the name of isbn for the search is "reference"
                kwargs['reference'] = kwargs['isbn']
                kwargs.pop('isbn')
            self.url = SOURCE_URL_SEARCH  # ready to add query+args+parameters
            q = ""
            for k, v in kwargs.iteritems():
                urlend = "+".join(val for val in v)
                q += "&%s=%s" % (k, urlend)

            self.url += q

        else:
            self.query = "+".join(args)
            self.url = SOURCE_URL_SEARCH + self.query
            log.debug('search url: %s' % self.url)

        self.req = requests.get(self.url)
        #TODO: to be continued
        self.soup = BeautifulSoup(self.req.text)

    def _product_list(self):
        items = self.soup.find_all(class_="categorySummary")
        return items

    @catch_errors
    def _title(self, product):
        title = product.find(class_="prodTitle").h3.a.text.strip()
        return title

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="prodTitle").h3.a.attrs["href"].strip()
        details_url = SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _price(self, product):
        price = product.find(class_="bookPrise").text
        price = price.replace("EUR", "").strip()
        price = priceStr2Float(price)
        return price

    @catch_errors
    def _authors(self, product):
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
        img = product.find(class_="icoBook").img.attrs["src"]
        img = "http:" + img
        return img

    @catch_errors
    def _publisher(self, product):
        publisher = product.find(class_="year").text.strip()
        publisher = publisher.split("-")[1].strip()
        return [publisher]

    @catch_errors
    def _date(self, product):
        date = product.find(class_="year").text.strip()
        date = date.split("-")[0].split(":")[1].strip()
        return date

    @catch_errors
    def _isbn(self, product):
        pass

    def search(self, *args, **kwargs):
        """Searches books.

        Returns: a couple list of books / stacktraces.
        """
        bk_list = []
        stacktraces = []
        product_list = self._product_list()
        status = self.req.status_code
        if (status / 100) in [4,5]: # get 400 and 500 errors
            stacktraces.append("The remote source has a problem, we can not connect to it.")

        for product in product_list:
            b = {}
            b["data_source"] = SOURCE_NAME
            b["isbn"] = self._isbn(product) # missing
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
            b["card_type"] = TYPE_BOOK
            bk_list.append(b)

        return bk_list, stacktraces

def postSearch(card):
    """Complementary informations to fetch on a details' page.

    - isbn (compulsory)
    - description
    """
    url = card.get('details_url') or card.get('url')
    if not url:
        log.error("postSearch error: url is {} !".format(url))
        return None

    req = requests.get(url)
    soup = BeautifulSoup(req.text)
    details = soup.find_all(class_="productDetails-items-content")
    # The complementary information we need to return. Isbn is compulsory.
    to_ret = {"isbn": None}

    try:
        isbn = soup.find(class_="floatRight")
        isbn = isbn.find_all("p")[2].text.strip().split(":")[1].strip()
        isbn = isbn_cleanup(isbn)
        card["isbn"] = isbn
        card["isbn"] = isbn
        log.debug("postSearch of {}: we got isbn {}.".format(url, isbn))

    except Exception, e:
        log.debug("Error while getting the isbn of {} : {}".format(url, e))
        log.debug(e)

    try:
        description = soup.find(class_="alt_content").p.text.strip()
        card["description"] = description
    except Exception as e:
        log.debug("Error while getting the description of {}: {}".format(url, e))

    return card


if __name__=="__main__":
    import pprint
    scrap = Scraper("emma", "goldman")
    bklist, errors = scrap.search()
    map(pprint.pprint, bklist)
    print "Messages: ", errors
    print "Nb results: {}".format(len(bklist))
    print "1st book postSearch:"
    post = postSearch(bklist[0]["details_url"])
    print post
