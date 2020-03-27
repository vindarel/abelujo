#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
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
Transform a shelf into a place.

Use case: we did the inventory, and it turned out that "mezzanine"
should be the stocking place, not a shelf (so we can know what's in stock).

Usage:

python manage.py shelf2place --shelf <id> [--can_sell true/false]
"""


from django.core.management.base import BaseCommand

from search.models import Preferences, Place, Shelf

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--shelf',
                            dest="shelf",
                            action="store",
                            required=True,
                            help="shelf id.")

        parser.add_argument('--can_sell',
                            dest="can_sell",
                            action="store_true",
                            help="'true' if the new place is a point of sells, 'false' if it is a stocking place.")

    def handle(self, *args, **options):
        shelf = Shelf.objects.get(id=options.get('shelf'))

        self.stdout.write(""" Transform the shelf {} into a place of the same name with ALL the cards from the default place. We don't create a movement object.
        Consequently the moved cards won't have an associated shelf anymore.
        The shelf object will be deleted, and the inventories made against it too.
        You might want to save or export your DB beforehand.""".format(shelf))
        self.stdout.write("Nb of cards to move: {}".format(shelf.cards_qty))
        self.stdout.write("The new place will be {}.".format("a selling place" if options.get('can_sell') else "a stocking place"))

        confirmation = eval(input("Continue ? [Y/n]"))
        if confirmation == 'n':
            exit(0)

        default_place = Preferences.get_default_place()
        new_place, created = Place.objects.get_or_create(name=shelf.name,
                                                         defaults={'can_sell': options.get('can_sell')})

        if not created:
            self.stdout.write("A place with the same name already exists.")
            exit(1)

        for card in shelf.cards():
            default_place.move(new_place, card, card.quantity, create_movement=False)
            card.shelf = None
            card.save()  # that's a second save :/

        # Delete the shelf object (and its associated inventories).
        shelf.delete()

        self.stdout.write("-------------------")
        self.stdout.write("All done.")
