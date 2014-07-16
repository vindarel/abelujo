#!/bin/env python
# -*- coding: utf-8 -*-

from search.models import Card
from search.models import CardType
from search.models import Publisher
from search.models import Place
from search.models import Preferences
from search.models import Author

from search.views import get_reverse_url

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

import mock

fixture_search_datasource = [{"title":'fixture',
                         "ean": "111",
                         "details_url": "http://fake_url.com",
                         "data_source": "chapitre"
                     }]

fixture_no_ean = [{"title": "fixture no ean",
                   "details_url": "http://fake_url",
                   "data_source": "chapitre"
               }]

fake_postSearch = {"ean": "111"}

class DBFixture():
    """Create a card and required DB entries.

    The card gets an author, a type, a publisher;
    The required entries are the unknown card type, the Preferences with a default place.
    """
    def __init__(self):
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.fixture_ean = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title, ean=self.fixture_ean)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # mandatory: unknown card type
        self.typ = CardType(name="unknown")
        self.typ.save()
        # create other card types
        self.type_book = "book"
        self.typ = CardType(name=self.type_book)
        self.typ.save()
        # add a publisher
        self.pub = Publisher(name="agone")
        self.pub.save()
        self.autobio.publishers.add(self.pub)
        # a needed place:
        self.place = Place(name="test place", is_stand=False, can_sell=True)
        self.place.save()
        # Preferences: (default place)
        self.preferences = Preferences(default_place=self.place).save()


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


@mock.patch('search.views.search_on_data_source', return_value=(fixture_search_datasource, []))
class TestSearchView(TestCase):

    def setUp(self):
        self.c = Client()

    def get_for_view(self, cleaned_data):
        """Use our view utility to get the reverse url with encoded query parameters.
        """
        cleaned_data["source"] = "chapitre"
        # get the reverse url with encoded paramaters
        return self.c.get(get_reverse_url(cleaned_data, url_name="card_search"))

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

@mock.patch('search.views.search_on_data_source', return_value=fixture_search_datasource)
class TestAddView(TestCase):

    def setUp(self):
        # create an author
        self.GOLDMAN = "Emma Goldman"
        self.goldman = Author(name=self.GOLDMAN)
        self.goldman.save()
        # create a Card
        self.fixture_ean = "987"
        self.fixture_title = "living my life"
        self.autobio = Card(title=self.fixture_title, ean=self.fixture_ean)
        self.autobio.save()
        self.autobio.authors.add(self.goldman)
        # mandatory: unknown card type
        typ = CardType(name="unknown")
        typ.save()
        # create other card types
        self.type_book = "book"
        typ = CardType(name=self.type_book)
        typ.save()

        self.c = Client()

    @mock.patch('search.views._request_session_get', return_value=fixture_search_datasource)
    def test_addview_nominal(self, mock_data_source, fake_session):
        data = {"forloop_counter0": [0,],
                "quantity": [5,],
                "basket": [0,],
        }
        resp = self.c.post(reverse("card_add"), data)
        self.assertEqual(200, resp.status_code)
        # our fixture is registered to the DB:
        all_cards = Card.objects.all()
        self.assertEqual(2, len(all_cards))
        self.assertEqual(fixture_search_datasource[0]["ean"], all_cards[0].ean, "ean are not equal")
        self.assertEqual(fixture_search_datasource[0]["title"], all_cards[0].title, "title are not equal")
        self.assertEqual(fixture_search_datasource[0]["quantity"], all_cards[0].quantity, "quantities are not equal")

    @mock.patch('search.views._request_session_get', return_value=fixture_search_datasource)
    def test_form_not_valid(self, mock_data_source, fake_session):
        data = {"forloop_counter0": "not valid",
                "quantity": [1,],
                "basket": [0,],
        }
        resp = self.c.post(reverse("card_add"), data)
        self.assertEqual(400, resp.status_code)

    @mock.patch('search.views._request_session_get', return_value=fixture_no_ean)
    @mock.patch('search.views.postSearch', return_value=fake_postSearch)
    def test_call_postSearch_no_ean(self, mock_postSearch, fake_session, mock_data_source):
        data = {"forloop_counter0": [0,],
                "quantity": [1,],
                "basket": [0,],
        }
        resp = self.c.post(reverse("card_add"), data)
        mock_postSearch.assert_called_once_with(fixture_no_ean[0]["details_url"])


class TestCollectionView(TestCase, DBFixture):

    def setUp(self):
        DBFixture.__init__(self)
        self.c = Client()

    def test_nominal(self):
        resp = self.c.get(reverse("card_collection"))  # get the 5th first cards
        self.assertEqual(resp.status_code, 200)

    def test_search_title(self):
        form = {"q": "living",}
        resp = self.c.post(reverse("card_collection"), data=form)
        self.assertEqual(resp.status_code, 200)

    def test_search_ean(self):
        form = {"ean": self.fixture_ean,}
        resp = self.c.post(reverse("card_collection"), data=form)
        self.assertEqual(resp.status_code, 200)
