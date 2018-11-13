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

List all super users.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = User.objects.filter(is_superuser=True).all()
        self.stdout.write("-------------------")
        self.stdout.write("\n".join([it.username for it in users]))
