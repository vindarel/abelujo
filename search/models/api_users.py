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


import datetime
import os

from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import get_template
from weasyprint import HTML

from abelujo import settings
from search.models import Card
from search.models.users import Client
from search.models.utils import get_logger

log = get_logger()

def clients(request, **response_kwargs):
    """
    Get clients.
    """
    if request.method == 'GET':
        try:
            res = [it.to_dict() for it in Client.objects.all()]
            return JsonResponse({'data': res})
        except Exception as e:
            log.error(u"error getting clients: {}".format(e))
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
    template = 'pdftemplates/pdf-bill-main.jade'

    date = datetime.date.today()
    title = "Facture-xx-xx"
    filename = title + '.pdf'

    template = get_template(template)
    card = Card.objects.first()
    copies_set = card.placecopies_set.all()
    cards_qties = [(it.card, it.nb) for it in copies_set]
    sourceHtml = template.render({'cards_qties': cards_qties,
                              'name': title,
                              'total': 10.999,
                              'total_with_discount': 10.99,
                              'total_qty': 8,
                              'quantity_header': 18,
                              'date': date})

    filepath = os.path.realpath(os.path.join(settings.STATIC_PDF, filename))
    fileurl = "/static/{}".format(filename)
    to_ret = {'fileurl': fileurl,
              'filename': filename,
              'status': 200}

    try:
        with open(filepath, 'wb') as f:
            # XXX: créer avec LibreOffice ??!
            HTML(string=sourceHtml).write_pdf(target=f.name)
            response = JsonResponse(to_ret)
    except Exception as e:
        log.error(u"Error writing bill in pdf to {}: {}".format(filepath, e))
        response = JsonResponse({'status': 400})

    return response
