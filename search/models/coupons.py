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

"""
Coupons ("bons de réduction").

We sell a coupon for a client, it appears in the history.
The coupon is registered under a client's account.

The client uses a coupon, and completes the amount required with another payment method.

Each coupon has a unique identifier.
"""

from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

import uuid

from django.db import models
from django.utils.translation import ugettext as _  # in functions.
from django.utils.translation import ugettext_lazy as __  # in Meta and model fields.

from search.models import users
from search.models.common import CHAR_LENGTH
from search.models.common import TimeStampedModel
from search.models.utils import get_logger

log = get_logger()


# def create_default_coupons():
#     amounts = [10, 15, 20, 30, 50]
#     for amount in amounts:
#         coupon, created = CouponGeneric.get_or_create(amount=amount)
#         if created:
#             log.info("Coupon model of amount {} created.".format(amount))

@python_2_unicode_compatible
class CouponGeneric(TimeStampedModel):
    amount = models.FloatField(verbose_name=__("Amount"), null=False)
    active = models.BooleanField(default=True, max_length=CHAR_LENGTH,
                                 verbose_name=__("Active"),
                                 help_text=_("Can we currently generate coupons of this amount to clients?"))
    #: A code that is transformable into a barcode (image).
    code = models.CharField(max_length=CHAR_LENGTH, blank=True, editable=False)

    def __str__(self):
        return "amount {}".format(self.amount)

    def save(self, *args, **kwargs):
        code = '8000000000' + format(self.amount, '0>3')
        # assert len(code) == 13
        self.code = code
        super(CouponGeneric, self).save(*args, **kwargs)

    @staticmethod
    def search():
        """
        Return all active generic coupons.
        """
        return CouponGeneric.objects.exclude(active=False).all()


class Coupon(TimeStampedModel):
    """
    A coupon that was emitted to a client.
    """
    #: A name, may be useful to search for the coupon manually.
    name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: Which amount is it?
    generic = models.ForeignKey(CouponGeneric, null=True)
    #: An un-fakable id, to accept, and trace, coupons.
    #: It would be used to generate and print a barcode.
    #: Usually, the seller will use a UI to find a client and his coupon.
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    #: The beneficiary client
    client = models.ForeignKey(users.Client)
    #: The coupon is used usually in one, but possibly many, sells.
    # sells
    #: Was the coupon fully used? (not a cent available).
    exhausted = models.BooleanField(default=False, editable=False)
    #: Optional comment.
    comment = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
