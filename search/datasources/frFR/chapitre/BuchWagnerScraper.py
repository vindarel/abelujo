#!/bin/env python
# -*- coding: utf-8 -*-

"""
German Buch Wagner bookshop scraper.
http://www.buch-wagner.de
"""

from bs4 import BeautifulSoup
from functools import wraps
import json
import logging
import re
import requests
import requests_cache
import sys
import traceback

requests_cache.install_cache()
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

SOURCE_NAME = "BuchWagner"
SOURCE_URL_BASE = u"http://www.buch-wagner.de"
SOURCE_URL_SEARCH = u"http://www.buch-wagner.de/SearchCmd?storeId=55250&catalogId=4099276460822233274&langId=-3&knv_header=yes&pageSize=12&beginIndex=0&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&pageView=image&searchBtn=Search&searchFld=CATEGORY&searchFldName=Bücher&searchFldCount=29&searchFldId=4099276460822241224&searchTerm="
ERR_OUTOFSTOCK = u"product out of stock"
TYPE_BOOK = "book"
TYPE_DVD = "dvd"
# there is no comic type.
TYPE_DEFAULT = TYPE_BOOK

# xpath to retrieve information on the main search result page.
SEARCH = {
    "TITLE": ""
    }


"""
Some fields are not available directly in the search results page
but in the book's details page, which needs another GET
request. We don't request it for every book, this would be too
long. We will fetch those complementary informations when the user
recquires it (when it clicks to add a book or to get more
informations about one). We call the postSearch method, defined
above, which gets those complementary fields, if any.
"""



def catch_errors(fn):
    """Catch all sort of exceptions, print them, print the stacktrace.

    This is helpful to refactor try/except blocks.
    I.e:

    ```
    def method():
        try:
            foo._title(url)
        except Exception as e:
            log.debug("error at ...")
    ```
    becomes
    ```
    @catch_errors
    def method():
        foo._title()
    ```
    """

    @wraps(fn)  # juste to preserve the name of the decorated fn.
    def handler(inst, arg):
        try:
            return fn(inst, arg)
        except Exception as e:
            log.error("Error at method {}: {}".format(fn.__name__, e))
            log.error("for search: {}".format(inst.query))
            # The traceback must point to its origin, not to this decorator:
            exc_type, exc_instance, exc_traceback = sys.exc_info()
            log.error("".join(traceback.format_tb(exc_traceback)))

    return handler

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
        search() to get a list of results, or specific methods (_ean,
        _authors, _title, …).

        parameters: either a list of words (fires a global search) or
        keywords arguments (key/values pairs, values being lists).

        Keys can be: label (for title), author_names,publisher, ean, …
        the same as decitre (without the dctr_ prefix).

        """

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

        self.r = requests.get(self.url)
        #TODO: to be continued
        self.soup = BeautifulSoup(self.r.text)

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

    def search(self, *args, **kwargs):
        """Searches books.

        Returns: a couple list of books / stacktraces.
        """
        bk_list = []
        stacktraces = []
        product_list = self._product_list()
        for product in product_list:
            b = {}
            b["data_source"] = SOURCE_NAME
            b["title"] = self._title(product)
            b["details_url"] = self._details_url(product)
            b["authors"] = self._authors(product)
            b["price"] = self._price(product)
            b["description"] = self._description(product)
            b["img"] = self._img(product)
            b["publishers"] = self._publisher(product)
            b["date"] = self._date(product)
            b["card_type"] = TYPE_BOOK
            # b["ean"] = # missing
            bk_list.append(b)

        return bk_list, stacktraces

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
