#!/bin/env python
# -*- coding: utf-8 -*-

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

"""

# example search url:
# http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&titre=&ne=&n=0&auteur=&peopleId=&quicksearch=victor+hugo&editeur=&reference=&plng=&optSearch=ALL&beginDate=&endDate=&mot_cle=&prix=&themeId=&collection=&subquicksearch=&page=1

from bs4 import BeautifulSoup
import re
import requests
import requests_cache
import logging
import json

requests_cache.install_cache()

DATA_SOURCE_NAME = "Chapitre.com"
CHAPITRE_BASE_URL = "http://www.chapitre.com"
ERR_OOSTOCK = "produit indisponible"
TYPE_BOOK = "book"
TYPE_DVD = "dvd"
# there is no comic type.
TYPE_DEFAULT = TYPE_BOOK

class Book(object):
    """A title, list of authors,…

    The following fields are not available in the search results page
    but in the book's own page. So when the user wants to add a book
    or get more informations about one, abelujo calls the postSearch
    method which gets those complementary fields.

    - ean
    - collection

    """
    title = u""
    authors = []

    def __init__(self, *args, **kwargs):
        """
        """
        self.authors = []
        self.ean = u""
        self.isbn = u""
        self.publishers = u""
        self.price = 0
        self.img = u""
        #: name of the source
        self.data_source = u""
        #: link to the product's page
        self.details_url = u""
        self.description = u"" # null with chapitre

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __print__(self):
        """Pretty output"""
        print '"' + self.title + '", ' + " ".join([a for a in self.authors])
        print "\t" + self.publishers + " " + self.price + " ean: " + self.ean
        print "\tcover: " + self.img
        print "\n"

    def __todict__(self):
        res = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                res[attr] = getattr(self, attr)

        return res

    def __json__(self):
        """Returns a json representation of the object's attributes"""
        res = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                res[attr] = getattr(self, attr)

        return json.dumps(res, indent=4) #TODO:remove indent for prod


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


