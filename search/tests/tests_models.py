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

"""
Test the models.

Note: to compare two objects, don't use assertEqual but the == operator.
"""

import datetime

import factory
import logging
from django.test import TestCase
from django.test import TransactionTestCase
from django.utils import timezone
from factory.django import DjangoModelFactory

from search.models import ALERT_ERROR
from search.models import ALERT_SUCCESS
from search.models import ALERT_WARNING
from search.models import Author
from search.models import Basket
from search.models import Card
from search.models import CardType
from search.models import Collection
from search.models import Command
from search.models import Deposit
from search.models import Distributor
from search.models import Inventory
from search.models import InventoryCommand
from search.models import Place
from search.models import PlaceCopies
from search.models import Preferences
from search.models import Publisher
from search.models import Restocking
from search.models import RestockingCopies
from search.models import Sell
from search.models import Shelf
from search.models import SoldCards
from search.models import history
from search.models import Stats
from search.models.utils import get_logger
from search.models.utils import distributors_match

log = get_logger()

class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Sequence(lambda n: "author test %d" % n)

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
    due_date = datetime.date.today() + datetime.timedelta(days=30)

class DistributorFactory(DjangoModelFactory):
    class Meta:
        model = Distributor
    name = factory.Sequence(lambda n: "distributor test %s" % n)
    discount = 35

class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = Place
    name = factory.Sequence(lambda n: "place test %s" % n)
    is_stand = False
    can_sell = True

class PreferencesFactory(DjangoModelFactory):
    class Meta:
        model = Preferences
    default_place = PlaceFactory()
    vat_book = "5.5"

class PublisherFactory(DjangoModelFactory):
    class Meta:
        model = Publisher
    name = factory.Sequence(lambda n: "publisher test %s" % n)

class InventoryFactory(DjangoModelFactory):
    class Meta:
        model = Inventory


ISBN = "9782757837009"


class ShelfFactory(DjangoModelFactory):
    class Meta:
        model = Shelf

    name = factory.Sequence(lambda n: "shelf test id %s" % (n + 1))

class BasketFactory(DjangoModelFactory):
    class Meta:
        model = Basket

    name = factory.Sequence(lambda n: "basket test id %s" % (n + 1))
    distributor = None

class CardFactory(DjangoModelFactory):
    class Meta:
        model = Card

    title = factory.Sequence(lambda n: u'card title é and ñ %d' % n)
    isbn = factory.Sequence(lambda n: "%d" % n)
    card_type = None
    # distributor = factory.SubFactory(DistributorFactory)
    distributor = None
    price = 9.99
    isbn = ISBN

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
        self.fixture_isbn = ISBN
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title,
                            isbn=self.fixture_isbn,
                            shelf=ShelfFactory(),
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

    def tearDown(self):
        log.setLevel(logging.DEBUG)

    def test_shelf_repr(self):
        self.assertNotEqual("", self.autobio.shelf_repr)
        self.autobio.shelf = None
        self.autobio.save()
        self.assertEqual("", self.autobio.shelf_repr)

    def test_add(self):
        found = Card.objects.get(title__icontains="living")
        self.assertTrue(found.authors.all()[0] == self.goldman)
        self.assertEqual(found, self.autobio)

    def test_from_dict(self):
        TITLE = "Foo bar"
        ZINN = "zinn"
        to_add, msgs = Card.from_dict({"title": TITLE,
                                       "authors": [self.GOLDMAN, ZINN],
                                       "isbn": "foobar",
                                       "location": "here"})
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
        exists = Card.exists({'isbn': self.fixture_isbn})
        self.assertTrue(exists)
        doesnt_exist, msgs = Card.exists({"isbn": "whatever",
                                               "title": "a different title"})
        self.assertFalse(doesnt_exist)
        # The same title is not enough.
        same_title, msgs = Card.exists({"title": self.fixture_title})
        self.assertFalse(same_title)
        self.assertTrue(msgs)
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

    def test_exists_many(self):
        # Second card with same title, other authors
        self.card2 = Card(title=self.fixture_title,
                          isbn=self.fixture_isbn,
                          shelf=ShelfFactory())
        self.card2.save()
        author = AuthorFactory()
        self.card2.authors.add(author)
        self.card2.save()

        # we find our card when many have the same title.
        same_authors, msgs = Card.exists({"title": self.fixture_title,
                                           "authors": [author.name]})
        self.assertTrue(same_authors)
        # same title but different authors.
        other_authors, msgs = Card.exists({"title": self.fixture_title,
                                           "authors": [AuthorFactory()]})
        self.assertFalse(other_authors)
        # only the same title. Not enough to find a similar card.
        no_pubs_no_authors, msgs = Card.exists({"title": self.fixture_title, })
        self.assertFalse(no_pubs_no_authors)
        self.assertTrue(msgs)

        # TODO: and collection

    def test_cards_in_stock(self):
        res = Card.cards_in_stock()
        self.assertEqual(1, len(res))
        # cards only in baskets should not appear.
        basket = BasketFactory.create()
        card = CardFactory.create()
        basket.add_copy(card)
        res = Card.cards_in_stock()
        self.assertEqual(2, Card.objects.count())
        self.assertEqual(1, len(res))

    def test_is_in_stock(self):
        card_dict = self.autobio.to_list()
        # xxx: strange: card_dict['isbn'] is u"" but to_list()
        # returns the right thing :S
        # Without this, this test passes in TestCards, but not in the
        # full test suite.
        card_dict['isbn'] = self.autobio.isbn
        card_dict['id'] = None
        other = {
            "title": "doesn't exist",
            "isbn": None,
        }
        cards = Card.is_in_stock([card_dict, other])
        self.assertTrue(cards)
        self.assertEqual(cards[0]['in_stock'], self.autobio.quantity)
        self.assertEqual(cards[0]['id'], self.autobio.id)
        self.assertFalse(cards[1]['in_stock'])

    def test_from_dict_no_authors(self):
        TITLE = "I am a CD without authors"
        to_add, msgs = Card.from_dict({"title": TITLE})
        self.assertTrue(to_add)

    def test_update(self):
        #TODO: test that we update fields of the card when we use
        #from_dict but the card alreay exists.
        pass

    def test_search(self):
        # Should search with way more cards.
        res, meta = Card.search(["gold"], card_type_id=1)
        self.assertEqual(1, len(res))

    def test_search_notype(self):
        res, meta = Card.search(["gold"], card_type_id=999)
        self.assertFalse(res)

    def test_search_alltypes(self):
        res, meta = Card.search(["gold"], card_type_id=0)
        self.assertTrue(res)

    def test_search_only_type(self):
        # Doesn't pass data validation.
        self.assertTrue(Card.search("", card_type_id=1))

    def test_search_key_words(self):
        res, meta = Card.search(["liv", "gold"])
        self.assertEqual(1, len(res))

    def test_search_card_isbn(self):
        res, meta = Card.search([ISBN])
        self.assertEqual(len(res), 1)

    def test_search_shelf(self):
        res, meta = Card.search(["gold"], shelf_id=1)
        self.assertEqual(len(res), 1)
        # Shelf doesn't exist:
        res, meta = Card.search(["gold"], shelf_id=2)
        self.assertEqual(len(res), 0)

    def test_first_cards(self):
        res = Card.first_cards(10)
        self.assertEqual(len(res), 1)
        self.assertTrue(isinstance(res[0], Card))
        res = Card.first_cards(10, to_list=True)
        self.assertTrue(isinstance(res[0], dict))

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
        res, msgs = Card.get_from_id_list(cards_id)
        self.assertTrue(res)
        self.assertEqual(res[0].title, self.fixture_title)

    def test_get_from_id_list_non_existent(self):
        log.setLevel(logging.WARNING)
        cards_id = [1, 2]
        res, msgs = Card.get_from_id_list(cards_id)
        self.assertTrue(res)
        self.assertTrue(msgs)
        self.assertEqual(msgs[0]["message"], "The card of id 2 doesn't exist.")

    def test_placecopies(self):
        pass


