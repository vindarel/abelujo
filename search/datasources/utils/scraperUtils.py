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
