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

from search.models import Card, CardType

# py2/3
try:
    input = raw_input
except NameError:
    pass

def cards_not_book_types():
    book_type = CardType.objects.filter(name="book").first()
    res = Card.objects.exclude(card_type=book_type)\
                      .filter(isbn__startswith='97')
    return res

def update_all(queryset):
    book_type = CardType.objects.filter(name="book").first()
    queryset.update(card_type=book_type)
    return True

class Command(BaseCommand):

    help = "Search covers for cards that miss one (usually the ones coming from Dilicom)."

    def handle(self, *args, **options):
        cards = cards_not_book_types()
        self.stdout.write("Cards that don't have a type 'book' but have a book ISBN: {}".format(cards.count()))
        if cards.count() == 0:
            self.stdout.write("They are all clean! Nothing to do.")
            exit(0)
        confirmation = input("Set their type to 'book'? [Y/n]")
        if confirmation == "n":
            exit(0)
        update_all(cards)
        self.stdout.write("Done.")
