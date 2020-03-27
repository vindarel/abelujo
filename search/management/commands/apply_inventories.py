#!/bin/env python
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

"""
Apply one or many inventories.

./manage.py apply_inventories --ids [id,id,id,id] [--all]

"""


from django.core.management.base import BaseCommand

from search.models import Inventory

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--ids',
                            dest="ids",
                            action="store",
                            help="Apply these inventories. Takes a single id or a coma-separated list of ids.")
        parser.add_argument('--all',
                            dest="all",
                            action="store_true",
                            help="Apply all open inventories.")

    def handle(self, *args, **options):
        ids = options.get('ids')
        apply_all = options.get('all')
        if not apply_all:
            try:
                if ',' not in ids:
                    invs = [Inventory.objects.get(pk=ids)]
                else:
                    ids = ids.split(',')
                    invs = Inventory.objects.filter(pk__in=ids)
            except Exception as e:
                self.stderr.write("{}".format(e))
                exit(1)

        else:
            invs = Inventory.open_inventories()

        self.stdout.write("Applying the following inventories:")
        self.stdout.write("\n".join([it.__unicode__() for it in invs]))
        confirmation = eval(input("Continue ? [Y/n]"))
        if confirmation == "n":
            exit(0)

        self.stdout.write("""
        Applying a non-small inventory (> 200 cards) can take a couple of minutes.
        """)

        for inv in invs:
            self.stdout.write("- applying {}...".format(inv.id))
            if inv.applied:
                self.stdout.write("\tinv {} is already applied.".format(inv.id))
            else:
                inv.apply()

        self.stdout.write("-------------------")
        self.stdout.write("Done.")
