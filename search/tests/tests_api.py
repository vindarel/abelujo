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


import datetime
import http.client
import json
import logging
import unittest

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

import factory
from factory.django import DjangoModelFactory
from search import models
from search.models.api import getSellDict
from search.models.api import list_from_coma_separated_ints
from search.models.api import list_to_pairs
from search.models.common import (ALERT_SUCCESS,  # noqa: F401
                                  ALERT_ERROR,
                                  ALERT_INFO,
                                  ALERT_WARNING)
from search.models.utils import get_logger
from .tests_models import SellsFactory
from .tests_models import PlaceFactory
from .tests_models import PreferencesFactory

log = get_logger()

class DistributorFactory(DjangoModelFactory):
    class Meta:
        model = models.Distributor

    name = factory.Sequence(lambda n: "distributor-%s" % n)

class CardFactory(DjangoModelFactory):
    class Meta:
        model = models.Card

    title = factory.Sequence(lambda n: 'card title %d' % n)
    distributor = factory.SubFactory(DistributorFactory)
    price = 10

class BasketFactory(DjangoModelFactory):
    class Meta:
        model = models.Basket


# class ApiTest(TestCase, DBFixture):
class ApiTest(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.sell = SellsFactory.create()
        # Preferences, default Place.
        self.place = PlaceFactory.create()
        self.preferences = PreferencesFactory()
        self.preferences.default_place = self.place
        self.preferences.save()

        # Create a first Sell.
        models.Sell.sell_cards([{"id": "1", "price_sold": 1, "quantity": 1}])
        self.card_unicode = CardFactory.create(title="title unicode éèà")
        self.params = {
            "cards_id": "1,2",
            "distributor": self.card.distributor.name,
            "name": "depo test from client",
            "deposit_type": models.DEPOSIT_TYPES_CHOICES[0][1][0][0],  # lib, whatever
            "initial_nb_copies": 1,
            "minimal_nb_copies": 1,
            "auto_command": "true",
        }

        self.c = Client()

    def tearDown(self):
        pass

    def test_get_card(self):
        resp = self.c.get(reverse("api_card", args=(1,)))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['data']["id"], 1)

    def test_deposits_add(self):
        """Test a deposit creation with data coming from the client (i.e., can be wrong).
        """
        resp = self.c.post("/api/deposits", self.params)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_data["status"], ALERT_WARNING)

    def test_deposits_add_pubtype(self):
        due_date = datetime.date.today()
        self.params["due_date"] = due_date.isoformat()
        self.params["dest_place"] = 1
        resp = self.c.post("/api/deposits", self.params)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_data["status"], ALERT_WARNING)
        dep = models.Deposit.objects.order_by("created").first()
        self.assertEqual(dep.due_date, due_date)
        self.assertEqual(dep.dest_place.name, models.Place.objects.get(id=1).name)

    def test_deposits_no_card(self):
        """Yes it is possible to create one without cards.
        """
        self.params["cards_id"] = ""
        resp = self.c.post("/api/deposits", self.params)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp_data["alerts"][0]["level"], ALERT_SUCCESS)

    def test_sell_cards(self):
        self.params["to_sell"] = "1,9.5,2"
        self.params["date"] = "2015-04-17 00:00:00"
        resp = self.c.post("/api/sell", self.params)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp_data["status"], models.ALERT_SUCCESS)

    def test_sell_cards_nocards(self):
        log.setLevel(logging.ERROR)
        self.params["to_sell"] = ""
        resp = self.c.post("/api/sell", self.params)
        # resp_data = json.loads(resp.content)
        self.assertEqual(resp.status_code, http.client.OK)

    def test_sell_cards_unicode(self):
        self.params["to_sell"] = "2,9.5,2"
        resp = self.c.post("/api/sell", self.params)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp_data["status"], models.ALERT_SUCCESS)

    def test_history(self):
        resp = self.c.get(reverse("api_history_sells"))
        self.assertEqual(resp.status_code, http.client.OK)

    def test_alerts(self):
        alert = models.Alert(card=models.Card.objects.first())
        alert.save()
        resp = self.c.get(reverse("api_alerts"))
        self.assertEqual(resp.status_code, http.client.OK)

    def test_api_utils(self):
        self.assertEqual(list_from_coma_separated_ints(""), [])
        self.assertEqual(list_from_coma_separated_ints("1,2.2,3"), [1, 2.2, 3])
        #xxx: data validation againts invalid input.
        # self.assertEqual(list_from_coma_separated_ints("1,2+3a"), None)

        self.assertEqual(getSellDict(['37', '5', '9.8', '10.1', '1', '1']),
                                     [{"id": '37', "price_sold": '9.8', "quantity": '1'},
                                      {"id": '5', "price_sold": '10.1', "quantity": '1'}])

    def test_places(self):
        resp = self.c.get(reverse("api_places"))
        data = json.loads(resp.content)
        self.assertTrue(data[0]["name"] == self.place.name)

