#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2017 The Abelujo Developers
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

"""

from django.core.management.base import BaseCommand
from tqdm import tqdm

from search.models import Barcode64
from search.models import Card

class Command(BaseCommand):

    help = "Generate a base64 barcode for all ean (that don't have one)."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write("-------------------")
        self.stdout.write(u"Generating and saving barcodes in db…")
        for card in tqdm(Card.objects.all()):
            ean = card.ean or card.isbn
            if ean:
                if not Barcode64.objects.filter(ean=ean):
                    Barcode64.create_save(ean)

        # self.stdout.write(self.style.SUCCESS( "All done !")) # django 1.9
        self.stdout.write("All done !")
