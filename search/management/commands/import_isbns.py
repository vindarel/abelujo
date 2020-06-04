#!/bin/env python
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

"""
Import a csv files with two columns: an isbn and a quantity.

The quantity is the right one: we set it, we don't add it, like an inventory.

We can choose what shelf to add them in.

Usage:

./manage.py import_isbns -i path/to.csv [-s shelf_id]
"""
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Card
from search.models import Preferences
from search.models import Shelf
from search.models.api import to_int
from search.models.utils import is_isbn
from search.views_utils import search_on_data_source

# py2/3
try:
    input = raw_input
except NameError:
    pass

def find_separator(line, default=None):
    if ";" in line:
        return ";"
    if "," in line:
        return ","
    return default

class Command(BaseCommand):

    help = "Import a csv file with two columns: an isbn and a quantity."
    not_found = []

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
        parser.add_argument(
            '-s',
            dest='shelf_id',
            help='Set the shelf (by its id).',
        )

    def search_and_create_card(self, source, isbn, shelf=None):
        res, traces = search_on_data_source(source, isbn)
        if not res:
            print(" no result for {} :( Exiting.".format(isbn))
            self.not_found.append(isbn)
            return
            # exit(1)

        print(" ok ({} results)".format(len(res)))

        if len(res) > 1:
            print("INFO: got more than 1 result for {}, we pick the first one.".
                  format(isbn))

        res = res[0]
        if shelf:
            res['shelf'] = shelf

        print("\t Creating card {}: {}...".format(isbn, res['title']), end="")
        try:
            card, msgs = Card.from_dict(res)  # XXX quite long
        except Exception as e:
            print()
            print("Error with res {}: {}.".format(res, e))
            print("Exiting.")
            exit(1)

        return card

    def print_status(self, msg="Done"):
        self.stdout.write(msg)
        if self.not_found:
            self.stdout.write("ISBNs not found:\n{}".format("\n".join(self.not_found)))
        else:
            self.stdout.write("All ISBNs were found")

    def run(self, *args, **options):
        """
        Import cards and set their quantity.

        The script can add some cards and exit. If it is run a second time, it will process
        everything again.

        It is indempotent: we *set* the card's quantity, we don't *add* it to the stock (changed in january 2020).
        """
        WARN_MSG = "***** This script was changed in 2020/01. It is now indempotent: it sets the quantities instead of adding them. *****"
        print(WARN_MSG)
        yes = input("Continue ? [Y/n]")
        if yes not in ["", "Y"]:
            print("quit.")
            exit(1)

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

        shelf = None
        if options.get('shelf_id'):
            shelf = Shelf.objects.filter(id=options.get('shelf_id')).first()
            self.stdout.write(u"Found shelf: {}".format(shelf.name))

        default_place = Preferences.prefs().default_place
        if not default_place:
            print("We couldn't find a default place. Please check and try again.")
            exit(1)

        separator = find_separator(lines[0], default=";")
        # TODO: should count success & errors.
        try:
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                isbn, quantity = line.split(separator)
                isbn = isbn.strip()
                if not is_isbn(isbn):
                    self.stdout.write("It seems that {} is not a valid isbn or one that we know around here. Please check and try again.".format(isbn))
                    exit(1)

                card = Card.objects.filter(isbn=isbn).first()
                if not card:
                    print("[{}] - searching for {}...".format(i + 1, isbn), end="")
                    card = self.search_and_create_card(source, isbn, shelf=shelf)
                    if not card:
                        continue
                else:
                    # Update the shelf.
                    # Do it at once in the end? => no, the script can fail early.
                    if card.shelf != shelf:
                        self.stdout.write("\tupdating the shelf.")
                        card.shelf = shelf

                print("\t setting to {}...".format(default_place), end="")
                default_place.add_copy(card, to_int(quantity), add=False)
                print(" done quantity x{}.".format(quantity))

            self.print_status()

        except KeyboardInterrupt:
            self.print_status(msg="Abort.")

    def handle(self, *args, **options):
        try:
            self.run()
        except KeyboardInterrupt:
            self.stdout.write("User abort.")
