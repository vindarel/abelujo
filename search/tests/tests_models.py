#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 The Abelujo Developers
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
Test the models.

Note: to compare two objects, don't use assertEqual but the == operator.
"""

import datetime

from django.contrib import messages
from django.test import TestCase

import factory
from factory.django import DjangoModelFactory
from search.models import Author
from search.models import Alert
from search.models import Basket
from search.models import BasketCopies
from search.models import BasketType
from search.models import Card
from search.models import CardType
from search.models import Collection
from search.models import Deposit
from search.models import DepositCopies
from search.models import Distributor
from search.models import getHistory
from search.models import Place
from search.models import PlaceCopies
from search.models import Preferences
from search.models import Publisher
from search.models import Sell
from search.models import STATUS_ERROR
from search.models import STATUS_SUCCESS
from search.models import STATUS_WARNING

from search.models.utils import hist

class SellsFactory(DjangoModelFactory):
    class Meta:
        model = Sell

    created = datetime.date.today()

class DepositFactory(DjangoModelFactory):
    class Meta:
        model = Deposit
    name = factory.Sequence(lambda n: "deposit test %d" % n)
    distributor = None
    dest_place = None
    due_date = None

class DistributorFactory(DjangoModelFactory):
    class Meta:
        model = Distributor
    name = factory.Sequence(lambda n: "distributor test %s" % n)

class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = Place
    name = factory.Sequence(lambda n: "place test %s" % n)
    is_stand = False
    can_sell = True

class CardFactory(DjangoModelFactory):
    class Meta:
        model = Card

    title = factory.Sequence(lambda n: 'card title %d' % n)
    isbn = factory.Sequence(lambda n: "%d" %n)
    card_type = None
    # distributor = factory.SubFactory(DistributorFactory)
    distributor = None
    price = 9.99

class TestCards(TestCase):
    def setUp(self):
        # Create card types
        self.type_book = "book"
        typ = CardType(name=self.type_book)
        typ.save()
        # a Publisher
        self.pub_name = "pub test"
        self.publisher = Publisher(name=self.pub_name)
        self.publisher.save()
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.fixture_ean = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title,
                            ean=self.fixture_ean,
                            isbn=self.fixture_ean,
                            card_type=typ)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        self.autobio.publishers.add(self.publisher)
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # a needed place:
        self.place_name = "test place"
        self.place = Place(name=self.place_name, is_stand=False, can_sell=True)
        self.place.save()
        self.place.add_copy(self.autobio, nb=1)
        # mandatory: preferences table
        self.preferences = Preferences(default_place=self.place).save()

    def test_add(self):
        found = Card.objects.get(title__icontains="living")
        self.assertTrue(found.authors.all()[0] == self.goldman)
        self.assertEqual(found, self.autobio)

    def test_from_dict(self):
        TITLE = "Foo bar"
        ZINN = "zinn"
        to_add, msgs = Card.from_dict({"title":TITLE,
                                       "authors":[self.GOLDMAN, ZINN],
                                       "isbn": "foobar",
                                       "location":"here"})
        self.assertTrue(to_add)
        self.assertEqual(to_add.title, TITLE)
        self.assertEqual(len(Author.objects.all()), 2)
        names = [aut.name for aut in to_add.authors.all()]
        self.assertTrue(ZINN in names)
        self.assertTrue(self.GOLDMAN in names)
        # Check that the author was created
        self.assertTrue(Author.objects.get(name=ZINN))

    def test_exists(self):
        """Card.exists unit test.
        """
        exists = Card.exists({'isbn': self.fixture_ean})
        self.assertTrue(exists)
        doesnt_exist, msgs = Card.exists({"isbn": "whatever",
                                               "title":"a different title"})
        self.assertFalse(doesnt_exist)
        same_title, msgs = Card.exists({"title": self.fixture_title})
        self.assertTrue(same_title)
        good_authors, msgs = Card.exists({"title": self.fixture_title,
                                          "authors": [self.GOLDMAN]})
        self.assertTrue(good_authors)
        good_publishers, msgs = Card.exists({"title": self.fixture_title,
                                             "authors": [self.GOLDMAN],
                                             "publishers": [self.pub_name]})
        self.assertTrue(good_publishers)
        bad_authors, msgs = Card.exists({"title": self.fixture_title,
                                         "authors": "bad author"})
        self.assertFalse(bad_authors)
        bad_publishers, msgs = Card.exists({"title": self.fixture_title,
                                            "authors": [self.GOLDMAN],
                                            "publishers": ["not a pub"]})
        self.assertFalse(bad_publishers)
        # TODO: and collection

    def test_from_dict_no_authors(self):
        TITLE = "I am a CD without authors"
        to_add, msgs = Card.from_dict({"title":TITLE})
        self.assertTrue(to_add)

    # def test_quantity_new(self):
    # TODO: put in test_move
    #     obj, msgs = Card.from_dict({"title": "New quantity test",
    #                           "ean": "111",
    #                           "quantity": 2})
    #     self.assertEqual(2, obj.quantity)

    def test_search(self):
        # Should search with way more cards.
        res = Card.search(["gold"], card_type_id=1)
        self.assertEqual(1, len(res))

    def test_search_notype(self):
        res = Card.search(["gold"], card_type_id=999)
        self.assertFalse(res)

    def test_search_alltypes(self):
        res = Card.search(["gold"], card_type_id=0)
        self.assertTrue(res)

    def test_search_only_type(self):
        # Doesn't pass data validation.
        self.assertTrue(Card.search("", card_type_id=1))

    def test_search_key_words(self):
        res = Card.search(["liv", "gold"])
        self.assertEqual(1, len(res))

    def test_sell(self):
        Card.sell(id=self.autobio.id, quantity=2)
        self.assertEqual(Card.objects.get(id=self.autobio.id).quantity, -1)

    def test_add_good_type(self):
        obj, msgs = Card.from_dict({"title": "living",
                              "card_type": self.type_book})
        self.assertEqual(self.type_book, obj.card_type.name)

    def test_add_bad_type(self):
        badtype = "badtype"
        obj, msgs = Card.from_dict({"title": "living",
                              "card_type": badtype})
        self.assertEqual(obj.title, "living")
        self.assertEqual(obj.card_type.name, "unknown")

    def test_type_unknown(self):
        obj, msgs = Card.from_dict({"title": "living",
                              "card_type": None})
        self.assertEqual(obj.card_type.name, "unknown")

        obj, msgs = Card.from_dict({"title": "living"})
        self.assertEqual(obj.card_type.name, "unknown")

    def test_get_from_id_list(self):
        cards_id = [1]
        res = Card.get_from_id_list(cards_id)
        self.assertTrue(res["result"])
        self.assertEqual(res["result"][0].title, self.fixture_title)

    def test_get_from_id_list_non_existent(self):
        cards_id = [1,2]
        res = Card.get_from_id_list(cards_id)
        self.assertTrue(res["result"])
        self.assertTrue(res["messages"])
        self.assertEqual(res["messages"][0]["message"], "the card of id 2 doesn't exist.")

    def test_placecopies(self):
        pass

class TestPublisher(TestCase):
    """Testing the addition of a publisher to a card.
    """

    def setUp(self):
        # create a Card
        self.autobio = Card(title="Living my Life", ean="987")
        self.autobio.save()
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # create a publisher
        self.publishers = Publisher(name="agone")
        self.publishers.save()

    def test_publisher_existing(self):
        pub = "agone"
        obj, msgs = Card.from_dict({"title": "living", "publishers": [pub]})
        all_pubs = obj.publishers.all()
        self.assertEqual(1, len(all_pubs))
        self.assertEqual(pub.lower(), all_pubs[0].name)

    def test_many_publishers(self):
        pub = ["agone", "maspero"]
        obj, msgs = Card.from_dict({"title": "living", "publishers": pub})
        all_pubs = obj.publishers.all()
        self.assertEqual(len(pub), len(all_pubs))
        self.assertEqual(pub[0].lower(), all_pubs[0].name)

    def test_publisher_non_existing(self):
        pub = "Foo"
        obj, msgs = Card.from_dict({"title": "living", "publishers": [pub]})
        self.assertEqual(pub.lower(), obj.publishers.all()[0].name)
        publishers = Publisher.objects.all()
        self.assertEqual(2, len(publishers))
        self.assertTrue(pub.lower() in [p.name for p in publishers])

class TestCollection(TestCase):
    """Testing the addition of a collection to a card.
    """

    def setUp(self):
        # create a Card
        self.autobio = Card(title="Living my Life", ean="987")
        self.autobio.save()
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # create a collection
        self.collection_name = "livre de poche"
        self.collection = Collection(name=self.collection_name)
        self.collection.save()

    def test_collection_existing(self):
        obj, msgs = Card.from_dict({"title": "living", "collection": self.collection_name})
        self.assertEqual(self.collection_name.lower(), obj.collection.name)

    def test_collection_non_existing(self):
        collection = "new collection"
        obj, msgs = Card.from_dict({"title": "living", "collection": collection})
        self.assertEqual(collection.lower(), obj.collection.name)
        collections = Collection.objects.all()
        self.assertEqual(2, len(collections))
        self.assertTrue(collection.lower() in [p.name for p in collections])

    def test_parent_collection(self):
        pass


class TestPlaceCopies(TestCase):

    def setUp(self):
        # Create a relation Card - PlaceCopies - Place
        self.place = Place(name="here", is_stand=False, can_sell=True); self.place.save()
        self.card = Card(title="test card")
        self.card.save()
        self.nb_copies = 9
        self.pl_cop = PlaceCopies(card=self.card, place=self.place, nb=self.nb_copies).save()
        self.prefs = Preferences(default_place=self.place).save()

    def tearDown(self):
        pass

    def test_add_copies(self):
        self.place.add_copy(self.card)
        new_nb = self.place.placecopies_set.get(card=self.card).nb
        self.assertEqual(self.nb_copies + 1, new_nb)
        self.place.add_copy(self.card, 10)
        new_nb = self.place.placecopies_set.get(card=self.card).nb
        self.assertEqual(self.nb_copies + 1 + 10, new_nb)

    def test_card_to_default_place(self):
        Place.card_to_default_place(self.card, nb=3)


class TestBaskets(TestCase):

    def setUp(self):
        # Create a Card, a Basket and the "auto_command" Basket.
        self.basket = Basket(name="test basket"); self.basket.save()
        self.basket_commands, created = Basket.objects.get_or_create(name="auto_command"); self.basket_commands.save()
        self.card = Card(title="test card") ; self.card.save()
        self.nb_copies = 9

    def tearDown(self):
        pass

    def test_basket_add_copy(self):
        # add a card.
        self.basket.add_copy(self.card)  # it creates the intermediate table if not found.
        self.assertEqual(self.basket.basketcopies_set.get(card=self.card).nb, 1)
        # idem, with specific nb.
        self.basket.add_copy(self.card, nb=self.nb_copies)
        self.assertEqual(self.basket.basketcopies_set.get(card=self.card).nb, 1 + self.nb_copies)

    def test_sell_auto_command_add_to_basket(self):
        """When a card reaches the threshold (0), pertains to a deposit and
        the deposit's auto_command is set to True, then add this card to the
        appropriate basket.
        """
        Card.sell(id=self.card.id)
        self.assertEqual(self.basket_commands.basketcopies_set.get(card=self.card).nb, 1)

class TestDeposits(TestCase):

    def setUp(self):
        self.distributor = DistributorFactory()
        self.distributor.save()
        self.goldman = Author(name="goldman")
        self.goldman.save()
        self.card = CardFactory()
        self.card.authors.add(self.goldman)
        self.card2 = CardFactory(distributor=self.distributor)
        self.card2.authors.add(self.goldman)
        self.deposit = DepositFactory(distributor=self.distributor)
        self.place = PlaceFactory()
        self.place.add_copy(self.card2)
        self.sell = SellsFactory()
        # self.sell.sell_cards(None, cards=[self.card2])

    def test_nominal(self):
        self.card.distributor = self.distributor
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(1, len(self.deposit.depositcopies_set.all()))
        self.assertEqual(1, self.card.quantity_deposits())
        self.deposit.add_copies([self.card])
        self.assertEqual(2, self.card.quantity_deposits())

    def test_no_distributor(self):
        self.card.distributor = None
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(len(msgs), 0)
        self.assertEqual(0, len(self.deposit.depositcopies_set.all()))

    def test_different_distributor(self):
        self.other_dist = Distributor(name="other dist").save()
        self.card.distributor = self.other_dist
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(len(msgs), 0)
        self.assertEqual(0, len(self.deposit.depositcopies_set.all()))

    def test_from_dict_nominal(self):
        self.card.distributor = self.distributor
        msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  })
        self.assertEqual(len(msgs), 1, "add deposit from dict: %s" % msgs)
        self.assertEqual(msgs[0]['level'], "success")


    def test_type_pub(self):
        """Of type "publisher", we set a due_date and a dest_place.
        """
        self.card.distributor = self.distributor
        due_date = datetime.date.today().isoformat() # getting it as str from JS
        dest_place = PlaceFactory.create()
        msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  'due_date': due_date,
                                  'dest_place': dest_place.id,
                                  'deposit_type': "publisher",
                                  })
        self.assertEqual(msgs[0]['level'], "success")
        dep = Deposit.objects.order_by("created").last()
        self.assertEqual(dep.dest_place.name, dest_place.name)
        self.assertEqual(dep.deposit_type, "publisher")

    def test_no_due_date(self):
        self.card.distributor = self.distributor
        dest_place = PlaceFactory.create()
        msgs = Deposit.from_dict({'name': 'test',
                                  'due_date': None,
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  'dest_place': dest_place.id,
                                  'deposit_type': "publisher",
                                  })
        self.assertEqual(msgs[0]['level'], "success")


    def test_from_dict_bad_deposit(self):
        self.card.distributor = None
        msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  })
        self.assertEqual(len(msgs), 2, "add deposit from dict: %s" % msgs)
        self.assertEqual(msgs[0]['level'], messages.WARNING)

    def test_from_dict_bad_deposit_one_good(self):
        self.card.distributor = None
        self.card2.distributor = self.distributor
        msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card, self.card2],
                                  'distributor': self.distributor,
                                  })
        self.assertEqual(len(msgs), 2, "add deposit from dict: %s" % msgs)
        self.assertEqual(msgs[0]['level'], messages.WARNING)

    def test_depostate_first(self):
        ret, msgs = self.deposit.checkout_create()
        # The deposit has no copies. Do nothing.
        self.assertEqual(None, ret)


        # Add cards to it.
        self.deposit.add_copies([self.card2])
        co, _ = self.deposit.checkout_create()
        # If it isn't ambiguous we can close it
        self.assertFalse(co.ambiguous)
        # We didn't sell anything yet but still should see the balance.
        bal = co.balance()
        self.assertEqual(0, bal["cards"][0][1].nb_sells)
        self.assertEqual(1, bal["cards"][0][1].nb_initial)
        self.assertEqual(1, bal["cards"][0][1].nb_current)

        # Sell a copy.
        self.sell.sell_cards(None, cards=[self.card2])

        # Check figures: how many copies we sold, how many we have
        co.update()
        balance = co.balance()
        self.assertFalse(co.closed)
        self.assertEqual(balance["cards"][0][1].nb_current, 0)
        self.assertEqual(balance["cards"][0][1].nb_initial, 1)
        self.assertEqual(balance["cards"][0][1].nb_sells, 1)
        self.assertEqual(balance["cards"][0][1].nb_to_command, 1)
        self.assertEqual(balance["cards"][0][1].nb_wanted, 1)
        co.close()
        self.assertTrue(co.closed)
        ret, msgs = co.add_copies([{'cards': [self.card2], 'sells': None}])
        self.assertFalse(ret)
        self.assertTrue(msgs)

    def test_depostate_second(self):
        Sell.sell_cards(None, cards=[self.card2])
        # Create a depositState, add copies, close it.
        self.deposit.add_copies([self.card2])
        co, msgs = self.deposit.checkout_create()
        co.close()
        self.assertTrue(co.closed)
        # Now test everythings' fine with a second depositState.
        # Let's sell another card.
        Sell.sell_cards(None, cards=[self.card2])
        # The deposit state should exist and show good information.
        checkout, msgs = self.deposit.checkout_create()
        self.assertEqual([], msgs)
        balance = checkout.balance()
        self.assertEqual(1, balance["cards"][0][1].nb_sells)
        self.assertEqual(-1, balance["cards"][0][1].nb_current)

        co, msgs = self.deposit.checkout_create()
        self.assertFalse(co)
        checkout.close()
        co, msgs = self.deposit.checkout_create()
        self.assertTrue(co)

    def test_depostate_dates(self):
        """Don't count sells anterior from the creation of the deposit.
        """
        Sell.sell_cards(None, cards=[self.card2])
        depo = DepositFactory(distributor=self.distributor)
        depo.add_copies([self.card2])
        co, msgs = depo.checkout_create()
        balance = co.balance()
        self.assertEqual(0, balance["cards"][0][1].nb_current)
        self.assertEqual(0, balance["cards"][0][1].nb_sells)

class TestSells(TestCase):

    def setUp(self):
        # Create card types
        self.type_book = "book"
        typ = CardType(name=self.type_book)
        typ.save()
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.autobio = CardFactory(card_type=typ)
        self.autobio.authors.add(self.goldman)
        # a second card:
        self.secondcard = CardFactory()
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # a needed place:
        self.place_name = "test place"
        self.place = Place(name=self.place_name, is_stand=False, can_sell=True)
        self.place.save()
        self.place.add_copy(self.autobio, nb=1)
        self.place.add_copy(self.secondcard, nb=1)
        # a Distributor:
        self.dist = Distributor(name="dist test")
        self.dist.save()
        # a Deposit:
        self.depo = Deposit(name="deposit test", distributor=self.dist)
        self.depo.save()
        # mandatory: preferences table
        self.preferences = Preferences(default_place=self.place).save()

    def tearDown(self):
        pass

    def test_sell_many_cards(self):
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1},
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(STATUS_SUCCESS, status)

        int_table = sell.soldcards_set.all()
        self.assertEqual(len(int_table), 2)
        # check prices
        self.assertEqual(int_table[0].price_sold, p1)
        self.assertEqual(int_table[1].price_sold, p2)
        # check quantities
        self.assertEqual(int_table[0].card.quantity, 0)
        self.assertEqual(int_table[1].card.quantity, -1)

    def test_sell_none(self):
        to_sell = []
        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(STATUS_WARNING, status)

    def test_sell_no_price(self):
        p1 = 7.7
        p2 = 9.9
        self.autobio.price = None
        self.autobio.save()
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    # "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]

        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(STATUS_WARNING, status)
        int_table = sell.soldcards_set.all()
        self.assertTrue(len(int_table), 1)

    def test_alert_deposit(self):
        """Create an ambigous sell, check an Alert is created."""
        self.place.add_copy(self.autobio) # 1 in deposit, 1 not: ambiguous
        # add a copy to the deposit:
        self.autobio.distributor = self.dist
        self.autobio.save()
        self.depo.add_copies([self.autobio])
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    # "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(Alert.objects.count(), 1)


class TestHistory(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.sell = SellsFactory.create()
        Sell.sell_cards([{"id":"1", "price_sold":1, "quantity": 1}])

    def tearDown(self):
        pass

    def test_history(self):
        hist, status, alerts = getHistory()
        self.assertEqual(3, len(hist)) # a Sell is created without any cards sold.
        self.assertEqual(STATUS_SUCCESS, status)

class TestAlerts(TestCase):

    def setUp(self):
        # a card in a deposit, with the same distributor each.
        self.dist = DistributorFactory.create()
        self.card = CardFactory.create()
        self.card.distributor = self.dist
        self.deposit = DepositFactory.create()
        self.deposit.distributor = self.dist
        self.deposit.add_copies([self.card])
        # the tested Alert.
        self.alert = Alert(card=self.card)
        self.alert.save()

    def test_get_alerts(self):
        self.alert.deposits.add(self.deposit)
        got = Alert.get_alerts(to_list=True)
        self.assertTrue(got)

    def test_nominal(self):
        self.alert.deposits.add(self.deposit)

    def test_add_deposits_of_card(self):
        self.alert.add_deposits_of_card(self.card)
        self.assertEqual(1, len(self.card.deposit_set.all()))
