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

"""
Apply one or many inventories.

./manage.py apply_inventories --ids [id,id,id,id] [--all]

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Sell
from search.models.utils import list_from_coma_separated_ints
from search.models.api import getSellDict


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--ids',
                            dest="ids",
                            action="store",
                            help="card ids, followed by their selling prices, followed by their quantities, all separated by comas.")

    def handle(self, *args, **options):
        """
        Example input:

        11025,3692,9698,3463,3543,9011,1795,11177,2796,11137,9007,2905,10509,1444,6256,11323,11324,11276,10900,11168,331,11325,5646,3724,11326,11327,9108,6500,3495,6231,11027,9864,8984,1797,1596,1513,11167,8980,1685,6289,1823,10371,1789,1816,11328,7007,11141,8579,11329,11330,10370,11331,10645,6526,11332,11333,11334,11335,1379,3523,2263,2798,10744,7458,11336,9470,3804,1425,3721,9900,1682,1454,1387,11337,2152,11338,11189,11339,11340,9533,11341,2907,11170,10130,11342,3457,10.92,7.735,7.735,10.52,9.009,5.4145,10.738000000000001,9.1,9.737,9.054499999999999,5.4145,12.74,8.372,5.4145,11.739,9.009,14.56,11.375,10.192,9.555,4.[Filtered],4.540900000000001,11.375,8.372,6.3245000000000005,10.8745,15.4245,8.099,13.6045,19.929,9.1,18.108999999999998,9.555,5.4145,7.735,5.915,9.919,9.555,9.555,7.735,10.646999999999998,10.92,10.646999999999998,14.56,13.559000000000001,9.1,13.6045,12.649000000000001,9.919,11.375,11.739,9.555,12.285,9.009,17.198999999999998,18.1545,11.375,18.108999999999998,5.551,7.234500000000001,11.83,10.192,11.556999999999999,11.83,9.054499999999999,12.285,7.234500000000001,9.009,11.102,6.3245000000000005,6.3245000000000005,6.3245000000000005,10.192,13.65,6.825,11.375,20.93,12.6945,12.6945,5.187,5.187,11.102,9.555,4.55,4.5045,10.01,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
        """
        to_sell = list_from_coma_separated_ints(options.get('ids'))

        to_sell = getSellDict(to_sell)
        # XXX: script to finish, or to use as a reference.
        date = "2020-12-23 20:00:00"
        place_id = 0
        payment_id = 1

        sell, status, alerts = Sell.sell_cards(to_sell, date=date, place_id=place_id, payment=payment_id,)
