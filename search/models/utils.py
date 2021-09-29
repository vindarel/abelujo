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

import decimal
import logging
import re
import string

import addict
import unidecode
from tabulate import tabulate

from django.utils import six

from abelujo import settings
from search.models.common import ALERT_ERROR
from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING

MAX_CELL = 60

PAGE_SIZE = 25

def get_logger():
    """Get the appropriate logger for PROD or DEBUG mode. On local
    development, don't use the sentry_logger (throws errors).
    """
    if settings.DEBUG:
        return logging.getLogger('debug_logger')
    else:
        return logging.getLogger('sentry_logger')


log = get_logger()


class Messages(object):
    """List of messages for UI <-> api communication in json.
    When adding a message, with a status, the global status is updated accordingly.

    Usage:

    >> msgs = Messages()
    >> msgs.add_success(_("ok !"))
    >> msgs.add_error("oh no") # -> global status is updated
    >> return val, msgs.to_dict()

    """

    def __init__(self):
        #: List of dicts with 'level' (str) and 'message' (str).
        self.msgs = []
        #: Global status. string, for bootstrap.
        self._status = ALERT_SUCCESS

    def __unicode__(self):
        return self.msgs

    def add(self, status, txt):
        self.msgs.append({'level': status, 'message': txt})

    def add_success(self, txt):
        self.add(ALERT_SUCCESS, txt)

    def add_error(self, txt):
        self.add(ALERT_ERROR, txt)
        self._status = ALERT_ERROR

    def add_info(self, txt):
        self.add(ALERT_INFO, txt)
        if self._status in [ALERT_SUCCESS]:
            self._status = ALERT_INFO

    def add_warning(self, txt):
        self.add(ALERT_WARNING, txt)
        if self._status in [ALERT_SUCCESS, ALERT_INFO]:
            self._status = ALERT_WARNING

    def merge(self, msgs):
        """
        - msgs: Messages instance
        """
        # here we want status as int…
        # error info success warning
        self.msgs += msgs.msgs
        self._status = self.check_status()

    def append(self, msgs):
        """
        - msgs: list of messages
        """
        self.msgs += msgs
        self._status = self.check_status()

    def check_status(self):
        """Find the global status again (happens after a merge of different messages).

        Return: a status (str)
        """
        if any([it['level'] == ALERT_ERROR for it in self.msgs]):
            return ALERT_ERROR

        if any([it['level'] == ALERT_WARNING for it in self.msgs]):
            return ALERT_WARNING

        if any([it['level'] == ALERT_INFO for it in self.msgs]):
            return ALERT_INFO

        return ALERT_SUCCESS

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        """Avoid that, it messes with merge.
        """
        if status:
            self._status = status

    @property
    def messages(self):
        return self.msgs

    def to_list(self):
        return self.to_dict()

    def to_dict(self):
        return {'status': self._status,
                'messages': self.msgs}

    def to_alerts(self):
        # to test more.
        return [{'status': it['level'],
                 'level': it['level'],
                 'message': it['message']}
                for it in self.msgs]


def truncate(it, max_length=MAX_CELL):
    """Truncate only strings to MAX_CELL characters.

    param string it: a string

    returns: a string
    """
    if it and (isinstance(it, six.text_type) or isinstance(it, six.string_types))\
       and len(it) >= max_length:
        return it[:max_length] + "..."
    return it

def _ppcard_listofdicts(cards):
    """Pretty print tabular data. For convenience, only call the ppcard
    function.

    cards: a list of dictionnaries with title, authors, publishers, distributor, ean and price.

    returns: a list of lists, ready to be passed to tabulate.

    """
    ncards = [addict.Dict(it) for it in cards]
    # addict allows dotted notation to the dict's attributes.
    tab = [
        [
            elt.title,
            elt.authors_repr,
            elt.pubs_repr,
            elt.distributor.name if elt.distributor else "-",
            # elt.ean,
            elt.price,
            elt.quantity,
        ]
        for elt in ncards]

    return tab

def total_quantity(cards):
    if isinstance(cards[0], dict):
        cards = [addict.Dict(it) for it in cards]
    return sum(it.quantity for it in cards)

