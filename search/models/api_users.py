# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

import json
import os

import pendulum
from django.http import JsonResponse
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import ugettext as _
from weasyprint import HTML

from abelujo import settings
from search.models import Card
from search.models import Preferences
from search.models import users
from search.models.users import Client
from search.models.utils import get_logger
from search.models.utils import price_fmt

log = get_logger()

def clients(request, **response_kwargs):
    """
    Get clients.
    """
    if request.method == 'GET':
        try:
            params = request.GET
            query = params.get('query')
            if query:
                res = Client.search(query, to_dict=True)
            else:
                res = [it.to_dict() for it in Client.objects.all()]
            return JsonResponse({'data': res})
        except Exception as e:
            log.error("error getting clients: {}".format(e))
            return JsonResponse()

def bill(request, *args, **response_kwargs):
    """
    Create a bill, as a PDF file.

    Either:
    - with the given products (list of ids)
      - each has an optional discount.
    - for the given client.

    or:
    - from an existing bill id.
    """
    if request.method == 'GET':
        return

    template = 'pdftemplates/pdf-bill-main.html'

    # ids, prices, quantities
    try:
        params = json.loads(request.body)
    except Exception as e:
        log.error('Sell bill: could not decode json body: {}\n{}'.format(e, request.body))

    language = params.get('language')
    if language:
        translation.activate(language)

    # Creation date, due date.
    DATE_FMT = '%d-%m-%Y'
    creation_date = pendulum.today()
    creation_date_label = _("Created")  # this can be in trans template tags.
    due_date_label = _("Due")

    # Sell and due dates.
    sell_date = params.get('date')
    if sell_date:
        creation_date = pendulum.parse(sell_date)
    else:
        # unlikely, JS always sets the date.
        creation_date = pendulum.today()
    creation_date_fmt = creation_date.strftime(DATE_FMT)
    due_date = creation_date.add(months=1)
    due_date_fmt = due_date.strftime(DATE_FMT)

    # payment_id = params.get('payment_id')
    ids = params.get('ids')
    prices = params.get('prices')
    prices_sold = params.get('prices_sold')
    quantities = params.get('quantities')
    discount = params.get('discount', {})
    discount_fmt = discount['name'] if discount else ''

    # Cards
    cards = Card.objects.filter(pk__in=ids)
    # sort as in ids and quantities:
    sorted_cards = sorted(cards, key=lambda x: ids.index(x.pk))
    cards_data = list(zip(sorted_cards, quantities))

    # Identity.
    bookshop = users.Bookshop.objects.first()

    # Client
    client_id = params.get('client_id')
    client = None
    if client_id:
        qs = Client.objects.filter(pk=client_id)
        if qs:
            client = qs.first()

    # Title, filename
    bill_label = _("Bill")
    bookshop_name = bookshop.name if bookshop else ""
    title = "{} {} - {}".format(bill_label, bookshop_name, creation_date_fmt)
    filename = title + '.pdf'

    # File 2, with books list.
    # details_title = "{} {} - {} - list".format(bill_label, bookshop_name, creation_date_fmt)
    # details_filename = title + '.pdf'
    # details_template = "pdftemplates/pdf-bill-details.html"

    # Totals
    total = 0
    total_discounted = 0
    if not (len(ids) == len(prices_sold) == len(prices) == len(quantities)):
        log.error("Bill: post params are malformed. ids, prices, prices_sold and quantities should be of same length.")
        return
    for i, price in enumerate(prices):
        # XXX: check price type and value
        total += price * quantities[i]
        total_discounted += prices_sold[i] * quantities[i]

    default_currency = Preferences.get_default_currency()
    total_fmt = price_fmt(total, default_currency)
    total_discounted_fmt = price_fmt(total_discounted, default_currency)

    template = get_template(template)
    card = Card.objects.first()
    copies_set = card.placecopies_set.all()
    cards_qties = [(it.card, it.nb) for it in copies_set]

    # Totals

    sourceHtml = template.render({'cards_qties': cards_qties,
                                  'name': title,
                                  'total_label': _("Total before discount"),
                                  'total_fmt': total_fmt,
                                  'total_discounted_fmt': total_discounted_fmt,
                                  'total_qty': 8,
                                  'quantity_header': 18,
                                  'creation_date_label': creation_date_label,
                                  'creation_date': creation_date,
                                  'creation_date_fmt': creation_date_fmt,
                                  'discount_label': _("Discount"),
                                  'discount_fmt': discount_fmt,
                                  'due_date_label': due_date_label,
                                  'due_date': due_date,
                                  'due_date_fmt': due_date_fmt,
                                  'bookshop': bookshop,
                                  'client': client,
                                  'cards_data': cards_data,
                                  'prices_sold': prices_sold,
    })

    # template2 = get_template(details_template)
    # details_html = template2.render({'cards': cards})

    filepath = os.path.realpath(os.path.join(settings.STATIC_PDF, filename))
    fileurl = "/static/{}".format(filename)
    to_ret = {'fileurl': fileurl,
              'filename': filename,
              'status': 200}

    # details_filepath = os.path.realpath(os.path.join(settings.STATIC_PDF, details_filename))
    # details_fileurl = '/static/{}'.format(details_filename)
    # to_ret['details_fileurl'] = details_fileurl
    # to_ret['details_filename'] = details_filename

    try:
        with open(filepath, 'wb') as f:
            HTML(string=sourceHtml).write_pdf(target=f.name)

        # with open(details_filepath, 'wb') as ff:
        #     HTML(string=details_html).write_pdf(target=ff.name)

        response = JsonResponse(to_ret)
    except Exception as e:
        log.error("Error writing bill in pdf to {}: {}".format(filepath, e))
        response = JsonResponse({'status': 400})

    return response
