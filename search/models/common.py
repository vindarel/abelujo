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

"""Common classes to use in different model files.
Avoid circular imports.
"""
from django.db import models
from django.utils.translation import ugettext as _

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CHAR_LENGTH = 200
TEXT_LENGTH = 10000

# Statuses for the client (understood by bootstrap).
ALERT_SUCCESS = "success"
ALERT_ERROR = "danger"
ALERT_WARNING = "warning"
ALERT_INFO = "info"

# warning: keep ids in sync with the UI in sellController.
PAYMENT_CHOICES = [
    (0, _("cash")),
    (1, _("check")),
    (2, _("credit card")),
    (3, _("gift")),
    (5, _("transfer")),
    (4, _("other")),
    ]

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
