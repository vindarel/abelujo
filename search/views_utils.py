# -*- coding: utf-8 -*-
# Copyright 2014 - 2019 The Abelujo Developers
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

from django.utils.translation import ugettext as _

import unicodecsv
from search.datasources.bookshops.all.discogs import discogsScraper as discogs  # noqa: F401
from search.datasources.bookshops.all.momox import momox  # noqa: F401
from search.datasources.bookshops.deDE.buchlentner import \
    buchlentnerScraper as buchlentner  # noqa: F401
from search.datasources.bookshops.esES.casadellibro import \
    casadellibroScraper as casadellibro  # noqa: F401
from search.datasources.bookshops.frFR.decitre import decitreScraper as decitre  # noqa: F401
from search.datasources.bookshops.frFR.librairiedeparis import \
    librairiedeparisScraper as librairiedeparis  # noqa: F401
from search.models import Card

#: Default datasource to be used when searching isbn, if source not supplied.
DEFAULT_DATASOURCE = "librairiedeparis"

def get_datasource_from_lang(lang):
    """From a lang (str), return the name (str) of the datasource module.

    And for CDs ? The client should be in "recordsop" mode.
    """
    if not lang:
        return DEFAULT_DATASOURCE

    if lang.startswith("fr"):
        return "librairiedeparis"
    elif lang.startswith("de"):
        return "buchlentner"
    elif lang.startswith("es"):
        return "casadellibro"
    elif lang in ["discogs", "momox"]:
        return lang
    else:
        return DEFAULT_DATASOURCE


def search_on_data_source(data_source, search_terms, PAGE=1):
    """search with the appropriate scraper.

    data_source is the name of an imported module.
    search_terms: list of strings.

    return: a couple (search results, stacktraces). Search result is a
    list of dicts.
    """
    # get the imported module by name.
    # They all must have a class Scraper.
    scraper = getattr(globals()[data_source], "Scraper")
    # res, traces = scraper(*search_terms).search()
    res, traces = scraper(search_terms, PAGE=PAGE).search()

    # Check if we already have these cards in stock (with isbn).
    res = Card.is_in_stock(res)

    return res, traces


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    # taken from Django docs
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def cards2csv(cards):
    pseudo_buffer = Echo()
    writer = unicodecsv.writer(pseudo_buffer, delimiter=';')
    content = writer.writerow("")

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
    content = "".join([writer.writerow(row) for row in rows])
    return content