def ppcard(cards):
    """
    Pretty Print a list of Card objects OR list of dicts.

    args: a list of Card objects or list of dicts.

    returns: a tabular representation, as text.

    - returns: str

    Exple:
    >> ppcard(cards)
    ---------------------------------------------------------------------------------  -------------------  -------------  -----  -------------  --------------------
    Apprendre à désobeir ; petite histoire de l'école qui résiste                      Biberfeld, Laurence  libertalia     aucun  9782918059363  produit indisponible
    Bourgeois et bras nus ; guerre sociale durant le Révolution française (1793-1795)  Daniel Guérin        libertalia     aucun  9782918059295  produit indisponible
    """
    if isinstance(cards[0], dict):
        # List of str.
        tab = _ppcard_listofdicts(cards)
    else:
        # List of Card objects.
        tab = [

            [
                elt.title,
                elt.display_authors(),
                elt.publishers.all()[0].name if elt.publishers.all() else "",
                elt.distributor.name if elt.distributor else "",
                # elt.ean,
                elt.price,
                elt.quantity,
            ]
            for elt in cards]

    headers = [
        "Title",
        "Author(s)",
        "Publisher(s)",
        "Distributor",
        "Price",
        "Quantity",
    ]

    # Truncate all attributes:
    tab = list([list(map(truncate, it)) for it in tab])
    tablength = len(tab)
    total = total_quantity(cards)
    tab = tabulate(tab, headers=headers)
    tab += "\n\ntotal: {} titles, {} exemplaries.".format(tablength, total)
    return tab

def split_query(string):
    """Return a list of words.
    Split by semicolon, comma or space (first separator found).
    Usually, the user query will be a comma-separated list of ISBNs (from a
    memory barcode scanner). It can contain other words too, so you might
    want to filter by is_isbn afterwards.
    """
    if ";" in string:
        separator = ";"
    elif "," in string:
        separator = ","
    else:
        separator = " "
    res = string.split(separator)
    return [it.strip() for it in res]

def isbns_from_query(string):
    words = split_query(string)
    return list(filter(is_isbn, words))

def is_isbn(it):
    """Return True is the given string is an ean or an isbn, i.e:

    - type: str
    - length of 13 or _
    """
    # caution: method duplicate in scraperUtils
    ISBN_ALLOWED_LENGTHS = [13]
    res = False
    pattern = re.compile("[0-9]+")
    if (isinstance(it, six.text_type) or isinstance(it, six.string_types)) and \
       len(it) in ISBN_ALLOWED_LENGTHS and \
       pattern.match(it):
        res = it

    return res

def isbn_cleanup(isbn):
    """Clean the string and return only digits. (actually, remove all
    punctuation, most of all the dash).


    Because a bar code scanner only prints digits, that's the format
    we want in the database.

    - isbn: a str / unicode
    - return: a string, with only [0-9] digits.

    """
    # WARNING: code duplicated from datasources.utils.scraperUtils,
    # because the modules should be independant. Still, beware.
    res = isbn
    if isbn:
        punctuation = set(string.punctuation)
        res = "".join([it for it in isbn if it not in punctuation])
    return res

def list_to_pairs(ll):
    """Get a list of ints: [1, 0, 2, 0]

    return a list of pairs: [ (1, 0), (2,0) ]

    why ? to deal with url parameters when django and angularjs don't
    work so well together. (card_add)

    """
    res = []
    for i in range(len(ll) - 1):
        if i % 2 == 0:
            res.append((ll[i], ll[i + 1]))
    return res

def toIntOrFloat(nb):
    try:
        return int(nb)
    except ValueError:
        nb = nb.replace(",", ".")
        if nb in ["null", "undefined"]:
            return None

        try:
            return float(nb) if nb else None  # can None happen? Coming from JS, certainly.
        except ValueError:
            log.warning("utils.toIntOrFloat: the number {} could not be coerced to an int nor a float. We'll try to extract a float, but this should not happen.".format(nb))

            extraction = re.findall(r"[-+]?\d*\.\d+|\d+", nb)
            if extraction:
                log.warning("utils.toIntOrFloat: the price {} is malformed and we extracted {}. There might be a slight price error :S".format(nb, extraction[0]))
                return float(extraction[0])
            raise Exception("utils.toIntOrFloat: the number {} is neither an int, a float or a string from which we extract a float. What is it??".format(nb))


def list_from_coma_separated_ints(s):
    """Gets a string with coma-separated numbers (ints or floats), like
    "1,2.2,3", returns a list with each number. Because on url
    parameters we can get a list of ids like this.

    """
    # Data validation: should check that we only have ints and comas...
    if s:
        return [toIntOrFloat(it) for it in s.strip(",").split(",")]
    else:
        return []

def ids_qties_to_pairs(string):
    pairs = []
    # [feb 19] old behaviour: string is like
    # '3037, 1;', '3976, 1;', '3064, 1;', '3497, 1;'
    # For unknown reason, we now get a proper list straight in.
    # So we removed the ; and we don't need this method anymore.
    # But is that in all methods using it ? see command_receive_update
    if string and (isinstance(string, six.string_types) or isinstance(string, six.text_type)) and ';' in string:
        together = string.split(';')
        pairs = [[x for x in it.split(',') if x != ""] for it in together]
        return pairs
    return None

