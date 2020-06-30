#!/bin/env python
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

from django.http import JsonResponse

from search.models.common import ALERT_ERROR
from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING

from search.models.common import PAYMENT_CHOICES


def api_payment_choices(request, **kwargs):
    if request.method == 'GET':
        ret = {}
        try:
            choices = []
            for id, name in PAYMENT_CHOICES:
                choices.append({'name': name, 'id': id})
        except Exception as e:
            log.error('Error while getting the Preferences: {}'.format(e))
            return JsonResponse({"status": ALERT_ERROR,
                                 'data': ret})

        ret['data'] = choices
        ret['status'] = ALERT_SUCCESS
        return JsonResponse(ret)
