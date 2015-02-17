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

from search.views import get_reverse_url

from django.core.urlresolvers import reverse
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