class TestDistributor(TestCase):

    def setUp(self):
        self.dist = DistributorFactory()
        self.to_command = BasketFactory()

    def tearDown(self):
        pass

    def test_set_distributor(self):
        basket = BasketFactory()
        # Put cards in basket.
        for _ in range(3):
            basket.add_copy(CardFactory())

        basket.distributor = DistributorFactory()
        basket.save()
        # Set the distributor of these cards.
        self.dist.set_distributor(basket.copies.all())

        self.assertEqual(basket.copies.last().distributor, self.dist)


class TestPublisher(TestCase):
    """Testing the addition of a publisher to a card.
    """

    def setUp(self):
        # create a Card
        self.autobio = Card(title="Living my Life", isbn="987")
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
        self.autobio = Card(title="Living my Life", isbn="987")
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


class TestPlace(TestCase):

    def setUp(self):
        self.place = PlaceFactory.create()
        self.card = CardFactory.create()

    def tearDown(self):
        pass

    def test_nominal(self):
        self.assertTrue("place" in self.place.__unicode__())
        self.assertEqual('/en/databasesearch/place/1/', self.place.get_absolute_url())

    def test_add_copy(self):
        self.assertEqual(0, history.Entry.objects.count())
        # normal
        self.assertFalse(self.card.in_stock)
        self.place.add_copy(self.card)
        self.assertTrue(self.card.in_stock)
        self.assertEqual(1, self.place.placecopies_set.count())
        self.assertEqual(1, self.place.placecopies_set.first().nb)
        self.assertEqual(1, history.Entry.objects.count())
        # give the quantity.
        self.place.add_copy(self.card, nb=2)
        self.assertEqual(3, self.place.placecopies_set.first().nb)
        self.assertEqual(2, history.Entry.objects.count())
        # do not add, set the quantity.
        self.place.add_copy(self.card, nb=2, add=False)
        self.assertEqual(2, self.place.placecopies_set.first().nb)
        self.assertEqual(3, history.Entry.objects.count())


