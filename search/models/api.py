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
# from models import Sell

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
    log.info("we have json distributors: ", data)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(json.dumps(data), **response_kwargs)

def distributors(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = Distributor.search(query)
        data = serializers.serialize("json", data)
        log.info("we have json distributors: ", data)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

def list_from_coma_separated_ints(str):
    """Gets a string with coma-separated integers, like "1,2,3",
    returns the list of ints.
    """
    # Data validation: should check that we only have ints and comas...
    if str:
        return [int(it) for it in str.split(",")]
    else:
        return []

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
            log.error("api/deposit error:", e)
            msgs["status"] = httplib.INTERNAL_SERVER_ERROR
            msgs["messages"].append(e)
            return HttpResponse(json.dumps(msgs), **response_kwargs)
        msgs = {"status": httplib.OK,
                "messages": depo_msgs}
        return HttpResponse(json.dumps(msgs), **response_kwargs)

def sell(request, **response_kwargs):
    """
    messages: we need, for the client, a list of dictionnaries:
       - level: is either "success", "danger" or "",
       - message: is a str of the actual message to display.
    """
    sell_msgs = [] # list of dicts with "level" and "message".
    success_msg = [{"level": "success",
                    "message": "Vente effectuée."}]
    if request.method == "POST":
        params = request.POST.copy()
        #TODO: data validation
        if params.get("cards_id") == "null":
            pass #TODO: return and display an error.
        response_kwargs["content_type"] = "application/json"
        cards_id = list_from_coma_separated_ints(params.get("cards_id"))

        try:
            for id in cards_id:
                sold, retcode = Card.sell(id)
                if not sold:
                    sell_msgs.append(
                        {"level": retcode, # retcode must be "success" or "danger"
                         "message": "La notice {} n'a pas été vendue.".format(id)})

        except Exception as e:
            log.error("api/sell error: ", e)
            sell_msgs.append({"level": httplib.INTERNAL_SERVER_ERROR,
                              "message": e})
            return HttpResponse(json.dumps(sell_msgs), **response_kwargs)

        if not sell_msgs:
            sell_msgs = success_msg
        return HttpResponse(json.dumps(sell_msgs), **response_kwargs)
