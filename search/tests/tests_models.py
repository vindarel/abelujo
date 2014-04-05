#!/bin/env python
# -*- coding: utf-8 -*-

"""
Test the models.

Note: to compare two objects, don't use assertEqual but the == operator.
"""

from django.test import TestCase

from search.models import Card
from search.models import Author

class TestCards(TestCase):
    def setUp(self):
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        self.autobio = Card(title="Living my Life", ean="987")
        self.autobio.save()
        self.autobio.authors.add(self.goldman)


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
