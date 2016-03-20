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

    query = ""


    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "librairiedeparis"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"http://www.librairie-de-paris.fr"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"http://www.librairie-de-paris.fr/listeliv.php?RECHERCHE=simple&LIVREANCIEN=2&MOTS="
        #: advanced url (searcf for isbns)
        self.SOURCE_URL_ADVANCED_SEARCH = u"http://www.librairie-de-paris.fr/listeliv.php?RECHERCHE=appro&LIVREANCIEN=2&MOTS="
        #: the url to search for an isbn.
        self.SOURCE_URL_ISBN_SEARCH = self.SOURCE_URL_SEARCH
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.URL_END = u"&x=0&y=0" # search books
        self.TYPE_BOOK = u"book"
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = u""
        #: Query param to search for the publisher (editeur)
        self.PUBLISHER_QPARAM = u"EDITEUR"
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = u"NOMBRE"
        self.NBR_RESULTS = 24 # 12 by default

    def __init__(self, *args, **kwargs):
        """
        """
        self.set_constants()
        super(Scraper, self).__init__(*args, **kwargs)

    def pagination(self):
        """Format the url part to grab the right page.

        Return: a str, the necessary url part to add at the end.
        """
        page_qparam = u""
        if type(self.page) in [type(u"u"), type("str")]:
            self.page = int(self.page)
        if self.NBR_RESULTS and self.NBR_RESULTS_QPARAM:
            page_qparam = u"&{}={}&{}={}".format(self.NBR_RESULTS_QPARAM,
                                                 self.NBR_RESULTS,
                                                 "DEBUT",
                                                 self.NBR_RESULTS * self.page)

        return page_qparam

    def _product_list(self):
        # The table doesn't have its css classes 'even' and 'odd' yet.
        plist = self.soup.find(class_='tab_listlivre')
        plist = plist.find_all('tr')
        if not plist:
            logging.info(u'Warning: product list is null, we (apparently) didn\'t find any result')
        return plist

    @catch_errors
    def _nbr_results(self):
        pass
        try:
            nbr_resultl_list = self.soup.find_all('div', class_='nbr_result')
            nbr_result = nbr_resultl_list[0].text.strip()
            res = re.search('\d+', nbr_result)
            if not res:
                print 'Error matching nbr_result'
            else:
                nbr = res.group(0)
                self.nbr_result = nbr
                logging.info(u'Nb of results: ' + nbr)
                return int(nbr)
        except Exception, e:
            print "\nError fetching the nb of results:", e

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="titre").a.attrs["href"].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _title(self, product):
        title = product.find(class_='titre').text.strip()
        logging.info(u'title: {}'.format(title))
        return title

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        authors = product.find(class_='auteurs').text # xxx many authors ?
        authors = authors.split('\n')
        authors = filter(lambda it: it != u"", authors)
        authors = [it.strip() for it in authors]
        logging.info(u'authors: '+ ', '.join(a for a in authors))
        return authors

    @catch_errors
    def _img(self, product):
        img = product.find(class_='visu').img['src']
        return img

    @catch_errors
    def _publisher(self, product):
        pub = product.find(class_="editeur").text.split('-')[0].strip()
        return pub

    def _price(self, product):
        "The real price, without discounts"
        try:
            price = product.find(class_='prix_indicatif').text.strip()
            price = priceFromText(price)
            price = priceStr2Float(price)
            return price
        except Exception, e:
            print 'Erreur getting price {}'.format(e)

    @catch_errors
    def _isbn(self, product):
        """
        Return: str
        """
        isbn = product.find(class_='gencod').text.strip()
        return isbn

    @catch_errors
    def _description(self, product):
        """To get with postSearch.
        """
        pass

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
                    logging.info(u'isbn: ' + details['isbn'])
                elif key == 'editeur :':
                    details['editor'] = k.em.text.strip()
                    logging.info(u'editor: ' + details['editor'])
                elif key == 'isbn :':
                    details['isbn'] = k.em.text.strip()
                    logging.info(u'isbn: '+ details['isbn'])

            if not details:
                logging.warning(u"Warning: we didn't get any details (isbn,…) about the book")
            return details

        except Exception, e:
            print 'Error on getting book details', e

    def search(self, *args, **kwargs):
        """Searches books. Returns a list of books.

        From keywords, fires a query on decitre and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=

        """
        bk_list = []
        stacktraces = []

        product_list = self._product_list()
        # nbr_results = self._nbr_results()
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
            b.isbn = self._isbn(product)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

def postSearch(card, isbn=None):
    """Get a card (dictionnary) with 'details_url'.

    Gets additional data:
    - description

    Check the isbn is valid. If not, return None. But that shouldn't happen !

    We can give the isbn as a keyword-argument (it can happen when we
    import data from a file). In that case, don't look for the isbn.

    Return a new card (dict) complemented with the new attributes.

    """
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
