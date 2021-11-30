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

import json
import os

import pendulum
from django.http import JsonResponse
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import ugettext as _
from weasyprint import HTML

from abelujo import settings
from search.models import Basket
from search.models import Bill
from search.models import Card
from search.models import CardType
from search.models import Preferences
from search.models import users
from search.models.users import Client
from search.models.users import Reservation
from search.models.utils import enrich_cards_dict_for_quantity_in_command
from search.models.utils import get_logger
from search.models.utils import price_fmt
# from search.models.common import ALERT_ERROR
# from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS
# from search.models.common import ALERT_WARNING
from .utils import _is_truthy


log = get_logger()

def clients(request, **response_kwargs):
    """
    Get clients.
    """
    if request.method == 'GET':
        try:
            params = request.GET
            query = params.get('query')
            ongoing_reservations = None
            if query:
                res = Client.search(query, to_dict=True)

                # Does this client have ongoing reservations?
                check_reservations = params.get('check_reservations')
                check_reservations = _is_truthy(check_reservations)
                ongoing_reservations = None
                client_id = None
                if check_reservations and res and len(res) == 1 and \
                   res[0] and res[0]['id']:
                    client_id = res[0]['id']
                    ongoing_reservations = Reservation.client_has_reservations(client_id)
                    res[0]['ongoing_reservations'] = ongoing_reservations

                # But how many of them are in stock, ready to be sold?
                if ongoing_reservations and client_id:
                    ready_reservations = Reservation.client_has_ready_reservations(client_id)
                    res[0]['ready_reservations'] = ready_reservations

            else:
                res = Client.get_clients(to_dict=True)
            return JsonResponse({'data': res})
        except Exception as e:
            log.error(u"error getting clients: {}".format(e))
            return JsonResponse({'data': None})

def bill_from_basket():
    pass

def is_only_books(cards):
    type_book = CardType.get_book_type()
    for it in cards:
        if it.card_type != type_book:
            return False
    return True

