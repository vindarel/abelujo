# -*- coding: utf-8 -*-
# Copyright 2014 - 2016 The Abelujo Developers
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

from common import ALERT_ERROR
from common import ALERT_SUCCESS
from common import ALERT_WARNING
from common import DATE_FORMAT
from common import PAYMENT_CHOICES
from common import TimeStampedModel
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q

log = logging.getLogger(__name__)

CHAR_MAX_LENGTH = 200
PAGE_SIZE = 50

class InternalMovement(TimeStampedModel):
    """An internal movement
    For a single Card (or a Basket).
    """
    origin = models.ForeignKey("search.Place", related_name="mvt_origin")
    dest = models.ForeignKey("search.Place", related_name="mvt_dest")
    card = models.ForeignKey("search.Card")
    basket = models.ForeignKey("search.Basket", null=True, blank=True)
    nb = models.IntegerField()

    def __unicode__(self):
        return "move card {} from '{}' to '{}', x{}, at {}".format(
            self.card.id, self.origin.name, self.dest.name, self.nb, self.created)

    def to_dict(self):
        """
        return: a Dict
        """
        ret = {"card": self.card.to_list(),
               "origin": self.origin.to_dict(),
               "dest": self.dest.to_dict(),
               "nb": self.nb,
               "created": self.created.strftime(DATE_FORMAT),
               "model": self.__class__.__name__,
        }
        return ret

class EntryCopies(TimeStampedModel):
    card = models.ForeignKey("search.Card", db_index=True)
    entry = models.ForeignKey("Entry")
    #: we may want to remember the price of the card at this time.
    price_init = models.FloatField(null=True, blank=True)

    @staticmethod
    def last_entry(card):
        """Get informations about the last entry of the given card.

        return: EntryCopies object
        """
        try:
            last = EntryCopies.objects.filter(card__id=card.id)\
                                         .order_by("-created").first()
        except Exception as e:
            log.error(e)
            return None

        return last

class EntryTypes:
    purchase = 1
    deposit = 2
    gift = 3


class Entry(TimeStampedModel):
    """An entry. Can be for many cards at once.
    We record the original price.

    """

    ENTRY_TYPES_CHOICES = (
        (1, "purchase"),
        (2, "deposit"),
        (3, "gift"),
        (4, "sell canceled"),
    )

    #: has a one-to-many relationship with EntryCopies
    #: through the attribute entrycopies_set
    # entrycopies_set
    #: Type of this entry (a purchase by default).
    typ = models.IntegerField(default=EntryTypes.purchase,
                              choices=ENTRY_TYPES_CHOICES)
    payment = models.CharField(choices=PAYMENT_CHOICES,
                               max_length=CHAR_MAX_LENGTH, blank=True, null=True)
    reason = models.CharField(max_length=CHAR_MAX_LENGTH, blank=True, null=True)

    def __unicode__(self):
        return "type {}, created at {}".format(self.typ, self.created)

    def get_absolute_url(self):
        """Actually, return the url of the related Entry.
        """
        return reverse("history_entry", args=(self.id,))

    def to_list(self):
        """
        """
        ec = self.entrycopies_set.all()
        payment = self.payment
        if isinstance(self.payment, unicode):
            payment = int(self.payment)

        copies = [{
            "price_init": it.price_init,
            "card": it.card.to_list(),
        } for it in ec]
        try:
            ret = {"created": self.created.strftime(DATE_FORMAT),
                   "model": self.__class__.__name__,
                   "type": self.ENTRY_TYPES_CHOICES[self.typ - 1][1],
                   "payment": PAYMENT_CHOICES[payment - 1][1] if payment else "",
                   "copies": copies}
        except Exception as e:
            log.error(e)
            return {}

        return ret

    def add_copies(self, copies):
        """Add the given list of copies.

        copies: list

        return:
        """
        try:
            for card in copies:
                ent_set = EntryCopies(entry=self, card=card)
                ent_set.price_init = card.price
                ent_set.save()

        except Exception as e:
            log.error(e)
            return False

        return True

    @staticmethod
    def new(copies, payment=None, reason=None):
        """Create a new record for the given list of copies.

        - copies: list
        - payment: int

        return: a tuple Entry object, boolean
        """
        try:
            if isinstance(payment, unicode) or isinstance(payment, str):
                payment = int(payment)
            en = Entry(payment=payment, reason=reason)
            en.save()
            en.add_copies(copies)

            return en, True

        except Exception as e:
            log.error(e)

            return None, False

    @staticmethod
    def history(to_dict=True, to_list=True, page=None, page_size=PAGE_SIZE):
        """
        """
        alerts = []
        entries = []

        try:
            entries = Entry.objects.order_by("-created")[:page_size]
        except Exception as e:
            log.error('Error in Entry.history: {}'.format(e))

        if to_list:
            entries = [it.to_list() for it in entries]

        return entries, ALERT_SUCCESS, alerts
