#!/bin/env python
# -*- coding: utf-8 -*-

from models import Deposit
from models import Distributor
from models import Card

from django.http import HttpResponse
from django.core import serializers

import json

def cards(request, **response_kwargs):
    """return the json list of all cards.
    """
    data = ['goldman', 'arendt', 'hello from django json']
    # import ipdb; ipdb.set_trace()
    query = request.GET.get("query")
    distributor = request.GET.get("distributor")
    # data = serializers.serialize("json", Card.search(query))
    data = Card.search(query, to_list=True, distributor=distributor)
    print "we have json cards:", data
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(json.dumps(data), **response_kwargs)

def distributors(request, **response_kwargs):
    if request.method == "GET":
        query = request.GET.get("query")
        data = Distributor.search(query)
        data = serializers.serialize("json", data)
        response_kwargs['content_type'] = 'application/json'
        print "we have json distributors: ", data
        return HttpResponse(data, **response_kwargs)

def deposits(request, **response_kwargs):
    if request.method == "POST":
        params = request.POST
        # TODO: validation. Use django-angular.
        if params["distributor_name"] == "null":
            pass #return validation error

        response_kwargs['content_type'] = 'application/json'
        try:
            cards_id = params.get("cards_id").split(",")
            dist = Distributor.objects.get(name=params["distributor_name"]) # needs validation: may be undefined
            depo = Deposit.objects.create(name=params["deposit_name"], distributor=dist)
            # TODO: add *multiple* cards. Use Deposit.from_dict
            depo.save()
        except Exception as e:
            print "api/deposit error:", e
            return HttpResponse(json.dumps(["error"]), **response_kwargs)
        return HttpResponse(json.dumps(["success"]), **response_kwargs)
