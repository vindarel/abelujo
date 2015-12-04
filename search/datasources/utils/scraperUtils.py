#!/usr/bin/env python
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

import re
import string


def priceFromText(text):
    """Extract the price from text with regexp.
    """
    match = re.search('\d+,?\d*', text)
    price = match.group()
    return price

def priceStr2Float(str):
    """Gets a str, performs basic formatting and returns a Float.

    Formatting: replaces commas with dots.

    arg: string
    returns: Float
    """
    return float(str.replace(",", "."))

def isbn_cleanup(isbn):
    """Clean the string and return only digits. (actually, remove all
    punctuation, most of all the dash).

    Because a bar code scanner only prints digits, that's the format
    we want in the database.

    - isbn: a str / unicode
    - return: a string, with only [0-9] digits.

    """
    # note: we duplicated this function in models.utils
    res = isbn
    if isbn:
        # note: punctuation is just punctuation, not all fancy characters like « or @
        punctuation = set(string.punctuation)
        res = "".join([it for it in isbn if it not in punctuation])

    return res

def is_isbn(it):
    """Return True is the given string is an ean or an isbn, i.e:

    - is of type str (or unicode). The string must contain only
      alpha-numerical characters.
    - length of 13 or 10
    """
    # note: method duplicated from models.utils
    ISBN_ALLOWED_LENGTHS = [13, 10]
    res = False
    pattern = re.compile("[0-9]+")
    if (type(it) == type(u'u') or type(it) == type('str'))and \
       len(it) in ISBN_ALLOWED_LENGTHS and \
       pattern.match(it):
        res = True

    return res
