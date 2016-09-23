#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2016 The Abelujo Developers
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
from django.contrib import messages
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.utils.six import StringIO
from factory.django import DjangoModelFactory

from search.models import ALERT_ERROR
from search.models import ALERT_SUCCESS
from search.models import ALERT_WARNING
from search.models import Alert
from search.models import Author
from search.models import Basket
from search.models import BasketCopies
from search.models import BasketType
from search.models import Card
from search.models import CardType
from search.models import Collection
from search.models import Deposit
from search.models import DepositCopies
from search.models import DepositState
from search.models import Distributor
from search.models import Inventory
from search.models import Place
from search.models import PlaceCopies
from search.models import Preferences
from search.models import Publisher
from search.models import Sell
from search.models import Shelf
from search.models import getHistory


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

class CardFactory(DjangoModelFactory):
    class Meta:
        model = Card

    title = factory.Sequence(lambda n: u'card title é and ñ %d' % n)
    isbn = factory.Sequence(lambda n: "%d" %n)
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
        exists = Card.exists({'isbn': self.fixture_isbn})
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
        # only the same title. Should exist.
        no_pubs_no_authors, msgs = Card.exists({"title": self.fixture_title,})
        self.assertTrue(no_pubs_no_authors)
        self.assertEqual(len(no_pubs_no_authors), 2)

        # TODO: and collection

    def test_from_dict_no_authors(self):
        TITLE = "I am a CD without authors"
        to_add, msgs = Card.from_dict({"title":TITLE})
        self.assertTrue(to_add)

    def test_update(self):
        #TODO: test that we update fields of the card when we use
        #from_dict but the card alreay exists.
        pass

    # def test_quantity_new(self):
    # TODO: put in test_move
    #     obj, msgs = Card.from_dict({"title": "New quantity test",
    #                           "isbn": "111",
    #                           "quantity": 2})
    #     self.assertEqual(2, obj.quantity)

    def test_search(self):
        # Should search with way more cards.
        res, msgs = Card.search(["gold"], card_type_id=1)
        self.assertEqual(1, len(res))

    def test_search_notype(self):
        res, msgs = Card.search(["gold"], card_type_id=999)
        self.assertFalse(res)

    def test_search_alltypes(self):
        res, msgs = Card.search(["gold"], card_type_id=0)
        self.assertTrue(res)

    def test_search_only_type(self):
        # Doesn't pass data validation.
        self.assertTrue(Card.search("", card_type_id=1))

    def test_search_key_words(self):
        res, msgs = Card.search(["liv", "gold"])
        self.assertEqual(1, len(res))

    def test_search_card_isbn(self):
        res, msgs = Card.search([ISBN])
        self.assertEqual(len(res), 1)

    def test_search_shelf(self):
        res, msgs = Card.search(["gold"], shelf_id=1)
        self.assertEqual(len(res), 1)
        # Shelf doesn't exist:
        res, msgs = Card.search(["gold"], shelf_id=2)
        self.assertEqual(len(res), 0)

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
        cards_id = [1,2]
        res, msgs = Card.get_from_id_list(cards_id)
        self.assertTrue(res)
        self.assertTrue(msgs)
        self.assertEqual(msgs[0]["message"], "the card of id 2 doesn't exist.")

    def test_quantity_to_zero(self):
        self.card2 = Card(title=self.fixture_title,
                          isbn=self.fixture_isbn,
                          shelf=ShelfFactory())
        self.card2.save()
        author = AuthorFactory()
        self.card2.authors.add(author)
        self.card2.save()
        self.place.add_copy(self.card2, nb=3)

        Card.quantities_to_zero()
        self.assertEqual(self.autobio.quantity_compute(), 0)
        self.assertEqual(Card.quantities_total(), 0)

    def test_command_reset_quantities(self):
        """Test our custom management command.
        """
        out = StringIO()
        call_command("my_reset_quantities", stdout=out)
        self.assertIn("All done !", out.getvalue())

        self.assertEqual(Card.quantities_total(), 0)

    def test_placecopies(self):
        pass

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

        # a Distributor
        self.distributor = DistributorFactory(); self.distributor.save()

    def tearDown(self):
        pass

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
        """The card has a different distributor: reject.
        """
        # Another dist:
        dist2 = DistributorFactory()
        # add a card
        self.card.distributor = dist2; self.card.save()
        self.basket.add_copy(self.card)
        # add a Distributor
        dep, msgs = self.basket.to_deposit(self.distributor, name="depo test")
        self.assertTrue(msgs)

    def test_to_deposit_nominal(self):
        """
        """
        # add a card
        self.card.distributor = self.distributor; self.card.save()
        self.basket.add_copy(self.card)
        # add a Distributor
        dep, msgs = self.basket.to_deposit(self.distributor, name="depo test")
        self.assertFalse(msgs)

