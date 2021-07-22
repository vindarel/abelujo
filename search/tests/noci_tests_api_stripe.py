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


"""
Run tests manually:

$ ./manage.py test search.tests.tests_api_stripe.TestStripe

Send test data to a running server:

$ ./manage.py test search.tests.tests_api_stripe.TestLive
"""

import requests
import json

from django.test import TestCase

from search import api_stripe
from search.models import Reservation

from tests_api import CardFactory

# Payload
# La partie Stripe_Payload est à passer tel-quelle à stripe.checkout.Session.create.
test_payload = {
    # 'buyer': {
    #    'billling_address': {
    #       'last_name',
    #       'first_name',
    #       'email',
    #       'address',
    #       'address_comp',
    #       'city',
    #       'postcode',
    #       'country'
    #    },
    #    'delivery_address': {
    #       'last_name',
    #       'first_name',
    #       'email',
    #       'address',
    #       'address_comp',
    #       'city',
    #       'postcode',
    #       'country',
    #       'phone'
    #    },
    # },


    'order': {
        'online_payment': True,
        'shipping_method': 'local',  # | 'colissimo' | 'colissimo_sign' | 'mondial_relay',
        'mondial_relay_AP': 'identifiant',  # or null
        'amount': 100,  # int
        'abelujo_items': [{'id': 712, 'qty': 1},
                          {'id': 713, 'qty': 5}],  # list(Card),

        'stripe_payload': {
            'payment_method_types': ["card"],
            'line_items': [{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'T-shirt',
                    },
                    'unit_amount': 2000,
                },
                'quantity': 1,
            }],
            'mode': "payment",
            'success_url': "https://example.com/success",
            'cancel_url': "https://example.com/cancel",
        }
    }
}

real_test_payload = {
    'buyer': {
        'billling_address': {
            'last_name': 'Sifoni',
            'first_name': 'Lucas',
            'email': 'lucas@documents.design',
            'address': '20 avenue victor ségoffin',
            'address_comp': 'appart 4',
            'city': 'Toulouse',
            'postcode': '31400',
            'country': 'France',
            'phone': '07 33',
        },
        'delivery_address': {
            'last_name': 'Sifoni',
            'first_name': 'Lucas',
            'email': 'lucas@documents.design',
            'address': '20 avenue victor ségoffin',
            'address_comp': 'appart 4',
            'city': 'Toulouse',
            'postcode': '31400',
            'country': 'France',
            'phone': '07 67 02 55 72'
        },
    },
    'order': {
        'online_payment': True,
        'shipping_method': 'colissimo',
        'mondial_relay_AP': None,
        'amount': 5050,
        'abelujo_items': [{'id': 1, 'qty': 1}],
        'stripe_payload': {
            'payment_method_types': ["card"],
            'line_items': [
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': 'Art Du Chantier, Construire Et Demolir Du Xvi Au Xxie Siecle',
                            'description': 'ISBN: 9789461614728',
                        },
                        'unit_amount': 4200,
                    },
                    'quantity': 1,
                },
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': 'Frais de port',
                            'description': 'Colissimo, 1450g',
                        },
                        'unit_amount': 850,
                    },
                    'quantity': 1,
                }
            ],
            'mode': "payment",
            'success_url': 'https://techne-bookshop.fr/commande-effectuee',
            'cancel_url': 'https://techne-bookshop.fr/commande-annulee',
        }
    }
}

def send_test_payload():
    session = requests.post("http://localhost:8000/api/checkout", data=json.dumps(real_test_payload))
    return session

class TestStripe(TestCase):

    def setUp(self):
        self.card = CardFactory.create()

    def tearDown(self):
        pass

    def test_initial(self):
        session = api_stripe.create_checkout_session(test_payload)
        self.assertTrue(session)
        print(session)

        nb_resas_orig = Reservation.objects.count()
        session = api_stripe.handle_api_stripe(real_test_payload)
        self.assertTrue(session)
        nb_resas = Reservation.objects.count()
        self.assertTrue(nb_resas_orig < nb_resas)
        print(session)

class TestLive(TestCase):
    def test_send_payload(self):
        req = send_test_payload()
        self.assertTrue(req)
        print(req.text)
