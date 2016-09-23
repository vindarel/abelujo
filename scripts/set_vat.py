#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2016 The Abelujo Developers
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

from __future__ import print_function

import json
import os

import yaml
from tqdm import tqdm

from search.models.models import Card
from search.models.models import CardType
from search.models.models import Place
from search.models.models import Preferences
from search.models.models import Shelf


"""
Set the VTA tax.

Run with the runscript management command.

Usage:

./manage.py runscript set_vta --script-args=scripts/shelfs_fr.yaml
"""

def run(*args):
    """
    """

    LANG = "fr"
    src = "scripts/init-data.yaml"

    with open(src, "r") as f:
        data = yaml.load(f.read())

    if not data:
        print("No file data given")
        exit(1)

    lang = args[0] if args else LANG
    langchoices = data.keys()
    if lang not in langchoices:
        print("The requested language ({}) isn't in the initial data. Choices: {}".format(lang, langchoices))
        exit(1)

    data = data[lang]
    prefs = data['Preferences']
    if not prefs['vat_book']:
        print("We can't find a vat_book in {}".format(prefs))
        exit(1)

    vat_book = prefs['vat_book']

    print("=== setting the vat for books...===")
    msgs, status = Preferences.setprefs(vat_book=vat_book)
    if status == "success":
        print("==== ok ===")
    else:
        print("==== pb: {}".format(msgs))
