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

"""Django signals.
https://docs.djangoproject.com/en/1.8/topics/signals/

When a Card is saved, we want to generate its base64 barcode svg
representation (to speed up the pdf generation).

Signals are initiated inside apps.py.

"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from search.models.models import Barcode64
from search.models.models import Card
from search.models.utils import get_logger
from search.models.utils import is_isbn

log = get_logger()

@receiver(post_save, sender=Card, dispatch_uid="barcode64_signal")
def card_saved_callback(sender, **kwargs):
    """Callback to receive the post_save models signal of Card.

    Generate the barcode base64 if it doesn't exist.
    """
    card = kwargs['instance']
    if is_isbn(card.ean):
        if not Barcode64.objects.filter(ean=card.ean):
            # save the barcode
            base64 = Barcode64.ean2barcode(card.ean)
            try:
                barcode = Barcode64(ean=card.ean, barcodebase64=base64)
                barcode.save()
            except Exception as e:
                log.error(u'Error while saving barcode base 64 of ean {}: {}'.format(card.ean, e))
