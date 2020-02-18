#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2019 The Abelujo Developers
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

import httplib
import json
import locale
import logging
import os

from django_q.tasks import async

from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _

from drfserializers import PreferencesSerializer
from models import Alert
from models import Author
from models import Basket
from models import Card
from models import CardType
from models import Command
from models import Deposit
from models import Distributor
from models import Inventory
from models import Place
from models import Preferences
from models import Publisher
from models import Restocking
from models import Sell
from models import Shelf
from models import Stats
from search.datasources.bookshops.frFR.librairiedeparis.librairiedeparisScraper import \
    reviews as frenchreviews
from search.models import history
from search.models import do_inventory_apply
from search.models import do_command_apply
from search.models.common import ALERT_ERROR
from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING
from search.models.utils import Messages
from search.models.utils import get_logger
from search.models.utils import get_page_count
from search.models.utils import page_start_index
from search.models.utils import price_fmt
from search.views_utils import get_datasource_from_lang
from search.views_utils import search_on_data_source

from .utils import ids_qties_to_pairs
from .utils import is_invalid
from .utils import is_isbn, split_query, isbns_from_query
from .utils import list_from_coma_separated_ints
from .utils import list_to_pairs
from .utils import _is_truthy

# Improve sorting.
locale.setlocale(locale.LC_ALL, "")

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = get_logger()

# To search objects and send them as json:
# - call the search method of the model
# - serialize the result to a list and to json manually, not with django's serializer.
# With serializer, the access to the dict properties is deeper (inside object.fields),
# so it makes it not straightforward with js widgets, like ui-select.

# This file needs more uniformisation. Some methods return a dict with
# 'data', 'alerts' and 'msgs', some just a list. Everything should be
# in a dict (good practive influenced by the JsonResponse that likes a
# dict better).


#: id of the basket of automatic commands.
AUTO_COMMAND_ID = 1

PAGE_SIZE = 25


def get_user_info(request, **response_kwargs):
    """
    """
    data = {'data': {'username': request.user.username, }}
    return JsonResponse(data)

def preferences(request, **response_kwargs):
    """
    Get or set preferences.
    """
    ret = {}

    if request.method == 'GET':
        try:
            pref = Preferences.prefs()
        except Exception as e:
            log.error('Error while getting the Preferences: {}'.format(e))
            return JsonResponse({"status": ALERT_ERROR,
                                 'data': ret})

        ret['data'] = PreferencesSerializer(pref).data
        ret['all_preferences'] = pref.to_dict()
        ret['status'] = ALERT_SUCCESS
        return JsonResponse(ret)


def datasource_search(request, **response_kwargs):
    """Search for new cards on external sources.

    If query is an ISBN, search into our DB first.

    The query can be a list of ISBNs (separated by comas or spaces).
    WARNING: we can reach the limit of the GET parameters (aronud 2048 chars).

    Parameters:
    - query (str)
    - datasource (str): librairiedeparis, ...
    - page [optional] defaults to 1. str or int.
    - language: the user language on the page (fr, en), to keep urls consistent.

    - return: a JsonResponse with data, alerts, and status.
    """
    res = []
    traces = []
    query = request.GET.get('query')
    if not query:
        log.debug("No search query given.")
        return JsonResponse({'error': 'no search query given.'})

    language = request.GET.get('language')
    if language:
        translation.activate(language)

    isbn_list = None  # when the user queries a list of ISBNs at once.
    isbn_list_search_complete = False  # True when we find all of them.

    is_isbn_query = is_isbn(query)
    if is_isbn_query:
        res = Card.objects.filter(isbn=query).first()
        if res:
            res = [res.to_dict()]
    else:
        # XXX: This works with comas in the user input list of ISBNs, not semi-colons.
        # JS side seems to truncate the input up to the first semicolon.
        isbn_list = isbns_from_query(query)
        if isbn_list:
            res = Card.objects.filter(isbn__in=isbn_list)
            if res:
                res = [it.to_dict() for it in res]
            if len(res) == len(isbn_list):
                isbn_list_search_complete = True

    if isbn_list and not isbn_list_search_complete:
        # TODO: search remaining ISBNs on the datasource.
        logging.error("Not implemented: searching many ISBNs at once on the datasource.")

    default_datasource = 'librairiedeparis'
    if os.getenv('DEFAULT_DATASOURCE'):
        default_datasource = os.getenv('DEFAULT_DATASOURCE')
    if (not is_isbn_query and not isbn_list) or not res:
        datasource = request.GET.get('datasource', default_datasource)
        page = request.GET.get('page', 1)
        if (not is_isbn_query) and datasource == 'dilicom' and os.getenv('DILICOM_USER'):
            # We can not make text searches on Dilicom :/ Only ISBN queries.
            # So we make keyword searches with the right datasource.
            datasource = default_datasource
        res, traces = search_on_data_source(datasource, query, PAGE=page)

    data = {"data": res,
            "alerts": traces,
            "message": None,
            "message_status": None,
            "status": 200, }

    if isbn_list and len(isbn_list) > 1:
        data['message'] = _("You asked for {} ISBNs. {} found.".format(len(isbn_list), len(res)))
        if isbn_list_search_complete:
            data['message_status'] = ALERT_SUCCESS
        else:
            data['message_status'] = ALERT_WARNING

    return JsonResponse(data)


def cards(request, **response_kwargs):
    """Search for cards in the stock with the given query, or return all of them (with
    a limit).

    Don't return cards added in the DB but not bought.

    If we don't find anything in our db and we have an isbn as input,
    search the title on the internet. To have added a card in stock or
    not should not be a limitation when we manipulate books (doing the
    inventory, lists, etc).

    """
    data = []
    query = request.GET.get("query", "")
    query = split_query(query)
    language = request.GET.get("language")
    distributor = request.GET.get("distributor")
    distributor_id = request.GET.get("distributor_id")
    card_type_id = request.GET.get("card_type_id")
    publisher_id = request.GET.get("publisher_id")
    place_id = request.GET.get("place_id")
    deposit_id = request.GET.get("deposit_id")
    shelf_id = request.GET.get("shelf_id")
    order_by = request.GET.get("order_by")
    # bought = request.GET.get("in_stock")
    quantity_choice = request.GET.get("quantity_choice")
    price_choice = request.GET.get("price_choice")

    # The quantity of a card is costly. It was a bottleneck. Avoid
    # this calculation if possible.
    with_quantity = request.GET.get("with_quantity", True)
    with_quantity = _is_truthy(with_quantity)

    # pagination
    page = request.GET.get("page", 1)
    page = to_int(page)
    page_size = request.GET.get("page_size", PAGE_SIZE)
    page_size = to_int(page_size)

    # Set the language (for url prefix, error messages, etc)
    if language:
        translation.activate(language)

    data, meta = Card.search(query, to_list=True,
                             distributor=distributor,
                             distributor_id=distributor_id,
                             publisher_id=publisher_id,
                             card_type_id=card_type_id,
                             place_id=place_id,
                             deposit_id=deposit_id,
                             shelf_id=shelf_id,
                             order_by=order_by,
                             in_deposits=True,
                             with_quantity=with_quantity,
                             quantity_choice=quantity_choice,
                             price_choice=price_choice,
                             page=page,
                             page_size=page_size)
    # XXX: :return the msgs.
    # msgs = Messages()
    # msgs = meta.get('msgs')

    lang = request.GET.get("lang")
    # Search our stock on a keyword search, but search also the web on an isbn search,
    # if we don't find it in stock.
    if not data:
        isbn_in_query = filter(is_isbn, query)
        if isbn_in_query:
            datasource = get_datasource_from_lang(lang)
            data, traces = search_on_data_source(datasource, isbn_in_query[0])

            # add the result into our db
            if data:
                try:
                    # We need to wait for it to get its id.
                    card, _ = Card.from_dict(data[0], to_list=True)
                    data = [card]
                except Exception as e:
                    log.warning(u"Error while adding card from isbn search in db: {}".format(e))

    to_ret = {
        'cards': data,
        'meta': meta,
    }
    return JsonResponse(to_ret)

