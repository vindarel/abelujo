#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2018 The Abelujo Developers
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

"""
Import a csv files with two columns: an isbn and a quantity.
"""
from __future__ import print_function

import os

from django.core.management.base import BaseCommand

from search.models import Card
from search.models import Preferences
from search.models.api import to_int
from search.models.utils import is_isbn
from search.views_utils import search_on_data_source


def find_separator(line, default=None):
    if ";" in line:
        return ";"
    if "," in line:
        return ","
    return default

class Command(BaseCommand):

    help = "Import a csv file with two columns: an isbn and a quantity."

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            dest='input',
            help='CSV file of input.',
        )
        parser.add_argument(
            '-l',
            dest='lang',
            help='Set the language to better choose the bibliographic source.',
        )

    def handle(self, *args, **options):
        """
        Add a card with a quantity.

        !!! the script can add some cards and exit. It is not indempotent !
        """
        WARN_MSG = "***** This script is not indempotent. If you run it twice it will add cards twice. Contact us if you are in such a situation. *****"
        print(WARN_MSG)

        csvfile = options.get('input')
        if not csvfile.endswith('csv'):
            self.stdout.write("Please give a .csv file as argument.")
            exit(1)

        with open(csvfile, "r") as f:
            lines = f.readlines()

        lines = [it.strip() for it in lines]

        source = 'librairiedeparis'
        print("INFO: the default bibliographic source is FR. See the (unimplemented) -l option.")
        if options.get('lang'):
            self.stdout.write("Unimplemented. Would you buy me a beer ?")
            exit(1)

        default_place = Preferences.prefs().default_place
        if not default_place:
            print("We couldn't find a default place. Please check and try again.")
            exit(1)

        separator = find_separator(lines[0], default=";")
        for i, line in enumerate(lines):
            isbn, quantity = line.split(separator)
            if not is_isbn(isbn):
                self.stdout.write("It seems that {} is not a valid isbn or one that we know around here. Please check and try again.".format(isbn))
                exit(1)

            print("[{}] - searching for {}...".format(i + 1, isbn), end="")
            res, traces = search_on_data_source(source, isbn)
            if not res:
                print(" no result :( Exiting.")
                exit(1)
            print(" ok ({} results)".format(len(res)))

            if len(res) > 1:
                print("INFO: got more than 1 result for {}, we pick the first one.".\
                      format(isbn))

            res = res[0]

            print("\t adding to {}...".format(default_place), end="")
            try:
                card, msgs = Card.from_dict(res)  # XXX quite long
            except Exception as e:
                print()
                print("Error with res {}: {}.".format(res, e))
                print("Exiting.")
                exit(1)
            default_place.add_copy(card, to_int(quantity))
            print(" done quantity x{}.".format(quantity))
