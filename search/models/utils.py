# -*- coding: utf-8 -*-
# Copyright 2014 - 2017 The Abelujo Developers
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

import datetime
import decimal
import logging
import re
import string

import addict
# from models import getHistory # don't import model here-> circular
from tabulate import tabulate

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
        if any(map(lambda it: it['level'] == ALERT_ERROR, self.msgs)):
            return ALERT_ERROR

        if any(map(lambda it: it['level'] == ALERT_WARNING, self.msgs)):
            return ALERT_WARNING

        if any(map(lambda it: it['level'] == ALERT_INFO, self.msgs)):
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


def truncate(it):
    """Truncate only strings to MAX_CELL characters.

    param string it: a string

    returns: a string
    """
    if it and (isinstance(it, str) or isinstance(it, unicode))\
       and len(it) >= MAX_CELL:
        return it[:MAX_CELL] + "..."
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
    """Pretty Print a list of Card objects OR list of dicts.

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
    tab = map(lambda it: map(truncate, it), tab)
    tablength = len(tab)
    total = total_quantity(cards)
    tab = tabulate(tab, headers=headers)
    tab += "\n\ntotal: {} titles, {} exemplaries.".format(tablength, total)
    return tab

def is_isbn(it):
    """Return True is the given string is an ean or an isbn, i.e:

    - type: str
    - length of 13 or _
    """
    # caution: method duplicate in scraperUtils
    ISBN_ALLOWED_LENGTHS = [13]
    res = False
    pattern = re.compile("[0-9]+")
    if (isinstance(it, unicode) or isinstance(it, str)) and \
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

def list_from_coma_separated_ints(s):
    """Gets a string with coma-separated numbers (ints or floats), like
    "1,2.2,3", returns a list with each number. Because on url
    parameters we can get a list of ids like this.

    """
    def toIntOrFloat(nb):
        try:
            return int(nb)
        except ValueError:
            nb = nb.replace(",", ".")
            if nb in ["null", u"null", "undefined"]:
                return None
            return float(nb) if nb else None

    # Data validation: should check that we only have ints and comas...
    if s:
        return [toIntOrFloat(it) for it in s.strip(",").split(",")]
    else:
        return []

def ids_qties_to_pairs(string):
    pairs = []
    if string:
        together = string.split(';')
        pairs = [filter(lambda x: x != "", it.split(',')) for it in together]
        return pairs
    return None

def roundfloat(nb):
    """Round the given float to two decimals.

    return: a float
    """
    if nb is None:
        return 0.00
    return float(decimal.Decimal(nb).quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP))

def date_last_day_of_month(anyday):
    """Get a day (datetime), return a datetime at the last day of the month.
    Return: datetime, as the input.
    """
    return (anyday.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

def _is_truthy(txt):
    """
    - txt: string
    """
    # should be automatic !
    if txt in ['true', 't', u'true', 'yes']:
        return True
    return False


def is_invalid(txt):
    """When JS client sends "undefined" strings instead of nothing.
    """
    return txt in ['undefined', u'undefined', 0, "0", u"0"]


def page_start_index(page, size=PAGE_SIZE):
    page = int(page)
    return max((page - 1) * size, 0)


def get_page_count(entries, size=PAGE_SIZE):
    page_count = len(entries) / size
    if (PAGE_SIZE * page_count) > len(entries):
        page_count += 1
    return page_count or 1
