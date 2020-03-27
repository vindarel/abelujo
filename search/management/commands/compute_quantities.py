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
Compute the quantities and save to a DB field.

./manage.py compute_quantities

Takes around 3 minutes for a thousand objects.

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Card

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Go...")
        cards = Card.objects.all()
        self.stdout.write("Computing the quantities of {} Card objects.".format(cards.count()))
        confirmation = raw_input("Continue ? [Y/n]")
        if confirmation == "n":
            exit(0)

        count_ok = 0
        count_updated = 0
        for card in cards:
            qty = card.quantity_compute()
            if card.quantity == qty:
                count_ok += 1
                self.stdout.write("Card {}: OK ({})".format(card.id, qty))
            else:
                self.stdout.write("Card {}: quantity field VS computed property: {}, {}".format(
                    card.id, card.quantity, qty))
                card.quantity = qty
                card.save()  # yep, quantity_compute will be called twice.
                count_updated += 1

        self.stdout.write("-------------------")
        self.stdout.write("Cards OK: {}. Cards updated: {}".format(count_ok, count_updated))
        self.stdout.write("Done.")
