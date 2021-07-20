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

import httplib
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from abelujo import settings
from search.models.utils import get_logger

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_API_KEY
except ImportError:
    pass

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = get_logger()


def create_checkout_session(abelujo_payload):
    assert stripe.api_key
    session = None
    payload = abelujo_payload.get('order').get('stripe_payload')
    if payload:
        session = stripe.checkout.Session.create(
            success_url=payload.get('success_url'),
            cancel_url=payload.get('cancel_url'),
            payment_method_types=payload.get('payment_method_types'),
            line_items=payload.get('line_items'),
            mode=payload.get('mode'),
        )
    else:
        log.warning('No payload found in:\n{}'.format(abelujo_payload))
    return session

#
# Response:
#
# <Session checkout.session id=cs_test_a1YB0YtTZwCDbyyKVHOORALKGlYAPMIIHUEByGSWgnzO9a2yp5T4YFWgUW at 0x7f12dc0da180> JSON: {
#   "allow_promotion_codes": null,
#   "amount_subtotal": 200,
#   "amount_total": 200,
#   "automatic_tax": {
#     "enabled": false,
#     "status": null
#   },
#   "billing_address_collection": null,
#   "cancel_url": "https://example.com/cancel",
#   "client_reference_id": null,
#   "currency": "eur",
#   "customer": null,
#   "customer_details": null,
#   "customer_email": null,
#   "display_items": [
#     {
#       "amount": 100,
#       "currency": "eur",
#       "custom": {
#         "description": null,
#         "images": null,
#         "name": "lineitem1"
#       },
#       "quantity": 2,
#       "type": "custom"
#     }
#   ],
#   "id": "cs_test_a1YB0YtTZwCDbyyKVHOORALKGlYAPMIIHUEByGSWgnzO9a2yp5T4YFWgUW",
#   "livemode": false,
#   "locale": null,
#   "metadata": {},
#   "mode": "payment",
#   "object": "checkout.session",
#   "payment_intent": "pi_1JEwbgJqOLQjpdKj4T1cdrI3",
#   "payment_method_options": {},
#   "payment_method_types": [
#     "card"
#   ],
#   "payment_status": "unpaid",
#   "setup_intent": null,
#   "shipping": null,
#   "shipping_address_collection": null,
#   "submit_type": null,
#   "subscription": null,
#   "success_url": "https://example.com/success",
#   "total_details": {
#     "amount_discount": 0,
#     "amount_shipping": 0,
#     "amount_tax": 0
#   },
#   "url": "https://checkout.stripe.com/pay/cs_test_a1YB0YtTZwCDbyyKVHOORALKGlYAPMIIHUEByGSWgnzO9a2yp5T4YFWgUW#fidkdWxOYHwnPyd1blpxYHZxWk9TQHNxSEFsbGN0YnVvdFFJNjF1MkFJNTU1dEJ8cjQ2QE0nKSdjd2poVmB3c2B3Jz9xd3BgKSdpZHxqcHFRfHVgJz8ndmxrYmlgWmxxYGgnKSdga2RnaWBVaWRmYG1qaWFgd3YnP3F3cGB4JSUl"
# }


def api_stripe(request, **response_kwargs):
    """
    """
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            session = create_checkout_session(payload)
            return JsonResponse(session)
        except Exception as e:
            res['alerts'].append("{}".format(e))
            res['status'] = httplib.INTERNAL_SERVER_ERROR
            return JsonResponse(res, status=500)
    else:
        return JsonResponse({'alerts': ['Use a POST request']})

@csrf_exempt
def api_stripe_hooks(request, **response_kwargs):
    """
    Handle post-payment webhooks.
    https://stripe.com/docs/payments/handling-payment-events
    """
    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    event = None
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }

    try:
        # stripe.event.construct_from(
        #   json.loads(payload), stripe.api_key
        # )
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        res['data'].append('Invalid Stripe signature')
        return JsonResponse(res, status=400)
    except ValueError as e:
        # Invalid payload
        res['alerts'].append("{}".format(e))
        return JsonResponse(res, status=400)

    # Handle the event
    if event.get('type') == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        msg = "PaymentIntent was successful!"
        res['alerts'].append(msg)
        res['data'] = payment_intent
        print(msg)
    elif event.get('type') == 'payment_method.attached':
        payment_method = event.data.object  # contains a stripe.PaymentMethod
        msg = 'PaymentMethod was attached to a Customer!'
        print(msg)
        res['alerts'].append(msg)
        res['data'] = payment_method
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event.get('type')))
        res['alerts'].append('Unhandled event type: {}'.format(event.get('type')))
        return JsonResponse(res, status=200)

    return JsonResponse(res, status=200)
