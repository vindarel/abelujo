#!/usr/bin/env python
# Copyright 2014 The Abelujo Developers
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

import logging

from django.db import models
from common import CHAR_LENGTH
from common import TimeStampedModel

log = logging.getLogger(__name__)

class Address(models.Model):
    """Contact information.

    Distinguish the informations between a physical or a moral person ?
    """
    class Meta:
        app_label = "search"
        ordering = ("name",)

    name           = models.CharField(max_length=CHAR_LENGTH)
    surname        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    enterprise     = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    responsability = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    cellphone      = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    tel_private    = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    tel_office     = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    website        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    email          = models.EmailField(blank=True, null=True)
    email_pro      = models.EmailField(blank=True, null=True)

    address1       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    address2       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    zip_code       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    city           = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    state          = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    country        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)

    comment        = models.TextField(blank=True, null=True)

class BillCopies(models.Model):
    class Meta:
        app_label = "search"

    card = models.ForeignKey("search.Card")
    bill = models.ForeignKey("Bill")
    quantity = models.IntegerField(default=0)

    def __unicode__(self):
        return "for bill {} and card {}: x{}".format(self.bill.id, self.card.id, self.quantity)


class Bill(TimeStampedModel):
    """A bill represents the cost of a set of cards to pay to a
    distributor.

    We can have many bills for a single command (if some cards are
    sent later for example).

    When needed we want to associate a bill to a Card we buy.

    """
    class Meta:
        app_label = "search"

    # created and modified fields
    ref = models.CharField(max_length=CHAR_LENGTH)
    name = models.CharField(max_length=CHAR_LENGTH)
    distributor = models.ForeignKey("search.distributor",null=True)
    #: we must pay the bill at some time (even if the received card is
    #: not sold, this isn't a deposit!)
    due_date = models.DateField()
    #: total cost of the bill, without taxes.
    total_no_taxes = models.FloatField(null=True, blank=True)
    #: shipping costs, with taxes.
    shipping = models.FloatField(null=True, blank=True)
    #: reference also the list of cards, their quantity and their discount.
    copies = models.ManyToManyField("search.Card", through="BillCopies", blank=True)
    #: total to pay.
    total = models.FloatField()

    def __unicode__(self):
        return "{}, total: {}, due: {}".format(self.name, self.total, self.due_date)

    @property
    def long_name(self):
        """
        """
        return "{} ({})".format(self.name, self.ref)

    def add_copy(self, card, nb=1):
        """Add the given card to this bill.
        """
        created = False
        try:
            billcopies, created = self.billcopies_set.get_or_create(card=card)
            billcopies.quantity += nb
            billcopies.save()
        except Exception as e:
            log.error(e)

        return created
