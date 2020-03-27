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

"""
Test the forms.
"""
from __future__ import unicode_literals

from search import forms as viewforms

from django.test import TestCase

class TestCards(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_card_manually(self):
        card_form = viewforms.CardCreateForm()
        self.assertEqual(22, len(card_form.fields))

        # The form's cleaned_data gives us a dict.
        # No new authors or publisher yet.
        card_dict = {
            'title': 'Card created manually',
            'has_isbn': 'yes',
            'isbn': '9782757837009',
            'price': '9.99',
            'currency': 'CHF',
            'threshold': '0',
            'authors': [],
            'new_authors': [],
            'publishers': [],
            'new_publisher_name': '',
            'year_published': '',
            'distributor': '',
            'new_distributor_name': '',
            'new_distributor_discount': '',
            'collection': '',
            'shelf': '',
            'new_shelf_name': '',
            'cover': '',
            'date_publication': '',
            'summary': '',
            'comment': '',
        }
        card, msgs = viewforms.CardCreateForm.create_card(card_dict)

        assert card
        self.assertEqual(card_dict['title'], card.title)
        self.assertEqual(card_dict['isbn'], card.isbn)
        self.assertEqual(float(card_dict['price']), card.price)

        # We have this card in DB.
        # Same form, but we update the card with new data:
        # - a new publisher,
        # - new authors,
        # - a new distributor.
        card_dict['new_distributor_name'] = 'new dist'
        card_dict['new_distributor_discount'] = '35'
        card_dict['new_publisher_name'] = 'new pub'
        card_dict['new_shelf_name'] = 'new shelf'
        card_dict['new_authors'] = """author one
        author two"""

        card, msgs = viewforms.CardCreateForm.create_card(card_dict)
        assert card
        self.assertTrue(card.authors.all(), "No custom authors created.")
        self.assertEqual(card.authors.first().name, "author one")
        self.assertEqual(card.shelf.name, "new shelf")
        self.assertEqual(card.distributor.name, "new dist")
        self.assertEqual(card.distributor.discount, '35')  # no number? Interesting.
        self.assertTrue(card.publishers.all())
        self.assertEqual(card.publishers.first().name, "new pub")
