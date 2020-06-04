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
Custom management command.

Set all cards' quantities to zero.
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Card, PlaceCopies

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    help = "Set all the cards' quantities to zero, in every places. This doesn't touch lists, commands or inventories."

    def handle(self, *args, **options):
        self.stdout.write("-------------------")
        self.stdout.write("You are going to RESET all quantities to ZERO:")
        confirmation = raw_input("Continue ? [Y/n]")
        if confirmation == "n":
            exit(0)
        PlaceCopies.objects.all().update(nb=0)
        Card.objects.all().update(quantity=0)
        # self.stdout.write(self.style.SUCCESS( "All done !")) # django 1.9
        self.stdout.write("All done.")
