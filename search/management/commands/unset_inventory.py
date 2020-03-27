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

./manage.py apply_inventories --ids [id, id,id,id]

"""


from django.core.management.base import BaseCommand

from search.models import Inventory


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--id',
                            dest="id",
                            action="store",
                            help="Mark this inventory as unapplied. This doesn't effectively un-apply it.")

    def handle(self, *args, **options):
        try:
            inv = Inventory.objects.get(id=options.get('id'))
        except Exception as e:
            self.stderr.write("{}".format(e))
            exit(1)

        inv.closed = None
        inv.applied = False
        inv.save()
        self.stdout.write("Done.")