class TestPlaceCopies(TestCase):

    def setUp(self):
        # Create a relation Card - PlaceCopies - Place
        self.place = Place(name="here", is_stand=False, can_sell=True)
        self.place.save()
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
        self.basket = Basket(name="test basket")
        self.basket.save()
        self.basket_commands, created = Basket.objects.get_or_create(name="auto_command")
        self.basket_commands.save()
        self.card = Card(title="test card")
        self.card.save()
        self.nb_copies = 9

        # a Distributor
        self.distributor = DistributorFactory()
        self.distributor.save()

        # Preferences
        self.place = PlaceFactory.create()
        self.preferences = Preferences(default_place=self.place).save()

    def tearDown(self):
        log.setLevel(logging.DEBUG)

    def test_basket_add_copy(self):
        # add a card.
        self.basket.add_copy(self.card)  # it creates the intermediate table if not found.
        self.assertEqual(self.basket.basketcopies_set.get(card=self.card).nb, 1)
        # idem, with specific nb.
        self.basket.add_copy(self.card, nb=self.nb_copies)
        self.assertEqual(self.basket.basketcopies_set.get(card=self.card).nb, 1 + self.nb_copies)

    def test_basket_add_copies(self):
        self.basket.add_copies([1])
        qt = self.basket.quantity(card_id=1)
        self.assertEqual(qt, 1)
        self.assertEqual(1, self.basket.quantity())

    def test_sell_auto_command_add_to_basket(self):
        """When a card reaches the threshold (0), pertains to a deposit and
        the deposit's auto_command is set to True, then add this card to the
        appropriate basket.
        """
        Card.sell(id=self.card.id)
        # fix: create the initial basket
        # self.assertEqual(self.basket_commands.basketcopies_set.get(card=self.card).nb, 1)

    def test_to_deposit_card_no_dist(self):
        """Transform a basket to a deposit. The given card has no distributor,
        so will inherit the deposit one.
        """
        # add a card
        # self.card.distributor = self.distributor; self.card.save()
        self.basket.add_copy(self.card)
        # add a Distributor
        dep, msgs = self.basket.to_deposit(self.distributor, name="depo test")
        self.assertFalse(msgs)

    def test_to_deposit_different_dist(self):
        """The card has a different distributor: reject. !deprecated!
        """
        log.setLevel(logging.CRITICAL)
        # Another dist:
        dist2 = DistributorFactory()
        # add a card
        self.card.distributor = dist2
        self.card.save()
        self.basket.add_copy(self.card)
        # add a Distributor
        dep, msgs = self.basket.to_deposit(self.distributor, name="depo test")
        # deprecation warning: deposits rewrite: we don't reject this anymore.
        # self.assertTrue('Error' in msgs[0]['message'])

    def test_to_deposit_nominal(self):
        """
        """
        # add a card
        self.card.distributor = self.distributor
        self.card.save()
        self.basket.add_copy(self.card)
        # add a Distributor
        dep, msgs = self.basket.to_deposit(self.distributor, name="depo test")
        self.assertFalse(msgs)