class scraper:

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

        logging.info('args: ' + ' '.join(a for a in args))
        if not args and not kwargs:
            print 'Error: give args to the query'

        # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',
                   # 'Host':'www.decitre.fr',
                   # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

        logging.info('args, kwargs: ',  args, kwargs)
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
            logging.info('on recherche: ' + self.url)

        else:
            self.query = "+".join(args)
            self.url = "http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&quicksearch=" + self.query
            print 'search url: ', self.url

        self.r = requests.get(self.url)
        #TODO: to be continued
        self.soup = BeautifulSoup(self.r.text)

    def _product_list(self):

        try:
            plist = self.soup.find_all('div', class_='resultsProduct')
            if not plist:
                logging.info('Warning: product list is null :/')
            return plist
        except Exception, e:
            print 'Error while getting the list of books', e


    def _nbr_results(self):
        try:
            nbr_result_list = self.soup.find('div', class_='nb_results')
            res = nbr_result_list.find('strong').text
            if not res:
                print 'Error matching nbr_result'
                res = "undefined"
            logging.info("nbr of results: " + res)
            return res

        except Exception, e:
            print "\nError fetching the nb of results:", e

    def _details_url(self, product):
        try:
            title = product.product.find_all(class_='productTitle')[0]
            url = title.a.attrs['href']
            logging.info('url:'+ url)
            return CHAPITRE_BASE_URL + url
        except Exception, e:
            print "Error while looking for the title", e

    def _title(self, product):
        try:
            title = product.product.find_all(class_='productTitle')[0]
            title = title.text.strip()
            logging.info('title:'+ title)
            return title
        except Exception, e:
            print "Error while looking for the title", e

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
            logging.info('authors: '+ ', '.join(a for a in authors))
            return authors
        except Exception, e:
            print "Error with authors", e

    def _img(self, product):

        try:
            img_elt = product.product.find(class_='picture')
            img_url = img_elt.a.img.attrs['src']

            if not img_url:
                logging.warning("img url is null")

            logging.info("img url: " + img_url)
            return img_url

        except Exception, e:
            logging.exception("Error getting the image's url")
            print e
            return ""

    def _price(self, product):
        "the real price, without -5%"
        try:
            # if product is out of stock, there is no price but a pb-inner with
            #   "ce produit est temporairement indisponible"

            realprice = product.product.find(class_='publicPrice')
            if realprice:
                match = re.search('\d+,?\d*', realprice.text)
                price = match.group()
            else:
                pb = product.product.find(class_="pb-inner")
                if pb:
                    price = ERR_OOSTOCK
                else:
                    price = "undefined"

            logging.info('price: ' + price)
            return price
        except Exception, e:
            print 'Error getting price', e


    def _description(self, product):
        """no desc with chapitre"""
        try:
            details_soup = product.getDetailsSoup()
            # description = details_soup.find(id="description").text.strip()
            description = "no description with chapitre.com"
            if not description:
                logging.info('the description is null :/')

            logging.info('description: ' + description)
            return description

        except Exception, e:
            print 'Error getting the description', e


    def _publisher(self, product):
        try:
            publisher = product.product.find(class_='editeur')
            if publisher:
                publisher = publisher.text.strip("Editeur :").strip().strip(".")
            else:
                publisher = "undefined"
            logging.info('publisher:' + publisher)
            return [publisher]

        except Exception, e:
            print "Error while getting the publisher", e

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
            print "Error while getting the type", e

    def search(self, *args, **kwargs): # rename in getBooks ?
        """Searches books. Returns a list of books.

        From keywords, fires a query on decitre and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=

        """
        bk_list = []
        product_list = self._product_list()
        nbr_results = self._nbr_results()
        # print "nbr_results: "+ nbr_results
        for product in product_list:
            b = Book()
            dom_product = DomProduct(product)
            b.data_source = DATA_SOURCE_NAME
            b.title = self._title(dom_product)
            b.details_url = self._details_url(dom_product)
            b.authors = self._authors(dom_product)

            b.price = self._price(dom_product)
            # Summary (4e de couv ?)
            # b.description = self._description(dom_product) #no desc with chapitre
            b.img = self._img(dom_product)
            b.publishers = self._publisher(dom_product)
            b.card_type = self._type(dom_product)

            bk_list.append(b.__todict__())

        return bk_list


def postSearch(url):
    """gets the complementary informations of that product:

    - ean (mandatory)
    - collection

    url: the url to the details of the product where we can get the ean (fiche produit)

    returns: a dict
    """
    if not url.startswith('http'):
        print "warning: url must start with http ;)"
    req = requests.get(url)
    soup = BeautifulSoup(req.text)
    details = soup.find_all(class_="productDetails-items-content")
    # The complementary information we need to return. Ean is compulsory.
    to_ret = {"ean": None,
              "collection": None}
    EAN_LABEL = "isbn"
    COLLECTION_LABEL = u"collection"  # lower case

    try:
        for det in details:
            if (det.span is not None and det.span.attrs is not None and
                det.span.attrs['itemprop'] is not None):
                itemprop = det.span.attrs["itemprop"]
                itemtext = det.span.text.strip()
                if itemprop == EAN_LABEL:
                    # this is EAN13
                    print "========= ean found: ", itemtext
                    to_ret["ean"] = itemtext

            else:
                try:
                    parent = det.findParent()
                    itemprop = parent.span.text.strip().strip(":").strip().lower()
                    if itemprop == COLLECTION_LABEL:
                        itemtext = parent.a.text
                        to_ret["collection"] = itemtext
                        print "=== postSearch: found collection: %s" % (itemtext,)
                except Exception:
                    pass

        return to_ret

    except Exception, e:
        print "Error while getting the ean of %s :" % (url,)
        print e
        return to_ret
