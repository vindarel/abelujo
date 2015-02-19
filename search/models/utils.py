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

from tabulate import tabulate

def ppcard(cards):
    """Pretty Print a list of Cards.

    args: a list of Card objects.

    returns: nothing

    prints:

    ---------------------------------------------------------------------------------  -------------------  -------------  -----  -------------  --------------------
    Apprendre à désobeir ; petite histoire de l'école qui résiste                      Biberfeld, Laurence  libertalia     aucun  9782918059363  produit indisponible
    Bourgeois et bras nus ; guerre sociale durant le Révolution française (1793-1795)  Daniel Guérin        libertalia     aucun  9782918059295  produit indisponible
    """
    # suggestion: truncate long fields.
    tab = [
        [
            elt.title,
            ", ".join(aut.name for aut in elt.authors.all()),
            elt.publishers.all()[0].name,
            elt.distributor.name if elt.distributor else "no dist",
            elt.ean,
            elt.price,
        ]
           for elt in cards]

    print tabulate(tab)