class TestDeposits(TransactionTestCase):
    # Run those in a TransactionTestCase, or we get pb with an atomic block, only during testing.

    def setUp(self):
        # a distributor
        self.distributor = DistributorFactory()
        self.distributor.save()
        self.goldman = Author(name="goldman")
        self.goldman.save()
        # two cards, one with the distributor
        self.card = CardFactory()
        self.card.authors.add(self.goldman)
        self.card2 = CardFactory(distributor=self.distributor)
        self.card2.authors.add(self.goldman)
        # a deposit with the distributor
        self.deposit = DepositFactory(distributor=self.distributor)
        self.place = PlaceFactory()
        self.place.add_copy(self.card2)
        self.sell = SellsFactory()
        # self.sell.sell_cards(None, cards=[self.card2])

        # a needed place:
        self.place_name = "test place"
        self.place = Place(name=self.place_name, is_stand=False, can_sell=True)
        self.place.save()
        # Preferences
        self.preferences = Preferences.objects.create(default_place=self.place)
        self.preferences.save()

    def tearDown(self):
        log.setLevel(logging.DEBUG)

    def test_create(self):
        dist = Deposit.objects.create(name="new dist", distributor=self.distributor)
        self.assertTrue(dist.depositstate_set.count())
        self.assertFalse(dist.depositstate.closed)

    def test_from_dict(self):
        depo_dict = {
            'name': "depo test",
            "distributor": self.distributor,
            "copies": [self.card2],  # same distributor as the deposit.
            "quantities": ['1', '1'],
            "deposit_type": "fix",
            "minimal_nb_copies": "1",
            "auto_command": "",
            "due_date": "undefined",
            "dest_place": "",
        }
        depo, msgs = Deposit.from_dict(depo_dict)
        self.assertEqual(msgs.status, 'success')
        self.assertTrue('successfully created' in msgs.msgs[0]['message'])

        # We must have one depositstate closed: our initial one.
        self.assertEqual(2, depo.depositstate_set.count())
        self.assertTrue(depo.depositstate_set.first().closed)
        # as usual:
        self.assertFalse(depo.depositstate_set.last().closed)

        depo_dict = {
            'name': "depo test",  # same name
            "distributor": self.distributor,
            "copies": [self.card2],
            "quantities": ['1', '1'],
            "deposit_type": "fix",
            "minimal_nb_copies": "1",
            "auto_command": "",
            "due_date": "undefined",
            "dest_place": "",
        }
        depo, msgs = Deposit.from_dict(depo_dict)
        self.assertEqual(msgs.status, 'danger')
        self.assertTrue("that name already exists" in msgs.msgs[0]['message'])

        depo_dict = {
            'name': "depo test 2",
            "distributor": self.distributor,
            "copies": [self.card, self.card2],  # another card without a distributor.
            "quantities": ['1', '1'],
            "deposit_type": "fix",
            "minimal_nb_copies": "1",
            "auto_command": "",
            "due_date": "undefined",
            "dest_place": "",
        }
        depo, msgs = Deposit.from_dict(depo_dict)
        self.assertEqual(msgs.status, 'warning')
        self.assertTrue("should be all of the same supplier" in msgs.msgs[0]['message'])

    def test_distributors_match(self):
        self.assertFalse(distributors_match([self.card, self.card2]))
        self.card.distributor = self.distributor
        self.card.save()
        self.assertTrue(distributors_match([self.card, self.card2]))

    def test_ensure_open_depostate(self):
        depo = Deposit.objects.create(name="depo foo")
        self.assertEqual(1, depo.depositstate_set.count())
        checkout = depo.ensure_open_depostate()
        self.assertEqual(1, depo.depositstate_set.count())
        checkout.close()
        checkout.save()
        self.assertTrue(checkout.closed)
        checkout = depo.ensure_open_depostate()
        self.assertFalse(depo.depositstate_set.last().closed)
        self.assertEqual(2, depo.depositstate_set.count())
        depo.ensure_open_depostate()
        self.assertEqual(2, depo.depositstate_set.count())

    def test_add_copies(self):
        # add copies with the same distributor.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copy(self.card, nb=3)
        self.assertTrue(status)
        self.assertEqual(msgs, [])
        self.assertEqual(3, self.deposit.quantity_of(self.card))
        status, msgs = self.deposit.add_copy(self.card)
        self.assertEqual(4, self.deposit.quantity_of(self.card))

        # Can not add copies with a different dist each.
        self.card.distributor = None
        self.card.save()
        status, msgs = self.deposit.add_copies([self.card, self.card2])
        self.assertFalse(status)

        # we can find the deposits from the card
        # (although there is not a direct relationship (anymore)).
        dep_tups = self.card.deposits
        self.assertTrue(dep_tups)
        self.assertEqual(1, len(dep_tups))
        self.assertTrue('deposit test ' in dep_tups[0][0])

        dep_tups = self.card2.deposits
        self.assertEqual(0, len(dep_tups))

    def test_checkout_create(self):
        # add copies.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copies([self.card, self.card2], nb=2)
        old_co = self.deposit.ongoing_depostate
        # Create a checkout/deposit state = remember the current state at a point in time.
        co, msgs = self.deposit.checkout_create()
        # The current quantities of the old should be reported to the initial and current ones.
        old_dscopies = old_co.depositstatecopies_set.all()
        co_dscopies = co.depositstatecopies_set.all()
        for i, it in enumerate(old_dscopies):
            self.assertEqual(it.nb_current, co_dscopies[i].nb_current)
            self.assertEqual(it.nb_current, co_dscopies[i].nb_initial)

    def test_sell_card(self):
        # add copies.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copies([self.card, self.card2], nb=2)
        # sell from the deposit.
        # Since we don't give a sell object, don't output warnings.
        log.setLevel(logging.CRITICAL)
        self.deposit.sell_card(self.card)
        co = self.deposit.ongoing_depostate
        self.assertEqual(1, self.deposit.quantity_of(self.card))
        self.assertEqual(2, self.deposit.quantity_of(self.card2))
        # sell again.
        self.deposit.sell_card(self.card, nb=2)
        self.assertEqual(-1, self.deposit.quantity_of(self.card))

        # Sell from the Sell class.
        log.setLevel(logging.DEBUG)
        sellobj, status, msgs = Sell.sell_card(self.card, deposit=self.deposit)
        self.assertTrue(sellobj)
        self.assertEqual(-2, self.deposit.quantity_of(self.card))
        dscopy = co.depositstatecopies_set.first()
        self.assertEqual(1, dscopy.nb_sells)

    def test_sell_undo(self):
        # add copies.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copies([self.card, self.card2], nb=2)
        # sell
        sellobj, status, msgs = Sell.sell_card(self.card, deposit=self.deposit)
        self.assertTrue(sellobj)
        self.assertEqual(1, self.deposit.quantity_of(self.card))

        # undo the sell.
        status, msgs = self.deposit.sell_undo(self.card)
        self.assertEqual(status, 'success')
        self.assertEqual(2, self.deposit.quantity_of(self.card))

    def test_various_numbers(self):
        price = self.card.price
        # add 1 card.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copy(self.card)

        self.assertFalse(self.deposit.last_checkout_date)
        self.assertEqual(price, self.deposit.total_init_price)
        self.assertEqual(price, self.deposit.total_current_cost)
        self.assertEqual(1, self.deposit.init_qty)
        self.assertEqual(1, self.deposit.checkout_nb_current)
        # below: we didn't create a first checkout, we can't have those numbers.
        self.assertEqual(0, self.deposit.checkout_nb_initial)
        self.assertEqual(0, self.deposit.checkout_nb_cards_sold)
        self.assertEqual(0, self.deposit.checkout_total_sells)
        self.assertEqual(0, self.deposit.checkout_total_to_pay)
        self.assertEqual(0, self.deposit.checkout_margin)

        # Add a 2nd card.
        status, msgs = self.deposit.add_copy(self.card2)

        self.assertEqual(2 * price, self.deposit.total_init_price)
        self.assertEqual(2 * price, self.deposit.total_current_cost)
        self.assertEqual(2 * 1, self.deposit.init_qty)
        self.assertEqual(2, self.deposit.checkout_nb_current)

        # Create a checkout.
        self.deposit.checkout_create()
        self.assertTrue(self.deposit.last_checkout_date)
        self.assertEqual(2 * price, self.deposit.total_init_price)
        self.assertEqual(2 * price, self.deposit.total_current_cost)
        self.assertEqual(2 * 1, self.deposit.init_qty)
        self.assertEqual(2, self.deposit.checkout_nb_current)
        self.assertEqual(2, self.deposit.checkout_nb_initial)
        self.assertEqual(0, self.deposit.checkout_nb_cards_sold)
        self.assertEqual(0, self.deposit.checkout_total_sells)
        self.assertEqual(0, self.deposit.checkout_total_to_pay)
        self.assertEqual(0, self.deposit.checkout_margin)
        # and add a 3rd card.
        status, msgs = self.deposit.add_copy(self.card2)
        self.assertEqual(2 * price, self.deposit.total_init_price)
        self.assertEqual(3 * price, self.deposit.total_current_cost)
        self.assertEqual(2 * 1, self.deposit.init_qty)
        self.assertEqual(3, self.deposit.checkout_nb_current)
        self.assertEqual(2, self.deposit.checkout_nb_initial)
        self.assertEqual(0, self.deposit.checkout_nb_cards_sold)
        self.assertEqual(0, self.deposit.checkout_total_sells)
        self.assertEqual(0, self.deposit.checkout_total_to_pay)
        self.assertEqual(0, self.deposit.checkout_margin)

        # Sell a card.
        sellobj, status, msgs = Sell.sell_card(self.card, deposit=self.deposit)
        self.assertEqual(2 * price, self.deposit.total_init_price)
        self.assertEqual(2 * price, self.deposit.total_current_cost)
        self.assertEqual(2, self.deposit.init_qty)
        self.assertEqual(2, self.deposit.checkout_nb_current)
        self.assertEqual(2, self.deposit.checkout_nb_initial)
        self.assertEqual(1, self.deposit.checkout_nb_cards_sold)
        self.assertEqual(price, self.deposit.checkout_total_sells)
        discount = self.deposit.distributor.discount
        to_pay = price * discount / 100
        self.assertEqual(to_pay, self.deposit.checkout_total_to_pay)
        self.assertEqual(price - to_pay, self.deposit.checkout_margin)

        # balance
        balance = self.deposit.checkout_balance()
        self.assertTrue(balance)

    def test_is_in_deposits(self):
        self.assertFalse(self.card.is_in_deposits())
        # Add a card.
        self.card.distributor = self.distributor
        status, msgs = self.deposit.add_copy(self.card)
        self.assertTrue(self.card.is_in_deposits())


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
        self.assertEqual(self.place.quantity_of(self.autobio), 1)
        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(self.place.quantity_of(self.autobio), 0)
        self.assertEqual(ALERT_SUCCESS, status)

        int_table = sell.soldcards_set.all()
        self.assertEqual(len(int_table), 2)
        # Check prices
        self.assertEqual(int_table[0].price_sold, p1)
        self.assertEqual(int_table[1].price_sold, p2)
        # Check quantities
        self.assertEqual(int_table[0].card.quantity, 0)
        self.assertEqual(int_table[1].card.quantity, -1)
        # Check quantities through Card.quantity
        self.assertEqual(self.autobio.quantity_compute(), 0)
        # Sell again:
        sell, status, msgs = Sell.sell_cards(to_sell)
        self.assertEqual(self.autobio.quantity_compute(), -1)
        self.assertEqual(self.place.quantity_of(self.autobio), -1)

        # Stats.
        stats = Stats.sells_month()
        self.assertEqual(2 * 3, stats['nb_cards_sold'])
        self.assertEqual(2 * 2, stats['nb_sells'])
        self.assertEqual(2 * 2, stats['best_sells'][0]['quantity'])
        self.assertEqual(2 * 1, stats['best_sells'][1]['quantity'])
        self.assertEqual(2 * p1 + 4 * p2, stats['revenue'])

    def test_sell_none(self):
        to_sell = []
        sell, status, msgs = Sell.sell_cards(to_sell, silence=True)
        self.assertEqual(ALERT_WARNING, status)

    def test_sell_no_price(self):
        # p1 = 7.7
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

        sell, status, msgs = Sell.sell_cards(to_sell, silence=True)
        self.assertEqual(ALERT_WARNING, status)
        int_table = sell.soldcards_set.all()
        self.assertTrue(len(int_table), 1)

    def test_sell_place_id(self):
        status, msgs = Card.sell(id=self.autobio.id, place_id=1)
        self.assertEqual(self.place.quantity_of(self.autobio), 0)

        # bad place_id
        status, msgs = Card.sell(id=self.autobio.id, place_id=9, silence=True)

    def test_sell_deposit(self):
        self.depo.add_copy(self.autobio)

        # Generic Sell.sell_card:
        sell, status, msgs = Sell.sell_cards(None, cards=[self.autobio], deposit_id=self.depo.id)
        self.assertEqual(0, self.depo.quantity_of(self.autobio))

        # deposit.sell
        status, msgs = self.depo.sell_card(card_id=self.autobio.id, sell=sell)
        self.assertEqual(status, ALERT_SUCCESS, msgs)
        self.assertEqual(-1, self.depo.quantity_of(self.autobio))

        # bad card id
        status, msgs = self.depo.sell_card(card_id=999, silence=True)
        self.assertEqual(status, ALERT_ERROR)

    def test_sell_deposit_isolated(self):
        """
        sell from a deposit, don't count it in the other one.
        """
        # See also TestSellSearch.
        # Another deposit.
        self.depo2 = Deposit(name="deposit test 2", distributor=self.dist)
        self.depo2.save()
        # Add the same card than in depo 1.
        self.depo.add_copies([self.autobio])
        self.depo2.add_copies([self.autobio])
        # Create a checkout (register their initial state).
        checkout, msgs = self.depo.checkout_create()
        co2, msgs = self.depo2.checkout_create()

        # Sell.
        p1 = 7.7
        # p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1}]
        # Sell for depo 1.
        Sell.sell_cards(to_sell, deposit_id=self.depo.id)

        self.assertEqual(1, checkout.nb_sells)
        self.assertEqual(0, co2.nb_sells)

    def test_sell_from_place(self):
        """
        Sell from a place, don't count it in the deposit,
        """
        self.depo.add_copies([self.autobio])
        # Sell.
        p1 = 7.7
        # p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1}]
        # Sell for the place.
        Sell.sell_cards(to_sell, place_id=self.place.id)

        # The deposit/ongoing deposit state doesn't see any sell.
        self.assertEqual(0, self.depo.checkout_nb_cards_sold)

    def test_alert_deposit(self):
        """Create an ambigous sell, check an Alert is created."""
        pass  # xxx

    def test_undo_card(self):
        """Undo a sell, test only the Card method.
        """
        # Sell a card
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        sell, status, msgs = Sell.sell_cards(to_sell)

        # undo from Card:
        status, msgs = self.autobio.sell_undo()
        self.assertEqual(self.autobio.quantity, 1)
        status, msgs = self.autobio.sell_undo()
        # self.assertTrue(msgs)

    def test_undo_from_place(self):
        """Undo a sell, put it back on the original place.
        """
        # Create a second place.
        self.secondplace = Place(name="second place", is_stand=False, can_sell=True)
        self.secondplace.save()
        self.secondplace.add_copy(self.autobio)

        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": 7.7,
                    },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": 9.9,
                    }]
        # Sell, set a place.
        sell, status, msgs = Sell.sell_cards(to_sell, place=self.secondplace)

        # undo the sell, put it back on the original place.
        self.assertEqual(self.secondplace.quantity_of(self.autobio), 0)
        sell.undo()
        # TODO: add place to Sell.to_list
        self.assertEqual(self.secondplace.quantity_of(self.autobio), 1)

    def test_undo_sell(self):
        """
        """
        # Sell a card
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        sell, status, msgs = Sell.sell_cards(to_sell)
        # complete undo from Sell:
        sell.undo()

        self.assertEqual(self.autobio.quantity_compute(), 1)
        self.assertEqual(self.autobio.quantity, 1)

    def test_undo_soldcard(self):
        """
        Undo only a soldcard, not a whole sell with many cards.
        """
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        sell, status, msgs = Sell.sell_cards(to_sell)

        # undo
        status, msgs = SoldCards.undo(2)
        self.assertEqual(True, status)
        self.assertEqual(SoldCards.objects.count(), 2)  # the soldcard object is still history.
        self.assertEqual(SoldCards.objects.first().card_id,
                         self.autobio.id)

    def test_undo_from_deposit(self):
        p1 = 7.7
        p2 = 9.9
        to_sell = [{"id": self.autobio.id,
                    "quantity": 1,
                    "price_sold": p1
                },
                   {"id": self.secondcard.id,
                    "quantity": 2,
                    "price_sold": p2}]
        # Add the two cards to the deposit.
        status, msgs = self.depo.add_copies([self.autobio, self.secondcard])
        self.assertEqual(self.depo.quantity_of(self.autobio), 1)
        self.assertEqual(self.depo.quantity_of(self.secondcard), 1)
        self.assertTrue(status != 'danger')
        # Sell cards.
        sell, status, msgs = Sell.sell_cards(to_sell, deposit=self.depo)
        self.assertTrue(status == 'success')
        self.assertEqual(self.depo.quantity_of(self.autobio), 0)
        self.assertEqual(self.depo.quantity_of(self.secondcard), -1)
        # Undo the sell. It knows it was from a deposit.
        sell.undo()
        self.assertEqual(self.depo.quantity_of(self.secondcard), 1)

    def test_sell_restocking(self):
        # Create one required Restocking intermediate record.
        restock = Restocking()
        restock.save()

        self.reserve = Place(name="reserve", can_sell=False)
        self.reserve.save()
        # We have 1 copy in the shelf, 1 copy in the reserve.
        self.reserve.add_copy(self.autobio, nb=1)

        # Sell 1.
        Sell.sell_card(self.autobio)
        # When the cards reach 0 in the selling place and they are
        # available in stock, we should see it in the restocking list.
        self.assertEqual(Restocking.nb_ongoing(), 1)
        self.assertEqual(restock.restockingcopies_set.first().quantity, 1)

        # Sell 2. Sell it again.
        # We don't have enough in stock to add 1 quantity in the restocking list.
        Sell.sell_card(self.autobio)
        # We had 2 sells, the remaining quantity to -1.
        # We'd like to move another one, but we don't have enough in stock.
        self.assertEqual(restock.restockingcopies_set.first().quantity, 1)
        self.assertEqual(self.autobio.quantity_compute(), 0)

        # Validate. Move the copies and create a movement.
        self.assertEqual(-1, self.place.quantity_of(self.autobio))
        self.assertEqual(1, self.reserve.quantity_of(self.autobio))
        restock.validate()
        self.assertEqual(0, self.place.quantity_of(self.autobio))
        self.assertEqual(0, self.reserve.quantity_of(self.autobio))


