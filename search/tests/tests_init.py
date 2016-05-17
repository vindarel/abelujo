#! /usr/bin/python
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

"""
Testing redirects, templates used, the views, etc.

run with: "manage.py test search".

Do not call the real scrapers: use the mock library.

"""
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

search_on_data_source_fixture = (
    [{"title":'fixture'}], # results
    []  # stacktraces
)

class SimpleTest(TestCase):

    def setUp(self):
        self.c = Client()
        self.c.login(username="admin", password="admin")

    @mock.patch('search.views.search_on_data_source', return_value=search_on_data_source_fixture)
    def test_templates_used(self, mymock):

        response = self.c.get(reverse("card_search"), {u'q': u'emma goldman', 'source':'chapitre'})
        mymock.return_value = ['uie']
        mymock.assert_called_once_with("chapitre", [u'emma', u'goldman'])
        self.assertTemplateUsed(response, 'search/search_result.jade')

    def test_urls(self):
        res = self.c.get(reverse("card_index"), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "search/search_result.jade")
        res = self.c.get("/BAR?q=hello")
        self.assertEqual(res.status_code, 404)
        # Don't fire the query. We may want to setup cache.
        # res = self.c.get("/search?q=living+life&source=chapitre", follow=True)
        # self.assertEqual(res.status_code, 200)
