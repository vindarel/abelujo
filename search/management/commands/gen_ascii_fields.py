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
"""
from __future__ import print_function
from __future__ import unicode_literals

from tqdm import tqdm

from django.core.management.base import BaseCommand

from search.models import Card
from search.models import Preferences
from search.models import Shelf
from search.models.api import to_int
from search.models.utils import to_ascii
from search.views_utils import search_on_data_source

import logging
logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.WARNING)

def update_author(author):
    if not author.name_ascii:
        res = to_ascii(author.name_ascii)
        author.save()
        return True

    return False


def update_card(card):
    """
    Return True: card updated.
    False: card had ascii title and authors already. We didn't update them.
    """
    title = card.title
    title_ascii = card.title_ascii
    edited = False

    if not title_ascii:
        res = to_ascii(title)
        if res:
            card.title_ascii = res
            card.save()
            edited = True

    authors = card.authors.all()
    for author in authors:
        status = update_author(author)
        edited = edited or status

    return edited, card, None


def update_all(cards):
    cards_updated = []
    cards_ok = []
    for card in tqdm(cards):
        status, card, traces = update_card(card)
        if status:
            cards_updated.append(card)
        else:
            cards_ok.append(card)

    return cards_updated, cards_ok


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

        cards = Card.objects.all()
        cards_updated, cards_ok = update_all(cards)

        self.stdout.write("Cards updated: {} / {}".format(len(cards_updated), cards.count()))
        self.stdout.write("Cards untouched: {} / {}".format(len(cards_ok), cards.count()))
