#!/usr/bin/env python
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

from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as __  # in Meta and model fields.

from common import CHAR_LENGTH
from common import TEXT_LENGTH
from common import TimeStampedModel
from search.models.utils import get_logger
from search.models.utils import Messages

log = get_logger()


class Reservation(TimeStampedModel):
    """
    A reservation links a client to a card he reserved.
    """
    class Meta:
        pass

    def __str__(self):
        if self.client:
            return "client {}".format(self.client)
        else:
            return ""

    client = models.ForeignKey("search.Client")
    card = models.ForeignKey("search.Card", null=True, blank=True)
    #: optional: a quantity to reserve. Defaults to 1.
    nb = models.IntegerField(default=1, null=True, blank=True)
    #: If we have taken an action on this reservation.
    #: We can put the book on the side, waiting for the client or
    #: send an email.
    notified = models.BooleanField(default=False)
    #: This reservation is dealed with.
    archived = models.BooleanField(default=False)
    #: If it is archived, is it upon success ?
    success = models.BooleanField(default=True)

    def to_dict(self):
        res = {
            "id": self.pk,
            "created": self.created,
            "client_id": self.client.id if hasattr(self, 'client') and self.client else None,
            "client_repr": self.client.__repr__() if hasattr(self, 'client') else None,
            "client": self.client.to_dict() if hasattr(self, 'client') and self.client else None,
            "card_id": self.card.id if hasattr(self, 'card') and self.card else None,
            "nb": self.nb,
            "notified": self.notified,
        }
        return res

    @staticmethod
    def get_card_reservations(card_id, to_dict=False):
        res = Reservation.objects.filter(card=card_id)
        if to_dict:
            res = [it.to_dict() for it in res]
        return res

    @staticmethod
    def putaside(card, client):
        """
        Remove 1 exemplary from the stock.
        """
        msgs = Messages()
        resa = Reservation.objects.filter(card=card, client=client).first()
        if not resa:
            msgs.add_error("No reservation for this card and this client exist.")
            return False, msgs.msgs()
        try:
            card.remove_card()
            resa.notified = True
            resa.save()
        except Exception as e:
            msgs.add_error(u"Could not put card {} aside: {}".format(card.pk, e))
            log.error(msgs.msgs)
            return False, msgs.msgs

        return True, msgs.msgs


class Contact(models.Model):
    """
    A contact information (client or supplier), with payment information, etc.

    Distinguish the informations between a physical or a moral person ?
    """
    class Meta:
        ordering = ("firstname",)
        abstract = True

    name = models.CharField(max_length=CHAR_LENGTH)
    firstname = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    mobilephone = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    telephone = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    email = models.EmailField(blank=True, null=True)
    website = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)

    # Official numbers
    company_number = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("The company's registered number (State's industry chamber)"))
    bookshop_number = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("The bookshop's official number."))

    # Address
    address1 = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    address2 = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    zip_code = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    city = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    state = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    country = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)

    presentation_comment = models.TextField(blank=True, null=True, max_length=TEXT_LENGTH, verbose_name=__("A comment to add after the default presentation, which contains name, address, contact and official number. Can be useful when the bookshop is officially administrated by another entity. This appears on bills."))

    # Bank/payment details
    checks_order = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("Checks order (if different from name)"))
    checks_address = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("Checks address (if different than address)"))
    bank_IBAN = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("IBAN"))
    bank_BIC = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH, verbose_name=__("BIC"))
    is_vat_exonerated = models.BooleanField(default=False, verbose_name=__("Exonerated of VAT?"))

    comment = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        name: uppercase
        firstname: capitalize
        """
        if self.name:
            self.name = self.name.upper()
        if hasattr(self, 'firstname') and self.firstname:
            self.firstname = self.firstname.capitalize()

        super(Contact, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return "/admin/search/{}/{}".format(self.__class__.__name__.lower(),
                                            self.id)

    def to_dict(self):
        rep = self.__repr__()
        return {'id': self.id,
                'name': self.name.upper(),
                'firstname': self.firstname.capitalize(),
                'mobilephone': self.mobilephone,
                '__repr__': rep,
                'repr': rep,  # in templates, can't use __repr__
                'url': self.get_absolute_url(),
        }

    def __repr__(self):
        return u"{} {} - {}".format(self.name, self.firstname, self.mobilephone)


class Client(Contact):
    """
    A client of the bookshop.
    He can reserve books (not implemented), buy coupons, etc.
    """
    #: Default discount. Specially useful when the client is a collectivity.
    discount = models.IntegerField(blank=True, null=True, verbose_name=__("Discount (%)"))

    #: A client is linked to sells.
    #
    #: When we register a new client on this software, we might want
    # to port data from our previous system.
    #: One data is the number of sells he currently has.
    # So, his fidelity card is not reset to 0.
    initial_sells_quantity = models.IntegerField(default=0, verbose_name=__("The number of registered sells the client has on the previous system."))

    # Other noticeable methods:
    # Sell.count_client_soldcards(client)

    def __repr__(self):
        return u"{} {}".format(self.name, self.firstname)

    def repr(self):
        # for templates. Method cannot start with an underscore. Stupid templates
        return self.__repr__()

    def __unicode__(self):
        return "{} {}".format(self.name, self.firstname)

    def to_dict(self):
        # res = super(Contact, self).to_dict()
        rep = self.__repr__()
        return {'id': self.id,
                'name': self.name.upper(),
                'firstname': self.firstname.capitalize(),
                'mobilephone': self.mobilephone,
                '__repr__': rep,
                'repr': rep,  # in templates, can't use __repr__
                'url': self.get_absolute_url(),
                # addition:
                'discount': self.discount,
        }

    @staticmethod
    def search(query, to_dict=False):
        res = Client.objects.filter(Q(name__icontains=query) |
                                    Q(firstname__icontains=query))
        if to_dict:
            res = [it.to_dict() for it in res]

        return res

    def reserve(self, card_id):
        """
        Reserve this card.

        Return a tuple: Reservation object, created? (boolean).
        """
        resa, created = Reservation.objects.get_or_create(
            client=self,
            card_id=card_id,
        )
        resa.save()
        return resa, created


class Bookshop(Contact):
    """
    Me, the bookshop. My address and payment details.
    """
    pass

    def __repr__(self):
        return "Bookshop {}".format(self.name)


class BillCopies(models.Model):
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
    # created and modified fields
    ref = models.CharField(max_length=CHAR_LENGTH)
    name = models.CharField(max_length=CHAR_LENGTH)
    # distributor = models.ForeignKey("search.distributor", null=True)
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
