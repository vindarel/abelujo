# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import unicodecsv
import termcolor

from django.utils.translation import ugettext as _

from search.models.utils import is_isbn
from search.datasources.bookshops.all.discogs import discogsScraper as discogs  # noqa: F401
from search.datasources.bookshops.all.momox import momox  # noqa: F401
from search.datasources.bookshops.deDE.buchlentner import \
    buchlentnerScraper as buchlentner  # noqa: F401
from search.datasources.bookshops.esES.casadellibro import \
    casadellibroScraper as casadellibro  # noqa: F401
from search.datasources.bookshops.frFR.librairiedeparis import \
    librairiedeparisScraper as librairiedeparis  # noqa: F401
from search.datasources.bookshops.frFR.dilicom import \
    dilicomScraper as dilicom  # noqa: F401
from search.datasources.bookshops.frFR.lelivre import \
    lelivreScraper as lelivre  # noqa: F401
from search.datasources.bookshops.frFR.filigranes import \
    filigranesScraper as filigranes  # noqa: F401
from search.datasources.bookshops.all.bookdepository import \
    bookdepositoryScraper as bookdepository  # noqa: F401
from search.models import Card

from abelujo import settings

from search.models import utils

try:
    # The Electre API connector is installed separetely.
    import pyelectre
except:
    pass

#: Default datasource to be used when searching isbn, if source not supplied.
DEFAULT_DATASOURCE = "librairiedeparis"
if os.getenv('DILICOM_PASSWORD') and os.getenv('DILICOM_PASSWORD').strip():
    DEFAULT_DATASOURCE = 'dilicom'
    print(termcolor.colored('default datasource is DILICOM', 'blue'))

def electre_enabled():
    return os.getenv('ELECTRE_PASSWORD') is not None \
        and os.getenv('ELECTRE_USER') is not None

if electre_enabled():
    DEFAULT_DATASOURCE = 'electre'
    print(termcolor.colored('default datasource is ELECTRE', 'blue'))

if os.getenv('DEFAULT_DATASOURCE') and os.getenv('DEFAULT_DATASOURCE').strip():
    DEFAULT_DATASOURCE = os.getenv('DEFAULT_DATASOURCE')

def get_datasource_from_lang(lang):
    """From a lang (str), return the name (str) of the datasource module.

    And for CDs ? The client should be in "recordsop" mode.
    """
    if os.getenv('DEFAULT_DATASOURCE'):
        # Required to set the swiss source by default over the french one.
        return os.getenv('DEFAULT_DATASOURCE')

    if not lang:
        return DEFAULT_DATASOURCE

    if lang.startswith("fr") and not os.getenv('DILICOM_PASSWORD'):
        return "librairiedeparis"
    elif lang.startswith("fr") and os.getenv('DILICOM_PASSWORD'):
        return "dilicom"
    elif lang.startswith('ch'):
        return 'lelivre'
    elif lang.startswith("de"):
        return "buchlentner"
    elif lang.startswith("es"):
        return "casadellibro"
    elif lang in ["discogs", "momox"]:
        return lang
    else:
        return DEFAULT_DATASOURCE


def search_on_data_source(data_source, search_terms, PAGE=1):
    """
    Search with the appropriate scraper.

    - data_source is the name of an imported module.  Electre takes
      priority (it supports EAN search and free search, but not search of
      many EANs).
    - search_terms: list of strings.

    Return: a tuple (search results, stacktraces). Search result is a
    list of dicts.
    """
    if data_source == 'electre':
        res, traces = pyelectre.search_on_electre(search_terms)
    else:
        # get the imported module by name.
        # They all must have a class Scraper.
        scraper = getattr(globals()[data_source], "Scraper")
        # res, traces = scraper(*search_terms).search()
        res, traces = scraper(search_terms, PAGE=PAGE).search()

    # Check if we already have these cards in stock (with isbn).
    res = Card.is_in_stock(res)

    return res, traces


