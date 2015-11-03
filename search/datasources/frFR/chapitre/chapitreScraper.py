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

"""Program responsible to find books on chapitre.com. The search is
based on key words or on the ean.

The search works in 2 steps:

- fire the search and get a result page. In that page, we find books,
  the link to their detailed page, and some information. We get all we
  can of that page and return a list of dictionaries to display in the
  UI.

- but some important information may be missing from this page and be
  only available from the detailed book's page (like the ean, in the
  case of chapitre.com). But we MUST fetch the ean and register it to
  the database. So we first display the information we have, and when
  the user clicks "add this book", then we look for the ean on this
  book's details page. That way we don't do it for every book of the
  search result, that would be too long.

A scraper must have:
- a class named Scraper, with a method  "search"
- a function named postSearch.
"""

# example search url:
# http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&titre=&ne=&n=0&auteur=&peopleId=&quicksearch=victor+hugo&editeur=&reference=&plng=&optSearch=ALL&beginDate=&endDate=&mot_cle=&prix=&themeId=&collection=&subquicksearch=&page=1

from bs4 import BeautifulSoup
import logging
import os
import requests
import requests_cache
import sys
import json

# Add "datasources" to sys.path (independant from Django project,
# to clean up for own module).
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
cdppp, _ = os.path.split(cdpp)
sys.path.append(cdppp)

from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float

requests_cache.install_cache()
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

DATA_SOURCE_NAME = "chapitre"
CHAPITRE_BASE_URL = "http://www.chapitre.com"
ERR_OOSTOCK = 0
"""what to set the price with when we don't find it."""
TYPE_BOOK = "book"
TYPE_DVD = "dvd"
# there is no comic type.
TYPE_DEFAULT = TYPE_BOOK


class DomProduct:
    """factorize the request for the sources of the details; be able to call
    for _title or _details independently."""
    def __init__(self, product_detail):
        self.details_soup = ""
        self.product = product_detail

    def getDetailsSoup(self):
        if self.details_soup:
            return self.details_soup
        else:
            # get the url for the details and run the sources through BeautifulSoup
            title = self.product.find_all(class_='resultsProduct')[0]
            details_href = title.a.attrs['href']
            self.details_src = requests.get(details_href)
            self.details_soup = BeautifulSoup(self.details_src.text)
            return self.details_soup


