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
Update cards' information after a Dilicom lookup.

SEE UPDATE_ALL_WITH_DILICOM !

Here:
- their price,
- their theme,
- for all cards added with Dilicom since january, 1st.

./manage.py fix_dilicom_info

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.utils import timezone

from search.models import Card
from search.datasources.bookshops.frFR.dilicom import dilicomScraper

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Go...")
        start = timezone.datetime(year=2020, month=01, day=01)

        # Only the ones from Dilicom ? Bad idea.
        # cards = Card.objects.filter(created__gt=start).filter(data_source='dilicom')

        # All cards.
        cards = Card.objects.filter(created__gt=start)

        # Cards whose price has no decimal, hence are suspicious.

        # If needed, to filter some prices:
        # cards = list(filter(lambda card: card.price % 1 == 0, cards))

        self.stdout.write("Looking up {} cards on Dilicom.".format(len(cards)))
        self.stdout.write("(Not all will need an update)")
        confirmation = raw_input("Continue ? [Y/n]")
        if confirmation == "n":
            exit(0)

        isbns = [it.isbn for it in cards]
        dilicom_query = dilicomScraper.Scraper(*isbns)
        bklist, errors = dilicom_query.search()
        if not len(bklist) == len(cards):
            self.stdout.write("The search results have not the same length that our query... something went wrong. Aborting")
            exit(1)

        cards_updated = []
        count_ok = 0
        for card in cards:
            bk = list(filter(lambda it: it['isbn'] == card.isbn, bklist))
            to_save = False
            if bk:
                bk = bk[0]

            if not bk:
                self.stdout.write("No matching result for card {}. Pass.".format(card.isbn))
                continue

            if bk['price'] != card.price:
                self.stdout.write("{}: {} => {}".format(card.title, card.price, bk['price']))
                card.price = bk['price']
                to_save = True
            else:
                count_ok += 1

            if bk['theme'] and bk['theme'] != card.theme:
                self.stdout.write("theme of {}: {} => {}".format(card.id, card.theme, bk['theme']))
                card.theme = bk['theme']
                to_save = True

            if card.data_source != "dilicom":
                card.data_source = "dilicom"
                to_save = True

            if to_save:
                card.save()
                cards_updated.append(card)

        self.stdout.write("-------------------")
        self.stdout.write("Cards OK: {}.".format(count_ok))
        self.stdout.write("Cards updated:{}".format(len(cards_updated)))
        self.stdout.write("Done.")
