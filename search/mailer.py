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
"""
# Sendgrid Mail doesn't like UTF8 params.
# Bad library quality overall :(
# from __future__ import unicode_literals

import logging

from django.template.loader import get_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from abelujo import settings
from search.models.users import Bookshop
from search.models.utils import get_logger

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = get_logger()

# FROM_EMAIL = settings.EMAIL_SENDER  # doesn't like UTF8...
FROM_EMAIL = 'contact+commandes@abelujo.cc'

TEST_SUBJECT = "Abelujo: new message"
TEST_BODY = '<strong>Hello from Abelujo</strong> with Sendgrid.'
TEST_TO_EMAILS = "".join(list(reversed('gro.zliam@leradniv')))  # me@vindarel

def send_email(from_email=FROM_EMAIL,
               to_emails=TEST_TO_EMAILS,
               reply_to=None,
               subject=TEST_SUBJECT,
               html_content=TEST_BODY,
               verbose=False):
    # message = Mail(
    #     # Use a verified sender.
    #     from_email='contact+commandes@abelujo.cc',
    #     to_emails='ehvince@mailz.org',
    #     subject='Sending with Twilio SendGrid is Fun',
    #     html_content='<strong>and easy to do anywhere, even with Python</strong>')

    message_obj = Mail(
        # Use a verified sender.
        from_email=from_email,
        to_emails=to_emails,
        # reply_to="ehvince@mailz.org",  # unavailable, LOL. Sent a PR.
        subject=subject,
        html_content=html_content)
    if reply_to:
        message_obj.reply_to = reply_to

    try:
        api_key = settings.SENDGRID_API_KEY,
        # api_key = os.environ.get('SENDGRID_API_KEY')
        if verbose:
            print(from_email, to_emails, subject, html_content)
            if api_key:
                print('api key OK')

        # Synchronous send:
        if isinstance(api_key, tuple):
            api_key = api_key[0]  # don't ask me why!!!
        sg = SendGridAPIClient(api_key)
        response = sg.send(message_obj)

        if verbose:
            print(response.status_code)
            print(response.body)
            print(response.headers)
    except Exception as e:
        print(str(e))
        return False

    return True


####################################################################
# Command confirmations.
####################################################################

SUBJECT_COMMAND_OK = "Votre commande"
SUBJECT_COMMAND_OWNER = "Nouvelle commande"


def generate_body_for_client_command_confirmation(price, cards, payload={}):
    template = get_template('mailer/client_confirmation_template.html')
    bookshop_name = Bookshop.name() or ""
    body = template.render({'payload': payload,
                            'bookshop_name': bookshop_name,
                            })
    try:
        body = body.encode('utf8')
    except Exception as e:
        log.warn('Could not encode the Django template to utf8: {}. Payload is: {}'.format(e, payload))
    return body


def generate_body_for_owner_confirmation(client,
                                         owner_name,
                                         payload={},
                                         is_online_payment = False,
                                         ):
    template = get_template('mailer/new_command_template.html')
    bookshop_name = Bookshop.name() or ""
    try:
        is_online_payment = payload.get('order').get('online_payment')
    except Exception as e:
        log.warn("generate_body_for_owner_confirmation: {}".format(e))
    body = template.render({'payload': payload,
                            'bookshop_name': bookshop_name,
                            'is_online_payment': is_online_payment,
                            })
    try:
        body = body.encode('utf8')
    except Exception as e:
        log.warn('Could not encode the Django template to utf8: {}. Payload is: {}'.format(e, payload))
    return body

def send_client_command_confirmation(cards=[],  # list of cards sold
                                     total_price="",
                                     payload={},
                                     to_emails=TEST_TO_EMAILS,
                                     reply_to=None,
                                     verbose=False):
    # Build HTML body.
    body = generate_body_for_client_command_confirmation(total_price, cards, payload=payload)

    # Send.
    res = send_email(to_emails=to_emails,
                     from_email=FROM_EMAIL,
                     reply_to=reply_to,
                     subject=SUBJECT_COMMAND_OK,
                     html_content=body,
                     verbose=verbose)
    if not res:
        print("Could not send email to owner: {}".format(res))
    return res


def send_owner_confirmation(cards=[], email="", client=None,
                            payload={},
                            owner_name="",
                            is_online_payment=None,
                            verbose=False):
    body = generate_body_for_owner_confirmation(client,
                                                owner_name,
                                                payload=payload,
                                                is_online_payment=is_online_payment,
                                                )

    res = send_email(to_emails=email,
                     from_email=FROM_EMAIL,
                     subject=SUBJECT_COMMAND_OWNER,
                     html_content=body,
                     verbose=verbose,
                     )
    if not res:
        log.warn("Could not send email to owner: {}".format(res))
    return res
