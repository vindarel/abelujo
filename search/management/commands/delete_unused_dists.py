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
Remove all distributors that are not linked to any card
"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Distributor

# py2/3
try:
    input = raw_input
except NameError:
    pass

class Command(BaseCommand):

    def run(self, *args, **options):
        to_del = []
        dists = Distributor.objects.exclude(name__icontains="default distributor").all().order_by("name")
        for dist in dists:
            if dist.card_set.count() == 0:
                to_del.append(dist)

        for it in to_del:
            self.stdout.write(it.__str__())

        self.stdout.write("Distributors to delete: {}/{}: ".format(len(to_del), dists.count()))

        yes = input("Confirm? [Y/n]")
        if yes in [None, "", "Y"]:
            for it in to_del:
                it.delete()

        self.stdout.write("Done.")

    def handle(self, *args, **options):
        try:
            self.run()
        except KeyboardInterrupt:
            self.stdout.write("User abort.")
