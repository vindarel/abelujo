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
After applying an inventory lately, it is possible that the PlaceCopies tables are left
with card_quantity records whose quantity is 0. These records should be deleted.

Indeed, a card will appear in the search of cards of a place even if its quantity in it is 0.
It is not a bug, it is not right.
"""


from django.core.management.base import BaseCommand

from search.models import PlaceCopies


class Command(BaseCommand):

    def handle(self, *args, **options):
        queryset = PlaceCopies.objects.filter(nb=0)
        count = queryset.count()
        if count:
            self.stdout.write("Let's cleanup {} records.".format(count))
        else:
            self.stdout.write("Everything's clean !")
            exit(0)

        queryset.delete()

        self.stdout.write("Done.")