def dilicom_enabled():
    """
    Return a boolean indicating if the connection to Dilicom is possible.
    Currently, check we have the required environment variables.
    """
    return os.getenv('DILICOM_PASSWORD') is not None \
        and os.getenv('DILICOM_USER') is not None


def update_from_dilicom(card):
    """
    Update data: price, price excl vat, vat, availability, distributor,
    dimensions, weight.
    - card: card object.

    Return:
    - card,
    - list of messages (str).
    """
    if not card or not card.isbn or not (is_isbn(card.isbn)):
        return card, []

    scraper = getattr(globals()['dilicom'], "Scraper")
    res, traces = scraper(card.isbn).search()

    if res and res[0]:
        to_save = False
        res = res[0]
        if card.price != res['price']:
            card.price = res['price']
            to_save = True

        if res['theme'] and card.theme != res['theme']:
            card.theme = res['theme']
            to_save = True

        if res.get('width') and card.width != res.get('width'):
            card.width = res.get('width')
            to_save = True
        if res.get('weight') and card.weight != res.get('weight'):
            card.weight = res.get('weight')
            to_save = True
        if res.get('height') and card.height != res.get('height'):
            card.height = res.get('height')
            to_save = True
        if res.get('thickness') and card.thickness != res.get('thickness'):
            card.thickness = res.get('thickness')
            to_save = True
        if res.get('details_url') and card.width != res.get('details_url'):
            card.details_url = res.get('details_url')
            to_save = True
        if res.get('data_source') and card.width != res.get('data_source'):
            card.data_source = res.get('data_source')
            to_save = True

        # # "price_excl_vat" is already a model property.
        # # We'll use the "fmt" one.
        # if card.price_excl_vat != res.get('price_excl_vat'):
        #     card.price_excl_vat = res.get('price_excl_vat')
        #     to_save = True

        if to_save:
            card.save()

        # trick: add object fields, not saved to the DB, only for display.
        card.vat1 = res.get('vat1')
        card.price_excl_vat_fmt = res.get('price_excl_vat_fmt')
        card.dilicom_price_excl_vat = res.get('dilicom_price_excl_vat')

        card.availability = res['availability']
        card.availability_fmt = res['availability_fmt']

    else:
        res = card
    return card, traces


def update_from_electre(card):
    """
    Update this card from Electre's API (using the pyelectre Electre).
    Search by ISBN and update the important fields.
    """
    if not card or not card.isbn or not (is_isbn(card.isbn)):
        return card, []

    res, traces = pyelectre.search_on_electre(card.isbn)
    if res and res[0]:
        res = res[0]
        newcard = Card.update_from_dict(card, res,
                                        distributor_name=res.get('distributor_name'),
                                        distributor_gln=res.get('distributor_gln'),
            )
        return newcard

    return card, traces


def _check_csv_format(rows):
    """
    For all these rows, check we have an ISBN and an integer.

    Return: boolean, messages.
    """
    for row in rows:
        if not row and not row[0]:
            return None, ["rows missing data. They are expected to have an ISBN and a number."]
        if not is_isbn(row[0]):
            return False, ["Not all lines contain an ISBN."]
        try:
            int(row[1])
        except Exception as e:
            print(e)
            return False, ["Not all lines contain a valid number."]

    return True, []

