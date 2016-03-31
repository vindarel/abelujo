#!/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import logging

from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.utils.translation import ugettext as _
from models import Alert
from models import Author
from models import Basket
from models import Card
from models import CardType
from models import Category
from models import Deposit
from models import Distributor
from models import Inventory
from models import Place
from models import Publisher
from models import Sell
from models import Stats
from models import getHistory
from search.models.common import ALERT_ERROR
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING
from search.views import postSearch
from search.views import search_on_data_source

from .utils import list_from_coma_separated_ints
from .utils import list_to_pairs

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


# To search objects and send them as json:
# - call the search method of the model
# - serialize the result to a list and to json manually, not with django's serializer.
# With serializer, the access to the dict properties is deeper (inside object.fields),
# so it makes it not straightforward with js widgets, like ui-select.

# This file needs more uniformisation. Some methods return a dict with
# 'data', 'alerts' and 'msgs', some just a list. Everything should be
# in a dict (good practive influenced by the JsonResponse that likes a
# dict better).

def datasource_search(request, **response_kwargs):
    """Search for new cards on external sources.

    - return: a JsonResponse with data, alerts, and status.
    """
    query = request.GET.get('query')
    datasource = request.GET.get('datasource')
    page = request.GET.get('page', 1)
    res, traces = search_on_data_source(datasource, query, PAGE=page)
    data = {"data": res,
            "alerts": traces,
            "status": 200,}
    return JsonResponse(data, safe=False)

def cards(request, **response_kwargs):
    """search for cards in the stock with the given query, or return all of them (with
    a limit).

    """
    data = []
    query = request.GET.get("query")
    query = query.split() if query else None
    distributor = request.GET.get("distributor")
    card_type_id = request.GET.get("card_type_id")
    publisher_id = request.GET.get("publisher_id")
    data = Card.search(query, to_list=True,
                       distributor=distributor,
                       publisher_id=publisher_id,
                       card_type_id=card_type_id)
    log.info(u"we have json distributors: ", data)
    return JsonResponse(data, safe=False)

def card(request, **kwargs):
    """Get a card by id.
    """
    ret = {"data": []}
    msgs = []
    if request.method == 'GET':
        pk = kwargs.pop('pk')
        try:
            card = Card.objects.get(id=pk)
            card = card.to_list()
            ret['data'] = card
            ret['alerts'] = msgs
            log.info("found card {}".format(pk))

        except Exception as e:
            msg = "couldn't find card of id {}: {}".format(pk, e)
            log.warning(msg)
            msgs.append({"message": msg, "level": ALERT_ERROR})

    ret["alerts"] = msgs
    return JsonResponse(ret)

def card_create(request, **response_kwargs):
    """Create a card with either request params or json in request.body

    Return: a tuple (card_id, status, alerts)
    """
    if request.method == "POST":
        params = request.POST.copy()
        status = httplib.OK
        alerts = []

        isbn = params.get('isbn')
        category = params.get('category')
        # Mixed style from client (to fix).
        if params:
            card_dict = {
                "title": params.get('title'),
                "price": params.get('price'),
                "card_type": params.get('type'),
                "distributor": params.get("distributor"),
                "publishers_ids": list_from_coma_separated_ints(params.get("publishers")),
                "authors": [Author.objects.get(id=it) for it in list_from_coma_separated_ints(params.get('authors'))],
                "isbn": isbn,
                "has_isbn": True if params.get("has_isbn") == "true" else False,
                "details_url": params.get("details_url"),
                "year": params.get("year_published"),
            }
            if category:
                card_dict['category'] = category

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
            log.error("Error adding a card: {}".format(e))
            alerts.append({"level": ALERT_ERROR,
                           "message":_("Woops, we can not create this card. This is a bug !")})


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
        alerts = []
        data = []

        pk = response_kwargs.pop("pk")
        card_obj = Card.objects.get(id=pk)

        distributor_id = params.get('distributor_id')
        category_id = params.get("category_id")
        deposits_ids_qties = params.get('deposits_ids_qties')
        baskets_ids_qties = params.get('baskets_ids_qties')
        places_ids_qties = params.get('places_ids_qties')

        # list of tuples (id, qty to add)
        # those params are ints separated by comas.
        d_tups = list_to_pairs(list_from_coma_separated_ints(deposits_ids_qties))
        b_tups = list_to_pairs(list_from_coma_separated_ints(baskets_ids_qties))
        p_tups = list_to_pairs(list_from_coma_separated_ints(places_ids_qties))

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

        if category_id:
            cat = Category.objects.get(id=category_id)
            card_obj.category = cat
            card_obj.save()

        return JsonResponse(status, safe=False)