class TestSellSearch(TestCase):

    # fixtures = ['test_sell_search']

    def setUp(self):
        # create a Card
        self.autobio = CardFactory()
        # a second card:
        self.secondcard = CardFactory()
        self.secondcard.price = 20
        self.secondcard.save()
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # a needed place:
        self.place = PlaceFactory()
        self.place.add_copy(self.autobio, nb=1)
        self.place.add_copy(self.secondcard, nb=1)
        # a Distributor:
        self.dist = DistributorFactory()
        # Preferences
        self.preferences = Preferences.objects.create(default_place=self.place).save()

    def tearDown(self):
        log.setLevel(logging.INFO)

    def test_search_sells_distributor(self):
        # sell cards, only one of wanted distributor.
        self.autobio.distributor = self.dist
        self.autobio.save()
        Sell.sell_cards(None, cards=[self.autobio, self.secondcard])
        sells = Sell.search(distributor_id=self.dist.id)
        sells = sells['data']
        self.assertEqual(len(sells), 1)

        self.secondcard.distributor = self.dist
        self.secondcard.save()
        Sell.sell_card(self.secondcard)
        sells = Sell.search(distributor_id=self.dist.id, to_list=True)
        self.assertEqual(len(sells['data']), 3)

    def test_search_sells_card(self):
        Sell.sell_card(self.autobio)
        Sell.sell_card(self.secondcard)
        sells = Sell.search(card_id=self.autobio.id)
        self.assertEqual(len(sells['data']), 1)

        # Test order and sortby.
        now = timezone.now()
        res = Sell.search(date_max=now)
        res_sorted = Sell.search(date_max=now, sortorder=0)
        self.assertEqual(res['data'][0].card.id, res_sorted['data'][0].card.id)

        res_inversed = Sell.search(date_max=now, sortorder=1)
        self.assertEqual(res['data'][0].card.id, res_inversed['data'][1].card.id)

        res_price = Sell.search(date_max=now, sortby="price")
        self.assertTrue(res_price['data'][0].price_sold > res_price['data'][1].price_sold)
        res_price = Sell.search(date_max=now, sortby="price", sortorder=1)
        self.assertTrue(res_price['data'][0].price_sold < res_price['data'][1].price_sold)
        # for coverage...
        Sell.search(date_max=now, sortby="created", page_size="10")
        Sell.search(date_max=now, sortby="title", page_size=10, page=1)
        Sell.search(date_max=now, sortby="sell__id")
        Sell.search(date_max=now, count=True)
        log.setLevel(logging.CRITICAL)
        Sell.search(date_max=now, sortby="warning")

    def test_search_sells_dates(self):
        Sell.sell_card(self.autobio)
        Sell.sell_card(self.secondcard, date=timezone.now() - timezone.timedelta(days=30))
        sells = Sell.search(date_min=timezone.now() - timezone.timedelta(days=7))
        self.assertEqual(len(sells['data']), 1)

    def test_search_sells_deposit_id(self):
        # Create two deposits.
        self.deposit = DepositFactory()
        self.deposit2 = DepositFactory()
        self.deposit.add_copies([self.autobio])
        # Two sells, one for deposit 1 only.
        Sell.sell_card(self.autobio)
        Sell.sell_card(self.autobio, deposit_id=self.deposit.id)
        sells = Sell.search(deposit_id=self.deposit.id)
        self.assertEqual(sells['nb_sells'], 2)

        # deposit 2 sees only one sell.
        sells = Sell.search(deposit_id=self.deposit2.id)
        self.assertEqual(sells['nb_sells'], 1)


