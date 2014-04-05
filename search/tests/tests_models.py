#!/bin/env python
# -*- coding: utf-8 -*-

"""
Test the models.
"""

from django.test import TestCase

from search.models import Card

class TestCards(TestCase):
    def setUp(self):
        pass

    def test_add(self):
        print "--- good runner !"
        assert Card
