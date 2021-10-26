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
from search.models.utils import get_total_weight

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

    If it isn't an online payment, warn the client and the bookshop already.

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

    # Is is an online payment?
    is_online_payment = False

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
    session = {}
    is_online_payment = payload.get('order').get('online_payment')
    is_online_payment = _is_truthy(is_online_payment)
    if is_online_payment:
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
            # status = 500
            # return JsonResponse(res, status=500)

    ################################################
    ## Create clients, commands.
    ## If online payment, they are not validated yet.
    ################################################
    billing_address = buyer.get('billing_address')
    # delivery_address = buyer.get('delivery_address')

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

    ##################################################
    # Test configuration?
    # If the client is the developer, we are testing.
    ##################################################
    its_only_a_test = False
    client_email = billing_address.get('email')
    client_lastname = billing_address.get('last_name').strip()
    client_firstname = billing_address.get('first_name').strip()
    if client_email == settings.TEST_EMAIL_BOOKSHOP_RECIPIENT \
       or client_lastname == settings.TEST_LASTNAME \
       or client_firstname == settings.TEST_FIRSTNAME:
        its_only_a_test = True

    ##################################################
    # Reserve.
    # (if it's not a live test by the developer)
    ##################################################
    # PERFORMANCE:
    reservations = []  # should be one for all...
    try:
        is_paid = True
        payment_intent = None
        if is_online_payment:
            is_paid = False  # needs to be validated in the webhook.
            payment_intent = session.get('payment_intent')
        payment_meta = payload
        try:
            payment_meta = json.dumps(payload)
        except Exception as e:
            log.warning("stripe api: we try to encode payload to JSON to store it in payment_meta, but that failed: {}".format(e))
        if not its_only_a_test:
            for card_qty in cards_qties:
                resa, created = existing_client.reserve(card_qty.get('card'),
                                                        nb=card_qty.get('qty'),
                                                        send_by_post=True,
                                                        is_paid=is_paid,
                                                        is_ready=False,
                                                        payment_origin="stripe",
                                                        payment_meta=payment_meta,
                                                        payment_session=session,
                                                        payment_intent=payment_intent)
                if resa:
                    reservations.append(resa)
            res['alerts'].append("client commands created successfully")

    except Exception as e:
        log.error("Error creating reservations for {}: {}".format(cards_qties, e))

    ##############################################
    ## Send confirmation email to both parties. ##
    ##############################################

    # If the client is the tester, send him the email.
    if its_only_a_test:
        mail_sent = mailer.send_client_command_confirmation(cards=cards,
                                                            to_emails=settings.TEST_EMAIL_BOOKSHOP_RECIPIENT,
                                                            payload=payload,
                                                            payment_meta=payload,
                                                            reply_to=settings.EMAIL_BOOKSHOP_RECIPIENT,
                                                            # added:
                                                            use_theme=True)
        log.warning("We send a confirmation email to the tester. Mail sent? {} cards: {}, payload: {}".format(mail_sent, cards, payload))
        if mail_sent:
            status = 200
        else:
            status = 500
        res['status'] = status

    if not is_online_payment:
        # Send confirmation to client.
        try:
            mail_sent = mailer.send_client_command_confirmation(cards=cards,
                                                                # to_emails=??
                                                                payload=payload,
                                                                reply_to=settings.EMAIL_BOOKSHOP_RECIPIENT)
            log.info("stripe: confirmation email sent to client ? {} (not an online payment). Payload: {}".format(mail_sent, payload))
            if not mail_sent:
                log.warning("stripe: confirmation email to client (not an online payment) was not sent :S")
                pass  # TODO: register info in reservation.
        except Exception as e:
            log.error("stripe: could not send confirmation email (not an online payment): {}".format(e))

        # Send confirmation to bookshop owner.
        if settings.EMAIL_BOOKSHOP_RECIPIENT:
            # Get total weight of cards.
            total_weight, weight_message = get_total_weight(cards)
            try:
                mail_sent = mailer.send_owner_confirmation(cards=cards,
                                                           total_weight=total_weight,
                                                           weight_message=weight_message,
                                                           payload=payload,
                                                           is_online_payment=is_online_payment,
                                                           email=settings.EMAIL_BOOKSHOP_RECIPIENT,
                                                           owner_name=settings.BOOKSHOP_OWNER_NAME,
                                               )
                log.info("stripe, reservation but no payment: confirmation sent to owner: {} ? {}".format(settings.EMAIL_BOOKSHOP_RECIPIENT, mail_sent))
                if not mail_sent:
                    log.warning("stripe: confirmation email to owner (not an online payment) was not sent :S")
            except Exception as e:
                log.error("api_stripe: could not send confirmation email to owner: {} (not a payment)".format(e))
        else:
            log.warning("stripe: sell with payment intent {} was successfull and we wanted to send an email to the bookshop owner, but we can't find its email in settings.".format(payment_intent))

    return res

