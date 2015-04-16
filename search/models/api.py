#!/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import logging

from django.core import serializers
from django.http import HttpResponse

from models import Card
from models import Basket
from models import Deposit
from models import Distributor
from models import Sell

log = logging.getLogger(__name__)

def cards(request, **response_kwargs):
    """return the json list of all cards.
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

def distributors(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = Distributor.search(query)
        data = serializers.serialize("json", data)
        log.info(u"we have json distributors: ", data)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

def list_from_coma_separated_ints(str):
    """Gets a string with coma-separated numbers (ints or floats), like
    "1,2.2,3", returns a list with each number.
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
            }
            depo_msgs = Deposit.from_dict(deposit_dict)
        except Exception as e:
            log.error(u"api/deposit error:", e)
            msgs["status"] = httplib.INTERNAL_SERVER_ERROR
            msgs["messages"].append(e)
            return HttpResponse(json.dumps(msgs), **response_kwargs)
        msgs = {"status": httplib.OK,
                "messages": depo_msgs}
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
                    "message": "Vente effectuée."}]
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
