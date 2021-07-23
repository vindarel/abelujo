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

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from abelujo import settings

# FROM_EMAIL = settings.EMAIL_SENDER  # doesn't like UTF8...
FROM_EMAIL = 'contact+commandes@abelujo.cc'

TEST_SUBJECT = "Abelujo: new message"
TEST_BODY = '<strong>Hello from Abelujo</strong> with Sendgrid.'
TEST_TO_EMAILS = "".join(list(reversed('gro.zliam@leradniv')))  # me@vindarel

def send_email(from_email=FROM_EMAIL,
               to_emails=TEST_TO_EMAILS,
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
        subject=subject,
        html_content=html_content)

    try:
        api_key = settings.SENDGRID_API_KEY,
        # api_key = os.environ.get('SENDGRID_API_KEY')
        if verbose:
            print(from_email, to_emails, subject, html_content)
            if api_key:
                print('api key OK')

        # Synchronous send:
        # import ipdb; ipdb.set_trace()
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

def generate_card_summary(cards):
    res = ""
    for card in cards:
        res += "- {}".format(card.title)
    return res

def generate_body_for_command_confirmation(price, cards):
    linebreak = "</br>"
    newline = "{} {}".format(linebreak, linebreak)
    body = """Bonjour, {newline}

Votre commande des titres suivants pour un total de {PRICE} a bien été reçue. {newline}

{CARDS}
{newline}

Merci beaucoup et à bientôt ! {newline}

L'équipe
    """
    body = body.format(linebreak=linebreak,
                       newline=newline,
                       PRICE=price,
                       CARDS=generate_card_summary(cards))
    return body


def send_command_confirmation(cards=[],  # list of cards sold
                              total_price="",
                              to_emails=TEST_TO_EMAILS,
                              verbose=False):
    # Build HTML body.
    body = generate_body_for_command_confirmation(total_price, cards)

    # Send.
    res = send_email(to_emails=to_emails,
                     from_email=FROM_EMAIL,
                     subject=SUBJECT_COMMAND_OK,
                     html_content=body,
                     verbose=verbose)
    return res


if __name__ == "__main__":
    exit(send_email())