class TestHistory(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.sell = SellsFactory.create()
        Sell.sell_cards([{"id": "1", "price_sold": 1, "quantity": 1}])

    def tearDown(self):
        pass


class TestInventory(TestCase):

    def setUp(self):
        self.place = PlaceFactory()
        self.card = CardFactory()
        # The place has a card before the inventory. But after the
        # inventory is applied, the place has what was in it.
        self.place.add_copy(self.card)
        self.inv = InventoryFactory()
        self.inv.place = self.place
        self.inv.save()

    def test_inventory_state(self):
        self.inv.add_copy(self.card, nb=2)
        state = self.inv.state()
        self.assertEqual(state['total_missing'], 0)
        self.assertEqual(state['nb_copies'], 2)
        self.assertEqual(state['nb_cards'], 1)

    def test_add_copy(self):
        res = self.inv.add_copy(self.card, nb=2)
        self.assertTrue(res)
        ic = self.inv.inventorycopies_set.get(card_id=self.card.id)
        self.assertEqual(ic.quantity, 2)

    def test_add_pairs(self):
        pairs = []
        status, msgs = self.inv.add_pairs(pairs)
        pairs = [[1, 3]]
        status, msgs = self.inv.add_pairs(pairs)
        pairs = [[1, 1]]
        status, msgs = self.inv.add_pairs(pairs)
        # add_pairs *sets* the quantities
        state = self.inv.state()
        self.assertEqual(state['nb_copies'], 1)

    def test_diff(self):

        self.card2 = CardFactory()
        self.card3 = CardFactory()
        self.place.add_copy(self.card2)
        self.inv.add_copy(self.card2, nb=2)
        self.inv.add_copy(self.card3, nb=1)
        # the inventory...
        d_diff, objname, _, _ = self.inv.diff()
        # - ... has not the card 1
        self.assertEqual(d_diff[1]['stock'], 1)
        self.assertEqual(d_diff[1]['inv'], 0)
        self.assertEqual(d_diff[1]['diff'], 1)
        self.assertEqual(d_diff[1]['in_orig'], True)

        # - has card2 with +1 copy
        self.assertEqual(d_diff[2]['stock'], 1)
        self.assertEqual(d_diff[2]['inv'], 2)
        self.assertEqual(d_diff[2]['diff'], -1)

        # - has card3 that the place doesn't have
        self.assertEqual(d_diff[3]['diff'], 1)
        self.assertEqual(d_diff[3]['inv'], 1)
        self.assertEqual(d_diff[3]['in_orig'], False)
        self.assertEqual(d_diff[3]['in_inv'], True)

        # With to_dict:
        d_diff, objname, _, _ = self.inv.diff(to_dict=True)
        self.assertTrue(d_diff)

    def test_apply(self):
        # create a few cards, put some in the place and in our
        # inventory.
        self.card2 = CardFactory()
        self.card3 = CardFactory()
        self.place.add_copy(self.card2)
        ADD2 = 2
        ADD3 = 1
        res = self.inv.add_copy(self.card2, nb=ADD2)
        res = self.inv.add_copy(self.card3, nb=ADD3)
        # Apply the inventory
        res, msgs = self.inv.apply()
        self.assertTrue(res)
        qty_after = self.place.quantities_total()
        self.assertEqual(qty_after, ADD2 + ADD3)
        self.assertTrue(self.inv.applied)
        self.assertTrue(self.inv.closed)

        # Can't apply it twice
        res, msgs = self.inv.apply()
        self.assertFalse(res)

    def test_apply_place(self):
        self.card2 = CardFactory()
        self.card3 = CardFactory()
        ADD2 = 2
        ADD3 = 1
        # This inv is of anoter place
        self.place2 = PlaceFactory()
        self.inv.place = self.place2
        self.inv.save()
        self.inv.add_copy(self.card2, nb=ADD2)
        self.inv.add_copy(self.card3, nb=ADD3)

        self.inv.apply()

        self.assertEqual(self.place2.quantities_total(), ADD2 + ADD3)  # no +1 here, it was in self.place
        self.assertEqual(self.place2.quantity_of(self.card3), ADD3)

    def test_apply_basket(self):
        # This inv is about a basket.
        basket = BasketFactory()
        self.inv.basket = basket
        self.inv.save()

        # we add a copy that is also in the place. Its quantity should add.
        self.inv.add_copy(self.card, nb=1)
        qty_before = self.place.quantities_total()

        self.inv.apply()
        self.assertEqual(self.place.quantities_total(), qty_before + 1)
        self.assertEqual(self.place.quantity_of(self.card), 1 + 1)

class TestPreferences(TestCase):

    def setUp(self):
        self.preferences = PreferencesFactory()
        self.preferences.default_place = PlaceFactory()
        self.preferences.save()
        self.new_place = PlaceFactory()

    def tearDown(self):
        pass

    def test_set_preferences(self):
        status, msgs = Preferences.setprefs(default_place=self.new_place)
        self.assertEqual(status, ALERT_SUCCESS)

        prefs = Preferences.prefs()
        place = prefs.default_place

        self.assertEqual(place, self.new_place)

    def test_set_vat(self):
        vat = 2
        status, msgs = Preferences.setprefs(vat_book=vat)
        self.assertEqual(status, ALERT_SUCCESS)
        self.assertEqual(Preferences.prefs().vat_book, vat, msgs)

    def test_price_excl_tax(self):
        self.assertEqual(Preferences.price_excl_tax(10), 9.45)

class TestCommands(TestCase):

    def setUp(self):
        self.card = CardFactory()
        self.publisher = PublisherFactory()
        # A Command:
        self.com = Command(publisher=self.publisher)
        self.com.save()

        # A default place in Preferences (to import views).
        # self.preferences = PreferencesFactory()
        # self.preferences.default_place = PlaceFactory()
        # self.preferences.save()
        # self.new_place = PlaceFactory()

    def tearDown(self):
        pass

    def test_initial(self):
        com = Command(publisher=self.publisher)
        com.save()
        qty, msgs = com.add_copy(self.card)
        self.assertTrue(com)
        self.assertTrue(com.supplier_name)
        self.assertEqual(1, qty)
        self.assertFalse(com.bill_received)
        self.assertFalse(com.payment_sent)
        self.assertFalse(com.received)

    def test_nb_ongoing(self):
        self.assertTrue(Command.nb_ongoing())

    def test_inventory_command(self):
        self.com.get_inventory()

    def test_inventory_command_state(self):
        inv = self.com.get_inventory()
        inv.state()

    def test_inventory_command_update(self):
        inv = self.com.get_inventory()
        qty = inv.add_copy(self.card, nb=2)
        self.assertEqual(qty, 2)
        self.assertFalse(self.com.received)

    def test_inventory_command_remove(self):
        inv = self.com.get_inventory()
        qty = inv.add_copy(self.card, nb=2)  # noqa: F841
        status = inv.remove_card(self.card.id)
        self.assertTrue(status)
        self.assertEqual(0, inv.nb_copies())

    def test_inventory_command_add_pairs(self):
        # Same as abvoe
        pairs = []
        inv = self.com.get_inventory()
        status, msgs = inv.add_pairs(pairs)
        pairs = [(1, 3)]
        status, msgs = inv.add_pairs(pairs)
        pairs = [(1, 1)]
        status, msgs = inv.add_pairs(pairs)
        # add_pairs *sets* the quantities
        state = inv.state()
        self.assertEqual(state['nb_copies'], 1)
        # if that fails, that means we did not save the objects in db.
        self.assertTrue(InventoryCommand.objects.get(id=inv.id))
        ask_again_inv = InventoryCommand.objects.get(id=inv.id)
        ask_again_state = ask_again_inv.state()
        self.assertEqual(ask_again_state['nb_copies'], 1)

    def test_inventory_command_diff(self):
        inv = self.com.get_inventory()
        inv.diff()

class TestCommandsReceive(TestCase):

    def setUp(self):
        self.card = CardFactory()
        self.publisher = PublisherFactory()
        # A Command:
        self.com = Command(publisher=self.publisher)
        self.com.save()

        # add cards to the command
        self.com.add_copy(self.card)

        # add cards to the command's inventory
        self.inv = self.com.get_inventory()
        self.inv.add_copy(self.card)

        # A default place in Preferences (to apply the parcel somewhere).
        self.preferences = PreferencesFactory()
        self.preferences.default_place = PlaceFactory()
        self.preferences.save()
        self.new_place = PlaceFactory()
        self.inv.place = self.preferences.default_place
        self.inv.save()

        # A distributor.
        self.distributor = DistributorFactory()
        self.distributor.save()

        # A deposit.
        self.deposit = DepositFactory()
        self.deposit.save()
        self.deposit.distributor = self.distributor

    def tearDown(self):
        pass

    def test_inventory_command_state(self):
        # may be redundant with test of add_pairs
        state = self.inv.state()
        self.assertEqual(state['total_missing'], 0)
        self.assertEqual(state['nb_cards'], 1)

    def test_inventory_command_apply(self):
        self.assertEqual(self.preferences.default_place.quantity_of(self.card), 0)
        self.inv.apply()
        self.assertTrue(self.inv.applied)
        self.assertEqual(self.preferences.default_place.quantity_of(self.card), 1)

    def test_inventory_command_apply_to_deposit(self):
        """
        Make the inventory of a command, apply it to a deposit.
        """
        self.assertEqual(self.deposit.quantity_of(self.card), 0)
        self.inv.apply(deposit_obj=self.deposit)
        self.assertEqual(self.deposit.quantity_of(self.card), 1)


class TestStats(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.card2 = CardFactory.create()
        CardType.objects.create(name="book")
        CardType.objects.create(name="unknown")

    def test_stats(self):
        """Dummy "it compiles" tests."""
        # "Stats".
        Stats.stock()
        Stats.stock_age(1)
        Stats.entries_month()
        Stats.sells_month()
