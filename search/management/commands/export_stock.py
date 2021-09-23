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
Export the stock in csv, pdf, txt.

./manage.py export_stock

"""


import os

import pendulum
from django.core.management.base import BaseCommand
from django.utils import timezone

from abelujo import settings
from search.models import Card
# from search.models.utils import ppcard
from search.views_utils import cards2csv

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--format',
                            dest="format",
                            action="store",
                            help="format (csv, pdf, txt). Defaults to csv.")

    def handle(self, *args, **options):
        formatt = options.get('format', 'csv')
        if not formatt:
            formatt = 'csv'

        self.stdout.write("Exporter all the stock in {}".format(formatt))
        confirmation = input("Continue ? [Y/n]")
        if confirmation in ["n", "N"]:
            exit(0)

        now = pendulum.date.strftime(pendulum.now(), '%Y-%m-%d %H:%M')

        # select = request.GET.get('select')
        # query = request.GET.get('query')
        # distributor = request.GET.get("distributor")
        # distributor_id = request.GET.get("distributor_id")
        # card_type_id = request.GET.get("card_type_id")
        # publisher_id = request.GET.get("publisher_id")
        place_id = 1
        # shelf_id = request.GET.get("shelf_id")
        order_by = "title"
        # quantity_choice = request.GET.get("quantity_choice")
        # bought = request.GET.get("in_stock")

        # Export all the stock or a custom search ?
        # if select == "selection":
        #     res, meta = Card.search(None,
        #                             to_list=True,
        #                             # distributor=distributor,
        #                             # distributor_id=distributor_id,
        #                             # publisher_id=publisher_id,
        #                             # card_type_id=card_type_id,
        #                             place_id=place_id,
        #                             # shelf_id=shelf_id,
        #                             # quantity_choice=quantity_choice,
        #                             order_by=order_by,
        #                             #in_deposits=True)

        # Select all cards in stock and quantity > 0
        res = Card.cards_in_stock()

        if not os.path.exists(settings.EXPORTS_ROOT):
            os.makedirs(settings.EXPORTS_ROOT)

        # Which format ?
        if formatt == 'txt':
            print("Export to TXT is useless here")
            exit(1)
            # content = ppcard(res)

        elif formatt == "csv":
            # Be careful. With to_list=True above, this should not be needed.
            if not isinstance(res[0], dict):
                res = [it.to_list() for it in res]
            content = cards2csv(res)

        else:
            content = "The export format {} isn't supported.".format(formatt)

        # Save the file.
        filename = "abelujo-stock-{}.{}".format(now, formatt)
        filepath = os.path.join(settings.EXPORTS_ROOT, filename)
        if formatt == 'csv':
            with open(filename, 'w') as f:
                f.write(content)
        else:
            with io.open(filepath, 'w', encoding='utf8') as f:
                f.write(content)

        # Build the response.
        print("Done. Saved file {}".format(filename))
