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

from search.models import Basket
from search.models import Bill
# from search.models import Card
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
        self.client = Client(name="Élodie Ô client test", discount=9)
        self.client.save()
        self.assertTrue(self.client.repr())
        self.assertTrue(self.client.to_dict())
        self.assertTrue(self.client.get_absolute_url())
        # a Card
        self.card = CardFactory.create()
        # a Place
        self.place = PlaceFactory.create()
        # the command Basket
        self.to_command = Basket.objects.create(name="auto_command").save()

    def tearDown(self):
        pass

    def test_nominal(self):
        self.assertTrue(Client.search("test"))

    def test_reserve(self):
        self.assertEqual(self.card.quantity_to_command(), 0)
        # Reserve: create a reservation object, decrement quantity.
        resa, created = self.client.reserve(self.card)
        self.assertTrue(resa)
        self.assertEqual(self.card.quantity_compute(), -1)

        # The book was added in the command list (because quantity is < 0).
        self.assertEqual(self.card.quantity_to_command(), 1)

        # Find open reservations.
        resas = Reservation.get_card_reservations(self.card)
        self.assertTrue(resas)

        # Cancel: put one in stock back.
        self.client.cancel_reservation(self.card)
        self.assertEqual(self.card.quantity_compute(), 0)

        # No more open reservations for this card.
        resas = Reservation.get_card_reservations(self.card.id)
        self.assertFalse(resas)

        # Somehow we reserve a card and add it to the command list.
        # Then somehow its quantity becomes > 1 (+1 button).
        # When we cancel the reservation, the card is removed from the command.
        # start with 1.
        self.place.add_copy(self.card)
        # reserve
        resa, created = self.client.reserve(self.card)
        self.assertEqual(self.card.quantity_compute(), 0)
        #
        self.assertEqual(self.card.quantity_to_command(), 1)
        # inc. quantity
        self.place.add_copy(self.card, nb=2)
        self.assertEqual(self.card.quantity, 2)
        # now we have 1 to command… why?
        # self.assertEqual(self.card.quantity_to_command(), 1)
        # cancel reservation.
        self.client.cancel_reservation(self.card)
        # quantity in command is back to 0.
        self.assertEqual(self.card.quantity_to_command(), 0)

    def test_cancel_reservation(self):
        # XXX: tests sur l'application moyennement concluants. Tjrs 1 dans la liste.
        # Same from above, but start with 0.
        # reserve
        resa, created = self.client.reserve(self.card)
        self.assertEqual(self.card.quantity_compute(), -1)
        # 1 to command so far.
        self.assertEqual(self.card.quantity_to_command(), 1)
        # inc. quantity in stock.
        self.place.add_copy(self.card, nb=2)
        self.assertEqual(self.card.quantity, 1)
        # still 1 to command.
        self.assertEqual(self.card.quantity_to_command(), 1)
        # cancel reservation.
        self.client.cancel_reservation(self.card)
        # quantity in command is back to 0.
        self.assertEqual(self.card.quantity_to_command(), 0)

    def test_cancel_after_sell(self):
        # Reserve, sell and cancel reservation.
        # quantity starts at 0.
        resa, created = self.client.reserve(self.card)
        self.assertEqual(self.card.quantity_compute(), -1)
        self.assertEqual(self.card.quantity_to_command(), 1)
        Sell.sell_card(self.card)
        self.assertEqual(self.card.quantity_compute(), -2)
        self.assertEqual(self.card.quantity_to_command(), 1)
        self.client.cancel_reservation(self.card)
        self.assertEqual(self.card.quantity_compute(), -1)
        # quantity to command is 1 (not -1, but how did that happen anyways?)
        self.assertEqual(self.card.quantity_to_command(), 1)

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