def cardtype(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = CardType.search(query)
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

def categories(request, **response_kwargs):
    if request.method == 'GET':
        data = Category.objects.all()
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
        data = json.dumps(data)
        return JsonResponse(data, safe=False)

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
    for i in xrange(len(lst)/3):
        sub = lst[i::len(lst)/3]
        to_sell.append({"id": sub[0],
                        "price_sold": sub[1],
                        "quantity": sub[2]})
    return to_sell


def deposits(request, **response_kwargs):
    """
    returns: a json response: status: 200, messages: a list of messages where each message is a dict
    {level: int, messages: str}
    """
    msgs = {"status": httplib.OK, "messages": []}

    if request.method == "POST":
        params = request.POST.copy()
        # TODO: validation. Use django-angular.
        if params.get("distributor") == "null":
            pass #return validation error

        try:
            cards_id = list_from_coma_separated_ints(params.get("cards_id"))
            cards_qty = list_from_coma_separated_ints(params.get("cards_qty"))
            if len(cards_qty) != len(cards_id):
                log.error("Creating deposit: the length of card ids and their qties is different.")
            cards_obj, card_msgs = Card.get_from_id_list(cards_id)
            distributor_obj = Distributor.objects.get(name=params.get("distributor"))

            deposit_dict = {
                "name"              : params.get("name"),
                "distributor"       : distributor_obj,
                "copies"            : cards_obj,
                "quantities"        : cards_qty,
                "deposit_type"      : params.get("deposit_type"),
                "minimal_nb_copies" : params.get("minimal_nb_copies"),
                "auto_command"      : params.get("auto_command"),
                "due_date"          : params.get("due_date"),
                "dest_place"        : params.get("dest_place"),
            }
            status, depo_msgs = Deposit.from_dict(deposit_dict)

        except Exception as e:
            log.error(u"api/deposit error: {}".format(e))
            msgs["status"] = httplib.INTERNAL_SERVER_ERROR
            msgs["messages"].append(e)
            return HttpResponse(json.dumps(msgs), **response_kwargs)
        msgs = {"status": status,
                "alerts": depo_msgs}

        return JsonResponse(msgs)

    # GET
    else:
        depos = Deposit.objects.all()
        depos_list = [it.to_list() for it in depos]
        res = {"data": depos_list,
               "msgs": msgs,
               "status": httplib.OK,
               }
        return JsonResponse(res)

def deposits_due_dates(request, **response_kwargs):
    """Get which deposits are to be paid in a (near) future.
    """
    depos = {}
    if request.method == 'GET':

        try:
            depos = Deposit.next_due_dates(to_list=True)
        except Exception as e:
            log.error(e)

        return JsonResponse(depos, safe=False)

def sell(request, **response_kwargs):

    """requested data: a list of dictionnaries with "id", "price_sold",
    "quantity". See models.Sell.

    messages: we need, for the client, a list of dictionnaries:
       - level: is either "success", "danger" or "",
       - message: is a str of the actual message to display.
    """
    alerts = [] # list of dicts with "level" and "message".
    success_msg = [{"level": "success",
                    "message": _("Sell successfull.")}]

    if request.method == "POST":
        params = request.POST.copy()
        #TODO: data validation
        if params.get("to_sell") == "null":
            pass #TODO: return and display an error.
        to_sell = list_from_coma_separated_ints(params.get("to_sell"))
        to_sell = getSellDict(to_sell)
        date = params.get("date")

        try:
            sell, status, alerts = Sell.sell_cards(to_sell, date=date)

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
        log.error("Calling /api/sell with GET instead of POST.")

def sell_undo(request, pk, **response_kwargs):
    """Undo the given sell id: re-buy the cards.
    """
    msgs = []
    status = True
    if request.method == "GET":
        if pk:
            status, msgs = Sell.sell_undo(pk)
        else:
            msgs.append({"message": u"Internal error: we didn't receive which sell to cancel.",
                         "status": ALERT_ERROR})

        to_ret = {"status": status,
                  "alerts": msgs}
        return JsonResponse(to_ret)

def history(request, **response_kwargs):
    alerts = []
    if request.method == "GET":
        params = request.GET.copy()
        try:
            hist, status, alerts = getHistory()
        except Exception as e:
            log.error(u"api/history error: {}".format(e))
            return HttpResponse(json.dumps(alerts), **response_kwargs)

        to_ret = {"status": status,
                  "alerts": alerts,
                  "data": hist}
        return JsonResponse(to_ret)

def auto_command_total(request, **response_kwargs):
    total = -1
    if request.method == "GET":
        params = request.GET.copy()
        try:
            total = Basket.auto_command_nb()
        except Exception as e:
            pass
    return JsonResponse(total, safe=False)


def basket(request, pk, action="", card_id="", **kwargs):
    """Get the list of cards or act on the given basket.

    pk: the basket id.

    actions:
      - add (POST): give card_ids as a list of coma-separated ints
      - remove (POST): complete the url with a card id, like .../remove/10
    """
    data = []
    msgs = []
    status = True
    to_ret = {"status": True,
              "data": data,
              "msgs": msgs}

    try:
        basket = Basket.objects.get(id=pk)
    except Exception as e:
        log.error(u"Error while getting basket {}: {}".format(pk, e))
        msgs.append(e.message)
        to_ret['status'] = False
        return JsonResponse(to_ret) # also return error message.

    if request.method == "GET":
        data = basket.copies.all()
        ret = [it.to_dict() for it in data]
        return JsonResponse(ret, safe=False)

    elif request.method == 'POST':
        # json request
        req = {}
        if request.body:
            # 'remove' doesn't use this.
            req = json.loads(request.body)
        # Add cards from ids (from the Collection view)
        if action and action == "add" and req.get('card_ids'):
            msgs = []
            ids = req.get('card_ids')
            id_list = list_from_coma_separated_ints(ids)

            try:
                msg = basket.add_copies(id_list)
                msgs.append(msg)
            except Exception as e:
                log.error(u'Error while adding copies {} to basket {}: {}'.format(id_list, pk, e))

        # Add cards from card dicts, not in db yet (from the search view).
        elif action and action == "add" and req.get('cards'):
            # req: dict where keys are an index (useless, js dependency) and values, the card dicts.
            cards = req['cards'].values()
            # Create the new cards in the DB.
            ids = []
            for card in cards:
                try:
                    exists = Card.objects.filter(isbn=card.get('isbn')).first()
                    if not exists:
                        card_obj, msgs = Card.from_dict(card)
                        ids.append(card_obj.id)
                    else:
                        ids.append(exists.id)

                except Exception as e:
                    log.error("Error while creating card from baskets: {}".format(e))

            # Add them to the basket.
            try:
                msg = basket.add_copies(ids)
            except Exception:
                log.error("Error while adding copies {} to basket {}: {}".format(ids, pk, e))

        # Remove a card
        elif action and action == "remove" and card_id:
            status, msgs = basket.remove_copy(card_id)

    to_ret['status'] = status
    to_ret['data'] = data
    to_ret['msgs'] = msgs
    return JsonResponse(to_ret)

def baskets(request, **kwargs):
    """Get the list of basket names. If a pk is given as argument, return
    the list of its copies.

    """
    if request.method == "GET":
        params = request.GET.copy()
        msgs = []
        status = httplib.OK
        if kwargs.get('pk'):
            pk = kwargs.pop('pk')
            try:
                data = Basket.objects.get(id=int(pk))
                data = data.copies.all()
            except Exception as e:
                log.error(e)

        else:
            try:
                data = Basket.objects.all()
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
                  "data": data,}
        return JsonResponse(to_ret)