class TestDeposits(TestCase):

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

    def test_nominal(self):
        self.card.distributor = self.distributor
        msgs = self.deposit.add_copies([self.card,], quantities=[3])
        self.assertEqual(1, len(self.deposit.depositcopies_set.all()))
        self.assertEqual(3, self.card.quantity_deposits())
        self.deposit.add_copies([self.card])
        balance = self.deposit.checkout_balance()
        # Bad length of 'quantities', will add 1 by default.
        self.deposit.add_copies([self.card], quantities=[10,11,12])
        balance = self.deposit.checkout_balance()
        self.assertEqual(5, balance['cards'][0][1].nb_current)

    def test_one_depo_per_card(self):
        self.card.distributor = self.distributor
        msgs = self.deposit.add_copies([self.card,])
        status, msgs = Deposit.from_dict({'name': 'new',
                                           'copies': [self.card],
                                           'distributor': self.distributor})
        self.assertEqual(status, ALERT_ERROR)

    def test_no_distributor(self):
        """card with no dist will inherit it.
        """
        self.card.distributor = None
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(len(msgs), 0)
        self.assertEqual(1, len(self.deposit.depositcopies_set.all()))

    def test_different_distributor(self):
        self.other_dist = DistributorFactory()
        self.card.distributor = self.other_dist
        self.card.save()
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(0, len(self.deposit.depositcopies_set.all()))

    def test_from_dict_nominal(self):
        self.card.distributor = self.distributor
        status, msgs = Deposit.from_dict({'name': 'test',
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
        status, msgs = Deposit.from_dict({'name': 'test',
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
        status, msgs = Deposit.from_dict({'name': 'test',
                                  'due_date': None,
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  'dest_place': dest_place.id,
                                  'deposit_type': "publisher",
                                  })
        self.assertEqual(msgs[0]['level'], "success")


    def test_from_dict_bad_deposit(self):
        self.card.distributor = None
        status, msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card,],
                                  'distributor': self.distributor,
                                  })
        self.assertEqual(len(msgs), 2, "add deposit from dict: %s" % msgs)
        self.assertEqual(msgs[0]['level'], messages.WARNING)

    def test_from_dict_bad_deposit_one_good(self):
        self.card.distributor = None
        self.card2.distributor = self.distributor
        status, msgs = Deposit.from_dict({'name': 'test',
                                  'copies': [self.card, self.card2],
                                  'distributor': self.distributor,
                                  })
        self.assertEqual(len(msgs), 2, "add deposit from dict: %s" % msgs)
        self.assertEqual(msgs[0]['level'], messages.WARNING)

    def test_close_deposit(self):
        # Add cards
        self.deposit.add_copies([self.card2], quantities=[3])
        co, msgs = self.deposit.checkout_create()
        self.assertFalse(co.closed)
        # Manipulate the objects
        co.closed = timezone.now()
        co.save()
        self.assertTrue(co.closed)
        self.deposit.checkout_close()
        co = self.deposit.last_checkout()
        self.assertTrue(co.closed) # fails only with date time field.

    def test_sell_update(self):
        """Test we update correctly the nb of sells and nb current after when
        we have a sell and we close the deposit state.

        """
        # Add cards to it.
        self.deposit.add_copies([self.card2], quantities=[3])
        bal = self.deposit.checkout_balance()
        self.assertEqual(0, bal["cards"][0][1].nb_sells)
        self.assertEqual(3, bal["cards"][0][1].nb_initial)
        self.assertEqual(3, bal["cards"][0][1].nb_current)

        # Sell a copy.
        self.sell.sell_cards(None, cards=[self.card2])

        # Update the deposit state
        co = self.deposit.last_checkout()
        co.update()
        bal = self.deposit.checkout_balance()
        self.assertEqual(1, bal["cards"][0][1].nb_sells)
        self.assertEqual(3, bal["cards"][0][1].nb_initial)
        self.assertEqual(2, bal["cards"][0][1].nb_current)

        # Close it and check again. We must not see a sell.
        self.deposit.checkout_close()
        co = self.deposit.last_checkout()
        co.update()
        bal = self.deposit.checkout_balance()
        self.assertEqual(0, bal["cards"][0][1].nb_sells)
        self.assertEqual(2, bal["cards"][0][1].nb_initial)
        self.assertEqual(2, bal["cards"][0][1].nb_current)

    def test_depostate_first(self):
        # Add cards to the deposit.
        self.deposit.add_copies([self.card2], quantities=[3])
        ret, msgs = self.deposit.checkout_create()
        # We didn't sell anything yet but still should see the balance.
        bal = self.deposit.checkout_balance()
        self.assertEqual(0, bal["cards"][0][1].nb_sells)
        self.assertEqual(3, bal["cards"][0][1].nb_initial)
        self.assertEqual(3, bal["cards"][0][1].nb_current)

        # Sell a copy.
        self.sell.sell_cards(None, cards=[self.card2])

        # Check figures: how many copies we sold, how many we have
        co = self.deposit.last_checkout()
        co = co.update()
        balance = co.balance()
        self.assertEqual(balance["cards"][0][1].nb_current, 2)
        self.assertEqual(balance["cards"][0][1].nb_initial, 3)
        self.assertEqual(balance["cards"][0][1].nb_sells, 1)

        # Close and check again.
        closed, msgs = self.deposit.checkout_close()
        co = self.deposit.last_checkout()
        self.assertTrue(co.closed)
        co, _ = self.deposit.checkout_create()
        ret, msgs = co.add_soldcards([{'card': self.card2, 'sells': []}])
        self.assertFalse(msgs)
        self.assertTrue(ret)

        balance = self.deposit.checkout_balance() # creates a new checkout
        # We started a new deposit state: the old "current" is the new "initial".
        self.assertEqual(balance["cards"][0][1].nb_current, 2)
        self.assertEqual(balance["cards"][0][1].nb_initial, 2)
        self.assertEqual(balance["cards"][0][1].nb_sells, 0)
        # test again, that we're not in a loop
        balance = self.deposit.checkout_balance()
        self.assertEqual(balance["cards"][0][1].nb_current, 2)
        self.assertEqual(balance["cards"][0][1].nb_initial, 2)
        self.assertEqual(balance["cards"][0][1].nb_sells, 0)

    def test_depostate_dates(self):
        """Don't count sells anterior from the creation of the deposit.
        """
        Sell.sell_cards(None, cards=[self.card2])
        depo = DepositFactory(distributor=self.distributor)
        depo.add_copies([self.card2])
        co, msgs = depo.checkout_create()
        balance = co.balance()
        self.assertEqual(1, balance["cards"][0][1].nb_current)
        self.assertEqual(0, balance["cards"][0][1].nb_sells)

    def test_next_due_dates(self):
        """Get which deposits we have to pay soon.
        """
        next = Deposit.next_due_dates(to_list=True)
        self.assertEqual(next[0]['id'], self.deposit.id)
        self.assertEqual(next[0]['due_date'], self.deposit.due_date.isoformat())

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
        self.assertEqual(ALERT_SUCCESS, status)

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
        self.assertEqual(ALERT_WARNING, status)

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
        self.assertEqual(ALERT_WARNING, status)
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
        self.assertEqual(self.autobio.quantity_compute(), 1)
        self.assertEqual(self.autobio.quantity, 1) # to fix
        status, msgs = self.autobio.sell_undo()
        self.assertTrue(msgs)

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

class TestHistory(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.sell = SellsFactory.create()
        Sell.sell_cards([{"id":"1", "price_sold":1, "quantity": 1}])

    def tearDown(self):
        pass

    def test_history(self):
        hist, status, alerts = getHistory()
        self.assertEqual(2, len(hist)) # a Sell is created without any cards sold.
        self.assertEqual(ALERT_SUCCESS, status)

class TestAlerts(TestCase):

    def setUp(self):
        # a card in a deposit, with the same distributor each.
        self.dist = DistributorFactory.create()
        self.card = CardFactory.create()
        self.card.distributor = self.dist
        self.deposit = DepositFactory.create()
        self.deposit.distributor = self.dist
        self.deposit.add_copies([self.card])
        # Put the Card in a default place, in 2 copies: one is the deposit,
        # one is ours.
        self.place = PlaceFactory.create()
        self.place.add_copy(self.card, nb=2)
        # A sell creates an alert
        Sell.sell_card(self.card)
        self.alerts, status, msgs = Alert.get_alerts()

    def test_get_alerts_nominal(self):
        self.assertTrue(self.alerts)
        self.assertTrue(self.alerts[0].card.ambiguous_sell())

    def test_add_deposits_of_card(self):
        self.alerts[0].add_deposits_of_card(self.card)
        self.assertEqual(1, len(self.card.deposit_set.all()))

    def test_alerts_auto_resolved(self):
        """An alert can be resolved if we sell the remaining copies of the card.
        """
        # If we sell the 2nd copy, they're all sold, so the alert is resolved.
        Sell.sell_card(self.card)
        alerts, status, msgs = Alert.get_alerts()
        alert = alerts[0]
        self.assertEqual(alert.card.quantity, 0)
        self.assertFalse(alert.card.ambiguous_sell())

class TestInventory(TestCase):

    def setUp(self):
        self.place = PlaceFactory()
        self.card = CardFactory()
        self.place.add_copy(self.card)
        self.inv = InventoryFactory()
        self.inv.place = self.place

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
        res = self.inv.add_copy(self.card2, nb=2)
        res = self.inv.add_copy(self.card3, nb=1)
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
        ADD2= 2
        ADD3 = 1
        res = self.inv.add_copy(self.card2, nb=ADD2)
        res = self.inv.add_copy(self.card3, nb=ADD3)
        # Apply the inventory
        res, msgs = self.inv.apply()
        self.assertTrue(res)
        qty_after = self.place.quantities_total()
        self.assertEqual(qty_after, 1 + ADD2 + ADD3) # 1 is from setUp()
        self.assertTrue(self.inv.applied)
        self.assertTrue(self.inv.closed)

        # Can't apply it twice
        res, msgs = self.inv.apply()
        self.assertFalse(res)

    def test_apply_place(self):
        self.card2 = CardFactory()
        self.card3 = CardFactory()
        ADD2= 2
        ADD3 = 1
        # This inv is of anoter place
        self.place2 = PlaceFactory()
        self.inv.place = self.place2
        self.inv.save()
        self.inv.add_copy(self.card2, nb=ADD2)
        self.inv.add_copy(self.card3, nb=ADD3)

        self.inv.apply()

        self.assertEqual(self.place2.quantities_total(), ADD2+ ADD3) # no +1 here, it was in self.place
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
        msgs, status = Preferences.setprefs(default_place=self.new_place)
        self.assertEqual(status, ALERT_SUCCESS, "%s" % msgs)

        prefs = Preferences.prefs()
        place = prefs.default_place

        self.assertEqual(place, self.new_place)
