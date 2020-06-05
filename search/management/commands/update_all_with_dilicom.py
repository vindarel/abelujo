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
Update all the cards' information after a Dilicom lookup, including:

- the distributor
- the publisher
- thickness, weight etc
- etc

This can take several minutes with thousands of cards.

Options:

- verbose: -V t

"""
from __future__ import unicode_literals

import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from search.datasources.bookshops.frFR.dilicom import dilicomScraper
from search.models import Card

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument(
        #     '-V',
        #     dest='verbose',
        #     help='debug output.',
        # )
        pass

    def update_all(self):
        # All cards with an ISBN.
        cards = Card.objects.filter(isbn__isnull=False)
        self.stdout.write("Updating {} cards.".format(cards.count()))

        confirmation = True
        # confirmation = raw_input("Continue ? [Y/n]")
        if confirmation == "n":
            exit(0)

        isbns = cards.values_list("isbn", flat=True)  # [it.isbn for it in cards]

        # isbns = isbns[50:500]  # TODO:
        # isbns = isbns[430:500]  # TODO:
        dilicom_query = dilicomScraper.Scraper(*isbns)
        self.stdout.write("Searching all on Dilicom...")
        bklist, errors = dilicom_query.search()

        if len(bklist) != len(isbns):
            self.stdout.write("--- beware: the search results have not the same length that our query: {} vs {}".format(len(bklist), len(isbns)))
            # exit(1)

        cards_updated = []
        cards_not_updated = []
        count_ok = 0
        for i, card in enumerate(cards):
            bk = list(filter(lambda it: it['isbn'] == card.isbn, bklist))
            if bk:
                bk = bk[0]

            if not bk:
                # self.stdout.write("No matching result for card {}. Pass.".format(card.isbn))
                cards_not_updated.append(card)
                continue

            # self.stdout.write("{}: => {}".format(card.title, bk))

            # THE update.
            # same publisher?
            # print("--publishers: {} VS {}".format(bk.get('publishers'), " + ".join([it.name for it in card.publishers.all()])))

            pub_name = ""
            if bk.get('publishers'):
                pub_name = bk.get('publishers')[0]

            print("* {} - updating {}".format(i, card.isbn))

            try:
                Card.update_from_dict(card, bk,
                                      distributor_gln=bk.get('distributor_gln'),
                                      publisher_name=pub_name)

                cards_updated.append(card)
                count_ok += 1
            except Exception as e:
                self.stdout.write(" ! failed for {}: {}".format(bk.get('isbn'), e))

            # Updating 4.000 cards is resource heavy.
            if i % 100 == 0:
                time.sleep(0.2)

        self.stdout.write("-------------------")
        self.stdout.write("Cards OK: {}.".format(count_ok))
        self.stdout.write("Cards updated:{}".format(len(cards_updated)))
        self.stdout.write("Cards not updated:{}".format(len(cards_not_updated)))
        # self.stdout.write("\n".join([it.isbn for it in cards_not_updated]))
        self.stdout.write("Done.")

    def handle(self, *args, **options):
        self.stdout.write("Go...")
        start = timezone.datetime(year=2020, month=01, day=01)

        try:
            self.update_all()
        except KeyboardInterrupt:
            self.stdout.write("User abort.")