def card(request, **kwargs):
    """Get a card by id.
    """
    ret = {"data": []}
    msgs = Messages()
    if request.method == 'GET':
        pk = kwargs.pop('pk')
        try:
            card = Card.objects.get(id=pk)
            card = card.to_list()
            ret['data'] = card
            ret['alerts'] = msgs

        except Exception as e:
            msg = _(u"couldn't find card of id {}: {}".format(pk, e))
            log.warning(msg)
            msgs.add_error(msg)

    ret["alerts"] = msgs.msgs
    return JsonResponse(ret)

def card_create(request, **response_kwargs):
    """Create or edit a card with either request params or json in request.body

    Return: a tuple (card_id, status, alerts)
    """
    msgs = {}
    if request.method == "POST":
        params = request.POST.copy()  # either here or in request.body
        status = httplib.OK
        alerts = []

        isbn = params.get('isbn')
        shelf = params.get('shelf_id')
        threshold = to_int(params.get('threshold'))
        # Mixed style from client (to fix).
        if params:
            card_dict = {
                "id": params.get('card_id'),  # create... or edit.
                "title": params.get('title'),
                "price": params.get('price'),
                "card_type": params.get('type'),
                "authors": [Author.objects.get(id=it) for it in list_from_coma_separated_ints(params.get('authors'))],
                "isbn": isbn,
                "has_isbn": True if params.get("has_isbn") == "true" else False,
                "details_url": params.get("details_url"),
                "year": params.get("year_published"),
            }
            if shelf:
                card_dict['shelf_id'] = shelf
            if params.get('distributor'):
                card_dict['distributor'] = params.get('distributor')
            if params.get('publishers'):
                card_dict['publishers_ids'] = list_from_coma_separated_ints(params.get('publishers'))
            if threshold is not None:
                card_dict['threshold'] = threshold

        # we got the card dict
        else:
            params = json.loads(request.body)
            card_dict = params.get('card')
            card_dict['has_isbn'] = True if card_dict.get('isbn') else False

        #TODO: call postSearch

        try:
            card_obj, msg = Card.from_dict(card_dict)
            alerts.append({"level": ALERT_SUCCESS,
                           "message": msg})

            msgs = {"status": status, "alerts": alerts, "card_id": card_obj.id}
            if card_obj:
                return JsonResponse(msgs)

        except Exception as e:
            log.error(u"Error adding a card: {}".format(e))
            alerts.append({"level": ALERT_ERROR,
                           "message": _("Woops, we can not create this card. This is a bug.")})

        return JsonResponse(msgs)

    else:
        log.error("creating a card should be done with POST.")

def card_add(request, **response_kwargs):
    """Add the given card to places (=buy it), deposits and baskets.

    - card_id
    - places_ids_qties:
    """
    if request.method == "POST":
        params = request.POST.copy()
        status = httplib.OK
        # alerts = []
        # data = []

        pk = response_kwargs.pop("pk")
        card_obj = Card.objects.get(id=pk)

        distributor_id = params.get('distributor_id')
        shelf_id = params.get("shelf_id")
        deposits_ids_qties = params.get('deposits_ids_qties')
        baskets_ids_qties = params.get('baskets_ids_qties')
        places_ids_qties = params.get('places_ids_qties')
        threshold = to_int(params.get('threshold'))

        # list of tuples (id, qty to add)
        # those params are ints separated by comas.
        d_tups = list_to_pairs(list_from_coma_separated_ints(deposits_ids_qties))
        b_tups = list_to_pairs(list_from_coma_separated_ints(baskets_ids_qties))
        p_tups = list_to_pairs(list_from_coma_separated_ints(places_ids_qties))

        to_save = False
        for id, qty in d_tups:
            if qty:
                obj = Deposit.objects.get(id=id)
                obj.add_copy(card_obj, nb=qty)

        for id, qty in b_tups:
            if qty:
                obj = Basket.objects.get(id=id)
                obj.add_copy(card_obj, nb=qty)

        for id, qty in p_tups:
            if qty:
                obj = Place.objects.get(id=id)
                obj.add_copy(card_obj, nb=qty)

        if shelf_id:
            cat = Shelf.objects.get(id=shelf_id)
            card_obj.shelf = cat
            to_save = True

        if distributor_id and distributor_id not in [-1, 0, '0', u'0',
                                                     'undefined', u'undefined']:
            if card_obj.distributor_id != distributor_id:
                distributor = Distributor.objects.get(id=distributor_id)
                card_obj.distributor = distributor
                to_save = True

        if threshold is not None:
            if threshold != card_obj.threshold:
                card_obj.threshold = threshold
                to_save = True

        if to_save:
            card_obj.save()

        return JsonResponse(status, safe=False)

