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
Test the user models.
"""

import datetime

from django.test import TestCase

from search.models import Bill

from tests_models import CardFactory
from tests_models import DistributorFactory

class TestBill(TestCase):

    def setUp(self):
        self.bill = Bill(ref="987",
                         distributor=DistributorFactory.create(),
                         name="bill test",
                         due_date=datetime.date.today(),
                         total=100,
                    )
        self.bill.save()

    def tearDown(self):
        pass

    def test_create(self):
        bill = Bill(ref="987",
                    name="test bill",
                    distributor=DistributorFactory.create(),
                    due_date=datetime.date.today(),
                    total=100,
                    )
        self.assertTrue(bill)

    def test_add_copy(self):
        created = self.bill.add_copy(CardFactory.create(), nb=2)
        self.assertTrue(created)
        self.assertEqual(self.bill.billcopies_set.first().quantity, 2)
