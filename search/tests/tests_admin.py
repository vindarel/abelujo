#!/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

from django.test import TestCase
from django.test.client import Client

class TestAdmin(TestCase):
    """Test the login to the admin app is ok.
    """

    def setUp(self):
        self.c = Client()

    def tearDown(self):
        pass

    def test_admin(self):
        resp = self.c.get("/admin/login/",
                           follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.c.post("/admin/login/",
                           {"username": "admin", "password": "admin"},
                           follow=True)
        self.assertEqual(resp.status_code, 200)
