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
from search import mailer
from search.models import Card
from search.models import Client
from search.models import Reservation
from search.models.utils import _is_truthy
from search.models.utils import get_logger

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_API_KEY
except ImportError:
    pass

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = get_logger()


def create_checkout_session(abelujo_payload):
    """
    Create a session object on Stripe.
    It returns a JSON. Our identifiers can be its ID or the payment_intent ID. We will find them back on the webhook.

    Mocked in unit tests.
    """
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
#   "payment_intent": "pi_1JEwbgJqOLQjpdKj4T1cdrI3",  # returned also in webhook
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

    If it's an online payment, create a stripe session and only pre-sell the reservations.
    They have to be validated in the webhook.

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
    online_payment = payload.get('order').get('online_payment')
    online_payment = _is_truthy(online_payment)
    try:
        if online_payment and payload.get('order').get('stripe_payload'):
            log.info("Processing Stripe payload...")
            session = create_checkout_session(payload)
            res['data'] = session
        else:
            log.info("No Stripe payload to process.")
        # return JsonResponse(session)
    except Exception as e:
        res['alerts'].append("{}".format(e))
        res['status'] = httplib.INTERNAL_SERVER_ERROR
        # status = 500
        # return JsonResponse(res, status=500)

    ################################################
    ## Create clients, commands.
    ## If online payment, they are not validated yet.
    ################################################
    billing_address = buyer.get('billing_address')
    delivery_address = buyer.get('delivery_address')

    existing_client = Client.objects.filter(email=billing_address.get('email')).first()
    # TODO: update existing client.
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
    #     res['alerts'].append(msgs)

    cards_qties = []
    cards = []
    for id_qty in ids_qties:
        card = Card.objects.filter(pk=id_qty.get('id')).first()
        if card:
            cards_qties.append({'card': card, 'qty': id_qty.get('qty')})
            cards.append(card)
        else:
            log.warning("Selling cards with Stripe, we could not find a card: {}".format(id_qty.get('id')))

    # Reserve.
    # PERFORMANCE:
    reservations = []  # should be one for all...
    try:
        is_paid = True
        payment_intent = None
        if online_payment:
            is_paid = False  # needs to be validated in the webhook.
            payment_intent = session.get('payment_intent')
        for card_qty in cards_qties:
            resa, created = existing_client.reserve(card_qty.get('card'),
                                                    nb=card_qty.get('qty'),
                                                    send_by_post=True,
                                                    is_paid=is_paid,
                                                    payment_origin="stripe",
                                                    payment_meta=payload,
                                                    payment_session=session,
                                                    payment_intent=payment_intent)
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
    # status = 200
    if request.method == 'POST':
        if request.body:
            payload = json.loads(request.body)
            try:
                res = handle_api_stripe(payload)
            except Exception as e:
                log.error("Error handling the api stripe payment: {}. Payload used: {}".format(e, payload))
                res['status'] = 500
                res['alerts'].append(e)

        return JsonResponse(res)

    else:
        return JsonResponse({'alerts': ['Use a POST request']})

def stripe_construct_event(payload, signature, webhook_secret):
    event = stripe.Webhook.construct_event(
        payload, signature, webhook_secret
    )
    return event

