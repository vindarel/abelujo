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
import logging
from django.utils.translation import ugettext as _

from abelujo import settings

def get_logger():
    # normally imported from utils, but circular import
    """Get the appropriate logger for PROD or DEBUG mode. On local
    development, don't use the sentry_logger (throws errors).
    """
    if settings.DEBUG:
        return logging.getLogger('debug_logger')
    else:
        return logging.getLogger('sentry_logger')


log = get_logger()

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CHAR_LENGTH = 200
TEXT_LENGTH = 10000

# Statuses for the client (understood by bootstrap).
ALERT_SUCCESS = "success"
ALERT_ERROR = "danger"
ALERT_WARNING = "warning"
ALERT_INFO = "info"

DEFAULT_PAYMENT_CHOICES = [
    # ids larger or equal than 100 are not counted for the total revenue.
    # For example, coupons were bought before.
    (1, _("cash")),
    (2, _("check")),
    (3, _("credit card")),
    (104, _("gift")),
    (5, _("transfer")),
    (100, _("coupon")),
    (6, _("other")),
]

try:
    if settings.config.PAYMENT_CHOICES:
        PAYMENT_CHOICES = settings.config.PAYMENT_CHOICES
    else:
        PAYMENT_CHOICES = DEFAULT_PAYMENT_CHOICES
except Exception:
    PAYMENT_CHOICES = DEFAULT_PAYMENT_CHOICES

def check_payment_choices():
    """Check all ids are unique."""
    seen = set()
    all_unique = not any(it[0] in seen or seen.add(it[0]) for it in PAYMENT_CHOICES)
    if not all_unique:
        log.warning("**** Some payment choices have the same id! ****")
    return all_unique


check_payment_choices()

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

DEFAULT_VAT_CHOICES = [
    # "2.1"  # in French DOM-TOM
    (1, "5.5"),
    (2, "20"),
]
try:
    if settings.config.VAT_CHOICES:
        VAT_CHOICES = settings.config.VAT_CHOICES
    else:
        VAT_CHOICES = DEFAULT_VAT_CHOICES
except Exception:
    VAT_CHOICES = DEFAULT_VAT_CHOICES


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
        try:
            if isinstance(id, tuple):
                # It can still happen to be "(7, 'ESP\\xc3\\x88CES')"
                # Originated as a bad migration default value.
                # *Should* be avoided now (current 2021, still happened in Sept.).
                # Transform Sell data on the REPL to fix in the DB.
                id = id[0]
            id = int(id)
            for it in PAYMENT_ABBR:
                if id == it[0]:
                    return it[1]
        except Exception as e:
            log.error("Error in get_payment_abbr for id {}: {}".format(id, e))
            return str(id)

    return get_payment_name(id)

def ignore_payment_for_revenue(id):
    """
    Register gifts and coupons in the history, but don't count them as revenue.
    """
    if id is None:
        return False
    # these payments must have an id larger than 100.
    res = (id / 100) >= 1
    return res


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
