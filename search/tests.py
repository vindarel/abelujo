#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Testing redirects, templates used, the views, etc.

run with: "manage.py test search".

Do not call the real scrapers: use the mock library.

"""

import mock

from django.test import TestCase
from django.test.client import Client


class SimpleTest(TestCase):
    fixture = [{"title":'fixture'}]

    def setUp(self):
        self.c = Client()

    def test_root_redirection(self):
        res = self.c.get("/", follow=True)
        self.assertRedirects(res, "/search/", status_code=301) # permanent redirection

    @mock.patch('search.views.search_on_data_source', return_value=fixture)
    def test_templates_used(self, mymock):

        response = self.c.get("/search", {u'q': u'emma goldman', 'source':'chapitre'})
        mymock.return_value = ['uie']
        mymock.assert_called_once_with("chapitre", [u'emma', u'goldman'])
        self.assertTemplateUsed(response, 'search/search_result.jade')

    def test_urls(self):
        res = self.c.get("/search", follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "search/search_result.jade")
        res = self.c.get("/BAR?title=hello")
        self.assertEqual(res.status_code, 404)

class TestViews(TestCase):
    pass # test views with RequestFactory

# test that text appears in the response: assertContains