def roundfloat(nb):
    """Round the given float to two decimals.

    return: a float
    """
    if nb is None:
        return 0.00
    return float(decimal.Decimal(nb).quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP))

def _is_truthy(txt):
    """
    - txt: string
    """
    if txt in [True, 'true', 't', 'yes', '1', 1]:
        return True
    return False


def is_truthy(txt):
    return _is_truthy(txt)

def is_invalid(txt):
    """When JS client sends "undefined" strings instead of nothing.
    """
    return txt in ['undefined', 0, "0"]


def page_start_index(page, size=PAGE_SIZE):
    page = int(page)
    return max((page - 1) * size, 0)


def get_page_count(entries, size=PAGE_SIZE):
    length = len(entries)
    page_count = length / size
    if (size * page_count) < length:
        page_count += 1
    return page_count or 1


def distributors_match(cards):
    """
    If the distributors of these cards are the same, return True.
    """
    if len(cards) <= 1:
        return True
    dists = [it.distributor for it in cards]
    no_duplicates = set(dists)
    return len(no_duplicates) == 1


def card_currency(card):
    """
    Currency symbol depending on the data source.
    This info is currently not saved in DB (and doesn't need it).
    """
    if card.data_source and 'lelivre' in card.data_source:
        return 'CHF'
    return '€'


def price_fmt(price, currency):
    """
    Return: a string, with the price formatted correctly with its currency symbol.

    ANN: See also the 'currency' template filter (new in January, 2021).

    Exemple: 10 € or CHF 10
    """
    if price is None or isinstance(price, six.string_types) or isinstance(price, six.text_type):
        return ''
    try:
        if not currency:
            # Happens in tests, in bare bones setup.
            return '{:.2f} €'.format(price)
        if currency.lower() == 'chf':
            return 'CHF {:.2f}'.format(price)
        else:
            return '{:.2f} €'.format(price)
    except Exception as e:
        log.warning('Error for models.utils.price_fmt: {}'.format(e))
        return '{:.2f}'.format(price)

def to_ascii(string):
    """
    Replace accentuated letters by their ascii equivalent, return lowercase.

    Éléphant => Elephant.
    """
    if not string:
        return None

    try:
        res = unidecode.unidecode(string)
        return res.lower()
    except UnicodeDecodeError:
        res = unidecode.unidecode(string)
    except Exception as e:
        log.debug(u"Could not create ascii equivalent for {}: {}".format(string, e))

def theme_name(code):
    "From the theme code in DB, get its name."
    try:
        return settings.CLIL_THEMES.get(code)
    except Exception:
        return ""

def parent_theme_name(code):
    """
    Get the first parent theme name.
    3781 (action et aventure) => Bande dessinée

    - code: string

    Return: string
    """
    if not code:
        return ""
    if isinstance(code, int):
        code = str(code)
    try:
        parents_list = settings.CLIL_THEME_HIERARCHIES.get(code)
        parents_list = [it.strip() for it in parents_list] if parents_list else []
        parent = None
        # element 0 is the first parent. List of 4 elements. The list ends with
        # the theme code (same as the key):
        # code => grand-parent, parent, code, blank string.
        if parents_list:
            if parents_list[0] == code:
                return ""
            elif parents_list[1] == code:
                parent = parents_list[0]
            elif parents_list[2] == code:
                parent = parents_list[1]
            elif parents_list[3] == code:
                parent = parents_list[2]
            return settings.CLIL_THEMES.get(parent)
        return ""
    except Exception as e:
        log.warning(u"Could not get the parent theme of {}: {}".format(code, e))
        return ""

def theme_composed_name(code):
    """
    From the code, return the name composed of 3 parents (max).
    """
    code = code.strip()
    hierarchie = settings.CLIL_THEME_HIERARCHIES.get(code)
    try:
        return " / ".join([it for it in [theme_name(themecode) for themecode in hierarchie] if it])
    except Exception as e:
        log.warning(u"Could not join theme names for {}: {}".format(code, e))
        return str(code)

def is_book(card):
    # assert isinstance(card, xxx)
    if card.card_type_id == 1:  # XXX: CardType
        return True
    if card.isbn.startswith('97'):
        return True
    return False

def enrich_cards_dict_for_quantity_in_command(cards, basket_copies):
    """
    - cards: list of dicts
    - basket_copies: queryset (from the command list).

    Return: cards, with quantity_in_command added in.
    """
    # Init.
    for card in cards:
        card['quantity_in_command'] = 0

    def find_id_in_cards_list(pk):
        for it in cards:
            if it['id'] == pk:
                return it
        return {}

    # Get the quantity in command.
    for bc in basket_copies:
        card_dict = find_id_in_cards_list(bc.card.id)
        if card_dict and bc.nb:
            card_dict['quantity_in_command'] = bc.nb

    return cards
