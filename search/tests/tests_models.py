#!/bin/env python
# -*- coding: utf-8 -*-

"""
Test the models.

Note: to compare two objects, don't use assertEqual but the == operator.
"""

from django.test import TestCase

from search.models import Author
from search.models import Card
from search.models import CardType
from search.models import Publisher

class TestCards(TestCase):
    def setUp(self):
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.autobio = Card(title="Living my Life", ean="987")
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # create other card types
        self.type_book = "book"
        typ = CardType(name=self.type_book)
        typ.save()

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

    def test_sell(self):
        Card.sell(ean="987", quantity=2)
        self.assertEqual(Card.objects.get(ean="987").quantity, -1)

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
        self.publisher = Publisher(name="Agone")
        self.publisher.save()

    def test_publisher_existing(self):
        pub = "Agone"
        obj = Card.from_dict({"title": "living", "publisher": pub})
        self.assertEqual(pub.lower(), obj.publisher.name)

    def test_publisher_non_existing(self):
        pub = "Foo"
        obj = Card.from_dict({"title": "living", "publisher": pub})
        self.assertEqual(pub.lower(), obj.publisher.name)
        publishers = Publisher.objects.all()
        self.assertEqual(2, len(publishers))
        self.assertTrue(pub.lower() in [p.name for p in publishers])
