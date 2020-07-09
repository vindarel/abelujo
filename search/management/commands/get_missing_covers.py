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
Get the cover URLs of cards that miss it.
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


def cards_without_cover():
    return Card.objects.filter(cover__isnull=True)

def update_card(card, source=""):
    isbn = card.isbn
    res, traces = search_on_data_source(source, isbn)
    if not res:
        print("{}: no result. Exiting. ('{}')".format(card.isbn, card.title))
        return False, card, traces

    print("{}: ok ({} results)".format(card.isbn, len(res)))

    if len(res) > 1:
        print("INFO: got more than 1 result for {}, we pick the first one.".format(isbn))

    res = res[0]

    try:
        if res['img']:
            card.cover = res['img']
            card.save()
            return True, card, None
        else:
            return False, card, "no cover url found!"

    except Exception as e:
        return False, card, "An error happened: {}".format(e)


def update_all(cards, source=""):
    cards_updated = []
    cards_missed = []
    for card in cards:
        status, card, traces = update_card(card, source=source)
        if status:
            cards_updated.append(card)
        else:
            cards_missed.append(card)

    return cards_updated, cards_missed


class Command(BaseCommand):

    help = "Search covers for cards that miss one (usually the ones coming from Dilicom)."

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            dest='lang',
            help='Set the language to better choose the bibliographic source.',
        )

    def print_status(self, msg="Done"):
        self.stdout.write(msg)
        if self.not_found:
            self.stdout.write("ISBNs not found:\n{}".format("\n".join(self.not_found)))
        else:
            self.stdout.write("All ISBNs were found")

    def handle(self, *args, **options):
        """
        """
        if options.get('lang'):
            self.stdout.write("Unimplemented. Would you buy me a beer ?")
            exit(1)

        source = 'librairiedeparis'
        print("INFO: the default bibliographic source is FR. See the (unimplemented) -l option.")

        cards = cards_without_cover()
        self.stdout.write("Cards without cover: {}".format(cards.count()))
        cards_updated, cards_missed = update_all(cards, source=source)

        self.stdout.write("Cards updated: {} / {}".format(len(cards_updated), cards.count()))
        self.stdout.write("Cards missed: {} / {}".format(len(cards_missed), cards.count()))