def cardtype(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = CardType.search(query)
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

def card_reviews(request, pk, **response_kwargs):
    """Get some reviews on other websites.
    """
    if request.method == 'GET':
        if pk:
            # if a french card
            card_obj = get_object_or_404(Card, id=pk)
            card = card_obj.to_list()
            revs = frenchreviews(card)
            return JsonResponse(revs, safe=False)

def cards_set_supplier(request, **response_kwargs):
    """
    Set the supplier of many cards.

    - params: cards_ids: list of ids.
    """
    if request.method == 'GET':
        return JsonResponse({"msg": "not implemented"})
    elif request.method == 'POST':
        status = httplib.OK

        params = request.POST.copy()
        cards_ids = params.get('cards_ids')
        request.session['set_supplier_cards_ids'] = cards_ids  # coma-separated ids
        return JsonResponse({
            'status': status,
            'url': "/stock/set_supplier/",
        })

def shelfs(request, **response_kwargs):
    # Note: for easier search, replace and auto-generation, we choose
    # to pluralize wrongly.
    if request.method == 'GET':
        data = Shelf.objects.order_by("name").all()
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

    else:
        return HttpResponse(json.dumps({"404"}), **response_kwargs)

def authors(request, **response_kwargs):
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        data = Author.search(params["query"])
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

def distributors(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        if query:
            data = Distributor.search(query, to_list=True)
        else:
            data = Distributor.objects.all()
            data = [it.to_list() for it in data]
        return JsonResponse(data, safe=False)

def get_distributor(request, pk):
    if request.method == "GET":
        to_ret = {
            'data': {},
            'status': ALERT_SUCCESS,
        }
        try:
            dist = Distributor.objects.get(id=pk)
        except ObjectDoesNotExist as e:
            log.warning(e)
            return JsonResponse({})

        to_ret['data'] = dist.to_dict()
        return JsonResponse(to_ret)

def publishers(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = Publisher.search(query)
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

def getSellDict(lst):
    """We have a list of int and floats representing the card ids, their
    price, their quantity. They are ordered: ids first, then prices,
    then quantities. We must return a list of dicts with "id",
    "price_sold", "quantity".

    >>> [39, 1, 10, 9.5, 1, 1] # means: card of id 39, sold 10, 1 exemplary
    [{"id": 39, "price_sold": 10, "quantity": 1}, {"id":1, etc

    (Note: this shitty stuff comes from angular and django pb of encoding parameters. See services.js)
    """
    to_sell = []
    for i in xrange(len(lst) / 3):
        sub = lst[i::len(lst) / 3]
        to_sell.append({"id": sub[0],
                        "price_sold": sub[1],
                        "quantity": sub[2]})
    return to_sell


def deposits(request, **response_kwargs):
    """
    returns: a json response: status: 200, messages: a list of messages where each message is a dict
    {level: int, messages: str}
    """
    msgs = Messages()

    if request.method == "POST":
        params = request.POST.copy()
        if params.get("distributor") == "null":
            pass  # return validation error

        try:
            cards_id = list_from_coma_separated_ints(params.get("cards_id"))
            cards_qty = list_from_coma_separated_ints(params.get("cards_qty"))
            if cards_qty and len(cards_qty) != len(cards_id):
                log.info("Creating deposit: the length of card ids and their qties is different.")

            cards_obj, card_msgs = Card.get_from_id_list(cards_id)

            distributor_obj = None
            if not params.get('deposit_type') == 'publisher':
                distributor_obj = Distributor.objects.filter(name=params.get("distributor"))

                if not distributor_obj:
                    return HttpResponse(json.dumps({
                        "data": {},
                        "messages": [{'level': ALERT_WARNING,
                                      'message': _(u'Please provide a supplier'), }]
                    }))
                distributor_obj = distributor_obj[0]

            deposit_dict = {
                "name": params.get("name"),
                "distributor": distributor_obj,
                "copies": cards_obj,
                "quantities": cards_qty,
                "deposit_type": params.get("deposit_type"),
                "minimal_nb_copies": params.get("minimal_nb_copies"),
                "auto_command": params.get("auto_command"),
                "due_date": params.get("due_date"),
                "dest_place": params.get("dest_place"),
            }

            depo, msgs = Deposit.from_dict(deposit_dict)

        except Exception as e:
            log.error(u"api/deposit error: {}".format(e))
            msgs["status"] = httplib.INTERNAL_SERVER_ERROR
            msgs["messages"].append({"level": ALERT_ERROR,
                                     "message": "internal error, sorry !"})

            return HttpResponse(json.dumps(msgs), **response_kwargs)

        to_ret = {
            'status': msgs.status,
            'alerts': msgs.to_alerts(),
        }
        return JsonResponse(to_ret)

    # GET
    else:
        depos = Deposit.objects.all()
        depos_list = [it.to_list() for it in depos]
        res = {"data": depos_list,
               "msgs": msgs.to_alerts(),
               "status": httplib.OK,
        }
        return JsonResponse(res)

def sell(request, **response_kwargs):
    """
    - GET: get one or query many.
      - query args: date_min, date_min, distributor_id, card_id

    - POST: create a new sell.
    requested data: a list of dictionnaries with "id", "price_sold",
    "quantity". See models.Sell.

    messages: we need, for the client, a list of dictionnaries:
       - level: is either "success", "danger" or "",
       - message: is a str of the actual message to display.
    """
    alerts = []  # list of dicts with "level" and "message".
    success_msg = [{"level": "success",
                    "message": _("Sell successfull.")}]

    if request.method == "POST":
        params = request.POST.copy()

        language = params.get('language')
        # Translate user messages returned to the UI.
        if language:
            translation.activate(language)

        #TODO: data validation
        if params.get("to_sell") == "null":
            pass  # TODO: return and display an error.
        to_sell = list_from_coma_separated_ints(params.get("to_sell"))
        to_sell = getSellDict(to_sell)
        date = params.get("date")
        deposit_id = int(params.get("deposit_id", 0))
        place_id = int(params.get("place_id", 0))
        payment_id = int(params.get("payment_id", 0))

        # Sell from a deposit, then normal sell.
        if deposit_id and deposit_id not in [0, "0"]:
            # 0 is the default client side but doesn't exist.
            try:
                deposit_obj = Deposit.objects.get(id=deposit_id)  # noqa: F841
            except ObjectDoesNotExist:
                log.error(u"Couldn't get deposit of id {}.".format(deposit_id))
            except Exception as e:
                log.error(u"Error while getting deposit of id {}: {}".format(deposit_id, e))

        # Sell from a place.
        try:
            sell, status, alerts = Sell.sell_cards(to_sell, date=date,
                                                   place_id=place_id,
                                                   payment=payment_id,
                                                   deposit_id=deposit_id)

        except Exception as e:
            log.error(u"api/sell error: {}".format(e))
            alerts.append({"level": "error",
                           "message": e})
            return JsonResponse(alerts, safe=False)

        if not alerts:
            alerts = success_msg
        to_ret = {"status": status,
                  "alerts": alerts}
        return JsonResponse(to_ret)

    elif request.method == "GET":
        params = request.GET.copy()
        sells = Sell.search(to_list=True, **params.dict())
        status = ALERT_SUCCESS
        ret = {
            'data': sells['data'],
            'status': status,
            'alerts': [],
        }
        return JsonResponse(ret)

def sell_undo(request, pk, **response_kwargs):
    """
    Undo a whole sell with its many cards.

    - pk: Sell id (we undo the sell and all its soldcards).

    Re-buy the card.
    """
    msgs = []  # returned by undo()
    status = True
    if request.method == 'POST':
        if pk:
            # We undo only 1 card, not the entire sell (grouping many cards).
            # status, msgs = SoldCards.undo(pk)
            # We undo the entire sell.
            status, msgs = Sell.sell_undo(pk)
        else:
            msgs.append({"message": u"Internal error: we didn't receive which sell to cancel.",
                         "status": ALERT_ERROR})

        to_ret = {"status": status,
                  "alerts": msgs,
        }
        return JsonResponse(to_ret)


def restocking_validate(request):
    """
    Validate the restocking list, with ids given as POST parameters if any.
    """
    msgs = Messages()
    status = True
    to_ret = {'status': status, 'alerts': []}
    if request.method == 'POST':
        params = json.loads(request.body)
        if params:
            ids = params.get('ids')
            qties = params.get('qties')
            assert len(ids) == len(qties)
            if ids and qties:
                cards = Card.objects.filter(id__in=ids)
                Restocking.validate(cards=cards, quantities=qties)
                msgs.add_success(_("Cards moved with success"))

    to_ret['alerts'] = msgs.msgs
    return JsonResponse(to_ret)

def restocking_remove(request, pk):
    """
    Remove the given card (id, string) to the current restocking list.
    """
    msgs = Messages()
    status = True
    to_ret = {'status': status, 'alerts': []}
    if request.method == 'POST':
        try:
            Restocking.remove_card_id(pk)
        except Exception as e:
            msgs.add_error(_("An error happened. We were notified about it."))
            logging.error(u"Error on removing the card {} from restocking list: {}".format(pk, e))
        msgs.add_success(_("The card was removed with success."))
        to_ret['alerts'] = msgs.msgs
        return JsonResponse(to_ret)


TO_RET = {"status": ALERT_SUCCESS,
          "alerts": [],
          "data": []}

def history_sells(request, **response_kwargs):
    """deprecated: use simply 'sell' above.

    - params: - month= int[1,12], the current month by default.
              - page
    """
    alerts = []
    status = ALERT_SUCCESS
    if request.method == "GET":
        params = request.GET.copy()
        # distributor_id = params.get('distributor_id')
        page = params.get('page', 1)
        if page is not None:
            page = int(page)
        page_size = params.get('page_size')
        if page_size is not None:
            page_size = int(page_size)
        sortby = params.get('sortby')
        sortorder = params.get('sortorder', 0)
        month = params.get('month')
        if not month and not is_invalid(month):
            month = timezone.now().month
        year = params.get('year')
        if not year and not is_invalid(year):
            year = timezone.now().year

        try:
            hist = Sell.search(month=month,
                               year=year,
                               page=page, page_size=page_size,
                               sortby=sortby, sortorder=sortorder,
                               to_list=True)
        except Exception as e:
            log.error(u"api/history error: {}".format(e))
            return HttpResponse(json.dumps(alerts), **response_kwargs)

        to_ret = {"status": status,
                  "alerts": alerts,
                  "data": hist}
        return JsonResponse(to_ret)

def history_entries(request, **response_kwargs):
    if request.method == "GET":
        # params = request.GET.copy()
        entries, status, alerts = history.Entry.history()
        to_ret = TO_RET
        to_ret['data'] = entries
        return JsonResponse(to_ret)


def auto_command_total(request, **response_kwargs):
    total = -1
    if request.method == "GET":
        # params = request.GET.copy()
        try:
            total = Basket.auto_command_nb()
        except Exception:
            pass
    return JsonResponse(total, safe=False)


def auto_command_basket(request, action="", **response_kwargs):
    """Get the copies of the auto command basket.

    Don't return all copies that don't have a distributor, use
    pagination. They are the limiting factor so far.

    When dist_id is -1, return the cards in this basket that don't
    have a distributor (with pagination).

    Actions:
    - add

    """
    msgs = []
    to_ret = {}
    page = 1
    page_size = PAGE_SIZE
    num_pages = 0
    # meta = {}

    try:
        basket = Basket.objects.get(id=AUTO_COMMAND_ID)
    except Exception as e:
        log.error(u"Error while getting autocommand basket: {}".format(e))
        msgs.append(e.message)
        to_ret['status'] = False
        return JsonResponse(to_ret)  # also return error message.

    if request.method == 'GET':
        if to_int(request.GET.get('dist_id')) == -1:
            # Cards with no distributor.
            copies_no_dist = basket.basketcopies_set.filter(card__distributor__isnull=True)

            page = to_int(request.GET.get('page', 1))
            page_size = to_int(request.GET.get('page_size', page_size))
            copies_no_dist = copies_no_dist[page_start_index(page): page * page_size]
            copies_no_dist = [it.to_dict() for it in copies_no_dist]
            to_ret = {
                'copies_no_dist': copies_no_dist,
            }
            return JsonResponse(to_ret)

        page = request.GET.get('page', page)
        page_size = request.GET.get('page_size', page_size)
        page_size = to_int(page_size)

        # The most probably largest set of copies is the one with no distributor.
        # We do pagination with this one only for now.
        copies = basket.basketcopies_set.filter(card__distributor__isnull=False)\
                                        .order_by("card__title").all()
        nb_results = copies.count()

        copies_no_dist = basket.basketcopies_set.filter(card__distributor__isnull=True)
        nb_copies_no_dist = copies_no_dist.count()
        nb_results = nb_results + nb_copies_no_dist

        num_pages = get_page_count(copies_no_dist)  # better with Django's paginator
        to_ret['page_count'] = num_pages
        to_ret['data_length'] = nb_results
        if page:
            page = int(page)
            copies_no_dist = copies_no_dist[page_start_index(page): page * page_size]

        # ret = [it.to_dict() for it in copies]
        ret = [it.to_dict() for it in copies[:3]]
        to_ret['data'] = ret
        no_dist = [it.to_dict() for it in copies_no_dist]
        to_ret['copies_no_dist'] = no_dist
        to_ret['basket_name'] = basket.name
        to_ret['meta'] = {
            'page': page,
            'page_size': page_size,
            'nb_results': nb_results,
            'num_pages': num_pages,
            'nb_copies_no_dist': nb_copies_no_dist,
        }

        return JsonResponse(to_ret)

def basket(request, pk, action="", card_id="", **kwargs):
    """
    Get the list of cards or act on the given basket.

    For the basket of auto_commands, return data in a special format.

    On POST:
    - add: add many cards,
    - remove: remove card(s),
    - update: one card
    - to_deposit: transform to a deposit. args: deposit_id, name

    pk: the basket id.

    Example url: /api/baskets/1/add/ with query parameters "card_ids": "10,2,11,1"

    - return: a list of messages.
    """
    data = []
    msgs = []
    status = True
    page = 1
    page_size = PAGE_SIZE
    num_pages = 0
    nb_results = 0
    to_ret = {"status": True,
              "data": data,
              "meta": {},
              "msgs": msgs}

    try:
        basket = Basket.objects.get(id=pk)

    except Exception as e:
        log.info(u"Couldn't get basket of id {}: {}".format(pk, e))
        msgs.append(e.message)
        to_ret['status'] = False
        return JsonResponse(to_ret)  # xxx: also return error message.

    if request.method == "GET":
        if to_int(pk) == AUTO_COMMAND_ID:
            return auto_command_basket(request, action=action, **kwargs)

        page = request.GET.get('page', page)
        page_size = request.GET.get('page_size', page_size)
        page_size = to_int(page_size)
        copies = basket.basketcopies_set.order_by("card__title").all()
        # We must re-sort to get downcase and accents right.
        copies = sorted(copies, cmp=locale.strcoll, key=lambda it: it.card.title)
        nb_results = len(copies)
        to_ret['data_length'] = nb_results
        num_pages = get_page_count(copies, size=page_size)  # better with Django's paginator
        to_ret['page_count'] = num_pages
        if page:
            page = int(page)
            # see utils.get_page_count
            copies = copies[page_start_index(page): page * page_size]
        ret = [it.to_dict() for it in copies]
        to_ret['data'] = ret
        to_ret['basket_name'] = basket.name
        to_ret['meta'] = {
            'page': page,
            'page_size': page_size,
            'nb_results': nb_results,
            'num_pages': num_pages,
            'default_currency': Preferences.get_default_currency(),
        }
        return JsonResponse(to_ret, safe=False)

    elif request.method == 'POST':
        # json request
        req = {}
        body = request.body  # for test
        if request.POST.get('card_ids'):
            req = request.POST.copy()
        elif body:
            # 'remove' doesn't use this.
            req = json.loads(body)

        # Add cards from ids (from the Collection view or from a Basket).
        if action and action == "add":
            msgs = []
            if req.get('card_ids'):
                # Add the given ids (from the Collection).
                ids = req.get('card_ids')
                id_list = list_from_coma_separated_ints(ids)
                try:
                    msg = basket.add_copies(id_list)
                except ObjectDoesNotExist as e:
                    log.error(u"Error while adding copies {} to basket {}: {}".format(id_list, pk, e))

            elif req.get('basket_id'):
                # No card ids: use all the basket copies (from another basket).

                # Basket of origin. It may associate a distributor.
                basket_id = req.get('basket_id')
                try:
                    basket_orig = Basket.objects.get(id=basket_id)
                except ObjectDoesNotExist as e:
                    log.error(u"Error on command: {}.".format(e))
                    msg = u"Error: the list of id {} does not exist.".format(basket_id)

                if basket_orig.distributor is not None:
                    try:
                        # Set the cards' distributor, if defined in the basket.
                        basket_orig.distributor.set_distributor(basket=basket_orig)
                    except Exception as e:
                        log.error(u"Error trying to set the distributor of the cards, for basket {}: {}".
                                format(basket.id, e))
                        return  # xxx error message

                try:
                    msg = basket.add_cards(basket_orig.copies.all())
                    msgs.append(msg)
                except Exception as e:
                    log.error(u'Error while adding cards of basket {} to basket {}: {}'.
                            format(basket_id, pk, e))

        # Add cards from card dicts, not in db yet (from the Searchresults view or a Vue Basket).
        if action and action == "add" and req.get('cards'):
            # req: dict where keys are an index (useless, js dependency) and values, the card dicts.
            # From a Vue Basket: we get usual dicts.
            cards = req.get('cards')
            if type(cards) != list:
                cards = req['cards'].values()
            # Create the new cards in the DB.
            ids = []
            for card in cards:
                try:
                    exists = False
                    if card.get('isbn'):
                        exists = Card.objects.filter(isbn=card.get('isbn')).first()
                    if not exists:
                        card_obj, msgs = Card.from_dict(card)
                        ids.append(card_obj.id)
                    else:
                        ids.append(exists.id)

                except Exception as e:
                    log.error(u"Error while creating card from baskets: {}".format(e))

            # Add them to the basket.
            try:
                msg = basket.add_copies(ids)
            except Exception:
                log.error("Error while adding copies {} to basket {}: {}".format(ids, pk, e))

        # Remove a card
        elif action and action == "remove" and card_id:
            status, msgs = basket.remove_copy(card_id)

        # Update one card
        elif action and action == "update" and req.get('id_qty'):
            card_id, qty = list_from_coma_separated_ints(req.get('id_qty'))
            try:
                basket_qty = basket.basketcopies_set.get(card__id=card_id)
                basket_qty.nb = qty
                basket_qty.save()
            except Exception as e:
                log.error(u"Error while setting the card qty in list {}: {}".format(basket.id, e))
                msgs.append({'level': "error",
                             'message': _("We couldn't set the quantity of the card.")})

        # Transform the basket to a deposit
        elif action and action == "to_deposit":
            distributor_id = req.get('distributor_id')
            name = req.get('name')
            if not distributor_id:
                msgs.append({'level': 'error',
                             'message': "please give the distributor_id as a parameter"})

            if not name:
                msgs.append({'level': 'error',
                             'message': "please give the name as parameter"})

            try:
                basket.to_deposit(distributor=distributor_id, name=name)
            except Exception as e:
                log.error('Error while transforming basket {} to deposit: {}'.format(basket.id, e))
                msgs.append({'level': 'error',
                             'message': _("We couldn't set this list as a deposit. Sorry !")})

    to_ret['status'] = status
    to_ret['data'] = data
    to_ret['msgs'] = msgs
    return JsonResponse(to_ret)

def baskets(request, **kwargs):
    """Get the list of basket names. If a pk is given as argument, return
    the list of its copies.
    """
    if request.method == "GET":
        # params = request.GET.copy()
        msgs = []
        nb_results = None
        meta = {}
        status = httplib.OK
        if kwargs.get('pk'):
            pk = kwargs.pop('pk')
            page = request.GET.get('page', 1)
            page = to_int(page)
            page_size = request.GET.get('page_size', PAGE_SIZE)
            try:
                data = Basket.objects.get(id=int(pk))
                nb_results = data.count()
                data = data.copies.all()
            except Exception as e:
                log.error(e)

            paginator = Paginator(data, page_size)
            if data is not None:
                try:
                    data = paginator.page(page)
                except EmptyPage:
                    data = paginator.page(paginator.num_pages)
                finally:
                    data = data.object_list
            else:
                data = paginator.object_list

            meta = {
                'page': page,
                'page_size': page_size,
                'num_pages': paginator.num_pages,
                'nb_results': nb_results,
            }

        else:
            try:
                data = Basket.objects.exclude(archived=True).all()
            except Exception as e:
                log.error(e)
                status = httplib.INTERNAL_SERVER_ERROR
                msgs.append({"level": "error",
                             "msg": "There was an error. We can not load the baskets, sorry."
                })

        data = [it.to_dict() for it in data]
        # we can't mix serializers and a custom to_ret
        to_ret = {"status": status,
                  "alerts": msgs,
                  "data": data,
                  "meta": meta, }
        return JsonResponse(to_ret)

def baskets_create(request, **response_kwargs):
    """Create a new basket.
    Return its id.
    """
    if request.method == "GET":
        return JsonResponse({'data': "Use a POST request"})

    if request.method == "POST":
        # When the client asks to encode params in url parameters: POST.get
        # name = request.POST.get('name')
        # (older client code).
        # Otherwise they get in the request body.
        params = json.loads(request.body)
        name = params.get('name')
        b_obj, status, msgs = Basket.new(name=name)
        to_ret = {"data": b_obj.to_dict() if b_obj else {},
                  "alerts": msgs,
                  "status": status}

        return JsonResponse(to_ret)

def baskets_update(request, pk, **response_kwargs):
    """Update the given fields of basket of id 'pk'.

    What to update:
    - the comment
    - a card's quantity: set card_id and quantity fields in request.body.

    """
    # see also baskets and its actions above.
    to_ret = {"data": [],
              "alerts": [],
              "status": ALERT_SUCCESS, }
    if request.method == "POST":
        try:
            basket = Basket.objects.get(id=pk)
        except Exception as e:
            log.error(u"Basket update: {}".format(e))
            return JsonResponse(to_ret)

        # fields are in request.body
        params = json.loads(request.body)
        comment = params.get('comment')
        if comment is not None:  # accept ""
            basket.comment = comment
            basket.save()

        card_id = params.get('card_id')
        quantity = params.get('quantity')
        if card_id and quantity is not None:
            basket.set_copy(card_id=card_id, nb=quantity)

        return JsonResponse(to_ret)

def baskets_add_card(request, pk, **response_kwargs):
    """Add a Card to Basket pk.

    *newer Vue api* api/v2/baskets

    Card can be already in stock (with an id) or not. In that case it
    will be created from the given json.

    Works for a Card without id (from a keywords search from new Vue UI).

    Return:
    - data: <new id>
    """
    msgs = Messages()
    to_ret = {"data": [],
              "alerts": [],
              "status": ALERT_SUCCESS, }
    created = False
    if request.method == 'POST':
        try:
            b_obj = Basket.objects.get(id=pk)
        except ObjectDoesNotExist:
            return

        body = json.loads(request.body)

        if 'params' in body:
            # get a card id, certainly a dist id.
            card_id = body['params']['card_id']
            dist_id = body['params'].get('dist_id')
            card_obj = Card.objects.get(id=card_id)
            dist_obj = None
            dist_name = ""
            COMMAND_IDS = [-1, "-1", u"-1", 0, "0", u"0"]
            if dist_id and dist_id not in COMMAND_IDS:
                dist_obj = Distributor.objects.get(id=dist_id)

            language = body['params'].get('language')
            if language:
                translation.activate(language)  # XXX: not working. Works in a break.

            if dist_obj:
                if not card_obj.distributor:
                    card_obj.distributor = dist_obj
                    card_obj.save()
                    dist_name = dist_obj.name
                elif card_obj.distributor != dist_obj:
                    msgs.add_error(_(u"This card has already a supplier ({}), we can't mark it to command for {}.".format(
                        card_obj.distributor.name, dist_obj.name)))
                    to_ret['alerts'] = msgs.to_alerts()
                    to_ret['status'] = msgs.status
                    return JsonResponse(to_ret)

            if card_obj.distributor:
                dist_name = card_obj.distributor.name

            b_obj.add_copy(card_obj)
            if dist_name:
                msgs.add_success(_(u"The card '{}' was successfully added to the supplier '{}'.".format(
                    card_obj.title, dist_name)))
            else:
                msgs.add_success(_(u"The card '{}' was successfully marked to command, with no default supplier.").
                                 format(card_obj.title))
            to_ret['alerts'] = msgs.to_alerts()
            to_ret['card'] = card_obj.to_dict()  # to update the client.
            return JsonResponse(to_ret)

        elif body:
            # Add a card from json.
            card_id = body.get('id')
            if card_id:
                try:
                    card_obj = Card.objects.get(id=card_id)

                except ObjectDoesNotExist:
                    log.error(u"Card of id {} doesn't exist.".format(card_id))
                    return JsonResponse({'status': ALERT_ERROR,
                                         'message': u"The card {} does not exist.".format(card_id)})

            else:
                try:
                    card_obj, created = Card.from_dict(body)
                except Exception as e:
                    log.error(u"Error creating card: {}".format(e))

            # Add or increment the card.
            try:
                b_obj.add_copy(card_obj)
            except Exception as e:
                log.error(u"Error adding card {} to basket {}: {}".format(card.id, b_obj.id, e))
                return JsonResponse({'status': ALERT_ERROR,
                                     'message': u"Error, could not add card '{}'".format(card_obj.title)})

            # update the card's id in client.
            to_ret = {"data": {"card": card_obj.to_dict(),
                               "basket_qty": b_obj.quantity(card=card_obj),
                               "created": created}}
            return JsonResponse(to_ret)

        else:
            # no data
            pass

def baskets_return(request, pk, **kw):
    if request.method == "POST":
        to_ret = {
            'status': ALERT_SUCCESS,
            'alerts': []
        }
        msgs = Messages()

        try:
            basket = Basket.objects.get(id=pk)
        except Exception as e:
            log.error(u"return basket {}: {}".format(pk, e))
            to_ret['status'] = ALERT_ERROR
            to_ret['alerts'].append("Error: the basket {} doesn't exist.".format(pk))
            return JsonResponse(to_ret)

        try:
            out, msgs = basket.create_return()
        except Exception as e:
            log.error(u"return basket {}: {}".format(pk, e))
        finally:
            to_ret['alerts'] = msgs.msgs
            to_ret['status'] = msgs.status
            return JsonResponse(to_ret)

def baskets_add_to_shelf(request, pk, **kw):
    """
    Add the cards of the given basket to the given shelf, and empty the basket.

    POST params:
    - shelf_id (int)
    """
    to_ret = {}
    msgs = Messages()
    if request.method == 'POST':
        shelf_id = request.POST.get('shelf_id')
        if not shelf_id:
            msgs.add_error('No shelf id to add the basket to')
            to_ret['alerts'] = msgs.msgs
            to_ret['status'] = ALERT_ERROR
            return JsonResponse(to_ret)

        try:
            shelf = Shelf.objects.get(id=shelf_id)
            shelf.add_cards_from(basket_id=pk)
        except Exception as e:
            raise e

        msgs.add_success('The card were successfully added to the shelf.')
        to_ret['alerts'] = msgs.msgs
        return JsonResponse(to_ret)

def baskets_archive(request, pk, **kw):
    """
    Archive the given basket.
    """
    if request.method == "POST":
        msg = {'status': ALERT_SUCCESS,
               "message": _("Basket archived succesfully.")}
        try:
            b_obj = Basket.objects.get(id=pk)
        except Exception as e:
            log.error(u"Basket archive: {}".format(e))
            return JsonResponse({'status': ALERT_ERROR,
                                 'message': "We could not archive the basket n° {}.".format(pk)})

        try:
            b_obj.archive()
        except Exception as e:
            log.error(u"Basket {} could not be archived: {}".format(b_obj.id, e))
            msg = {'status': ALERT_ERROR,
                    'message': _("The basket could not be archived")}
        to_ret = {
            "status": ALERT_SUCCESS,
            "alerts": [msg],
        }
        return JsonResponse(to_ret)

def baskets_delete(request, pk, **kw):
    """Delete the given basket.
    """
    if request.method == "POST":
        msg = {'status': ALERT_SUCCESS,
               "message": _("Basket deleted succesfully")}
        try:
            b_obj = Basket.objects.get(id=pk)
        except Exception as e:
            log.error(u"Basket delete pk {}: {}".format(pk, e))
            return JsonResponse({'status': ALERT_ERROR,
                                 'message': "basket {} does not exist".format(pk)})

        try:
            b_obj.delete()
        except Exception as e:
            log.error(u"Basket {} could not be deleted: {}".format(b_obj.id, e))
            msg = {'status': ALERT_ERROR,
                    'message': _("The basket could not be deleted")}
        to_ret = {
            "status": ALERT_SUCCESS,
            "alerts": [msg],
        }
        return JsonResponse(to_ret)


def baskets_inventory_get_or_create(request, **response_kwargs):
    """
    Get and update the current inventory id and its copies, or create
    one for the basket pk (in url).

    Archive the original basket. It is not needed anymore, all its content is transformed
    to an inventory of the command.
    """
    data = {}
    msgs = []
    status = True
    # Get or post ? In most cases it's only a get, and we want to create one if needed. GET prefered.
    if request.method == 'POST' or request.method == 'GET':
        pk = response_kwargs.pop('pk')
        basket = None
        try:
            basket = Basket.objects.get(id=pk)
            existing = Inventory.objects.filter(basket__id=pk)
            if existing:
                inv = existing[0]
            else:
                inv = Inventory(basket=basket)
                inv.save()

            # Update the cards and quantities of the inventory.
            inv.update_copies(basket.basketcopies_set.all())

            # The client does a redirection to this inventory.
            data['inv_id'] = inv.id

        except Exception as e:
            log.error(e)
            msgs.append({'level': 'error',
                         'message': _("Internal error, sorry !")})

        finally:
            # Archive the original basket.
            basket.archive()

        to_ret = {"status": status,
                  "data": data,
                  "msgs": msgs}
        return JsonResponse(to_ret)

def alerts(request, **response_kwargs):
    msgs = []
    alerts = []
    status = 0
    if request.method == "GET":
        # params = request.GET.copy()
        try:
            alerts, status, msgs = Alert.get_alerts(to_list=True)

        except Exception:
            pass

    to_ret = {"status": status,
              "alerts": msgs,
              "data": alerts}
    return JsonResponse(to_ret)

def alerts_open(request, **response_kwargs):
    total = 0
    if request.method == "GET":
        # params = request.GET.copy()
        try:
            total = Alert.objects.count()
        except Exception:
            pass

    return JsonResponse(total, safe=False)

def places(request, **response_kwargs):
    obj = []
    if request.method == "GET":
        # params = request.GET.copy()
        try:
            obj = Place.objects.all()
        except Exception as e:
            log.error(u"api error while getting places: {}".format(e))

    data = [it.to_dict() for it in obj]
    return JsonResponse(data, safe=False)

def inventories(request, **kwargs):
    """GET: get the list of open inventories, with a place's pk in url the
    inventories of that given place.

    POST: create a new inventory for the given place (place_id in POST params).

    """
    to_ret = {
        "data": None,
    }
    msgs = []

    if request.method == "POST":
        try:
            params = json.loads(request.body)
            place_id = params.get("place_id")
            shelf_id = params.get("shelf_id")
            publisher_id = params.get("publisher_id")
        except Exception as e:
            log.error(u'Error while getting query params for inventories with request {}: {}'.
                      format(request, e))
            data = {
                "status": ALERT_ERROR,
                "datab": []
            }
            return JsonResponse(data, **kwargs)

        try:
            inv = Inventory()
            dosave = True
            # shelf_id is always populated by the UI. If another one
            # is populated, that's what we want
            # XXX weak UI!
            if publisher_id:
                inv.publisher = Publisher.objects.get(id=publisher_id)
            elif place_id:
                inv.place = Place.objects.get(id=place_id)
            elif shelf_id:
                inv.shelf = Shelf.objects.get(id=shelf_id)
            else:
                log.error('Inventory create: we have neither a shelf_id nor a place_id, this shouldnt happen.')
                dosave = False

            if dosave:
                inv.save()

        except Exception as e:
            log.error(e)
            msgs.append({'level': 'error',
                         'message': _("We couldn't create the requested inventory. This is an error, sorry !")})

        to_ret = {"data":
                  {
                      "inventory_id": inv.id,
                  },
                  'messages': msgs
        }
        return JsonResponse(to_ret)

    elif request.method == "GET":
        # Pagination
        page = request.GET.get('page', 1)
        page = to_int(page)
        page_size = request.GET.get('page_size', PAGE_SIZE)
        page_size = to_int(page_size)
        nb_results = None

        if kwargs.get("pk"):
            pk = kwargs.pop("pk")
            try:
                inv = Inventory.objects.get(id=pk)
                state = inv.state(page=page, page_size=page_size)
                to_ret['data'] = state
            except Exception as e:
                log.error(u"Error getting inventory state of {}: {}".format(pk, e))
                # and return error msg

        else:
            try:
                # In our inventories view, we are used to looking at the "applied?"checkbox,
                # useful during an inventory session,
                # so we differentiate between applied+closed and archived inventories.
                invs = Inventory.open_inventories()
                nb_results = invs.count()

                paginator = Paginator(invs, page_size)
                if invs is not None:
                    try:
                        invs = paginator.page(page)
                    except EmptyPage:
                        invs = paginator.page(paginator.num_pages)
                    finally:
                        invs = invs.object_list
                else:
                    invs = paginator.object_list

                to_ret['meta'] = {
                    'page': page,
                    'page_size': page_size,
                    'num_pages': paginator.num_pages,
                    'nb_results': nb_results,
                }
                invs = [it.to_dict(details=True) for it in invs]
                to_ret['data'] = invs
                to_ret['status'] = ALERT_SUCCESS

            except Exception as e:
                log.error(u"Error getting list of inventories: {}".format(e))
                to_ret['data'] = "Internal error"
                to_ret['status'] = ALERT_ERROR

    return JsonResponse(to_ret)

def inventories_copies(request, **kwargs):
    """
    Get copies, with pagination.
    """
    if kwargs.get('pk'):
        pk = kwargs.pop('pk')
        try:
            inv = Inventory.objects.get(id=pk)
        except Exception as e:
            log.error(u"Error getting inventory {}: {}".format(pk, e))

        if request.method == 'GET':
            # Pagination
            page = request.GET.get('page', 1)
            page = to_int(page)
            page_size = request.GET.get('page_size', PAGE_SIZE)
            page_size = to_int(page_size)

            try:
                copies = inv.copies_set.order_by("card__title").all()
                paginator = Paginator(copies, page_size)
                if page is not None:
                    try:
                        copies = paginator.page(page)
                    except EmptyPage:
                        copies = paginator.page(paginator.num_pages)
                    finally:
                        copies = copies.object_list
                else:
                    copies = paginator.object_list

                copies = [it.to_dict() for it in copies]

                return JsonResponse(copies, safe=False)

            except Exception as e:
                log.error(u"Error getting copies of inventory {}: {}".format(pk, e))
                return JsonResponse({})

def inventories_update(request, **kwargs):
    """Update copies and their quantities.

    - pk in url: id of inventory
    - ids_qties in request.body: cards ids and their quantities
    """
    msgs = []
    to_ret = {
        "data": None,
        "msgs": msgs,
    }

    if request.method == "POST":
        if kwargs.get('pk'):
            pk = kwargs.pop('pk')
            try:
                inv = Inventory.objects.get(id=pk)
            except Exception as e:
                log.error(u"Trying to update inventory {}: e".format(pk))
                msgs.append(_("Internal error. We couldn't save the inventory"))
                return  # XXX return 400 error

            params = request.body
            params = json.loads(params)
            # We don't receive a well formatted json.
            # We receive this:
            # {u'ids_qties': [u'185, 1;,50, 1;']}
            # a string with ids an their quantities.
            ids = params.get('ids_qties')
            pairs = []
            if ids:
                together = ids.split(';')
                pairs = [filter(lambda x: x != "", it.split(',')) for it in together]

            cards = params.get('cards')
            if cards:
                # XXX: we are requesting the id of cards we are
                # searching on the web: they don't have an id, except
                # if they already existed in the stock.
                # If that's not the case, create the card.
                for _nop, card_dict in cards.iteritems():
                    if not card_dict.get('id'):
                        try:
                            card_obj, _nop = Card.from_dict(card_dict)
                            card_dict['id'] = card_obj.id
                        except Exception as e:
                            log.error(u"Error creating the card {} to add to inventory {}: {}".
                                      format(card_dict['title'], inv.id, e))

                pairs = [(card['id'], 1) for __, card in cards.iteritems()]

            status, _msgs = inv.add_pairs(pairs)
            msgs.append(_msgs)

            to_ret['status'] = status
            nb_cards = inv.nb_cards()
            to_ret['nb_cards'] = nb_cards
            nb_copies = inv.nb_copies()
            to_ret['nb_copies'] = nb_copies
            to_ret['missing'] = inv._orig_cards_qty() - nb_copies
            to_ret['total_value'] = inv.value()
            if status == "success":  # XXX import satuses from models
                to_ret['msgs'] = msgs.append(_("Inventory saved. Keep working !"))

    return JsonResponse(to_ret)

def inventories_remove(request, **kwargs):
    """Remove a card from the inventory.

    - as post param in request.body: 'card_id'

    """
    msgs = []
    to_ret = {}
    if request.method == "POST":
        if kwargs.get('pk'):
            pk = kwargs.pop('pk')

            try:
                inv = Inventory.objects.get(id=pk)
            except Exception as e:
                log.error(e)
                msgs.append(_("Internal error. We couldn't update the inventory"))
                return  # XXX return 400 error

            params = request.body
            params = json.loads(params)
            ids = params.get('card_id')

            status = inv.remove_card(ids)

            to_ret['status'] = status

    return JsonResponse(to_ret)

def inventory_diff(request, pk, **kwargs):
    diff, name, total_copies_in_inv, total_copies_in_stock = Inventory.diff_inventory(pk, to_dict=True)
    to_ret = {'cards': diff,
              'total_copies_in_inv': total_copies_in_inv,
              'total_copies_in_stock': total_copies_in_stock,
              'name': name}
    return JsonResponse(to_ret)

def inventory_apply(request, pk, **kwargs):
    """Apply this inv to the stock.
    """
    if pk is None or pk == "undefined":
        log.error(u'Error: you want to apply an inventory but its given pk is undefined')
        to_ret = {
            "status": ALERT_ERROR,
            "datab": []
        }
        return JsonResponse(to_ret)

    inv = Inventory.objects.get(id=pk)
    if inv.applied:
        return JsonResponse(
            {"data": "already applied",
             "alerts": [
                 {"level": ALERT_INFO,
                  "message": _(u"This inventory is already applied")}
             ]})

    # Run asynchronously:
    async(do_inventory_apply, pk, task_name='apply inventory {}'.format(pk))  # XXX: async_task in python 3.7

    to_ret = {
        "status": ALERT_INFO,
        "alerts": [
            {"level": ALERT_INFO,
             "message": _("The inventory is being applied. This may take a few minutes.")}
        ],
        "data": None
    }
    return JsonResponse(to_ret)

def stats(request, **kwargs):
    """Return stats about the stock.
    """
    language = request.GET.get("language")
    # Translate the graph labels.
    if language:
        translation.activate(language)

    stock = Stats.stock()
    return JsonResponse(stock)

def to_int(string):
    """Parse the string to int.
    Return the int or None.
    """
    if not string:
        return None
    try:
        return int(string)
    except Exception:
        log.error(u"Unable to parse {} to an int".format(string))
        return None

def stats_sells_month(request, **kwargs):
    """ Return some stats about a given month (the current one by default):
    - best 10 sells
    - total revenue
    - number of products sold
    - mean
    Optional arguments:
    - month (str): ...
    - year (str): ...

    Return: a dict
    """
    LIMIT = 10
    month = None
    year = None

    if request.GET.get('month'):
        month = request.GET.get('month')
        month = to_int(month)
        year = to_int(request.GET.get('year'))

    res = Stats.sells_month(limit=LIMIT, year=year, month=month)
    return JsonResponse(res)


###############################################################################
# Commands
###############################################################################

def commands_supplier(request, pk):
    """
    Return the list of cards to command from the given distributor.

    If pk == 0, get the list of cards to command that don't have a supplier.

    (actually return basket_copy objects, with the basket_qty)
    """
    dist_id = int(pk)
    # Get all cards from the commands list...
    basket_copies = Basket.auto_command_copies(dist_id=dist_id)
    copies_from_dist = []
    # ... and filter the ones with the distributor required.
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 100))

    if dist_id == 0:
        copies_from_dist = basket_copies
    else:
        for it in basket_copies:
            if it.card.distributor and it.card.distributor.id == dist_id:
                copies_from_dist.append(it)

    # TODO:
    totals = {}
    totals['total_cards'] = len(copies_from_dist)
    totals['total_copies'] = sum([it.quantity for it in copies_from_dist])
    totals['total_price'] = sum([it.card.price if it.card.price else 0
                                 for it in copies_from_dist])
    totals['total_price_fmt'] = price_fmt(totals['total_price'], Preferences.get_default_currency())
    # total_price_discounted
    # total_price_excl_vat
    # total_price_discounted_excl_vat

    # Calling to_dict() is the costly part.
    # page starts at 1.
    if page == 0:
        page = 1
    beg = (page - 1) * page_size
    end = page * page_size
    nb_results = len(copies_from_dist)
    num_pages = get_page_count(copies_from_dist, size=page_size)
    copies_from_dist = [it.to_dict() for it in copies_from_dist[beg:end]]
    to_ret = {
        'status': ALERT_SUCCESS,
        'data': copies_from_dist,
        'totals': totals,
        'num_pages': num_pages,
        'nb_results': nb_results,
    }
    return JsonResponse(to_ret)

def nb_commands_ongoing(request, **kwargs):
    """
    """
    if request.method == 'GET':
        nb = Command.nb_ongoing()
        to_ret = {
            'status': ALERT_SUCCESS,
            'data': nb,
        }
        return JsonResponse(to_ret)

def nb_restocking_ongoing(request, **kwargs):
    if request.method == 'GET':
        nb = Restocking.nb_ongoing()
        to_ret = {
            'status': ALERT_SUCCESS,
            'data': nb,
        }
        return JsonResponse(to_ret)

def commands_ongoing(request, **kwargs):
    if request.method == 'GET':
        res = Command.ongoing(to_dict=True) or []
        return JsonResponse(res, safe=False)

def commands_create(request, **kwargs):
    """Create a new command with given list of ids and their quantities.
    """
    msgs = Messages()
    if request.method == "POST":
        params = json.loads(request.body)
        ids_qties = params.get('ids_qties')
        distributor_id = params.get('distributor_id')
        if ids_qties:
            # The format changed, we don't recall doing anything...
            # see old utils.ids_qties_to_pairs
            assert isinstance(ids_qties, list)
            ids_qties = [it.split(',') for it in ids_qties]
            # Create the command and remove the cards from the command list.
            cmd, msgs = Command.new_command(ids_qties=ids_qties,
                                            distributor_id=distributor_id)
            msgs.merge(msgs)

            to_ret = {
                'status': msgs.status,
                'alerts': msgs.to_alerts(),
            }
            return JsonResponse(to_ret)

    return JsonResponse({'status': 'not implemented error'})

def commands_update(request, **kwargs):
    msgs = Messages()
    to_ret = {
        'status': msgs.status,
        'alerts': msgs.to_alerts(),
    }

    if request.method == 'POST':
        params = json.loads(request.body)
        date = params.get('date')
        date_label = params.get('date_label')
        cmd_id = params.get('cmd_id')

        # A bit of argument data validation.
        if not all([date, date_label, cmd_id]):
            log.warning(u"command update: we don't have date, date_label or the command id: {}, {}, {}"
                        .format(date, date_label, cmd_id))

            to_ret['status'] = ALERT_ERROR
            return JsonResponse(to_ret)

        msgs = Command.update_date_attr(cmd_id, date_label, date)
        to_ret['status'] = msgs.status
        to_ret['alerts'] = msgs.to_alerts()

    return JsonResponse(to_ret)

def _get_command_or_return(pk):
    """
    Return the command object, or return a request with an error message.
    """
    msgs = Messages()
    to_ret = {
        'status': msgs.status,
        'alerts': msgs.to_alerts(),
    }
    try:
        cmd = Command.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        log.warning(u"Command {} does not exist. {}".format(pk, e))
        msgs.add_error(u"Command {} does not exist.")
        to_ret['status'] = msgs.status
        to_ret['alerts'] = msgs.to_alerts()
        return JsonResponse(to_ret)

    return cmd


def command_receive(request, pk, **kwargs):
    msgs = Messages()
    to_ret = {
        'status': msgs.status,
        'alerts': msgs.to_alerts(),
    }
    cmd = _get_command_or_return(pk)
    inv = cmd.get_inventory()
    state = inv.state()
    to_ret['data'] = state

    return JsonResponse(to_ret)


def command_receive_update(request, pk, **kwargs):
    msgs = Messages()
    to_ret = {
        'status': msgs.status,
        'alerts': msgs.to_alerts(),
    }
    if request.method == 'POST':
        if request.body and pk:
            try:
                cmd = Command.objects.get(id=pk)
                inv_obj = cmd.get_inventory()
            except ObjectDoesNotExist:
                return
            try:
                ids_qties = json.loads(request.body)
                ids_qties = ids_qties_to_pairs(ids_qties['ids_qties'])
                status, _msgs = inv_obj.add_pairs(ids_qties)
                msgs.append(_msgs)
                to_ret['status'] = msgs.status
                to_ret['alerts'] = msgs.to_alerts()
            except Exception as e:
                log.error(u"Error updating the parcel {}: {}".format(pk, e))
                msgs.add_error(_("An error occured. We have been notified."))
            finally:
                to_ret['alerts'] = msgs.msgs

            return JsonResponse(to_ret)

    raise NotImplementedError

def command_receive_remove(request, pk, **kwargs):
    raise NotImplementedError

def command_receive_diff(request, pk, **kwargs):
    msgs = Messages()
    to_ret = {
        'status': msgs.status,
        'alerts': msgs.to_alerts(),
    }
    cmd = _get_command_or_return(pk)
    inv = cmd.get_inventory()
    diff, obj_name, total_copies_in_inv, total_copies_in_stock = inv.diff(to_dict=True)
    to_ret = {'cards': diff,
              'total_copies_in_inv': total_copies_in_inv,
              'total_copies_in_stock': total_copies_in_stock,
              'name': obj_name}
    return JsonResponse(to_ret)

def command_receive_apply(request, pk, **kwargs):
    """
    Apply this inv to the stock, asynchronously (django-q task).
    """
    if pk is None or pk == "undefined":
        log.error(u'Error: you want to apply an inventory but its given pk is undefined')
        to_ret = {
            "status": ALERT_ERROR,
            "datab": []
        }
        return JsonResponse(to_ret)

    cmd = _get_command_or_return(pk)
    inv = cmd.get_inventory()
    if inv.applied:
        return JsonResponse(
            {"data": "already applied",
             "alerts": [
                 {"level": ALERT_INFO,
                  "message": _(u"This inventory is already applied")}
             ]})

    # Run asynchronously:
    async(do_command_apply, pk, task_name='apply command {}'.format(pk))  # XXX: async_task in python 3.7

    to_ret = {
        "status": ALERT_INFO,
        "alerts": [
            {"level": ALERT_INFO,
             "message": _("The inventory is being applied. This may take a few minutes.")}
        ],
        "data": None
    }

    return JsonResponse(to_ret)
