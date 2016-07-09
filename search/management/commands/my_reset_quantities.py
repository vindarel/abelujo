#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2016 The Abelujo Developers
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
Custom management command.

Set all cards' quantities to zero.
"""

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from tqdm import tqdm

from search.models import PlaceCopies


class Command(BaseCommand):

    help = "Set all the cards' quantities to zero"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write("-------------------")
        self.stdout.write("Resetting all quantities to zero !")
        for place_copies in tqdm(PlaceCopies.objects.all()):
            place_copies.quantity_set(0)

        # self.stdout.write(self.style.SUCCESS( "All done !")) # django 1.9
        self.stdout.write("All done !")
