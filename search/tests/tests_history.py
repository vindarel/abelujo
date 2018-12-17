#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2017 The Abelujo Developers
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

from django.test import TestCase
from search.models import Entry
from search.models import OutMovement

from tests_models import BasketFactory
from tests_models import CardFactory
from tests_models import DistributorFactory
from tests_models import PlaceFactory

class TestEntry(TestCase):

    def setUp(self):
        self.card = CardFactory()

    def test_entry(self):
        en, created = Entry.new([self.card])
        self.assertTrue(created)


class TestOutMovement(TestCase):

    def setUp(self):
        self.card = CardFactory()
        self.card2 = CardFactory()
        self.card3 = CardFactory()
        self.basket = BasketFactory()
        self.distributor = DistributorFactory()
        # A place, with all the cards.
        self.place = PlaceFactory()
        self.place.add_copies([self.card, self.card2, self.card3])
        # Add 2 cards to the basket
        self.basket.add_cards([self.card, self.card2])
        self.basket.distributor = self.distributor

    def tearDown(self):
        pass

    def test_return_basket(self):
        # preliminary check of the stock.
        self.assertEqual(1, self.card.quantity)

        # Create the return.
        obj, msgs = self.basket.create_return()
        # (yes, inconsistency to return the Message object)
        self.assertEqual('success', msgs.status)
        self.assertTrue(obj)
        self.assertEqual(2, obj.copies.count())
        self.assertTrue(self.card3 not in obj.copies.all())
        self.assertEqual(1, len(OutMovement.returns()))
        # The cards were decremented from the stock.
        self.assertEqual(0, self.card.quantity)
        self.assertEqual(0, self.place.quantity_of(self.card))
        self.assertEqual(0, self.card2.quantity)
        self.assertEqual(1, self.card3.quantity)
        self.assertEqual(1, self.place.quantity_cards())

        # Ignore quantity < 0
        card = CardFactory()
        self.place.add_copy(card, nb=-1)
        self.place.remove(card, quantity=card.quantity)
        self.assertEqual(-1, card.quantity)
