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
Test the user models.
"""
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from search.models import Bill
from search.models import Card
from search.models import Client
from search.models import Reservation
from search.models import Sell

from tests_models import CardFactory
from tests_models import PlaceFactory

class TestBill(TestCase):

    def setUp(self):
        self.bill = Bill(ref="987",
                         name="bill test",
                         due_date=datetime.date.today(),
                         total=100,
                    )
        self.bill.save()

    def tearDown(self):
        pass

    def test_create(self):
        bill = Bill(ref="987",
                    name="test bill",
                    due_date=datetime.date.today(),
                    total=100,
                    )
        self.assertTrue(bill)

    def test_add_copy(self):
        created = self.bill.add_copy(CardFactory.create(), nb=2)
        self.assertTrue(created)
        self.assertEqual(self.bill.billcopies_set.first().quantity, 2)

class TestClient(TestCase):

    def setUp(self):
        self.client = Client(name="client test", discount=9)  # TODO: fails with unicode
        self.client.save()
        self.assertTrue(self.client.repr())
        self.assertTrue(self.client.to_dict())
        self.assertTrue(self.client.get_absolute_url())
        # a Card
        self.card = CardFactory.create()
        # a Place
        self.place = PlaceFactory.create()

    def tearDown(self):
        pass

    def test_nominal(self):
        self.assertTrue(Client.search("test"))

    def test_reserve(self):
        # Reserve: create a reservation object, decrement quantity.
        resa, created = self.client.reserve(self.card)
        self.assertTrue(resa)
        self.assertEqual(self.card.quantity_compute(), -1)

        # Find open reservations.
        resas = Reservation.get_card_reservations(self.card)
        self.assertTrue(resas)

        # Cancel: put one in stock back.
        self.client.cancel_reservation(self.card)
        self.assertEqual(self.card.quantity_compute(), 0)

        # No more open reservations for this card.
        resas = Reservation.get_card_reservations(self.card.id)
        self.assertFalse(resas)

    def test_putaside(self):
        # bare bones: no reservation.
        status, msgs = Reservation.putaside(self.card, self.client)
        self.assertFalse(status)
        self.assertTrue(msgs)

        # With an ongoing reservation.
        resa, created = self.client.reserve(self.card)
        status, msgs = Reservation.putaside(self.card, self.client)
        self.assertTrue(status)
        self.assertFalse(msgs)

    def test_reserve_and_sell(self):
        # Reserve: create a reservation object, decrement quantity.
        resa, created = self.client.reserve(self.card)
        resas = Reservation.get_card_reservations(self.card)
        self.assertTrue(resas)

        # Sell: don't decrement it again, archive reservations.
        self.assertEqual(self.card.quantity_compute(), -1)
        Sell.sell_card(self.card, client=self.client)
        self.assertEqual(self.card.quantity_compute(), -1)

        # No more open reservations.
        resas = Reservation.get_card_reservations(self.card)
        self.assertFalse(resas)

        # Sell again: all normal.
        Sell.sell_card(self.card)
        self.assertEqual(self.card.quantity_compute(), -2)
