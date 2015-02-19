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

from django.contrib import messages
from django.test import TestCase

from search.models import Author
from search.models import Basket
from search.models import BasketCopies
from search.models import BasketType
from search.models import Card
from search.models import CardType
from search.models import Collection
from search.models import Deposit
from search.models import DepositCopies
from search.models import Distributor
from search.models import Place
from search.models import PlaceCopies
from search.models import Publisher
from search.models import Preferences


class TestCards(TestCase):
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
        self.fixture_ean = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title,
                            ean=self.fixture_ean,
                            card_type=typ)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # a needed place:
        self.place_name = "test place"
        self.place = Place(name=self.place_name, is_stand=False, can_sell=True)
        self.place.save()
        # mandatory: preferences table
        self.preferences = Preferences(default_place=self.place).save()

    def test_add(self):
        found = Card.objects.get(title__icontains="living")
        self.assertTrue(found.authors.all()[0] == self.goldman)
        self.assertEqual(found, self.autobio)

    def test_from_dict(self):
        TITLE = "Foo bar"
        ZINN = "zinn"
        to_add = Card.from_dict({"title":TITLE,
                                 "authors":[self.GOLDMAN, ZINN],
                                 "location":"here"})
        self.assertTrue(to_add)
        self.assertEqual(to_add.title, TITLE)
        self.assertEqual(len(Author.objects.all()), 2)
        names = [aut.name for aut in to_add.authors.all()]
        self.assertTrue(ZINN in names)
        self.assertTrue(self.GOLDMAN in names)
        # Check that the author was created
        self.assertTrue(Author.objects.get(name=ZINN))

    def test_from_dict_no_authors(self):
        TITLE = "I am a CD without authors"
        to_add = Card.from_dict({"title":TITLE})
        self.assertTrue(to_add)

    def test_increment_quantity(self):
        obj = Card.from_dict({"title": self.fixture_title,
                              "ean": self.fixture_ean,})
        self.assertEqual(1, obj.quantity)

        obj = Card.from_dict({"title": self.fixture_title,
                              "ean": self.fixture_ean,
                              "quantity": 2})
        self.assertEqual(3, obj.quantity)

        obj = Card.from_dict({"title": self.fixture_title,
                              "ean": self.fixture_ean,
                              # quantity: one by default
                          })
        self.assertEqual(4, obj.quantity)

    def test_quantity_new(self):
        obj = Card.from_dict({"title": "New quantity test",
                              "ean": "111",
                              "quantity": 2})
        self.assertEqual(2, obj.quantity)

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
        self.assertFalse(Card.search("", card_type_id=1))

    def test_search_key_words(self):
        res = Card.search(["liv", "gold"])
        self.assertEqual(1, len(res))

    def test_sell(self):
        Card.sell(id=self.autobio.id, quantity=2)
        self.assertEqual(Card.objects.get(id=self.autobio.id).quantity, -1)

    def test_add_good_type(self):
        obj = Card.from_dict({"title": "living",
                              "card_type": self.type_book})
        self.assertEqual(self.type_book, obj.card_type.name)

    def test_add_bad_type(self):
        badtype = "badtype"
        obj = Card.from_dict({"title": "living",
                              "card_type": badtype})
        self.assertEqual(obj.title, "living")
        self.assertEqual(obj.card_type.name, "unknown")

    def test_type_unknown(self):
        obj = Card.from_dict({"title": "living",
                              "card_type": None})
        self.assertEqual(obj.card_type.name, "unknown")

        obj = Card.from_dict({"title": "living"})
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
        obj = Card.from_dict({"title": "living", "publishers": [pub]})
        all_pubs = obj.publishers.all()
        self.assertEqual(1, len(all_pubs))
        self.assertEqual(pub.lower(), all_pubs[0].name)

    def test_many_publishers(self):
        pub = ["agone", "maspero"]
        obj = Card.from_dict({"title": "living", "publishers": pub})
        all_pubs = obj.publishers.all()
        self.assertEqual(len(pub), len(all_pubs))
        self.assertEqual(pub[0].lower(), all_pubs[0].name)

    def test_publisher_non_existing(self):
        pub = "Foo"
        obj = Card.from_dict({"title": "living", "publishers": [pub]})
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
        obj = Card.from_dict({"title": "living", "collection": self.collection_name})
        self.assertEqual(self.collection_name.lower(), obj.collection.name)

    def test_collection_non_existing(self):
        collection = "new collection"
        obj = Card.from_dict({"title": "living", "collection": collection})
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
        self.place.add_copies(self.card)
        new_nb = self.place.placecopies_set.get(card=self.card).nb
        self.assertEqual(self.nb_copies + 1, new_nb)
        self.place.add_copies(self.card, 10)
        new_nb = self.place.placecopies_set.get(card=self.card).nb
        self.assertEqual(self.nb_copies + 1 + 10, new_nb)

    def test_card_to_default_place(self):
        Place.card_to_default_place(self.card, nb=3)


class TestBaskets(TestCase):

    def setUp(self):
        # Create a Card and a Basket.
        self.basket = Basket(name="test basket"); self.basket.save()
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


class TestDeposits(TestCase):

    def setUp(self):
        self.distributor = Distributor(name="my dist")
        self.distributor.save()
        self.goldman = Author(name="goldman")
        self.goldman.save()
        self.card = Card(title="test card"); self.card.save()
        self.card.authors.add(self.goldman)
        self.card2 = Card(title="test card2"); self.card2.save()
        self.card2.authors.add(self.goldman)
        self.deposit = Deposit(name="deposit nominal",
                               distributor=self.distributor,)

    def test_nominal(self):
        self.card.distributor = self.distributor
        msgs = self.deposit.add_copies([self.card,])
        self.assertEqual(1, len(self.deposit.depositcopies_set.all()))

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
