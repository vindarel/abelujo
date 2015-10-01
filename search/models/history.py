# -*- coding: utf-8 -*-
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

import datetime
import logging
from datetime import date

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.http import quote
from django.apps import apps

from common import TimeStampedModel

log = logging.getLogger(__name__)

# class MovementType(models.Model):
#     """Different movements:
#     - an entry
#     - an exit
#     - an internal movement
#     """
#     class Meta:
#         app_label = "search"

#     name = models.CharField()


class EntryCopies(TimeStampedModel):
    card = models.ForeignKey("search.Card", db_index=True)
    entry = models.ForeignKey("Entry")
    #: we may want to remember the price of the card at this time.
    price_init = models

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
    )

    class Meta:
        app_label = "search"

    #: has a one-to-many relationship with EntryCopies
    #: through the attribute entrycopies_set
    # entrycopies_set
    #: Type of this entry (a purchase by default).
    typ = models.IntegerField(default=EntryTypes.purchase,
                              choices=ENTRY_TYPES_CHOICES)

    def __unicode__(self):
        return "type {}, created at {}".format(self.typ, self.created)

    def get_absolute_url(self):
        """Actually, return the url of the related Entry.
        """
        return reverse("history_entry", args=(self.id,))

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
    def new(copies):
        """Create a new record for the given list of copies.

        - copies: list

        return: a tuple Entry object, boolean
        """
        try:
            en = Entry()
            en.save()
            en.add_copies(copies)

            return en, True

        except Exception as e:
            log.error(e)

            return None, False
