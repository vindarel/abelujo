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

import addict

from models import getHistory
from tabulate import tabulate

MAX_CELL=30

def truncate(it):
    """Truncate only strings to MAX_CELL characters.

    param string it: a string

    returns: a string
    """
    if it and (type(it) == type("") or type(it) == type(u""))\
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
    # Allows dotted notation to attributes (and more).
    # The code would be the same with @properties, wouldn't it ?
    tab = [
        [
            elt.title,
            elt.authors,
            elt.publishers,
            elt.distributor,
            # elt.ean,
            elt.price,
            elt.quantity,
        ]
            for elt in ncards]

    return tab

def total_quantity(cards):
    if type(cards[0]) == type({}):
        cards = [addict.Dict(it) for it in cards]
    return sum(it.quantity for it in cards)

def ppcard(cards):
    """Pretty Print a list of Card objects OR list of dicts.

    args: a list of Card objects.

    returns: a tabular representation

    returns a text representation:

    ---------------------------------------------------------------------------------  -------------------  -------------  -----  -------------  --------------------
    Apprendre à désobeir ; petite histoire de l'école qui résiste                      Biberfeld, Laurence  libertalia     aucun  9782918059363  produit indisponible
    Bourgeois et bras nus ; guerre sociale durant le Révolution française (1793-1795)  Daniel Guérin        libertalia     aucun  9782918059295  produit indisponible
    """
    if type(cards[0]) == type({}):
        # List of str.
        tab = _ppcard_listofdicts(cards)
    else:
        # List of Card objects.
        tab = [

            [
                elt.title,
                ", ".join(aut.name for aut in elt.authors.all()),
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

def hist():
    """Print a recent history.
    """
    hist, status, alerts = getHistory(sells=True)
    print "Sells:"
    print hist