def api_stripe(request, **response_kwargs):
    """
    API entry point of the Stripe handling machinery. The frontend calls here.

    If Stripe settings are configured (we find the secret API key) and if
    we receive a POST request, then call `handle_api_stripe` to do the job.

    Return: a JsonResponse to return to the web client.
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

def _stripe_construct_event(payload, signature, webhook_secret):
    """
    Helper to construct a Stripe event object.

    Return: a stripe event object.
    """
    event = stripe.Webhook.construct_event(
        payload, signature, webhook_secret
    )
    return event

@csrf_exempt
def api_stripe_hooks(request, **response_kwargs):
    """
    API endpoint to handle post-payment webhooks and validate the payment.
    https://stripe.com/docs/payments/handling-payment-events

    Find the pre-saved reservations with the payment_intent ID and validate them.

    Then, send validation emails to the client and the bookshop.

    Return: a JsonResponse (to Stripe).
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

    ongoing_reservations = []
    cards = []
    event = None
    res = {'data': "",
           'alerts': [],
           'status': httplib.OK,
           }
    sell_successful = None

    # Build a Stripe event object from the payload.
    event = {}
    try:
        # stripe.event.construct_from(
        #   json.loads(payload), stripe.api_key
        # )
        if not is_test:
            event = _stripe_construct_event(payload, signature, webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        res['alerts'].append('Invalid Stripe signature')
        return JsonResponse(res, status=400)
    except ValueError as e:
        # Invalid payload
        res['alerts'].append("{}".format(e))
        return JsonResponse(res, status=400)

    # Handle the event.
    # We consider the sell successfull on receiving the session.completed event.
    if is_test:
        sell_successful = True
    if event and event.get('type') == 'checkout.session.completed':
        # We consider the payment was succesfull only with this event.
        sell_successful = True
        log.info("stripe hook: received checkout.session.completed signal. Now looking for the payment intent id.")
    # ... handle other event types
    else:
        log.info('Unhandled event type {}'.format(event.get('type')))
        res['alerts'].append('Unhandled event type: {}'.format(event.get('type')))
        return JsonResponse(res, status=200)

    # If the sell was not successful, warn the bookshop.
    # ... or let Stripe handle it.
    if not sell_successful:
        return JsonResponse(res, status=200)

    #
    # Look for the payment intent ID.
    #
    payload = json.loads(request.body)
    payment_intent = None
    from pprint import pprint
    pprint(payload)
    if sell_successful:
        try:
            payment_intent = payload['data']['object']['payment_intent']
            log.info("stripe hook: found payment intent: {}. Everything goes well.".format(payment_intent))
        except Exception as e:
            log.error("Could not get the payment intent ID in in webhook (in data.object.payment_intent). Let me search in charges.0.data now. {}".format(e))

        if not payment_intent:
            try:
                payload_data = payload['data']['object']['charges']['data']
                if payload_data and len(payload_data):
                    payment_intent = payload_data[0].get('payment_intent')
                    log.info("stripe hook: found payment intent inside charges.data.0: {}. Payload: {}".format(payment_intent, payload))

                if len(payload_data) > 1:
                    log.info("stripe hook: payload's charges has more than 1 element and we don't handle it: {}".format(payload_data))
            except Exception as e:
                log.warning("stripe hook: looking for the payment_intent failed: it was not in data.object.payment_intent and we don't find it in data.object.charges.data.0 either. {}".format(e))

    #
    # If no payment ID found, log, but send an email to the owner anyways
    # (so she knows something happened).
    #
    if not payment_intent:
        log.warning("stripe hook: we did not find the payment_intent, so we won't validate reservations or send emails. {}".format(e))

    #
    # Confirm the reservations.
    #
    ongoing_reservations = None
    payment_meta = None  # Data from the first POST: buyer.billing_address, order.amount etc.
    if payment_intent:
        ongoing_reservations = Reservation.objects.filter(payment_intent=payment_intent)
    # So we have several reservation objects, but they should be of the same client and
    # part of the same command...
    client = None
    # send_by_post = False
    if ongoing_reservations:
        client = ongoing_reservations.first().client
        log.info("stripe hook: found client: {}".format(client))
        # send_by_post = ongoing_reservations.first().send_by_post
        cards = [it.card for it in ongoing_reservations]
        payment_meta = ongoing_reservations.first().payment_meta  # text field
        log.info("stripe hook: found payment meta data: {}".format(payment_meta))
        try:
            payment_meta = json.loads(payment_meta)
            log.info("payment_meta decoded from json")
        except Exception as e:
            log.warning("stripe hook: we are trying to decode the payment_meta from a JSON string, but it failed. We maybe have data from before sept, 14th. {}".format(e))
            payment_meta = None  # prevent decoding errors in templates (?).

    else:
        log.warning("stripe webhook: we didn't find any ongoing reservation with payment intent {}. We won't be able to find a related client and to send confirmation emails.".format(payment_intent))

    # Quickly check we have the same clients.
    if client:
        for resa in ongoing_reservations:
            if resa.client != client:
                log.warning("mmh we have ongoing reservations with payment_intent {} but not the same client ?? {} / {}".format(payment_intent, client, resa.client))

    ###############################
    ## Send confirmation emails. ##
    ###############################
    to_email = ""
    # amount = None
    # amount_fmt = ""
    # currency = ""
    # currency_symbol = "EUR"
    description = ""
    is_stripe_cli_test = False
    cli_test_sign = "(created by Stripe CLI)"
    if sell_successful:
        # Now, validate the reservations.
        # for resa in ongoing_reservations:
        #     resa.is_paid = True
        #     resa.save()
        if ongoing_reservations:
            ongoing_reservations.update(is_paid=True, is_ready=True)
        # ongoing_reservations.update(is_ready=True)

        # Get emails.
        if client:
            to_email = client.email if client else ""

        try:
            description = payload['data']['object']['charges']['data'][0]['description']
            if description and cli_test_sign in description:
                is_stripe_cli_test = True
        except Exception as e:
            log.info("api_stripe_hooks: could not get the description, so we are probably NOT in a stripe cli test but in production. The exception is: {}".format(e))

        # try:
        #     amount = payload['data']['object']['amount_total']
        #     currency = payload['data']['object']['currency']
        #     if currency in ['eur', u'eur']:
        #         currency_symbol = "EUR"  # PySendgrid doesn't like UTF8 symbols? It works locally though :S
        #     amount_fmt = "{:.2f} {}".format(amount / 100.0, currency_symbol)
        # except Exception as e:
        #     log.warning("api_stripe_hooks: could not get the amount: {}".format(e))

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
                mail_sent = mailer.send_client_command_confirmation(cards=cards,
                                                                    # total_price=amount_fmt,
                                                                    to_emails=to_email,
                                                                    payload=payload,
                                                                    payment_meta=payment_meta,
                                                                    is_online_payment=True,
                                                                    reply_to=settings.EMAIL_BOOKSHOP_RECIPIENT)
                log.info("stripe webhook: confirmation mail sent to {} ? {}".format(to_email, mail_sent))

                if not mail_sent:
                    # TODO: register info in reservation.
                    log.warning("stripe hook: payment confirmation email to client was not sent :S")
        except Exception as e:
            log.error("api_stripe: could not send confirmation email: {}".format(e))

        # Send the same email to the developer, to check theme rendering.
        try:
            mail_sent = mailer.send_client_command_confirmation(cards=cards,
                                                                is_online_payment=True,
                                                        to_emails=settings.TEST_EMAIL_BOOKSHOP_RECIPIENT,
                                                        payload=payload,
                                                        payment_meta=payload,
                                                        reply_to=settings.EMAIL_BOOKSHOP_RECIPIENT,
                                                        # added: use custom theme.
                                                        use_theme=True)
            log.info("stripe webhook: confirmation mail sent to {} ? {}".format(settings.TEST_EMAIL_BOOKSHOP_RECIPIENT, mail_sent))
        except Exception as e:
            log.warn("api_stripe hook: could not send email with custom theme to developer: {}".format(e))

        #
        # Send confirmation to bookshop owner.
        #
        if settings.EMAIL_BOOKSHOP_RECIPIENT:
            # Get total weight of cards.
            total_weight, weight_message = get_total_weight(cards)
            try:
                mail_sent = mailer.send_owner_confirmation(cards=cards,
                                                           total_weight=total_weight,
                                                           weight_message=weight_message,
                                                           payload=payload,
                                                           payment_meta=payment_meta,
                                                           is_online_payment=True,
                                                           client=client,
                                                           # total_price=amount_fmt,
                                                           email=settings.EMAIL_BOOKSHOP_RECIPIENT,
                                                           owner_name=settings.BOOKSHOP_OWNER_NAME,
                                                           )
                log.info("stripe webhook: confirmation sent to owner: {} ? {}".format(settings.EMAIL_BOOKSHOP_RECIPIENT, mail_sent))
                if not mail_sent:
                    log.warning("stripe hook: payment confirmation email to client was not sent :S")
            except Exception as e:
                log.error("api_stripe webhook: could not send confirmation email to owner: {}".format(e))
        else:
            log.warning("stripe webhook: sell with payment intent {} was successfull and we wanted to send an email to the bookshop owner, but we can't find its email in settings.".format(payment_intent))

    # Sell not validated.
    else:
        pass

    return JsonResponse(res, status=200)