def baskets_create(request, **response_kwargs):
    """Create a new basket.
    Return its id.
    """
    if request.method == "GET":
        return JsonResponse({'data': "Use a POST request"})

    if request.method == "POST":
        name = request.POST.get('name')
        b_obj, status, msgs = Basket.new(name=name)
        to_ret = {"data": b_obj.to_dict() if b_obj else {},
                  "alerts": msgs,
                  "status": status}

        return JsonResponse(to_ret)

def baskets_inventory_get_or_create(request, **response_kwargs):
    """Get the current inventory id and its copies, or create one for the basket pk (in url).
    """
    data = {}
    msgs = []
    status = True
    # Get or post ? In most cases it's only a get, and we want to create one if needed. GET prefered.
    if request.method == 'POST' or request.method == 'GET':
        pk = response_kwargs.pop('pk')
        try:
            existing = Inventory.objects.filter(basket__id=pk)
            if existing:
                inv = existing[0]
                cards = inv.copies.all()
                cards = [it.to_dict() for it in cards]
                data['cards'] = cards
            else:
                basket = Basket.objects.get(id=pk)
                inv = Inventory(basket=basket)
                inv.save()

            data['inv_id'] = inv.id

        except Exception as e:
            log.error(e)
            msgs.append({'level': 'error',
                         'message': _("Internal error, sorry !")})

        to_ret = {"status": status,
                  "data": data,
                  "msgs": msgs}
        return JsonResponse(to_ret)

