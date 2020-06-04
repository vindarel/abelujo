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

Delete a super user.
"""
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'], is_superuser=True)
        except User.DoesNotExist:
            raise CommandError("There is no superuser named {}".format(options['username']))

        self.stdout.write("-------------------")
        self.stdout.write("Deleting superuser {}".format(options.get('username')))
        user.delete()
        self.stdout.write("Done.")
