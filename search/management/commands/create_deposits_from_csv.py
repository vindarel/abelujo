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
Create a deposit for each card in the csv (isbn and quantity).

The quantity is the right one: we set it, we don't add it, like an inventory.

We have to choose what shelf to add them in.

Usage:

./manage.py <script name> -i path/to.csv [-s shelf_id]
"""
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.datasources.bookshops.frFR.dilicom import dilicomScraper
from search.models import Card
from search.models import Deposit
from search.models import Preferences
from search.models import Shelf
from search.models import Publisher
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
            '-s',
            dest='shelf_id',
            help='Set the shelf (by its id).',
        )

    def run(self, *args, **options):
        """
        Import cards and set their quantity.

        The script can add some cards and exit. If it is run a second time, it will process
        everything again.

        It is indempotent: we *set* the card's quantity, we don't *add* it to the stock (changed in january 2020).
        """
        WARN_MSG = "This script adds the quantities to a new deposit for each card (it does not *set* them)."
        print(WARN_MSG)
        yes = input("Continue ? [Y/n]")
        if yes not in ["", "Y"]:
            print("quit.")
            exit(1)

        shelf = None
        if options.get('shelf_id'):
            shelf = Shelf.objects.filter(id=options.get('shelf_id')).first()
            self.stdout.write(u"Found shelf: {}".format(shelf.name))

        csvfile = options.get('input')
        if not csvfile.endswith('csv'):
            self.stdout.write("Please give a .csv file as argument.")
            exit(1)

        with open(csvfile, "r") as f:
            lines = f.readlines()

        lines = [it.strip() for it in lines]

        separator = find_separator(lines[0], default=";")

        # dev
        splitted_lines = [it.split(separator) for it in lines]
        isbns = [it[0] for it in splitted_lines]
        quantities = [it[1] for it in splitted_lines]

        dilicom_query = dilicomScraper.Scraper(*isbns)
        self.stdout.write("Searching all on Dilicom...")
        bklist, errors = dilicom_query.search()

        found_isbns = []
        if len(bklist) != len(isbns):
            self.stdout.write("--- beware: the search results have not the same length that our query: {} vs {}".format(len(bklist), len(isbns)))
            found_isbns = [it.get('isbn') for it in bklist]
            self.stdout.write("--- isbns not found: {}".format(list(set(isbns) - set(found_isbns))))


        cards_updated = []
        count_ok = 0
        for i, bk in enumerate(bklist):
            quantity = quantities[i]

            bk['shelf'] = shelf

            pub_name = ""
            if bk.get('publishers'):
                pub_name = bk.get('publishers')[0]
                pub, _created = Publisher.objects.get_or_create(name=pub_name)
                bk['publishers_ids'] = [pub.id]

            print("* {} - creating {}".format(i, bk.get('isbn')))

            try:
                card, msgs = Card.from_dict(bk)

                cards_updated.append(bk.get('isbn'))
                count_ok += 1
            except Exception as e:
                self.stdout.write(" ! failed for {}: {}".format(bk.get('isbn'), e))

            try:
                # XXX: our add_copy wants a Card object.
                # card = Card.objects.filter(isbn=bk.get('isbn')).first()
                self.stdout.write(" adding x{} to a new deposit...".format(quantity))
                depo = None
                if card.deposits:
                    depo = card.deposits[0]
                else:
                    depo = Deposit(name=card.title_ascii)
                    depo.save()
                depo.add_copy(card, nb=to_int(quantity))
                self.stdout.write("✓ card added to its deposit.")
            except Exception as e:
                self.stdout.write("could not add to a deposit: {}".format(e))

        self.stdout.write("-------------------")
        self.stdout.write("Cards OK: {}.".format(count_ok))
        self.stdout.write("Cards updated:{}".format(len(cards_updated)))
        if len(bklist) != len(isbns):
            self.stdout.write("isbns not found: {}".format(list(set(isbns) - set(found_isbns))))
        self.stdout.write("Done.")

    def handle(self, *args, **options):
        try:
            self.run(*args, **options)
        except KeyboardInterrupt:
            self.stdout.write("User abort.")
