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


from django.http import JsonResponse

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