@csrf_exempt
def api_stripe_hooks(request, **response_kwargs):
    """
    Handle post-payment webhooks.
    https://stripe.com/docs/payments/handling-payment-events

    Find the pre-saved reservations with the payment_intent ID and validates them.
    Then, send validation emails.
    """
    if not settings.STRIPE_SECRET_API_KEY:
        # Don't fail unit tests on CI.
        # I don't feel like installing the Stripe python lib by default…
        return

    # Mocking stripe functions, request object and having the right payloads
    # is not so easy, so let's use is_test...
    is_test = response_kwargs.get('is_test')
    if not is_test:
        payload = request.body
        signature = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    cards = []  # TODO:
    event = None
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }
    sell_successful = None

    try:
        # stripe.event.construct_from(
        #   json.loads(payload), stripe.api_key
        # )
        event = None
        if not is_test:
            event = stripe_construct_event(payload, signature, webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        res['alerts'].append('Invalid Stripe signature')
        return JsonResponse(res, status=400)
    except ValueError as e:
        # Invalid payload
        res['alerts'].append("{}".format(e))
        return JsonResponse(res, status=400)

    # Handle the event
    if is_test:
        sell_successful = True
    if event and event.get('type') == 'checkout.session.completed':
        # We consider the payment was succesfull only with this event.
        sell_successful = True
    elif event and event.get('type') == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        cards = []
        msg = "PaymentIntent was successful!"
        res['alerts'].append(msg)
        # res['data'] = payment_intent  # this is not a JSON but an object.
        # print(msg)
        # sell_successful = True
    elif event and event.get('type') == 'payment_method.attached':
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

    # Send confirmation emails.
    payload = json.loads(request.body)
    payment_intent = None
    from pprint import pprint
    pprint(payload)
    try:
        payment_intent = payload['data']['object']['payment_intent']
    except Exception as e:
        log.error("Could not get the payment intent ID in webhook: {}".format(e))

    ongoing_reservations = Reservation.objects.filter(payment_intent=payment_intent)
    # So we have several reservation objects, but they should be of the same client,
    # part of the same command...
    client = None
    send_by_post = False
    if ongoing_reservations:
        client = ongoing_reservations.first().client
        send_by_post = ongoing_reservations.first().send_by_post
    else:
        log.warning("stripe webhook: we didn't find any ongoing reservation with payment intent {}. We won't be able to find a related client and to send confirmation emails.".format(payment_intent))

    # Quickly check we have the same clients.
    if client:
        for resa in ongoing_reservations:
            if resa.client != client:
                log.warning("mmh we have ongoing reservations with payment_intent {} but not the same client ?? {} / {}".format(payment_intent, client, resa.client))

    to_email = ""
    amount = 0
    description = ""
    is_stripe_cli_test = False
    cli_test_sign = "(created by Stripe CLI)"
    if sell_successful:
        # Now, validate the reservations.
        # for resa in ongoing_reservations:
        #     resa.is_paid = True
        #     resa.save()
        ongoing_reservations.update(is_paid=True)

        # Get emails.
        to_email = client.email if client else ""

        try:
            description = payload['data']['object']['charges']['data'][0]['description']
            if description and cli_test_sign in description:
                is_stripe_cli_test = True
        except Exception as e:
            log.info("api_stripe_hooks: could not get the description, I don't know if we are in a stripe cli test: {}".format(e))

        try:
            amount = payload['data']['object']['charges']['data'][0]['amount']
        except Exception as e:
            log.warning("api_stripe_hooks: could not get the amount: {}".format(e))

        # Ensure ascii for python Stripe library... shame on you.
        if is_stripe_cli_test:
            to_email = "".join(list(reversed('gro.zliam@leradniv')))  # me@vindarel
        if to_email:
            try:
                to_email = to_email.encode('ascii', 'ignore')
            except Exception as e:
                log.warning("api_stripe: error trying to encode the email address {} to ascii: {}".format(to_email, e))

        # Send it, damn it.
        try:
            if to_email:
                mailer.send_command_confirmation(cards=cards, total_price=amount,
                                                 to_emails=to_email)
                log.info("stripe webhook: confirmation mail sent to {}".format(to_email))
        except Exception as e:
            log.error("api_stripe: could not send confirmation email: {}".format(e))

        # Send confirmation to bookshop owner.
        if settings.EMAIL_BOOKSHOP_RECIPIENT:
            try:
                mailer.send_owner_confirmation(cards=cards,
                                               client=client,
                                               total_price=amount,
                                               email=settings.EMAIL_BOOKSHOP_RECIPIENT,
                                               owner_name=settings.BOOKSHOP_OWNER_NAME,
                                               send_by_post=send_by_post,
                                               )
                log.info("stripe webhook: confirmation sent to owner: {}".format(settings.EMAIL_BOOKSHOP_RECIPIENT))
            except Exception as e:
                log.error("api_stripe webhook: could not send confirmation email to owner: {}".format(e))
        else:
            log.warning("stripe webhook: sell with payment intent {} was successfull and we wanted to send an email to the bookshop owner, but we can't find its email in settings.".format(payment_intent))

    return JsonResponse(res, status=200)
