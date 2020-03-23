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
Test creating and selling coupons.
"""

from django.test import TransactionTestCase

from search.models import Coupon
from search.models import CouponGeneric
from search.tests import factories


class TestCoupons(TransactionTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_coupons(self):
        client = factories.ClientFactory()
        generic = CouponGeneric.objects.create(amount=15)
        coupon = Coupon.objects.create(generic=generic,
                                       client=client)
        assert coupon.generic
        self.assertEqual(coupon.generic.amount, 15)