class TestBasket(TestCase):

    def setUp(self):
        self.c = Client()

        # ToCommand, a basket.
        self.to_command = BasketFactory.create()
        self.basket = BasketFactory.create()

        # Add cards to basket.
        for _ in range(3):
            self.basket.add_copy(CardFactory.create())

        # a Distributor.
        self.dist = DistributorFactory.create()

        # Preferences, default Place.
        self.place = PlaceFactory.create()
        self.preferences = models.Preferences(default_place=self.place).save()

    def tearDown(self):
        pass

    def test_add_ids(self):
        """
        Add cards from ids.
        From
        """
        pass

    def test_add_cards(self):
        """
        We add a card to the autocommand with an id, with a distributor
        (auto_command page quicksearch & add).
        """
        def do_post(dist_id=self.to_command.id):
            data = json.dumps({'params':
                               {'card_id': 1,
                                'dist_id': dist_id}})
            return self.c.post(reverse('api_basket_add_card', args=(1,)),
                               data=data,
                               content_type='application/json')

        resp = do_post()
        self.assertEqual(resp.status_code, http.client.OK)
        self.assertTrue(self.to_command.copies.count())
        just_added = self.to_command.copies.first()
        self.assertTrue(just_added.distributor)

        # We try again: it should pass.
        resp = do_post()
        self.assertEqual(resp.status_code, http.client.OK)

        # We try to add with a wrong distributor.
        resp = do_post(dist_id=2)
        self.assertEqual(just_added.distributor.id, 1)
        self.assertTrue('message' in resp.content and 'danger' in resp.content)

    def test_add_basket(self):
        """
        Add all the cards from a basket.
        From List/Command.
        """
        self.basket.distributor = self.dist

        data = json.dumps({'basket_id': 2})  # not needed in django 2.
        resp = self.c.post('/api/baskets/1/add/', data=data, content_type='application/json')
        data = json.loads(resp.content)
        self.assertTrue(data['status'])
        self.assertEqual(self.to_command.copies.count(), self.basket.copies.count())
        # bad factory, creates 3 dists. Never mind, set_distributor is unit tested.
        # self.assertEqual(self.to_command.copies.last().distributor, self.dist)


class TestBaskets(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.basket = BasketFactory.create()
        self.basket.add_copy(self.card)
        self.params = {
            "cards_id": self.card.id,
        }
        self.place = PlaceFactory.create()
        self.preferences = models.Preferences(default_place=self.place).save()
        self.c = Client()

    # XXX: Django: we can't read request.body twice. It appears a middleware reads it before us
    # in api.basket. We get:
    # RawPostDataException: You cannot access body after reading from request's data stream
    # => write end to end tests.

    # def test_basket_add_card(self):
    #     resp = self.c.post(reverse("api_basket_act", args=('1', 'add')), self.params)
    #     data = json.loads(resp.content)
    #     self.assertTrue(data['status'] )
    #     self.assertFalse(data['msgs'] )

    def test_basket_remove_card(self):
        # self.params["cards_id"] = ""
        # resp = self.c.post("/api/deposits", self.params)
        # Setting the content type makes the test work (there's no body params here, so ok).
        # https://github.com/tomchristie/django-rest-framework/issues/2774
        resp = self.c.post(reverse("api_basket_act", args=('1', 'remove', "1,")), content_type='application/json')
        data = json.loads(resp.content)
        self.assertTrue(data['status'])
        self.assertEqual(data['msgs'][0]['level'], ALERT_SUCCESS)

    def test_basket_delete(self):
        self.c.post(reverse("api_basket_delete", args=('1')),
                           content_type='application/json')
        baskets = models.Basket.objects.all()
        self.assertFalse(baskets)

    def test_basket_delete_bad(self):
        log.setLevel(logging.CRITICAL)
        resp = self.c.post(reverse("api_basket_delete", args=('9')),
                           content_type='application/json')
        data = json.loads(resp.content)
        self.assertEqual(data['status'], ALERT_ERROR)


class TestUtils(TestCase):

    def test_list_to_pairs(self):
        self.assertEqual(list_to_pairs([1, 0, 2, 0]), [(1, 0), (2, 0)])


if __name__ == '__main__':
    exit(unittest.main())