def extract_all_isbns_quantities(inputrows):
    """
    From a list of lines, find the ISBNs and an associated quantity.
    Ignore the other columns.

    If we have only lines of ISBNs, OK, associate 1 quantity by default.
    If we have a comma-separated CSV with an ISBN and a number, OK.
    If we have a space-separated CSV with an ISBN and a number, OK.

    If we have a CSV with more rows… find the quantity. Not implemented.

    Ignore other optional columns.

    Ignore the first line(s) starting by // (form embedded comment).

    Return: a tuple:
    - list of tuples ISBN/quantity,
    - list of messages (strings)
    """
    msgs = utils.Messages()
    lines = []  # inputrows, cleaned up.
    rows = []   # final list of tuples.
    res = []

    def falsy_col(col):
        return col in [None, '', u'']

    def is_comment(line):
        return line.startswith('//')

    # Quick cleanup.
    for row in inputrows:
        if row and not is_comment(row):
            lines.append(row.strip())

    # ;-separated CSV?
    if ';' in lines[0]:
        for row in lines:
            isbn, quantity = row.split(';')
            if isbn and not falsy_col(isbn):
                try:
                    quantity = int(quantity)
                    if not quantity:
                        quantity = 1  # just in case
                    rows.append([isbn.strip(), quantity])
                except Exception as e:
                    # logging.warning("extract_all_isbns_quantities: could not parse quantity {} to int: {}".format(quantity, e))
                    msgs.add_warning("Could not parse quantity for ISBN {}".format(isbn))

    # We have a space-separated ISBN_qty
    elif ' ' in lines[0] and is_isbn(lines[0].split(' ')[0]):
        import re
        for row in lines:
            isbn, quantity = re.split(' ', row, maxsplit=1)
            if isbn and not falsy_col(isbn):
                try:
                    quantity = int(quantity.strip())
                    if not quantity:
                        quantity = 1
                    rows.append([isbn.strip(), quantity])
                except Exception as e:
                    msgs.add_warning("Could not parse quantity for ISBN {}".format(isbn))

    # We simply have a list of ISBNs:
    elif is_isbn(lines[0]):
        for line in lines:
            rows.append([line, 1])  # default quantity
        return rows, []
    else:
        log.warning("extract_all_isbns_quantities: dead end.")

    # Collect ISBNs (and numbers).
    if rows and rows[-1] and len(rows[-1]) > 1:
        # Find where is the ISBNs (should be usually 1st position).
        first_col = rows[0][0]
        second_col = rows[0][1]
        try:
            int(second_col)
            is_number = True
        except Exception as e:
            print(e)
            is_number = False
        if is_isbn(first_col) and is_number:
            # Check all first columns are ISBNs, all second are numbers
            valid_csv, messages = _check_csv_format(rows)
            if not valid_csv:
                return None, messages
            res = rows

    else:
        msgs.add_warning("We couldn't recognize data. Please check the first rows are valid ISBNs and numbers. They can be CSV rows separated by ';' or only an ISBN on each line.")
        return [], msgs.msgs

    return res, msgs.msgs

def bulk_import_from_dilicom(isbns):
    """
    Import this list of ISBNs by batches of 100.

    Only Dilicom provides this batch request for now.
    Its search() methods handles the batch requests.

    - isbns: list of strings, all verified to be valid isbns.

    Return:
    """
    if not dilicom_enabled():
        return [], ["Dilicom is not enabled."]
    fel = dilicom.Scraper(*isbns)
    dicts, messages = fel.search()
    return dicts, messages

class Echo(object):
    """
    An object that implements just the write method of the file-like
    interface.
    """
    # taken from Django docs
    def write(self, value):
        """
        Write the value by returning it, instead of storing in a buffer.
        """
        return value


def cards2csv(cards):
    """
    Cards: as dicts.
    """
    pseudo_buffer = Echo()
    writer = unicodecsv.writer(pseudo_buffer, delimiter=b';')
    content = writer.writerow(b"")

    rows = [(it['title'],
             it['authors_repr'],
             it['price'],
             it['quantity'],
             it['shelf'],
             it['isbn'],
            )
            for it in cards]

    header = (_("title"),
              _("authors"),
              _("price"),
              _("quantity"),
              _("shelf"),
              _("isbn"),
    )
    rows.insert(0, header)
    content = b"".join([writer.writerow(row) for row in rows])
    return content


def format_price_for_locale(price):
    """
    For french-ish locales, a comma should be the decimal separator.
    """
    try:
        if settings.LOCALE_FOR_EXPORTS == "fr":
            return str(price).replace('.', ',')
    except:  # noqa: E722
        pass
    try:
        return str(price)
    except:  # noqa: E722
        return price
