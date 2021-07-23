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
from search.models import Card
from search.models import Client
from search.models.utils import get_logger

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_API_KEY
except ImportError:
    pass

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = get_logger()


def create_checkout_session(abelujo_payload):
    if settings.STRIPE_SECRET_API_KEY:
        assert stripe.api_key
    else:
        return
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


def handle_api_stripe(payload):
    """
    From this payload (dict), find or create the client, the reservation of the cards,
    create a stripe session if required.

    Important keys:
    - buyer.billing_address, buyer.shipping_address
    - order.stripe_payload (optional)

    Return: dict (data, status, alerts).
    """
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }
    buyer = payload.get('buyer')
    order = payload.get('order')

    ###################
    ## Basic checks. ##
    ###################
    if not order:
        msg = "We are asked to process a payment with no order, that's not possible. payload: {}".format(payload)
        log.warning(msg)
        res['alerts'].append(msg)
        res['status'] = 400
        # return JsonResponse(res, status=400)
        return res

    if not buyer:
        log.warning('We are asked to process a payment with no buyer, strange! payload is {}'.format(payload))

    ############################
    ## Handle Stripe session. ##
    ############################
    try:
        if payload.get('order').get('stripe_payload'):
            log.info("Processing Stripe payload...")
            session = create_checkout_session(payload)
            res['data'] = session
        else:
            log.info("No Stripe payload to process.")
        # return JsonResponse(session)
    except Exception as e:
        res['alerts'].append("{}".format(e))
        res['status'] = httplib.INTERNAL_SERVER_ERROR
        status = 500
        # return JsonResponse(res, status=500)

    ###########################################
    ## Create clients, commands, send bills. ##
    ###########################################
    billing_address = buyer.get('billing_address')
    delivery_address = buyer.get('delivery_address')

    existing_client = Client.objects.filter(email=billing_address.get('email'))
    if not existing_client:
        try:
            existing_client = Client(
                name=billing_address.get('last_name').strip(),
                firstname=billing_address.get('first_name').strip(),
                email=billing_address.get('email').strip(),
                city=billing_address.get('city').strip(),
                country=billing_address.get('country').strip(),
                zip_code=billing_address.get('postcode').strip(),
                address1=billing_address.get('address').strip(),
                address2=billing_address.get('address_comp').strip(),
                telephone=billing_address.get('phone').strip(),
            )
            existing_client.save()
        except Exception as e:
            log.error("This new client ({}) could not be created in DB: {}. billing_address is: {}".format(billing_address.get('name'), e, billing_address))
            res['alerts'].append('Error creating a new client')
            res['status'] = 500

    # cards we sell: list of 'id' and 'qty'.
    ids_qties = order.get('abelujo_items')
    # cards_ids = [it.get('id') for it in cards_qties]
    # cards, msgs = Card.get_from_id_list(cards_ids)
    # if msgs:
        # res['alerts'].append(msgs)

    cards_qties = []
    for id_qty in ids_qties:
        card = Card.objects.filter(pk=id_qty.get('id')).first()
        if card:
            cards_qties.append({'card': card, 'qty': id_qty.get('qty')})

    # Reserve.
    # PERFORMANCE:
    reservations = []  # should be one for all...
    try:
        for card_qty in cards_qties:
            resa, created = existing_client.reserve(card_qty.get('card'),
                                                    nb=card_qty.get('qty'))
            if resa:
                reservations.append(resa)
        res['alerts'].append("client commands created successfully")

    except Exception as e:
        log.error("Error creating reservations for {}: {}".format(cards_qties, e))

    return res

def api_stripe(request, **response_kwargs):
    """
    """
    if not settings.STRIPE_SECRET_API_KEY:
        # Don't fail unit tests on CI.
        # I don't feel like installing the Stripe python lib by default…
        return
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }
    payload = {}
    session = None
    status = 200
    if request.method == 'POST':
        if request.body:
            payload = json.loads(request.body)
            try:
                res = handle_api_stripe(payload)
            except Exception as e:
                log.error("Error handling the api stripe payment: {}. Payload used: {}".format(e, payload))
                res = None
                res['status'] = 500
                res['alerts'].append(e)

        return JsonResponse(res)

    else:
        return JsonResponse({'alerts': ['Use a POST request']})

@csrf_exempt
def api_stripe_hooks(request, **response_kwargs):
    """
    Handle post-payment webhooks.
    https://stripe.com/docs/payments/handling-payment-events
    """
    if not settings.STRIPE_SECRET_API_KEY:
        # Don't fail unit tests on CI.
        # I don't feel like installing the Stripe python lib by default…
        return
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