def alerts(request, **response_kwargs):
    msgs = []
    alerts = []
    status = 0
    if request.method == "GET":
        params = request.GET.copy()
        try:
            alerts, status, msgs = Alert.get_alerts(to_list=True)

        except Exception as e:
            pass

    to_ret = {"status": status,
              "alerts": msgs,
              "data": alerts}
    return JsonResponse(to_ret)

def alerts_open(request, **response_kwargs):
    total = 0
    if request.method == "GET":
        params = request.GET.copy()
        try:
            total = Alert.objects.count()
        except Exception as e:
            pass

    return JsonResponse(total, safe=False)

def places(request, **response_kwargs):
    obj = []
    if request.method == "GET":
        params = request.GET.copy()
        try:
            obj = Place.objects.all()
        except Exception as e:
            log.error("api error while getting places: {}".format(e))

    data = [it.to_dict() for it in obj]
    return JsonResponse(data, safe=False)

def inventories(request, **kwargs):
    """GET: get the list of inventories of the given place (pk given in url).

    POST: create a new inventory for the given place (place_id in POST params).
    """
    to_ret = {
        "data": None,
    }
    if request.method == "POST":
        params = request.POST.copy()
        place_id = params.get("place_id")
        if place_id:
            try:
                inv = Inventory()
                inv.place = Place.objects.get(id=place_id)
                inv.save()
            except Exception as e:
                log.error(e)

            to_ret = {"data":
                      {
                          "inventory_id": inv.id,
                      }
            }
            return JsonResponse(to_ret)

    elif request.method == "GET":
        if kwargs.get("pk"):
            pk = kwargs.pop("pk")
            try:
                inv = Inventory.objects.get(id=pk)
            except Exception as e:
                log.error(e)
                # and return error msg
            state = inv.state()
            to_ret['data'] = state

    return JsonResponse(to_ret)

def inventories_update(request, **kwargs):
    """Save copies and their quantities.
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
                log.error(e)
                msgs.append(_("Internal error. We couldn't save the inventory"))
                return # XXX return 400 error

            params = request.POST.copy()
            # We don't receive a well formatted json.
            # We receive this:
            # {u'ids_qties': [u'185, 1;,50, 1;']}
            # a string with ids an their quantities.
            ids = params.get('ids_qties')
            together = ids.split(';')
            pairs = [filter(lambda x: x!="", it.split(',')) for it in together]

            status, _msgs = inv.add_pairs(pairs)

            to_ret['status'] = status
            if status == "success": # XXX import satuses from models
                to_ret['msgs'] = msgs.append(_("Inventory saved. Keep working !"))

    return JsonResponse(to_ret)

def inventory_diff(request, pk, **kwargs):
    """
    """
    diff, name = Inventory.diff_inventory(pk, to_dict=True)
    to_ret = {'cards': diff,
              'name': name}
    return JsonResponse(to_ret)

def stats(request, **kwargs):
    """Return stats about the stock.
    """
    stats = Stats()
    stock = stats.stock()
    return JsonResponse(stock)

def stats_sells_month(request, **kwargs):
    """Return the 10 best sells of this month.
    """
    LIMIT = 10
    stats = Stats()
    res = stats.best_sells_month()[:LIMIT]
    return JsonResponse(res, safe=False)
