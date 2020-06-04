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
from __future__ import unicode_literals

from django.test import TestCase
from search.models import Card
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
        # 3 cards in stock.
        self.card = CardFactory()
        self.card2 = CardFactory()
        self.card3 = CardFactory()
        # 1 card not registered in stock.
        self.card4 = CardFactory()
        self.basket = BasketFactory()
        self.distributor = DistributorFactory()
        # A place, with the 3 cards.
        self.place = PlaceFactory()
        self.place.add_copies([self.card, self.card2, self.card3])
        # Add 3 cards to the basket:
        # - the 2 in stock
        # - and also the 4th one not in stock
        # "not in stock": its placecopies object can have been deleted when quantity=0.
        self.basket.add_cards([self.card, self.card2])
        self.basket.add_cards([self.card4])
        self.basket.distributor = self.distributor

    def tearDown(self):
        pass

    def test_return_basket(self):
        # preliminary check of the stock.
        self.assertEqual(1, self.card.quantity)
        self.assertEqual(3, self.place.placecopies_set.count())

        # Create the return.
        obj, msgs = self.basket.create_return()
        # (yes, inconsistency to return the Message object)
        self.assertEqual('success', msgs.status)
        self.assertTrue(obj)
        self.assertEqual(3, obj.copies.count())
        self.assertTrue(self.card3 not in obj.copies.all())
        self.assertEqual(1, len(OutMovement.returns()))
        # The cards were decremented from the stock.
        # Testing with self.card fails. self.card.quantity is not updated.
        # Fetching the card again is ok.
        card = Card.objects.first()
        card2 = Card.objects.all()[1]
        card3 = Card.objects.all()[2]
        card4 = Card.objects.all()[3]
        self.assertEqual(0, card.quantity_compute())
        self.assertEqual(0, card.quantity)
        self.assertEqual(0, self.place.quantity_of(self.card))
        self.assertEqual(0, card2.quantity)
        self.assertEqual(1, card3.quantity)
        # the card not in stock was *also* decremented.
        self.assertEqual(-1, card4.quantity)
        self.assertEqual(0, self.place.quantity_cards())
        self.assertEqual(4, self.place.placecopies_set.count())

        # Ignore quantity < 0
        card = CardFactory()
        self.place.add_copy(card, nb=-1)
        self.place.remove(card, quantity=card.quantity)
        self.assertEqual(-1, card.quantity)