class Scraper:
    """Must have:

    - an init to construct the url

    - a search() method to fire the query, which must return a tuple
      search results/stacktraces.
    """

    query = ""

    def _getDetailsSoup(self, product):
        if not self.details_soup:
            title = product.find_all('div', class_='h1')[0]
            details_href = title.a.attrs['href']
            self.details_src = requests.get(details_href) #it is slow
            self.details_soup = BeautifulSoup(self.details_src.text)

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
            # http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&titre=&ne=&n=0&auteur=&peopleId=&quicksearch=victor+hugo&editeur=&reference=&plng=&optSearch=ALL&beginDate=&endDate=&mot_cle=&prix=&themeId=&collection=&subquicksearch=&page=1
            self.url = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam="
            q = ""
            for k, v in kwargs.iteritems():
                urlend = "+".join(val for val in v)
                q += "&%s=%s" % (k, urlend) # working for ean 8-1-14

            self.url += q

        else:
            self.query = "+".join(args)
            self.url = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&quicksearch=" + self.query
            log.debug('search url: %s' % self.url)

        self.r = requests.get(self.url)
        #TODO: to be continued
        self.soup = BeautifulSoup(self.r.text)

    def _product_list(self):

        try:
            plist = self.soup.find_all('div', class_='resultsProduct')
            if not plist:
                log.warning('Warning: product list is null :/')
            return plist
        except Exception, e:
            log.debug('Error while getting the list of books: %s' % e)


    def _nbr_results(self):
        try:
            nbr_result_list = self.soup.find('div', class_='nb-results')
            res = nbr_result_list.find('strong').text
            if not res:
                log.warning('Error matching nbr_result')
                res = "undefined"
            return res

        except Exception, e:
            log.debug("\nError fetching the nb of results: %s" % e)

    def _details_url(self, product):
        try:
            title = product.product.find_all(class_='productTitle')[0]
            url = title.a.attrs['href']
            return CHAPITRE_BASE_URL + url
        except Exception, e:
            log.debug("Error while looking for the title: %s" % e)

    def _title(self, product):
        try:
            title = product.product.find_all(class_='productTitle')[0]
            title = title.text.strip()
            return title
        except Exception, e:
            log.debug("Error while looking for the title %s" % e)

    def _authors(self, product):
        authors = []
        try:
            authors_l = product.product.find_all('em')
            for a in authors_l:
                aut = a.text.strip()
                # author_hrf = aut.a.attrs["href"]
                aut = aut.replace("(auteur)", "").replace("(Auteur)", "").split(";")
                authors += aut
                authors = [a.strip() for a in authors]
            return authors
        except Exception, e:
            log.debug("Error with authors %s" % e)

    def _img(self, product):

        try:
            img_elt = product.product.find(class_='picture')
            img_url = img_elt.a.img.attrs['src']

            if not img_url:
                log.warning("img url is null")

            return img_url

        except Exception, e:
            log.error("Error getting the image's url")
            log.debug(e)
            return ""


    def _price(self, product):
        """The real price, without -5%.

        return: an int
        """
        try:
            # if product is out of stock, there is no price but a pb-inner with
            #   "ce produit est temporairement indisponible"

            realprice = product.product.find(class_='publicPrice')
            if realprice:
                price = priceFromText(realprice.text)
            else:
                pb = product.product.find(class_="actualPrice")
                if pb:
                    price = priceFromText(pb.text)
                else:
                    price = 0

            price = priceStr2Float(price)
            return price

        except Exception as e:
            log.debug('Error getting price', e)


    def _description(self, product):
        """no desc with chapitre"""
        try:
            details_soup = product.getDetailsSoup()
            # description = details_soup.find(id="description").text.strip()
            description = "no description with chapitre.com"
            if not description:
                log.info('the description is null :/')

            return description

        except Exception, e:
            log.debug('Error getting the description', e)


    def _publisher(self, product):
        try:
            publisher = product.product.find(class_='editeur')
            if publisher:
                publisher = publisher.text.strip("Editeur :").strip().strip(".")
            else:
                publisher = "undefined"
            return [publisher]

        except Exception, e:
            log.debug("Error while getting the publisher %s" % e)

    def _type(self, product):
        try:
            type_ = product.product.find(class_="sourceBOOKS")
            if type_:
                return TYPE_BOOK
            else:
                type_ = product.product.find(class_="sourceDVD")
                if type_:
                    return TYPE_DVD
                else:
                    return TYPE_DEFAULT

        except Exception, e:
            log.debug("Error while getting the type %s" % e)

    def search(self, *args, **kwargs): # rename in getBooks ?
        """Searches books. Returns a couple (list of books, stacktraces of
        errors).

        From keywords, fires a query on decitre and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=
        returns: a tuple (list of books dictionnaries, list of stacktraces).

        """
        bk_list = []
        stacktraces = []
        product_list = self._product_list()
        nbr_results = self._nbr_results()
        for product in product_list:
            dom_product = DomProduct(product)
            b = {}
            b["data_source"] = DATA_SOURCE_NAME
            b["title"] = self._title(dom_product)
            b["details_url"] = self._details_url(dom_product)
            b["search_url"] = self.url
            b["search_terms"] = self.query
            b["authors"] = self._authors(dom_product)

            b["price"] = self._price(dom_product)
            # Summary (4e de couv ?)
            # b["description"] = self._description(dom_product) #no desc with chapitre
            b["img"] = self._img(dom_product)
            b["publishers"] = self._publisher(dom_product)
            b["card_type"] = self._type(dom_product)

            bk_list.append(b)

        return bk_list, stacktraces


def postSearch(card):
    """gets the complementary informations of that product:

    - isbn (mandatory)
    - collection
    - summary (back cover text)

    card: a dict, with key 'details_url', the url to the details of
    the product where we can get the isbn (fiche produit)

    returns: a dict

    """
    url = card.get('details_url')
    if not url:
        return {}
    if not url.startswith('http'):
        log.debug("warning: url must start with http ;)")
    req = requests.get(url)
    soup = BeautifulSoup(req.text)
    details = soup.find_all(class_="productDetails-items-content")
    # The complementary information we need to return. Isbn is compulsory.
    to_ret = {"isbn": None,
              "collection": None,
              "summary": "",
    }
    COLLECTION_LABEL = u"collection"  # lower case
    collection_id = "ctl00_PHCenter_productTop_productDetail_rpDetails_ctl03_rpLinks_ctl00_hlLabel"

    try:
        card["isbn"] = soup.find(itemprop="isbn").text
        card["collection"] = soup.find(id=collection_id).text
        log.debug("postSearch of chapitre for {}: found {}".format(url, to_ret))

    except Exception as e:
        log.debug("Error while getting the isbn of {} : {}".format(url, e))

    try:
        node = soup.find(itemprop="description")
        card["summary"] = node.span.text.strip() + node.find(class_="cutedText").text.strip()
    except Exception as e:
        log.debug("Could not get the summary of {}: {}".format(url, e))

    return card
