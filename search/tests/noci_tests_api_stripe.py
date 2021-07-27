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
import mock

from django.test import TestCase

from abelujo import settings
from search import api_stripe
from search import mailer
from search.models import Client
from search.models import Reservation

from tests_api import CardFactory

# Payload
# La partie Stripe_Payload est à passer tel-quelle à stripe.checkout.Session.create.
test_payload = {
    # 'buyer': {
    #    'billing_address': {
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
        'billing_address': {
            'last_name': 'Vincent',
            'first_name': 'vindarel',
            'email': 'vindarel@mailz.org',
            'address': 'here my city',
            'address_comp': 'comp',
            'city': 'Touwin',
            'postcode': '34100',
            'country': 'France',
            'phone': '07 33 88 88 77',
        },
        'delivery_address': {
            'last_name': 'Vincent',
            'first_name': 'vindarel',
            'email': 'vindarel@mailz.org',
            'address': 'here France',
            'address_comp': 'comp',
            'city': 'Touwin',
            'postcode': '34100',
            'country': 'France',
            'phone': '07 98 88 88 88'
        },
    },
    'order': {
        'online_payment': True,
        'shipping_method': 'colissimo',
        'mondial_relay_AP': None,
        'amount': 5050,
        # 'abelujo_items': [{'id': 100, 'qty': 1}, {'id': 101, 'qty': 1}],
        'abelujo_items': [{'id': 1, 'qty': 1}, {'id': 2, 'qty': 1}],
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

# Sent by stripe cli to our webhook.
# the payment_intent helps find our ongoing reservations, to be validated.
test_webhook_payload = """
{u'api_version': u'2019-10-17',
 u'created': 1627323959,
 u'data': {u'object': {u'amount': 2000,
                       u'amount_capturable': 0,
                       u'amount_received': 2000,
                       u'application': None,
                       u'application_fee_amount': None,
                       u'canceled_at': None,
                       u'cancellation_reason': None,
                       u'capture_method': u'automatic',
                       u'charges': {u'data': [{u'amount': 2000,
                                               u'amount_captured': 2000,
                                               u'amount_refunded': 0,
                                               u'application': None,
                                               u'application_fee': None,
                                               u'application_fee_amount': None,
                                               u'balance_transaction': u'txn_1JHYV1JqOLQjpdKjXyZvS3PN',
                                               u'billing_details': {u'address': {u'city': None,
                                                                                 u'country': None,
                                                                                 u'line1': None,
                                                                                 u'line2': None,
                                                                                 u'postal_code': None,
                                                                                 u'state': None},
                                                                    u'email': None,
                                                                    u'name': None,
                                                                    u'phone': None},
                                               u'calculated_statement_descriptor': u'VINCENT DARDEL',
                                               u'captured': True,
                                               u'created': 1627323959,
                                               u'currency': u'usd',
                                               u'customer': None,
                                               u'description': u'(created by Stripe CLI)',
                                               u'destination': None,
                                               u'dispute': None,
                                               u'disputed': False,
                                               u'failure_code': None,
                                               u'failure_message': None,
                                               u'fraud_details': {},
                                               u'id': u'ch_1JHYV1JqOLQjpdKjA9vichZn',
                                               u'invoice': None,
                                               u'livemode': False,
                                               u'metadata': {},
                                               u'object': u'charge',
                                               u'on_behalf_of': None,
                                               u'order': None,
                                               u'outcome': {u'network_status': u'approved_by_network',
                                                            u'reason': None,
                                                            u'risk_level': u'normal',
                                                            u'risk_score': 32,
                                                            u'seller_message': u'Payment complete.',
                                                            u'type': u'authorized'},
                                               u'paid': True,
                                               u'payment_intent': u'pi_1JHYV0JqOLQjpdKjGbt1FEO9',
                                               u'payment_method': u'pm_1JHYV0JqOLQjpdKjiWLIRlag',
                                               u'payment_method_details': {u'card': {u'brand': u'visa',
                                                                                     u'checks': {u'address_line1_check': None,
                                                                                                 u'address_postal_code_check': None,
                                                                                                 u'cvc_check': None},
                                                                                     u'country': u'US',
                                                                                     u'exp_month': 7,
                                                                                     u'exp_year': 2022,
                                                                                     u'fingerprint': u'pkAubXBr6xFq2pRR',
                                                                                     u'funding': u'credit',
                                                                                     u'installments': None,
                                                                                     u'last4': u'4242',
                                                                                     u'network': u'visa',
                                                                                     u'three_d_secure': None,
                                                                                     u'wallet': None},
                                                                           u'type': u'card'},
                                               u'receipt_email': None,
                                               u'receipt_number': None,
                                               u'receipt_url': u'https://pay.stripe.com/receipts/acct_1FZIQmJqOLQjpdKj/ch_1JHYV1JqOLQjpdKjA9vichZn/rcpt_JvPJG5BMLBiRltoI4ILL5hx43kVrpFy',
                                               u'refunded': False,
                                               u'refunds': {u'data': [],
                                                            u'has_more': False,
                                                            u'object': u'list',
                                                            u'total_count': 0,
                                                            u'url': u'/v1/charges/ch_1JHYV1JqOLQjpdKjA9vichZn/refunds'},
                                               u'review': None,
                                               u'shipping': {u'address': {u'city': u'San Francisco',
                                                                          u'country': u'US',
                                                                          u'line1': u'510 Townsend St',
                                                                          u'line2': None,
                                                                          u'postal_code': u'94103',
                                                                          u'state': u'CA'},
                                                             u'carrier': None,
                                                             u'name': u'Jenny Rosen',
                                                             u'phone': None,
                                                             u'tracking_number': None},
                                               u'source': None,
                                               u'source_transfer': None,
                                               u'statement_descriptor': None,
                                               u'statement_descriptor_suffix': None,
                                               u'status': u'succeeded',
                                               u'transfer_data': None,
                                               u'transfer_group': None}],
                                    u'has_more': False,
                                    u'object': u'list',
                                    u'total_count': 1,
                                    u'url': u'/v1/charges?payment_intent=pi_1JHYV0JqOLQjpdKjGbt1FEO9'},
                       u'client_secret': u'pi_1JHYV0JqOLQjpdKjGbt1FEO9_secret_J1Ow6LxJji2ggHxuVHPLh8yY9',
                       u'confirmation_method': u'automatic',
                       u'created': 1627323958,
                       u'currency': u'usd',
                       u'customer': None,
                       u'description': u'(created by Stripe CLI)',
                       u'id': u'pi_1JHYV0JqOLQjpdKjGbt1FEO9',
                       u'invoice': None,
                       u'last_payment_error': None,
                       u'livemode': False,
                       u'metadata': {},
                       u'next_action': None,
                       u'object': u'payment_intent',
                       u'on_behalf_of': None,
                       u'payment_method': u'pm_1JHYV0JqOLQjpdKjiWLIRlag',
                       u'payment_method_options': {u'card': {u'installments': None,
                                                             u'network': None,
                                                             u'request_three_d_secure': u'automatic'}},
                       u'payment_method_types': [u'card'],
                       u'receipt_email': None,
                       u'review': None,
                       u'setup_future_usage': None,
                       u'shipping': {u'address': {u'city': u'San Francisco',
                                                  u'country': u'US',
                                                  u'line1': u'510 Townsend St',
                                                  u'line2': None,
                                                  u'postal_code': u'94103',
                                                  u'state': u'CA'},
                                     u'carrier': None,
                                     u'name': u'Jenny Rosen',
                                     u'phone': None,
                                     u'tracking_number': None},
                       u'source': None,
                       u'statement_descriptor': None,
                       u'statement_descriptor_suffix': None,
                       u'status': u'succeeded',
                       u'transfer_data': None,
                       u'transfer_group': None}},
 u'id': u'evt_1JHYV2JqOLQjpdKjNzO0YcIT',
 u'livemode': False,
 u'object': u'event',
 u'pending_webhooks': 2,
 u'request': {u'id': u'req_E20E4Ufb1jLlUH', u'idempotency_key': None},
 u'type': u'payment_intent.succeeded'}
"""
def send_test_payload():
    session = requests.post("http://localhost:8000/api/checkout", data=json.dumps(real_test_payload))
    return session

def send_test_webhook():
    # XXX: needs to set request.META['HTTP_STRIPE_SIGNATURE']
    res = requests.post("http://localhost:8000/api/webhooks", data=test_webhook_payload)
    return res


# Response from Stripe when create_checkout_session is called.
create_checkout_session_response = {
    "allow_promotion_codes": None,
    "amount_subtotal": 200,
    "amount_total": 200,
    "automatic_tax": {
        "enabled": False,
        "status": None
    },
    "billing_address_collection": None,
    "cancel_url": "https://example.com/cancel",
    "client_reference_id": None,
    "currency": "eur",
    "customer": None,
    "customer_details": None,
    "customer_email": None,
    "display_items": [
        {
            "amount": 100,
            "currency": "eur",
            "custom": {
                "description": None,
                "images": None,
                "name": "lineitem1"
            },
            "quantity": 2,
            "type": "custom"
        }
    ],
    "id": "cs_test_a1YB0YtTZwCDbyyKVHOORALKGlYAPMIIHUEByGSWgnzO9a2yp5T4YFWgUW",
    "livemode": False,
    "locale": None,
    "metadata": {},
    "mode": "payment",
    "object": "checkout.session",
    "payment_intent": "pi_1JEwbgJqOLQjpdKj4T1cdrI3",  # returned also in webhook
    "payment_method_options": {},
    "payment_method_types": [
        "card"
    ],
    "payment_status": "unpaid",
    "setup_intent": None,
    "shipping": None,
    "shipping_address_collection": None,
    "submit_type": None,
    "subscription": None,
    "success_url": "https://example.com/success",
    "total_details": {
        "amount_discount": 0,
        "amount_shipping": 0,
        "amount_tax": 0
    },
    "url": "https://checkout.stripe.com/pay/cs_test_a1YB0YtTZwCDbyyKVHOORALKGlYAPMIIHUEByGSWgnzO9a2yp5T4YFWgUW#fidkdWxOYHwnPyd1blpxYHZxWk9TQHNxSEFsbGN0YnVvdFFJNjF1MkFJNTU1dEJ8cjQ2QE0nKSdjd2poVmB3c2B3Jz9xd3BgKSdpZHxqcHFRfHVgJz8ndmxrYmlgWmxxYGgnKSdga2RnaWBVaWRmYG1qaWFgd3YnP3F3cGB4JSUl"
}


def mocked_checkout_session(*args, **kwargs):
    return create_checkout_session_response

class TestStripe(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.card2 = CardFactory.create()

    def tearDown(self):
        pass

    @mock.patch('search.api_stripe.create_checkout_session', side_effect=mocked_checkout_session)
    def test_initial(self, *args, **kwargs):
        session = api_stripe.create_checkout_session(test_payload)
        self.assertTrue(session)
        print(session)

        nb_resas_orig = Reservation.objects.count()
        res = api_stripe.handle_api_stripe(real_test_payload)
        self.assertTrue(res)
        self.assertTrue(res['status'])
        self.assertTrue(res['data'])
        self.assertTrue(res['alerts'])
        nb_resas = Reservation.objects.count()
        self.assertTrue(nb_resas_orig < nb_resas)
        resa = Reservation.objects.first()
        self.assertEqual(resa.payment_intent, create_checkout_session_response.get('payment_intent'))
        print(res)

    def test_webhooks(self):
        request = {
            'body': {
                'HTTP_STRIPE_SIGNATURE': 'test',
            }
        }
        res = api_stripe.api_stripe_hooks(request, is_test=True)
        return res

    def test_email_body(self):
        self.client = Client(name="toto", firstname="Firstname", address1="5 rue Hugo")
        self.client.save()
        res = mailer.generate_client_data(self.client)
        self.assertTrue(res)

        res = mailer.generate_body_for_owner_confirmation("10", [self.card, self.card2],
                                                          self.client,
                                                          owner_name=settings.BOOKSHOP_OWNER_NAME)
        self.assertTrue(res)

class TestLive(TestCase):

    def setUp(self):
        self.card = CardFactory.create()
        self.card2 = CardFactory.create()
        self.client = Client(name="toto", firstname="Firstname", address1="5 rue Hugo",
                             mobilephone="06 09 09 09 09", telephone="05 98 98 98 98",
                             email="test@test.fr",
                             city="Touwin", country="France", zip_code="31000")
        self.client.save()

    def notest_send_payload(self):
        req = send_test_payload()
        self.assertTrue(req)
        print(req.text)

    def notest_send_hook(self):
        """
        Send a test payload for the webhook.
        The other solution is to run the stripe CLI:
        $ stripe trigger payment_intent.succeeded
        """
        req = send_test_webhook()
        return req

    def notest_send_test_owner_email(self):
        req = mailer.send_owner_confirmation(cards=[self.card, self.card2],
                                             client=self.client,
                                             total_price=10,
                                             email=settings.TEST_EMAIL_BOOKSHOP_RECIPIENT,
                                             owner_name=settings.TEST_BOOKSHOP_OWNER_NAME,
                                             )
        self.assertTrue(req)
        return req
