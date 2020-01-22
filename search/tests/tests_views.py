#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2019 The Abelujo Developers
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

import mock
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from search.models import Author
from search.models import Basket
from search.models import Card
from search.models import CardType
from search.models import Deposit
from search.models import Distributor
from search.models import Place
from search.models import Preferences
from search.models import Publisher
from search.models import Sell
from search.views import get_reverse_url

from tests_models import CardFactory
from tests_models import DepositFactory
from tests_models import PlaceFactory
from django.contrib import auth

fixture_search_datasource = {
    "test search":
    [{"title": 'fixture',
      "isbn": "111",
      "details_url": "http://fake_url.com",
      "data_source": "chapitre"
  }],
    "éé":
    [{"title": "éé",
      "isbn": "222",
  }]
}

session_mock_data = {
    "search_result": {
        "emma gold":
        [{"title": 'fixture',
       "isbn": "111",
       "details_url": "http://fake_url.com",
       "data_source": "chapitre"
   }],
        "éé":
        [{"title": "éé",
       "isbn": "222",
   }]
    }}

fixture_no_isbn = {"test search":
                  [{"title": "fixture no isbn",
                    "details_url": "http://fake_url",
                    "data_source": "chapitre"  # must fetch module's name
                }]}

fake_postSearch = {"isbn": "111"}

class DBFixture():
    """Create a card and required DB entries.

    The card gets an author, a type, a publisher;
    The required entries are the unknown card type, the Preferences with a default place.
    """

    def __init__(self):
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.fixture_isbn = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title, isbn=self.fixture_isbn)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # mandatory: unknown card type
        self.typ = CardType(name="unknown")
        self.typ.save()
        # create other card types
        self.type_book = "book"
        self.typ = CardType(name=self.type_book)
        self.typ.save()
        # add a publisher
        self.pub = Publisher(name="agone")
        self.pub.save()
        self.autobio.publishers.add(self.pub)
        # a needed place:
        self.place = Place(name="test place", is_stand=False, can_sell=True)
        self.place.save()
        # Preferences: (default place)
        self.preferences = Preferences(default_place=self.place).save()
        # create a Basket
        self.basket = Basket(name="basket_test")
        self.basket.save()

        # a Distributor and a Deposit with no cards
        self.distributor_name = "distributor test"
        self.distributor = Distributor(name=self.distributor_name).save()
        self.deposit = Deposit(name="deposit test").save()

class TestLogin(TestCase):

    def setUp(self):
        self.c = Client()

    def test_login_no_user(self):
        resp = self.c.get(reverse("card_search"))
        self.assertEqual(resp.status_code, 302)

    def test_login(self):
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")
        resp = self.c.get(reverse("card_search"))
        self.assertEqual(resp.status_code, 200)

    def test_logout(self):
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")
        self.c.get(reverse("logout"))
        resp = self.c.get(reverse("card_search"))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue("login/?next" in resp.url)

    # def test_login_required(self):
    #     """Login is required for all the views of the "search" app.
    #     """
    #     for pattern in search_urls.urlpatterns:
    #         if pattern.name:
    #             # this approach doesn't work cause some views require
    #             # arguments. Still, we might do sthg about it.
    #             resp = self.c.get(reverse(pattern.name))
    #             self.assertEqual(resp.status_code, 302)

class TestViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        self.autobio = Card(title="Living my Life", isbn="123")
        self.autobio.save()
        self.autobio.authors.add(self.goldman)

        # see also test fixtures https://docs.djangoproject.com/en/1.7/topics/testing/tools/#django.test.TransactionTestCase.fixtures
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")

    def post_to_view(self, isbn=None):
        post_params = {}
        if isbn:
            post_params["isbn"] = isbn
        return self.c.post(reverse("card_sell"), post_params)

    def test_sell_isbn_doesnt_exist(self):
        resp = self.post_to_view(isbn="9876")
        self.assertTrue(resp)
        pass  # test views with RequestFactory

    def test_sell_isbn(self):
        resp = self.post_to_view(isbn="123")
        self.assertTrue(resp)

    def test_sell_no_isbn_in_post(self):
        resp = self.post_to_view()
        self.assertTrue(resp)

class TestSells(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")

    def populate(self):
        self.card = CardFactory.create()
        p1 = 7.7
        to_sell = [{"id": self.card.id,
                    "quantity": 1,
                    "price_sold": p1},
                  ]
        sell, status, msgs = Sell.sell_cards(to_sell)

    def test_sell_details_no_sell(self):
        resp = self.c.get(reverse("sell_details", args=(1,)))
        self.assertTrue(resp)

    def test_sell_details(self):
        self.populate()
        resp = self.c.get(reverse("sell_details", args=(self.card.id,)))
        self.assertTrue(resp.status_code, "200")


@mock.patch('search.views_utils.search_on_data_source', return_value=(fixture_search_datasource, []))
class TestSearchView(TestCase):

    def setUp(self):
        self.c = Client()
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")

    def get_for_view(self, cleaned_data, url_name="card_search"):
        """Use our view utility to get the reverse url with encoded query parameters.
        """
        cleaned_data["source"] = "chapitre"
        # get the reverse url with encoded paramaters
        return self.c.get(get_reverse_url(cleaned_data,
                                          url_name))

    def test_search_no_query_params(self, search_mock):
        resp = self.get_for_view({})
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_with_isbn(self, search_mock):
        resp = self.get_for_view({"isbn": "123"})
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_with_keywords(self, search_mock):
        data = {"q": "emma gold"}
        resp = self.get_for_view(data)
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_params_not_valid(self, search_mock):
        data = {"foo": "bar"}
        resp = self.get_for_view(data)
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)


@mock.patch('search.views_utils.search_on_data_source', return_value=fixture_search_datasource)
class TestAddView(TestCase):

    def setUp(self):
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.fixture_isbn = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title, isbn=self.fixture_isbn)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # Create a distributor
        self.dist = Distributor(name="dist test")
        self.dist.save()
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # create other card types
        self.type_book = "book"
        typ = CardType(name=self.type_book)
        typ.save()
        # create places and add copies (to Move)
        self.place = PlaceFactory.create()
        self.place2 = PlaceFactory.create()
        self.place.add_copy(self.autobio)

        self.c = Client()

        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")

    def test_move(self, mock_data_source):
        resp = self.c.get(reverse("card_move", args=(1,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.c.post(reverse("card_move", args=(1,)), data={
            "origin": 1,
            "destination": 2,
            "nb": 2,
        })
        # xxx: test we've been redirected to the right url (either search, either card).

class TestDeposit(TestCase, DBFixture):

    def setUp(self):
        DBFixture.__init__(self)
        self.c = Client()
        self.user = auth.models.User.objects.create_user(username="admin", password="admin")
        self.c.login(username="admin", password="admin")

    def test_new_nominal(self):
        resp = self.c.get(reverse("deposits_new"))
        self.assertEqual(resp.status_code, 200)

    def test_add_copies_form(self):
        deposit = DepositFactory()
        resp = self.c.get(reverse('deposit_add_copies', args=(deposit.id,)))
        self.assertEqual(resp.status_code, 200)
