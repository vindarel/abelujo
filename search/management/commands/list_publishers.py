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
Remove all publishers that are not linked to any card anymore.

This can happen after other scripts, such as update_all_with_dilicom.
"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Publisher


class Command(BaseCommand):

    def run(self, *args, **options):
        pubs = Publisher.objects.all().order_by("name")
        for pub in pubs.all():
            self.stdout.write(pub.__str__())

        self.stdout.write("Publishers: {}".format(pubs.count()))

    def handle(self, *args, **options):
        try:
            self.run()
        except KeyboardInterrupt:
            self.stdout.write("User abort.")
