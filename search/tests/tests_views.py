#!/bin/env python
# -*- coding: utf-8 -*-

from search.models import Card
from search.models import Author

from search.views import get_reverse_url

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

import mock

fixture = [{"title":'fixture'}]

class TestViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        self.autobio = Card(title="Living my Life", ean="123")
        self.autobio.save()
        self.autobio.authors.add(self.goldman)

    def post_to_view(self, ean=None):
        post_params = {}
        if ean:
            post_params["ean"] = ean
        return self.c.post(reverse("card_sell"), post_params)

    def test_sell_ean_doesnt_exist(self):
        resp = self.post_to_view(ean="9876")
        self.assertTrue(resp)
        pass # test views with RequestFactory

    def test_sell_ean(self):
        resp = self.post_to_view(ean="123")
        self.assertTrue(resp)

    def test_sell_no_ean_in_post(self):
        resp = self.post_to_view()
        self.assertTrue(resp)

@mock.patch('search.views.search_on_data_source', return_value=fixture)
class TestSearchView(TestCase):

    def setUp(self):
        self.c = Client()

    def get_for_view(self, cleaned_data):
        """Use our view utility to get the reverse url with encoded query parameters.
        """
        cleaned_data["source"] = "chapitre"
        return self.c.get(get_reverse_url(cleaned_data))

    def test_search_no_query_params(self, search_mock):
        resp = self.get_for_view({})
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_with_ean(self, search_mock):
        resp = self.get_for_view({"ean":"123"})
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_with_keywords(self, search_mock):
        data = {"q":"emma gold"}
        resp = self.get_for_view(data)
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_params_not_valid(self, search_mock):
        data = {"foo": "bar"}
        resp = self.get_for_view(data)
        self.assertTrue(resp)
        self.assertEqual(resp.status_code, 200)

    def test_search_with_session(self, search_mock):
        pass

@mock.patch('search.views.search_on_data_source', return_value=fixture)
class TestAddView(TestCase):

    def setUp(self):
        self.c = Client()

    def test_call_postSearch(self, mymock):
        pass
