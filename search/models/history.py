# -*- coding: utf-8 -*-
# Copyright 2014 - 2019 The Abelujo Developers
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

import pendulum
import calendar

from django.core.urlresolvers import reverse
from django.db import models

from common import DATE_FORMAT
from common import PAYMENT_CHOICES
from common import TimeStampedModel
from search.models.utils import get_logger

log = get_logger()

CHAR_MAX_LENGTH = 200
PAGE_SIZE = 50


def price_fmt(price, currency):
    """
    Similar as models.utils.
    """
    # Cannot import models.Preferences to get the default currency, circular import.
    if price is None or isinstance(price, str):
        return price
    if currency.lower() == 'chf':
        return 'CHF {:.2f}'.format(price)
    else:
        return '{:.2f} €'.format(price)

def card_currency(card):
    # models.utils
    if card.data_source and 'lelivre' in card.data_source:
        return 'CHF'
    return '€'


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
        return u"move card {} from '{}' to '{}', x{}, at {}".format(
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


class OutMovementCopies(models.Model):
    """
    When the movement is about many cards (a basket), remember the
    cards' quantities at that time.
    """
    created = models.DateTimeField(auto_now_add=True)
    card = models.ForeignKey("search.Card", db_index=True)
    movement = models.ForeignKey("OutMovement")
    quantity = models.IntegerField(default=1, blank=True, null=True)


class OutMovementTypes:
    sell = 1
    returned_supplier = 2
    loss = 3
    gift = 4


class OutMovement(models.Model):
    """
    A movement out of the stock: a return, a loss, a gift. We already have Sell objects.
    """
    OUTMOVEMENT_TYPES_CHOICES = (
        (1, "sell"),
        (2, "return"),
        (3, "loss"),
        (4, "gift"),
    )

    created = models.DateTimeField(auto_now_add=True)
    #: Type of this output. No default.
    #: In case of a basket, we also save the list of cards.
    typ = models.IntegerField(choices=OUTMOVEMENT_TYPES_CHOICES)
    comment = models.CharField(max_length=CHAR_MAX_LENGTH, blank=True, null=True)

    #: This movement can be for one card only:
    card = models.ForeignKey("search.Card", blank=True, null=True)
    #: in which case, it can be for more than one copies:
    nb = models.IntegerField(blank=True, null=True)
    #: Most of the time we should record the place of origin:
    origin = models.ForeignKey("search.Place", blank=True, null=True)
    #: This movement can also be for a whole basket:
    basket = models.ForeignKey("search.Basket", null=True, blank=True)
    #: in which case, we record the quantities of each card:
    copies = models.ManyToManyField("search.Card", blank=True,
                                    through="OutMovementCopies",
                                    related_name="copies")
    #: What's the destination ?
    #: In case of a sell: see other Sell class.
    #: In case of a return, the supplier, who is either a publisher either a distributor:
    publisher = models.ForeignKey("search.Publisher", blank=True, null=True)
    distributor = models.ForeignKey("search.Distributor", blank=True, null=True)
    #: In case of a loss, nothing.
    #: In case of a gift, the recipient:
    recipient = models.ForeignKey("search.Contact", blank=True, null=True)

    # def __unicode__(self):
    # return u"id {}, type {}".format(self.pk,
    # OutMovement.OUTMOVEMENT_TYPES_CHOICES[self.typ - 1])

    # def get_absolute_url(self):
    # return reverse("history_outmovement", args=(self.id,))

    @property
    def supplier(self):
        return self.publisher or self.distributor

    @staticmethod
    def _create_return(publisher=None, distributor=None,
                      card=None,
                      basket=None):
        if not publisher and not distributor \
           and not basket and not basket.distributor:
            return Exception("Please give a publisher, "
                             "a distributor or "
                             "a basket with one of these as argument..")

        out = OutMovement(typ=OutMovementTypes.returned_supplier)
        if publisher:
            out.publisher = publisher
        elif distributor:
            out.distributor = distributor
        elif basket and basket.distributor:
            out.distributor = basket.distributor

        out.save()

        if basket:
            out.basket = basket
            # Add all cards with quantities.
            for copy_qty in out.basket.basketcopies_set.all():
                out.outmovementcopies_set.get_or_create(card=copy_qty.card,
                                                        quantity=copy_qty.quantity)

        else:
            raise NotImplementedError()

        return out

    @staticmethod
    def return_from_basket(basket):
        """
        Remove the cards of this basket from the stock and record a movement object.

        Close the basket.

        If the card is in the default place, remove it from there.

        Otherwise, what's the best strategy ?
        We remove it from the oldest place.
        """
        out = OutMovement._create_return(basket=basket)
        # Decrement all cards from… a place.
        # Should the basket be applied to a place ?
        copies_qties = out.basket.basketcopies_set.all()

        # Grouping per place doesn't seem to help for faster requests.
        # the_place = lambda copy_qty: copy_qty.card.get_return_place()
        # places_cards = toolz.groupby(the_place, copies_qties)

        # from django.db import transaction
        # with transaction.atomic(): doesn't seem to help (tried with 100 cards).
        for card_qty in copies_qties:
            place = card_qty.card.get_return_place()
            place.remove(card_qty.card, quantity=card_qty.quantity)

        # close the basket ?

        return out

    @staticmethod
    def returns(*args, **kwargs):
        return OutMovement.objects.filter(typ=OutMovementTypes.returned_supplier).all()


class EntryCopies(TimeStampedModel):
    card = models.ForeignKey("search.Card", db_index=True)
    entry = models.ForeignKey("Entry")
    #: we may want to remember the price of the card at this time.
    price_init = models.FloatField(null=True, blank=True, default=0.0)

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

    An entry can be:
    - a new card saved in the DB
    - a card added in a place (new entry -> add)
    - a card received in a command
    - a sell, canceled
    - ...

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
        return u"type {}, created at {}".format(self.typ, self.created)

    def get_absolute_url(self):
        """Actually, return the url of the related Entry.
        """
        return reverse("history_entry", args=(self.id,))

    def to_dict(self):
        return self.to_list()

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
    def history(year=None, month=None, page=None, page_size=PAGE_SIZE):
        assert year
        assert month
        entries = []
        # beg = pendulum.now()
        fake_default_currency = '€'
        try:
            entries = EntryCopies.objects.order_by("-created").filter(created__year=year).filter(created__month=month)
        except Exception as e:
            log.error('Error in Entry.history: {}'.format(e))

        fake_default_currency = card_currency(entries.first().card)

        nb_entries = entries.count()
        now = pendulum.now()
        last_day = 31
        if now.month == month:
            last_day = now.day
        else:
            _, last_day = calendar.monthrange(year, month)

        # In the UI, we want to see all days of the month with their total of cards entered.
        entries_per_day = []
        entries_this_day = []
        price_entered = 0
        total_price_entered = 0
        TWO_DIGITS_SPEC = '0>2'
        YMD = '%Y-%M-%d'  # for datetime it is %m
        for day in range(1, last_day + 1):
            # start = pendulum.now()
            date = "{}-{}-{}".format(year,
                                     format(month, TWO_DIGITS_SPEC),
                                     format(day, TWO_DIGITS_SPEC))
            date_obj = pendulum.datetime.strptime(date, YMD)
            entries_this_day = entries.filter(created__day=day)
            price_entered = 0
            if entries_this_day:
                prices = entries_this_day.values_list('price_init', flat=True)
                prices = filter(lambda it: it is not None, prices)
                price_entered = sum(prices)
                # sum = bad perf. With 3 entries, total 42€: 0.25s. It sums up too.
                # XXX: now the model defaults to 0. We could apply a data migration script
                # and simply sum the values_list.
                total_price_entered += price_entered

            entries_per_day.append({'date': date,
                                    'date_obj': date_obj,
                                    'weekday': date_obj.weekday(),
                                    'nb_entered': len(entries_this_day),
                                    'price_entered': price_entered,
                                    'price_entered_fmt': price_fmt(price_entered,
                                                                   fake_default_currency),
            })
            # end = pendulum.now()
            # print("------- for day {}: {}".format(day, end - start))

        # en = pendulum.now()
        # print("--- entries search took {}".format(en - beg))

        return {'entries': entries,
                'nb_entries': nb_entries,
                'entries_per_day': entries_per_day,
                'total_price_entered': total_price_entered,
                'total_price_entered_fmt': price_fmt(total_price_entered,
                                                     fake_default_currency),
                }

    @staticmethod
    def history_day(day=None, month=None, year=None):
        """
        List of cards entered on this day.

        - day: int (mandatory)
        - month, year: int (optional)
        """
        assert day
        entries = EntryCopies.objects.order_by("-created")\
                                     .filter(created__year=year)\
                                     .filter(created__month=month)\
                                     .filter(created__day=day)

        return {'entries': entries}