def bill(request, *args, **response_kwargs):
    """
    Create a bill or an estimate, as a PDF file.

    From either:
    - the given products (list of ids)
      - each has an optional discount.
      - for the given client.
    - an existing bill id.
    - or a given basket id.
    - bill_or_estimate: 1 is bill, 2 is estimate.

    """
    if request.method == 'GET':
        return

    template = 'pdftemplates/pdf-bill-main.html'

    # ids, prices, quantities
    params = {}
    try:
        params = json.loads(request.body)
    except Exception as e:
        log.error('Sell bill: could not decode json body: {}\n{}. Referer: {}'.format(
            e, request.body, request.META.get('HTTP_REFERER')))

    language = params.get('language')
    if language:
        translation.activate(language)

    bill_or_estimate = params.get('bill_or_estimate', 1)  # bill
    # sellbooks = params.get('checkboxsell')  # a confirmation that we sell the books (from baskets).
    # sellbooks = is_truthy(sellbooks)

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
    ids = params.get('ids', [])
    prices = params.get('prices', [])
    prices_sold = params.get('prices_sold', [])
    quantities = params.get('quantities', [])

    # Client
    client_id = params.get('client_id')
    client = None
    if client_id:
        qs = Client.objects.filter(pk=client_id)
        if qs:
            client = qs.first()

    # Bon de commande (order form ID), to show on the PDF.
    bon_de_commande = params.get('bon_de_commande_id')

    discount = params.get('discount', {})
    if discount:
        discount_fmt = discount['name']
    elif client and client.discount:
        discount_fmt = "{} %".format(client.discount)
        discount = client.discount
    else:
        discount_fmt = '0%'

    basket_id = int(params.get('basket_id', -1))
    language = params.get('language')

    if language:
        translation.activate(language)

    cards = []
    sorted_cards = []
    cards_data = []
    if ids:
        # Cards
        cards = Card.objects.filter(pk__in=ids)
        # sort as in ids and quantities:
        sorted_cards = sorted(cards, cmp=lambda x, y: -1 if ids.index(x.pk) <= ids.index(y.pk) else 1)
        cards_data = list(zip(sorted_cards, quantities))

    elif basket_id:
        try:
            basket = Basket.objects.filter(id=basket_id).first()
            basket_copies = basket.basketcopies_set.order_by('card__title').all()
            cards = [it.card for it in basket_copies]
            sorted_cards = cards
            ids = basket_copies.values_list('card__pk', flat=True)
            prices = basket_copies.values_list('card__price', flat=True)
            # prices_sold = cards.values_list('price_sold', flat=True)  # Not Available
            quantities = basket_copies.values_list('nb', flat=True)
            cards_data = list(zip(sorted_cards, quantities))
            if client_id:
                client_id = int(client_id)
                # client_discount = 0
            # sell the books?
            # if sellbooks:
            #     ids_prices_quantities = []
            #     try:
            #         for i, card in enumerate(cards):
            #             ids_prices_quantities.append({
            #                 'id': card.id,
            #                 'price_sold': prices[i],
            #                 'quantity': quantities[i],
            #             })
            #         now = timezone.now()
            #         sell, status, alerts = Sell.sell_cards(
            #             ids_prices_quantities,
            #             date=now,
            #             client_id=client_id,
            #         )
            #     except Exception as e:
            #         to_ret = {'status': 500,
            #                   'messages': ['An error occured trying to sell the books.']}
            #         log.error("Error selling cards for a bill: {}".format(e))
            #         return JsonResponse(to_ret)
        except Exception as e:
            to_ret = {'status': 500,
                      'messages': ['An error occured generating the bill.']}
            log.error("Error generating bill from basket: {}".format(e))
            return JsonResponse(to_ret)

    # The bookshop identity.
    bookshop = None
    bookshop_name = ""
    try:
        bookshop = users.Bookshop.objects.first()
        bookshop_name = bookshop.name if bookshop else ""
    except Exception as e:
        log.warning("Error getting users.Bookshop: {}".format(e))

    # Name, filename
    bill_label = _("Bill")
    # Unique ID.
    # Even if we don't use the Bill object, create one so we get unique IDs.
    bill_object = Bill(name="{}-{}".format(bookshop_name, creation_date_fmt))
    bill_object.save()
    name = "{}-{}_{}-{}".format(bill_label, bookshop_name, bill_object.pk, creation_date_fmt)
    filename = name + '.pdf'

    # File 2, with books list.
    # details_name = "{} {} - {} - list".format(bill_label, bookshop_name, creation_date_fmt)
    # details_filename = name + '.pdf'
    # details_template = "pdftemplates/pdf-bill-details.html"

    # Totals
    total = 0
    total_discounted = 0  # when a discount is applied at the sell page.
    total_discounted_fmt = None
    total_with_client_discount = total
    if not (len(ids) == len(prices) == len(quantities)):  # prices_sold: not for basket(?)
        log.error("Bill: post params are malformed. ids, prices, prices_sold and quantities should be of same length.")
        return
    for i, price in enumerate(prices):
        # XXX: check price type and value
        if price is not None and quantities[i] is not None:
            total += price * quantities[i]
            if prices_sold:
                total_discounted += prices_sold[i] * quantities[i]

    default_currency = Preferences.get_default_currency()
    vat_book = Preferences.get_vat_book()
    total_fmt = price_fmt(total, default_currency)
    if client and client.discount:
        total_with_client_discount = total - total * client.discount / 100.0
        total_discounted = total_with_client_discount

    # if not prices_sold:
        # total_discounted = total_with_client_discount

    if not total_discounted:
        total_discounted = total
    total_discounted_fmt = price_fmt(total_discounted, default_currency)

    template = get_template(template)

    # Compute the VAT from the discounted price (after for example 9% discount to an official client).
    total_vat = 0
    # easy method when everything is books.
    if is_only_books(cards):
        # total_vat = Card.get_vat_for_cards(cards)
        tax = Preferences.get_vat_book()
        total_vat = total_discounted - total_discounted / (1 + tax / 100)
    # mixed method when there are not only books objects.
    # thing is, does it sum up correctly ?
    else:
        total_vat = Card.get_vat_for_mixed_cards(cards)
        # XXX: and quantity ?? in cards_data

    total_vat_fmt = price_fmt(total_vat, default_currency)

    # Document title.
    if bill_or_estimate in [1, "1"]:
        document_type = _("Bill")
    elif bill_or_estimate in [2, "2"]:
        document_type = _("Estimate")
    else:
        document_type = _("Bill")

    document_title = "{} {}-{}".format(document_type,
                                       bill_object.pk,
                                       pendulum.now().strftime('%Y%m%d'))

    # Totals

    sourceHtml = template.render({'name': name,
                                  'document_title': document_title,
                                  'bon_de_commande': bon_de_commande,
                                  'vat_book': vat_book,
                                  'total_vat': total_vat,
                                  'total_vat_fmt': total_vat_fmt,
                                  'total_label': _("Total before discount"),
                                  'total_fmt': total_fmt,
                                  'total_discounted_fmt': total_discounted_fmt,
                                  'total_with_client_discount': total_with_client_discount,
                                  'total_with_client_discount_fmt': price_fmt(total_with_client_discount, default_currency),
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

def card_reservations(request, pk, **kw):
    """
    Return the list of clients that reserved this card.
    """
    to_ret = {
        'data': {},
        'status': ALERT_SUCCESS,
        'alerts': [],
    }
    if request.method == 'POST':
        # params = kw.copy()
        # client_id = params.get('client_id')
        reservations = Reservation.get_card_reservations(pk, to_dict=True)
        to_ret['data'] = reservations
        return JsonResponse(to_ret)

def reserved_cards(request, **kw):
    """
    Return the list of cards that this client reserved.

    Used in the sell to import the cards a client reserved (and the
    ones that are available in the stock right now, quantity > 0).

    The returned card objects must be augmented for the sell:
    price_orig, quantity to sell, quantity in the command basket…

    Return: JsonResponse with object status, data, alerts.
    """
    to_ret = {
        'data': {},
        'status': ALERT_SUCCESS,
        'alerts': [],
    }
    params = request.GET.copy()
    if request.method == 'GET':
        client_id = None
        if params:
            client_id = params.get('client_id')
        qs = Reservation.objects.exclude(card__isnull=True) \
                            .exclude(client__isnull=True) \
                            .exclude(card_id__isnull=True) \
                            .exclude(archived=True) \
                            .exclude(is_ready=False)
        if client_id:
            qs = qs.filter(client=client_id)

        # Only the ones with quantity > 0 in stock?
        in_stock = params.get('in_stock')
        in_stock = _is_truthy(in_stock)
        if in_stock:
            qs = qs.filter(card__quantity__gte=0)

        cards = [it.card for it in qs.all()]
        res = [it.to_dict() for it in cards]  # PERF: slow with hundreds.

        # Enrich result with quantity in the command list.
        auto_command = Basket.auto_command_basket()
        ids = [it['id'] for it in res]
        basket_copies = auto_command.basketcopies_set.filter(card__id__in=ids).select_related()
        res = enrich_cards_dict_for_quantity_in_command(res, basket_copies)
        for card in res:
            card['quantity_sell'] = 1   # TODO: set the right quantity to sell
            card['price_sold'] = card['price']
            card['price_orig'] = card['price']

        to_ret['data'] = res
        return JsonResponse(to_ret)


def all_reservations(request, *args, **kw):
    """
    Return all reservations.
    If client_id is given, filter by this client (return her ongoing reservations).
    """
    # currently for CLI usage.
    params = request.GET.copy()
    if params:
        client_id = params.get('client_id')
    qs = Reservation.objects.exclude(card__isnull=True) \
                            .exclude(client__isnull=True) \
                            .exclude(card_id__isnull=True) \
                            .exclude(archived=True) \
                            .exclude(is_ready=False)
    if client_id:
        qs.filter(client=client_id)
    res = [it.to_dict() for it in qs.all()]
    return JsonResponse(res, safe=False)
