#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import sys

import addict
import clize
import requests
import requests_cache
from bs4 import BeautifulSoup
from sigtools.modifiers import annotate
from sigtools.modifiers import kwoargs

logging.basicConfig(level=logging.INFO) #to manage with ruche
requests_cache.install_cache()

# Add "datasources" to sys.path (independant from Django project,
# to clean up for own module).
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
cdppp, _ = os.path.split(cdpp)
sys.path.append(cdppp)
from datasources.utils.baseScraper import Scraper as baseScraper
from datasources.utils.scraperUtils import is_isbn
from datasources.utils.scraperUtils import isbn_cleanup
from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float
from datasources.utils.decorators import catch_errors

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

class Scraper(baseScraper):

    """
    Advanced search available:
    - publisher: "ed[iteur]:name"
    """

    query = ""


    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "decitre"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"http://www.decitre.fr"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"http://www.decitre.fr/rechercher/result/?q="
        #: advanced url
        self.SOURCE_URL_ADVANCED_SEARCH = u"http://www.decitre.fr/rechercher/advanced/result/?"
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.TYPE_BOOK = "book"
        self.URL_END = u"&search-scope=0&product_type=3" # search books
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = "dctr_ean"
        self.PUBLISHER_QPARAM = "dctr_publisher_name"

    def __init__(self, *args, **kwargs):
        """
        """
        self.set_constants()
        super(Scraper, self).__init__(*args, **kwargs)

    def _product_list(self):
        plist = self.soup.find_all(class_='fiche-produit')
        if not plist:
            logging.info('Warning: product list is null :/')
        return plist

    def _nbr_results(self):
        try:
            nbr_resultl_list = self.soup.find_all('div', class_='nbr_result')
            nbr_result = nbr_resultl_list[0].text.strip()
            res = re.search('\d+', nbr_result)
            if not res:
                print 'Error matching nbr_result'
            else:
                nbr = res.group(0)
                self.nbr_result = nbr
                logging.info('Nb of results: ' + nbr)
                return int(nbr)
        except Exception, e:
            print "\nError fetching the nb of results:", e

    @catch_errors
    def _details_url(self, product):
        details_url = product.find("div", class_="h1").a.attrs["href"].strip()
        return details_url

    @catch_errors
    def _title(self, product):
        # title = product.find_all('div', class_='h1')[0]
        title = product.find_all('div', class_='h1')[0]
        title = title.text.strip()
        logging.info('title:'+ title)
        return title

    @catch_errors
    def _authors(self, product):
        authors = []
        authors_l = product.find_all('div', class_='authors')
        for a in authors_l:
            aut = a.find('a').text.strip()
            authors.append(aut)
        logging.info('authors: '+ ', '.join(a for a in authors))
        return authors

    @catch_errors
    def _img(self, product):
        img = product.find('img').attrs['data-src']
        return img

    @catch_errors
    def _publisher(self, product):
        pub = product.find(class_="first").text.strip()
        return pub

    def _price(self, product):
        "the real price, without -5%"
        return None
        try:
            details_soup = product.getDetailsSoup()
            block_right = details_soup.find(class_='prod-top-r')
            realprice = block_right.find(class_='old-price')
            if realprice.text.endswith(u'\xa0\u20ac'):
                realprice.text.replace(u'\xa0\u20ac', '') #get rid of € sign
            if realprice.text.endswith(u'€'):
                realprice.text.replace(u'€', "")

            price = realprice.text
            logging.info('price: ' + price)
            return price
        except Exception, e:
            print 'Erreur getting price', e


    @catch_errors
    def _description(self, product):
        """Get the description with an ajax call. Adds a little bit of overhead.
        """
        pid = product.find(attrs={"data-infobulle-product-id":True}).attrs["data-infobulle-product-id"]
        req = requests.get("http://www.decitre.fr/catalog/ajax/loadProductAttribute/?product={}&attribute=description".format(pid))
        description = req.content
        return description

    @catch_errors
    def _details(self, product):
        try:
            details_soup = product.getDetailsSoup()
            tech = details_soup.find(class_='technic')
            li = tech.find_all('li')

            details = {}
            for k in li:
                key = k.contents[0].strip().lower()
                if key == 'ean :':
                    details['isbn'] = k.em.text.strip()
                    logging.info('isbn: ' + details['isbn'])
                elif key == 'editeur :':
                    details['editor'] = k.em.text.strip()
                    logging.info('editor: ' + details['editor'])
                elif key == 'isbn :':
                    details['isbn'] = k.em.text.strip()
                    logging.info('isbn: '+ details['isbn'])

            if not details:
                logging.warning("Warning: we didn't get any details (isbn,…) about the book")
            return details

        except Exception, e:
            print 'Error on getting book details', e

    def search(self, *args, **kwargs): # rename in getBooks ?
        """Searches books. Returns a list of books.

        From keywords, fires a query on decitre and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=

        """
        bk_list = []
        stacktraces = []

        product_list = self._product_list()
        nbr_results = self._nbr_results()
        for product in product_list:
            b = addict.Dict()
            b.search_terms = self.query
            b.data_source = self.SOURCE_NAME
            b.search_url = self.url

            b.details_url = self._details_url(product)
            b.title = self._title(product)
            b.authors = self._authors(product)
            b.price = self._price(product)
            b.publishers = [self._publisher(product)]
            b.card_type = self.TYPE_BOOK
            b.img = self._img(product)
            b.summary = self._description(product)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

def postSearch(card, isbn=None):
    """Get a card (dictionnary) with 'details_url'.

    Gets additional data:
    - isbn
    - price

    Check the isbn is valid. If not, return None. But that shouldn't happen !

    We can give the isbn as a keyword-argument (it can happen when we
    import data from a file). In that case, don't look for the isbn.

    Return a new card (dict) complemented with the new attributes.

    """
    given_isbn = isbn
    url = card.get('details_url') or card.get('url')
    if not url:
        log.error("postSearch: we must find a key 'details_url' or 'url'")
        return None

    #: the needed attributes to populate
    to_ret = {
        "isbn": given_isbn,
        "price": None
        }
    req = requests.get(url)
    soup = BeautifulSoup(req.content, "lxml")

    if not given_isbn:
        try:
            isbn = soup.find(itemprop='sku').text.strip()
            isbn = isbn_cleanup(isbn)

            if not is_isbn(isbn):
                import ipdb; ipdb.set_trace()
                log.error("The isbn {} is not valid. Return nothing.".format(isbn))
                isbn = given_isbn or None

            card['isbn'] = isbn
        except Exception as e:
            log.error("postSearch: error while getting the isbn of {}: {}".format(url, e))

    try:
        product = soup.find(class_="product-main-information")
        price = product.find(class_="final-price").span.attrs['content']
        card['price'] = priceStr2Float(price)
    except Exception as e:
        log.error("postSearch: error while getting price of {}: {}".format(url, e))

    return card


@annotate(words=clize.Parameter.REQUIRED)
@kwoargs()
def main(*words):
    """
    words: keywords to search (or isbn/ean)
    """
    if not words:
        print "Please give keywords as arguments"
        return
    import pprint
    scrap = Scraper(*words)
    bklist, errors = scrap.search()
    print "Nb results: {}".format(len(bklist))
    bklist = [postSearch(it) for it in bklist]
    print "cards after postSearch:"
    map(pprint.pprint, bklist)

if __name__ == '__main__':
    clize.run(main)
