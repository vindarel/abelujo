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

"""Common classes to use in different model files.
Avoid circular imports.
"""
from django.db import models
from django.utils.translation import ugettext as _

from abelujo import settings


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CHAR_LENGTH = 200
TEXT_LENGTH = 10000

# Statuses for the client (understood by bootstrap).
ALERT_SUCCESS = "success"
ALERT_ERROR = "danger"
ALERT_WARNING = "warning"
ALERT_INFO = "info"

DEFAULT_PAYMENT_CHOICES = [
    (1, _("cash")),
    (2, _("check")),
    (3, _("credit card")),
    (4, _("gift")),
    (5, _("transfer")),
    (6, _("other")),
]

try:
    if settings.config.PAYMENT_CHOICES:
        PAYMENT_CHOICES = settings.config.PAYMENT_CHOICES
    else:
        PAYMENT_CHOICES = DEFAULT_PAYMENT_CHOICES
except Exception:
    PAYMENT_CHOICES = DEFAULT_PAYMENT_CHOICES

PAYMENT_ABBR = [
     # Translators: abbreviation of the "cash" payment method.
    (1, _("CASH")),  # noqa: E131
     # Translators: abbreviation of the "check" payment method.
    (2, _("CHK")),
     # Translators: abbreviation of the "credit card" payment method.
    (3, _("card")),
     # Translators: abbreviation of "gift"
    (4, _("gift")),
     # Translators: abbreviation of the "transfert" payment method.
    (5, _("TR")),
]

CURRENCY_CHOICES = [
    ('euro', '€'),
    ('chf', 'CHF'),
]


def get_payment_name(id):
    res = filter(lambda payment: payment[0] == id, PAYMENT_CHOICES)
    if res:
        return res[0][1]
    return ""

def get_payment_abbr(id):
    if id is not None:
        id = int(id)
        for it in PAYMENT_ABBR:
            if id == it[0]:
                return it[1]

    return get_payment_name(id)


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
