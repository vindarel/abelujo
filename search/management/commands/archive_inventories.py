#!/bin/env python
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

"""
Archive (and close) a bunch of inventories.

./manage.py archive_inventories --all --exclude [id,id]

"""

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from search.models import Inventory


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--exclude',
                            dest="exclude",
                            action="store",
                            help="Do not touch these inventories. Takes a single id or a coma-separated list of ids.")
        parser.add_argument('--all',
                            dest="close_all",
                            action="store_true",
                            required="true",
                            help="Close all inventories, except the ones in the --exclude list.")

    def handle(self, *args, **options):
        exclude_ids= options.get('exclude')
        if ',' in exclude_ids:
            exclude_ids = exclude_ids.split(',')
            exclude_ids = [int(it) for it in exclude_ids]

        all_ids = Inventory.objects.filter(closed=None).all().values_list('id', flat=True)

        ids = sorted(list(set(all_ids) - set(exclude_ids)))

        invs = Inventory.objects.filter(pk__in=ids)

        self.stdout.write("Archiving the following {} inventories:".format(len(invs)))
        self.stdout.write("\n".join([it.__unicode__() for it in invs]))
        confirmation = raw_input("Continue ? [Y/n]")
        if confirmation not in ["", "Y", "y"]:
            exit(0)

        for inv in invs:
            self.stdout.write("- closing {}...".format(inv.id))
            inv.close()

        self.stdout.write("-------------------")
        self.stdout.write("Done.")
