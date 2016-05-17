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
from search.models import Entry

from search.views import get_reverse_url

from tests_models import CardFactory

class TestEntry(TestCase):

    def setUp(self):
        self.card = CardFactory()

    def test_entry(self):
        en, created = Entry.new([self.card])
        self.assertTrue(created)
