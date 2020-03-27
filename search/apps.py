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

from __future__ import unicode_literals

from django.apps import AppConfig

class SearchConfig(AppConfig):
    """Configuration for the app. Instantiate inside __init__.py.
    """
    name = "search"  # used for the db.
    verbose_name = "Abejulo"

    def ready(self):
        """Start signals.
        """
        import search.signals.signals  # pylint: disable=W0612 # noqa: F401
