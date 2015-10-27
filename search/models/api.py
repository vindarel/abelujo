#!/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import logging

from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
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
from models import getHistory

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

ALERT_SUCCESS = "success"
ALERT_ERROR = "error"

# To search objects and send them as json:
# - call the search method of the model
# - use django's serializer or manually transform the
#   objects to a list and to json.
# With serializer, the access to the dict properties is deeper (inside object.fields),
# so it makes it not straightforward with js widgets, like ui-select.

def cards(request, **response_kwargs):
    """search for cards with the given query, or return all of them (with
    a limit).

    """
    data = []
    query = request.GET.get("query")
    query = query.split() if query else None
    distributor = request.GET.get("distributor")
    card_type_id = request.GET.get("card_type_id")
    # data = serializers.serialize("json", Card.search(query))
    data = Card.search(query, to_list=True,
                       distributor=distributor,
                       card_type_id=card_type_id)
    log.info(u"we have json distributors: ", data)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(json.dumps(data), **response_kwargs)

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
            ret = json.dumps(ret)
            log.info("found card {}".format(pk))

        except Exception as e:
            msg = "couldn't find card of id {}".format(pk)
            log.warning(msg, e)
            msgs.append({"message": msg, "level": ALERT_ERROR})

    kwargs['content_type'] = "application/json"
    return HttpResponse(ret, **kwargs)

def card_create(request, **response_kwargs):
    if request.method == "POST":
        params = request.POST.copy()
        response_kwargs["content_type"] = "application/json"
        status = httplib.OK
        alerts = []

        isbn = params.get('isbn')
        if params.get("has_isbn") == "true":
            try:
                isbn = int(isbn)
            except TypeError:
                isbn = None
        else:
            isbn = None

        category = params.get('category')

        try:
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

            card_obj, msg = Card.from_dict(card_dict)
            alerts.append({"level": ALERT_SUCCESS,
                           "message": msg})

        except Exception as e:
            log.error("Error adding a card: {}".format(e))
            alerts.append({"level": ALERT_ERROR,
                           "message":_("Woops, we can not create this card. This is a bug !")})

        msgs = {"status": status, "alerts": alerts, "card_id": card_obj.id}
        if card_obj:
            return HttpResponse(json.dumps(msgs), **response_kwargs)

        return HttpResponse(json.dumps(msgs), **response_kwargs)

    else:
        log.error("creating a card should be done with POST.")

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
        data = Distributor.search(query, to_list=True)
        data = json.dumps(data)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

def publishers(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = Publisher.search(query)
        data = serializers.serialize("json", data)
        return HttpResponse(data, **response_kwargs)

def list_from_coma_separated_ints(str):
    """Gets a string with coma-separated numbers (ints or floats), like
    "1,2.2,3", returns a list with each number. Because on url
    parameters we can get a list of ids like this.

    """
    def toIntOrFloat(nb):
        try:
            return int(nb)
        except ValueError:
            nb = nb.replace(",", ".")
            return float(nb)

    # Data validation: should check that we only have ints and comas...
    if str:
        return [toIntOrFloat(it) for it in str.split(",")]
    else:
        return []

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

        response_kwargs['content_type'] = 'application/json'
        try:
            cards_id = list_from_coma_separated_ints(params.get("cards_id"))
            #ONGOING: form the dict to send to Deposit.from_dict,
            cards_obj = Card.get_from_id_list(cards_id)
            distributor_obj = Distributor.objects.get(name=params.get("distributor"))

            deposit_dict = {
                "name"              : params.get("name"),
                "distributor"       : distributor_obj,
                "copies"            : cards_obj.get("result"),
                "deposit_type"      : params.get("deposit_type"),
                "initial_nb_copies" : params.get("initial_nb_copies"),
                "minimal_nb_copies" : params.get("minimal_nb_copies"),
                "auto_command"      : params.get("auto_command"),
                "due_date"          : params.get("due_date"),
                "dest_place"        : params.get("dest_place"),
            }
            depo_msgs = Deposit.from_dict(deposit_dict)

        except Exception as e:
            log.error(u"api/deposit error: {}".format(e))
            msgs["status"] = httplib.INTERNAL_SERVER_ERROR
            msgs["messages"].append(e)
            return HttpResponse(json.dumps(msgs), **response_kwargs)
        msgs = {"status": httplib.OK,
                "alerts": depo_msgs}

        return HttpResponse(json.dumps(msgs), **response_kwargs)


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
        response_kwargs["content_type"] = "application/json"
        to_sell = list_from_coma_separated_ints(params.get("to_sell"))
        to_sell = getSellDict(to_sell)
        date = params.get("date")

        try:
            sell, status, alerts = Sell.sell_cards(to_sell, date=date)

        except Exception as e:
            log.error(u"api/sell error: {}".format(e))
            alerts.append({"level": "error",
                           "message": e})
            return HttpResponse(json.dumps(alerts), **response_kwargs)

        if not alerts:
            alerts = success_msg
        to_ret = {"status": status,
                  "alerts": alerts}
        return HttpResponse(json.dumps(to_ret), **response_kwargs)

    elif request.method == "GET":
        log.error("Calling /api/sell with GET instead of POST.")


def history(request, **response_kwargs):
    alerts = []
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        try:
            hist, status, alerts = getHistory()
        except Exception as e:
            log.error(u"api/history error: {}".format(e))
            return HttpResponse(json.dumps(alerts), **response_kwargs)

        to_ret = {"status": status,
                  "alerts": alerts,
                  "data": hist}
        return HttpResponse(json.dumps(to_ret), **response_kwargs)

def auto_command_total(request, **response_kwargs):
    total = -1
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        try:
            total = Basket.auto_command_nb()
        except Exception as e:
            pass
    return HttpResponse(json.dumps(total), **response_kwargs)

def baskets(request, **kwargs):
    """Get the list of basket names. If a pk is given as argument, return
    the list of its copies.

    """
    if request.method == "GET":
        params = request.GET.copy()
        msgs = []
        status = httplib.OK
        kwargs["content_type"] = "application/json"
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
        return HttpResponse(json.dumps(to_ret), **kwargs)


def alerts(request, **response_kwargs):
    msgs = []
    alerts = []
    status = 0
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        try:
            alerts, status, msgs = Alert.get_alerts(to_list=True)

        except Exception as e:
            pass

    to_ret = {"status": status,
              "alerts": msgs,
              "data": alerts}
    return HttpResponse(json.dumps(to_ret), **response_kwargs)

def alerts_open(request, **response_kwargs):
    total = 0
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        try:
            total = Alert.objects.count()
        except Exception as e:
            pass

    return HttpResponse(json.dumps(total), **response_kwargs)

def places(request, **response_kwargs):
    obj = []
    if request.method == "GET":
        params = request.GET.copy()
        response_kwargs["content_type"] = "application/json"
        try:
            obj = Place.objects.all()
        except Exception as e:
            log.error("api error while getting places: {}".format(e))

    data = [it.to_dict() for it in obj]
    return HttpResponse(json.dumps(data), **response_kwargs)

def inventories(request, **kwargs):
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
            return HttpResponse(json.dumps(to_ret), **kwargs)

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

    return HttpResponse(json.dumps(to_ret), **kwargs)
