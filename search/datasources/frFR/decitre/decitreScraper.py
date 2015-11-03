#!/bin/env python
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
from datasources.utils.baseScraper import baseScraper
from datasources.utils.scraperUtils import priceFromText
from datasources.utils.scraperUtils import priceStr2Float
from datasources.utils.decorators import catch_errors

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

class Scraper(baseScraper):

    query = ""


    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "decitre"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"http://www.decitre.fr"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"http://www.decitre.fr/rechercher/result/?q="
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.TYPE_BOOK = "book"
        self.URL_END = u"&search-scope=0"

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


    def _price(self, product):
        "the real price, without -5%"
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


    def _description(self, product):
        try:
            details_soup = product.getDetailsSoup()
            description = details_soup.find(id="description").text.strip()
            if not description:
                logging.info('the description is null :/')

            logging.info('description: ' + description)
            return description

        except Exception, e:
            print 'Erreur getting the description', e


    def _details(self, product):
        try:
            details_soup = product.getDetailsSoup()
            tech = details_soup.find(class_='technic')
            li = tech.find_all('li')

            details = {}
            for k in li:
                key = k.contents[0].strip().lower()
                if key == 'ean :':
                    details['ean'] = k.em.text.strip()
                    logging.info('ean: ' + details['ean'])
                elif key == 'editeur :':
                    details['editor'] = k.em.text.strip()
                    logging.info('editor: ' + details['editor'])
                elif key == 'isbn :':
                    details['isbn'] = k.em.text.strip()
                    logging.info('isbn: '+ details['isbn'])

            if not details:
                logging.warning("Warning: we didn't get any details (ean,…) about the book" +
                             title)
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
            b.details_url = self._details_url(product)
            b.title = self._title(product)
            b.authors = self._authors(product)
            b.price = self._price(product)

            # Summary (4e de couv ?)
            b.description = self._description(product)
            b.img = self._img(product)
            # Technical details: ean, editor,…
            # details_dict = self._details(product)
            # b.set_properties(**details_dict)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

def postSearch(card):
    """Get a card (dictionnary) with 'details_url'.

    Scrapes data, with selenium if needed and get the needed information.

    Return a dict with new attributes.
    """
    url = card.get('details_url') or card.get('url')
    if not url:
        log.error("postSearch: we must find a key 'details_url' or 'url'")
        return None

    #: the needed attributes to populate
    to_ret = {
        "isbn": None,
        "price": None
        }
    req = requests.get(url)
    soup = BeautifulSoup(req.content)

    try:
        info = soup.find_all(class_="information")
        isbn = info[3].text.split('\n')[-1].strip()
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


@kwoargs()
def main(*args):
    """args: the ods file

    """
    import pprint
    scrap = Scraper("emma", "goldman")
    bklist, errors = scrap.search()
    map(pprint.pprint, bklist)
    print "Nb results: {}".format(len(bklist))
    print "1st book postSearch:"
    post = postSearch(bklist[0].get("details_url"))
    print post

if __name__ == '__main__':
    clize.run(main)
