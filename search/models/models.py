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

"""
You can produce a graph of the db with django_extension's

    make graphdb

and see it here: http://dev.abelujo.cc/graph-db.png
"""
from __future__ import unicode_literals

# __unicode__ is now __str__
from django.utils.encoding import python_2_unicode_compatible
from django.utils import six

import calendar
import datetime
import locale
import json
import os
import tempfile
import urllib
from cachetools import cached, TTLCache
from datetime import date

import barcode
import dateparser
import pendulum
import pytz

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Q
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _  # in functions.
from django.utils.translation import ugettext_lazy as __  # in Meta and model fields.
from toolz.dicttoolz import update_in
from toolz.dicttoolz import valmap
from toolz.itertoolz import groupby

from abelujo import settings
from search.models import history
from search.models.users import Client
from search.models.common import ALERT_ERROR
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING
from search.models.common import CHAR_LENGTH
from search.models.common import CURRENCY_CHOICES
from search.models.common import DATE_FORMAT
from search.models.common import PAYMENT_CHOICES
from search.models.common import TEXT_LENGTH
from search.models.common import ignore_payment_for_revenue
from search.models.common import TimeStampedModel
from search.models import utils
from search.models.utils import Messages
from search.models.utils import get_logger
from search.models.utils import is_invalid
from search.models.utils import is_isbn
from search.models.utils import isbn_cleanup
from search.models.utils import card_currency
from search.models.utils import price_fmt
from search.models.utils import roundfloat
from search.models.utils import to_ascii
from search.models.utils import distributors_match

PAGE_SIZE = 20
#: Date format used to jsonify dates, used by angular-ui (datepicker)
# and the ui in general (datejs).
DEFAULT_PRICE = 0

log = get_logger()

DEPOSIT_TYPES_CHOICES = [
    ("Dépôt de libraire", (
        ("lib", "dépôt de libraire"),
        ("fix", "dépôt fixe"),
    )),
    ("Dépôt de distributeur", (
        ("dist", "dépôt de distributeur"),
    )),
]

THRESHOLD_DEFAULT = 0

MSG_INTERNAL_ERROR = _("An internal error occured, we have been notified.")

BAD_IDS = [None, 0, '0', '0', '-1', '-1', 'all', u'all']

PRESMAG = {
    "01": "Posé en linéaire",
    "02": "Sur broche",
    "03": "Présentoir",
    "05": "En palette présentoir",
}

PRESEDIT = {
    "R": "Relié",
    "B": "Broché",
    "P": "Poche",
    "J": "Jeu",
    "D": "Disque vinyle",
    "DC": "Disque compact",
    "DV": "Disque vidéo, DVD",
    "CD": "Cédérom",
    "LD": "Livre disque",
    "K": "Cassette",
    "KA": "Cassette audio",
    "KV": "Cassette vidéo",
    "LK": "Livre cassette",
    "C": "Cuir",
    "E": "Etui",
    "L": "Luxe",
    "X": "Journal, revue",
    "SM": "Support magnétique",
    "DI": "Diapositives",
    "PC": "Publicité",
    "AL": "Album",
    "CR": "Cartes routières",
    "PO": "Posters",
    "CA": "Calendriers",
    "O": "Objet",
    "N": "Contenu numérique",
}
# Improve sorting.
locale.setlocale(locale.LC_ALL, "")

def get_best_sells(soldcards):
    """
    From a list of SoldCard objets, return a dict where each key is the name of a card type, and the value a list of tuples containing a card and its quantity sold.
    The soldcards list is constructed and filtered on dates beforehand.

    Example output: {'book': (<card object>, 3) }
    """
    best_sells = {'book': {}}  # pk => quantity
    # There is no "group by" in Django ORM and annotations don't do. Screw it.
    # Get best sells by type.
    try:
        for soldcard in soldcards:
            card_type = soldcard.card.card_type
            if card_type and card_type.id == 1:
                card_type = 'book'
            elif card_type:
                card_type = CardType.objects.filter(name=card_type).first()
                if card_type:
                    best_sells[card_type] = {}
                else:
                    continue
            else:
                continue

            # Increment best sells.
            if soldcard.card not in best_sells['book']:
                best_sells[card_type][soldcard.card] = soldcard.quantity
            else:
                if soldcard.quantity > 0:
                    best_sells[card_type][soldcard.card] += soldcard.quantity

    except Exception as e:
        log.warning("get_best_sells: {}".format(e))
    finally:
        # sort best sells.
        limit = 10
        for card_type in best_sells.keys():
            res = best_sells[card_type].items()
            res = sorted(res, key=lambda it: it[1])
            res.reverse()
            best_sells[card_type] = res[:limit]

    return best_sells

@python_2_unicode_compatible
class Author(TimeStampedModel):
    name = models.CharField(unique=True, max_length=200, verbose_name=__("name"))
    name_ascii = models.CharField(null=True, blank=True, max_length=200, verbose_name=__("name_ascii"))

    class Meta:
        ordering = ('name',)
        verbose_name = __("author")

    def __str__(self):
        return "{}".format(self.name)

    def save(self, *args, **kwargs):
        """
        Create name_ascii, with no accentuated letters.
        """
        res = to_ascii(self.name)
        if res:
            self.name_ascii = res

        super(Author, self).save(*args, **kwargs)

    @staticmethod
    def search(query):
        """
        Search for names containing "query", return a queryset.

        The search doesn't consider accentuated letters: searching
        "éléphant" will return results with "éléphant" as well as
        "elephant".
        """
        try:
            if query:
                query_ascii = to_ascii(query)
                data = Author.objects.filter(name_ascii__icontains=query_ascii)
            else:
                data = Author.objects.all()
        except Exception as e:
            log.error("Author.search error: {}".format(e))
            data = [
                {"alerts": {"level": ALERT_ERROR,
                            "message": "error while searching for authors"}}
            ]

        # data = [auth.to_list() for auth in data]
        return data


@python_2_unicode_compatible
class Distributor(TimeStampedModel):
    """The entity that distributes the copies.

    If you want a mark a publisher as a distributor… just create a
    distributor with the same name.
    """
    # comment above: we have once considered that publishers can be distributors.
    # They should not. It complicates everything.

    name = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("name"))
    #: GLN (official ID, given by Dilicom).
    gln = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("GLN"))
    #: The discount (in %). When we pay the distributor we keep the amount of
    # the discount.
    discount = models.FloatField(default=0, blank=True, verbose_name=__("discount"))
    #: Star the distributors to give precendence to our favourite ones.
    stars = models.IntegerField(default=0, null=True, blank=True)
    #: Contact: email adress. To complete, create a Contact class.
    email = models.EmailField(null=True, blank=True)

    #: City
    city = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("City"))
    #: Postal code
    postal_code = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("Postal code"))
    #: Country
    country = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("Country"))
    #: Number of titles into the FEL (as of june, 2020)
    nb_titles_in_FEL = models.IntegerField(blank=True, null=True, verbose_name=__("Number of titles in FEL (june, 2020)"))
    #: Comm. via Dilicom
    # It is currently a boolean given with a character, let's suppose it could change to any
    # other short string (like "NA", "DEL" or whatnot), so let's use a CharField.
    # note: currently unused in favor of settings.DILICOM_DISTRIBUTORS loaded at startup.
    comm_via_dilicom = models.CharField(max_length=4, blank=True, null=True, verbose_name=__("Comm. via Dilicom: yes or no?"))

    class Meta:
        ordering = ("name",)
        verbose_name = __("distributor")

    def __str__(self):
        return "{}".format(self.name)

    def get_absolute_url(self):
        return "/admin/search/{}/{}".format(self.__class__.__name__.lower(),
                                            self.id)

    def __repr__(self):
        """Representation for json/javascript.
        """
        return "{} ({} %)".format(self.name, self.discount)

    def repr(self):
        return self.__repr__()

    @staticmethod
    def get_or_create(gln=""):
        if not gln:
            return

        dist = Distributor.objects.filter(gln=gln).first()
        # yes
        if dist:
            return dist
        # no dist in DB. It certainly has been loaded at startup.
        else:
            # All the distributors known by Dilicom are loaded into
            # settings.DILICOM_DISTRIBUTORS at startup.
            # Reminder: Dilicom doesn't give the name in the FEL, only its GLN.
            dist_data = settings.DILICOM_DISTRIBUTORS.get(gln)
            if dist_data:
                dist = Distributor(gln=gln,
                                   name=dist_data.get('name'),
                                   city=dist_data.get('city'),
                                   postal_code=dist_data.get('postal_code'),
                                   country=dist_data.get('country'),
                                   nb_titles_in_FEL=dist_data.get('nb_titles'),
                                   comm_via_dilicom=dist_data.get('via_dilicom'))
                dist.save()
                log.debug("--- new distributor {} created with GLN {}".format(
                    dist.name,
                    gln))
                return dist

    def dilicom_enabled(self):
        # copied from view_utils...
        return os.getenv('DILICOM_PASSWORD') is not None \
            and os.getenv('DILICOM_USER') is not None

    def is_comm_via_dilicom(self):
        dist_dict = settings.DILICOM_DISTRIBUTORS.get(self.gln)
        if dist_dict:
            if dist_dict.get('via_dilicom') in ['o', 'O']:
                return "Oui"
            return "Non"
        return "?"

    def to_list(self):
        return {
            "id": self.id,
            "name": self.name,
            "discount": self.discount,
            "stars": self.stars,
            "email": self.email,
            "repr": self.__repr__(),
            "get_absolute_url": self.get_absolute_url(),
        }

    def to_dict(self):
        return self.to_list()

    @staticmethod
    def get_all(**kwargs):
        """Return a list of deposits.

        No arguments: return all.
        """
        return Deposit.objects.order_by("name")

    @staticmethod
    def search(query=None, to_list=False):
        data = []
        if not query:
            data = Distributor.objects.all()

        if to_list:
            data = [it.to_list() for it in data]

        return data

    def set_distributor(self, cards):
        """Set this distributor for the given cards.

        - cards: list of cards (obj)

        Used for example when applying the inventory of a command,
        from a basket which was given a supplier.
        """
        for card in cards:
            if card.distributor != self:
                card.distributor = self
                # warning: performance
                card.save()


@python_2_unicode_compatible
class Publisher (models.Model):
    """The publisher of the card.
    """

    #: Name of the publisher
    name = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("name"))
    #: ISBN of the publisher
    isbn = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: Contact address (to put in own table)
    address = models.TextField(null=True, blank=True, verbose_name=__("address"))
    #: Optional comment
    comment = models.TextField(null=True, blank=True, verbose_name=__("comment"))

    class Meta:
        ordering = ("name",)
        verbose_name = __("publisher")

    def __str__(self):
        return "{}".format(self.name)

    def get_absolute_url(self):
        return "/admin/search/publisher/{}".format(self.id)

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
        }

    @staticmethod
    def search(query):
        try:
            if query:
                data = Publisher.objects.filter(name__icontains=query)
            else:
                data = Publisher.objects.all()
        except Exception as e:
            log.error("Publisher.search error: {}".format(e))
            data = [
                {"alerts": {"level": ALERT_ERROR,
                            "message": "error while searching for publishers"}}
            ]

        return data

@python_2_unicode_compatible
class Shelf(models.Model):
    """Shelves are categories for cards, but they have a physical location
    in the bookstore.

    - ...

    For now, a Card has only one shelf.

    """
    #: Name of the shelf
    name = models.CharField(unique=True, max_length=CHAR_LENGTH, verbose_name=__("name"))

    class Meta:
        verbose_name = __("shelf")
        verbose_name_plural = __("shelves")

    def get_absolute_url(self):
        return ""  # TODO: url parameters in stock search to reference a shelf.

    def __str__(self):
        #idea: show the nb of cards with that category.
        return "{}".format(self.name)

    def to_dict(self):
        """Return a dict with the shelf name and its list of cards.
        """
        to_ret = {
            'id': self.id,
            'name': self.name,
            # 'cards': Card.objects.filter(shelf=self.id),
        }
        return to_ret

    def cards(self, to_dict=False):
        """Return the list of cards of this shelf. (a list of Card obj, unless
        to_dict is set to True)

        """
        cards = Card.objects.filter(shelf=self.id)
        if to_dict:
            cards = [it.to_dict() for it in cards]

        return cards

    def cards_set(self):
        """
        - return: a dict of dicts:
           a card id: {'card': a card dict, 'nb': its quantity.}

        Used for an Inventory diff.
        """
        cards = self.cards()
        cards_set = {it.id: {'card': it,
                             'quantity': it.quantity}
                     for it in cards}
        return cards_set

    @property
    def cards_qty(self):
        """
        - return: int
        """
        qty = Card.objects.filter(shelf=self.id).count()
        return qty

    def add_cards_from(self, basket_id=None):
        """
        Mark all the cards of the basket to be of this shelf, and add their quantities to
        the default place. Then, empty the basket (so than we can repeat the operation
        with the same basket).
        """
        basket = Basket.objects.get(id=basket_id)

        # Set all the cards to be in this shelf.
        basket.copies.all().update(shelf=self)

        # Add the card's quantity from the basket into the default place.
        basket_copies = basket.basketcopies_set.all()
        place = Preferences.get_default_place()
        for copy in basket_copies:
            place.add_copy(copy.card, nb=copy.nb)

        # Empty the basket.
        basket.empty()

        return True

@python_2_unicode_compatible
class CardType(models.Model):
    """The type of a card: a book, a CD, a t-shirt, a DVD,…
    """
    name = models.CharField(max_length=100, null=True, verbose_name=__("name"))

    class Meta:
        verbose_name = __("Card type")

    def __str__(self):
        return "{}".format(self.name)

    @staticmethod
    def search(query):
        if not query:
            query = ""
        if query == "":
            return CardType.objects.all()

        try:
            data = CardType.objects.filter(name__icontains=query)
        except Exception as e:
            log.error("CardType.search error: {}".format(e))
            data = [
                {"alerts": {"level": ALERT_ERROR,
                            "message": "error while searching for authors"}}
            ]

        return data


@python_2_unicode_compatible
class Barcode64(TimeStampedModel):
    """SVG barcodes encoded as base64, to be included into an html img tag
    for pdf generation:

        img(alt="" src="data:image/png;base64,{{ barcode64 }}

    They are created automatically. See the `card_saved_callback` method.

    """
    ean = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    barcodebase64 = models.CharField(max_length=TEXT_LENGTH, null=True, blank=True)

    def __str__(self):
        return "ean: {}".format(self.ean)

    @staticmethod
    def ean2barcode(ean):
        """Return the base64 barcode (str).
        """
        EAN = barcode.get_barcode_class('ean13')
        if not ean:
            log.warning('Barcode generation: with have a null ean.')
            return None

        with tempfile.TemporaryFile() as fp:
            try:
                ean = EAN(ean)
                fullname = ean.save(fp.name)  # to svg by default
                # We'll include the barcode as a base64-encoded string.
                eanbase64 = open(fullname, "rb").read().encode("base64").replace("\n", "")
                return eanbase64
            except Exception as e:
                # this well may be an invalid ean. Shall we erase it ?
                log.warning('Barcode generation: error with ean {}: {}'.format(ean, e))
                return

    @staticmethod
    def create_save(ean):
        base64 = Barcode64.ean2barcode(ean)
        if base64:
            try:
                Barcode64(ean=ean, barcodebase64=base64).save()
            except Exception as e:
                log.error('could not save barcode of ean {}: {}'.format(ean, e))


@python_2_unicode_compatible
class Card(TimeStampedModel):
    """A Card represents a book, a CD, a t-shirt, etc. This isn't the
    physical object.
    """
    #: Title:
    title = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("title"))
    #: Internal representation without accents, used for search.
    title_ascii = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("title_ascii"), null=True, blank=True)

    #: type of the card, if specified (book, CD, tshirt, …)
    card_type = models.ForeignKey(CardType, blank=True, null=True, verbose_name=__("card type"))
    #: VAT (tax. French: TVA)
    vat = models.FloatField(null=True, blank=True, verbose_name=__("VAT tax"))
    sortkey = models.TextField('Authors', blank=True)
    authors = models.ManyToManyField(Author, blank=True, verbose_name=__("authors"))
    #: The public price.
    price = models.FloatField(null=True, blank=True, default=0.0, verbose_name=__("price"))
    #: An optional custom selling price, if different than the public price.
    selling_price = models.FloatField(null=True, blank=True,
                                      verbose_name="{} {}".format(
                                          __("Selling price"),
                                          __("(leave blank if it's the same than the public price)")))
    #: The price it was bought (alternative or complement to a supplier and its discount).
    # (don't default to 0. Zero means we bought it 0€)
    price_bought = models.FloatField(null=True, blank=True, verbose_name=__("price bought (leave blank if you use a supplier and its discount)"))
    #: Currency: euro, CHF, other?
    currency = models.CharField(max_length=10,
                                choices=CURRENCY_CHOICES,
                                # cannot access Preferences which wants Place.
                                # Python has no late bindings.
                                # default='euro',
                                null=True, blank=True, verbose_name=__("currency"))

    #: Maybe this card doesn't have an isbn. It's good to know it isn't missing.
    has_isbn = models.NullBooleanField(default=True, blank=True, null=True, verbose_name=__("has isbn"))
    #: ean/isbn (mandatory). For db queries, use isbn, otherwise "ean" points to the isbn.
    isbn = models.CharField(max_length=99, null=True, blank=True)
    #: Did we buy this card once, or did we register it only to use in
    #: lists (baskets), without buying it ?
    in_stock = models.BooleanField(default=False, verbose_name=__("in stock"))
    #: Quantity (caution: this field is denormalized, computed on each save).
    quantity = models.IntegerField(null=True, blank=True, editable=False, verbose_name=__("quantity"))
    #: The minimal quantity we want to always have in stock:
    threshold = models.IntegerField(blank=True, null=True, default=THRESHOLD_DEFAULT,
                                    verbose_name=__("Minimal quantity before command"))
    #: Publisher of the card:
    publishers = models.ManyToManyField(Publisher, blank=True, verbose_name=__("publishers"))
    year_published = models.DateField(blank=True, null=True, verbose_name=__("year published"))
    #: Distributor:
    distributor = models.ForeignKey("Distributor", blank=True, null=True, verbose_name=__("distributor"))
    #: Collection
    collection = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("collection"))
    #: Official theme, following the CLIL classification, given by Dilicom. A code of 4 digits.
    # Used as information and to guess our shelf.
    # So, let's not create a special table.
    theme = models.CharField(max_length=4, blank=True, null=True, verbose_name=__("Theme (Dilicom)"))
    #: Shelf (for now, only one shelf).
    shelf = models.ForeignKey("Shelf", blank=True, null=True, verbose_name=__("shelf"))
    # location = models.ForeignKey(Location, blank=True, null=True)
    #    default='?', on_delete=models.SET_DEFAULT)
    #: the places were we can find this card (and how many).
    places = models.ManyToManyField("Place", through="PlaceCopies", blank=True, verbose_name=__("places"))
    #: when and how this card was sold: sells (see the Sell table).
    #: an url to show a thumbnail of the cover:
    cover = models.URLField(null=True, blank=True, verbose_name=__("cover url"))
    #: the cover, saved on the file system. Use card.cover to get the most relevant.
    imgfile = models.ImageField(upload_to="covers", null=True, blank=True)
    #: the internet source from which we got the card's informations
    data_source = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True,
                                   editable=False,
                                   verbose_name=__("data source"))
    #: link to the card's data source
    details_url = models.URLField(max_length=CHAR_LENGTH, null=True, blank=True,
                                  editable=False,
                                  verbose_name=__("details url"))
    #: date of publication
    date_publication = models.DateField(blank=True, null=True, verbose_name=__("date publication"))
    #: the summary (of the back cover)
    summary = models.TextField(null=True, blank=True, verbose_name=__("summary"))
    #: Book format (pocket, big)
    fmt = models.TextField(null=True, blank=True,
                           editable=False,
                           verbose_name=__("Book format (pocket, etc)"))
    #: Thickness (in millimeters)
    thickness = models.IntegerField(blank=True, null=True, verbose_name=__("Thickness"))
    #: Height (in millimeters)
    height = models.IntegerField(blank=True, null=True, verbose_name=__("Height"))
    #: Width (in millimeters)
    width = models.IntegerField(blank=True, null=True, verbose_name=__("Width"))
    #: Weight (in grams)
    weight = models.IntegerField(blank=True, null=True, verbose_name=__("Weight"))
    #: Publisher presentation (relié, broché, poche, jeu, disque etc)
    presedit = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True,
                                editable=False,
                                verbose_name=__("Présentation éditeur"))
    #: a user's comment
    comment = models.TextField(blank=True, verbose_name=__("comment"))

    class Meta:
        ordering = ('sortkey', 'year_published', 'title')
        verbose_name = __("card")

    def __str__(self):
        """
        To pretty print a list of cards, see models.utils.ppcard.
        """
        MAX_LENGTH = 15
        authors = self.authors.all()
        authors = authors[0].name if authors else ""
        publishers = ", ".join([pub.name for pub in self.publishers.all()])
        if len(publishers) > MAX_LENGTH:
            publishers = publishers[0:MAX_LENGTH] + "..."
        distributor = self.distributor.name if self.distributor else _("none")
        return "{}:{}, {}, editor: {}, distributor: {}".format(self.id, self.title, authors, publishers, distributor)

    @property
    def ean(self):
        """Can't be used in queries, use isbn.
        """
        return self.isbn

    @property
    def price_discounted(self):
        """Return the price minus its discount.
        """
        discount = self.distributor.discount if self.distributor else None
        if discount and self.price is not None:
            return roundfloat(self.price - self.price * discount / 100)

        else:
            return self.price

    @property
    def price_discounted_excl_vat(self):
        """
        """
        # helper function(s) to help client side. More robust here.
        tax = Preferences.get_vat_book()
        try:
            return roundfloat(self.price_discounted - self.price_discounted * tax / 100)
        except Exception:
            return self.price_discounted

    @property
    def price_excl_vat(self):
        """Return the price excluding the taxes, i.e. the price minus its
        Value on Added Tax.

        French: prix - TVA

        return: a float
        """
        if hasattr(self, 'price_excl_vat_fmt'):  # only from Dilicom update.
            return self.price_excl_vat_fmt

        if hasattr(self, 'vat1'):  # only from Dilicom update.
            # (not saved in DB)
            tax = self.vat1
        else:
            tax = Preferences.get_vat_book()
        if tax and self.price is not None:
            return roundfloat(self.price - self.price * tax / 100)

        return self.price

    def check_vat(self):
        """
        I have observed that a price excluding taxes from Dilicom doesn't equal
        the price minus the VAT: 22.00€ with 5.50% equals 20.79€,
        yet Dilicom returns 20.85€.

        Let's check it.
        """
        if not self.price:
            return None, None
        if hasattr(self, 'dilicom_price_excl_vat'):  # from Dilicom update.
            price_excl_vat = self.dilicom_price_excl_vat
        else:
            return None, None
        if hasattr(self, 'vat1'):
            vat = self.vat1
        else:
            return None, None

        calculated_price = self.price - (self.price * vat / 100)
        real_vat = - (price_excl_vat - self.price) / self.price * 100
        return calculated_price, real_vat

    def price_fmt(self):
        """
        Return: a string, with the price formatted correctly with its currency symbol.

        Exemple: "10 €" or "CHF 10".
        """
        # WARN: duplicated from utils.py, because the template wants an object method.
        # I consider this a Python fail.
        if self.price is None or isinstance(self.price, six.string_types)\
           or isinstance(self.price, six.text_type):
            return self.price

        currency = self.get_currency()
        if currency.upper() == 'CHF':
            return 'CHF {:.2f}'.format(self.price)
        else:
            return '{:.2f} €'.format(self.price)

    @property
    def img(self):
        """
        Return the url of the file on disk if it exists, the remote url otherwise.
        """
        if not self.imgfile:
            return self.cover
        return self.imgfile.url

    def save(self, *args, **kwargs):
        """We override the save method in order to
        save covers on disk and denormalize the quantity.
        """
        # Update quantity.
        self.quantity = self.quantity_compute()

        # For a better search, create title_ascii, with no accentuated letters, lowercase.
        res = to_ascii(self.title)
        if res:
            self.title_ascii = res

        super(Card, self).save(*args, **kwargs)

        # Save cover.
        # After super, otherwise unique constraint error.
        self.save_cover()

    def save_cover(self):
        """
        Save this cover on disk if not done already.
        """
        if self.img and (not self.imgfile) and self.img != "":
            try:
                tmp_path, httpmessages = urllib.urlretrieve(self.img)
                self.imgfile.save(
                    os.path.basename(self.img),
                    File(open(tmp_path)))
            except Exception as e:
                log.error("Error retrieving the cover from url: {}".format(e))

    def display_authors(self):
            return ', '.join([a.name for a in self.authors.all()])

    def quantity_compute(self):
        """Return the quantity of this card in all places (not deposits).

        return: int
        """
        # Is this quicker...
        # places containing this card:
        places_ids = PlaceCopies.objects.filter(card=self).values_list('place').distinct()
        places_obj = [Place.objects.get(id=pk) for (pk,) in places_ids]
        quantity = sum([it.quantity_of(self) for it in places_obj])

        # ...than this ? => YES, dramatically.
        # DONE: this ~is~ was a bottleneck (slowing down to_dict and every view).
        # quantity = sum([pl.quantity_of(self) for pl in Place.objects.all()])
        return quantity

    @staticmethod
    def quantities_total():
        """Total of quantities for all cards in this stock (for tests).
        Return: int (None on error)
        """
        try:
            return sum([it.quantities_total() for it in Place.objects.all()])
        except Exception as e:
            log.error("Error while getting the total quantities of all cards: {}".format(e))

    @staticmethod
    def cards_without_eans():
        return Card.objects.filter(has_isbn=True).filter(isbn="")

    def get_return_place(self):
        """
        Return the place suitable to apply a return to the supplier.
        Either the default place, or the first we can sell from.
        If nothing applies, return the default place.

        Return: Place object.
        """
        places_qs = self.places
        default_place = Preferences.get_default_place()
        if default_place in places_qs.all():
            return default_place

        places_qs = places_qs.exclude(can_sell=False, is_stand=True)
        if places_qs.count():
            return places_qs.first()

        return default_place

    def get_distributor(self):
        """Get the list of distributors without an error in case it is
        null. To use in card_show template.
        """
        if self.distributor:
            return [self.distributor]
        else:
            return []

    def get_publishers(self):
        """Avoid error in case self.publisher is None. For direct use in
        templates."""
        if self.publishers:
            return self.publishers.all()
        else:
            return []

    def has_publisher(self, pub):
        """This card has the following publisher ? (id)

        Returns the publisher or a void list.
        """
        try:
            return self.publishers.filter(id=pub)
        except Exception as e:
            log.error("Error while checking if card {} has publisher {}: {}".format(self.id, pub, e))
            return None

    def has_distributor(self, dist):
        """
        - dist: int (id)
        """
        try:
            if not self.distributor:
                return False
            return self.distributor.id == dist
        except Exception as e:
            log.error("Error while checking if card {} has publisher {}: {}".format(self.id, dist, e), extra={'stack': True})
            return None

    def has_no_distributor(self):
        """
        """
        if not self.distributor:
            return True
        return False

    @property
    def pubs_repr(self):
        """Coma-separated str representation of this card's publishers.
        May need truncating ?

        Return: str
        """
        publishers = self.publishers.all()
        pubs_repr = ", ".join(it.name.capitalize() for it in publishers)
        return pubs_repr

    @property
    def authors_repr(self):
        """
        """
        authors = self.authors.all()
        authors_repr = ", ".join([it.name for it in authors])
        return authors_repr

    @property
    def shelf_repr(self):
        """Return the shelf name, or "".
        """
        if self.shelf:
            return self.shelf.name

        return ""

    @property
    def theme_name(self):
        "From the theme code in DB, get its name."
        if self.theme:
            return utils.theme_name(self.theme)
        return ""

    @property
    def parent_theme_name(self):
        """
        Get the first parent theme name.
        3781 (action et aventure) => Bande dessinée"""
        if not self.theme:
            return ""
        return utils.parent_theme_name(self.theme)

    @property
    def theme_composed_name(self):
        if self.theme:
            return utils.theme_composed_name(self.theme)
        return ""

    @property
    def presedit_name(self):
        return PRESEDIT.get(self.presedit) or ""

    @property
    def distributor_repr(self):
        if self.distributor:
            return self.distributor.to_list()['name']
        return ""

    def to_dict(self):
        return self.to_list()

    def to_list(self, in_deposits=False, with_quantity=True, with_authors=True,
                with_publishers=True):
        """
        Return a *dict* of this card's fields.

        The with_xxx parameters allow to gain some SQL queries and some speed up.
        """
        authors_repr = self.authors_repr
        pubs_repr = self.pubs_repr

        isbn = ""
        if self.isbn is not None:
            isbn = self.isbn
        elif self.ean is not None:
            isbn = self.ean

        dist_repr = self.distributor_repr
        if self.distributor:
            dist_repr = self.distributor.to_list()['name']
            dist = self.distributor.to_list()
        else:
            dist_repr = ""
            dist = {}

        try:
            get_absolute_url = self.get_absolute_url()
        except Exception as e:
            log.error(e)
            get_absolute_url = ""

        currency = self.get_currency()

        theme_code = self.theme
        theme_name = self.theme_name

        shelf_name = self.shelf.name if self.shelf else ""
        if hasattr(settings, "config") and hasattr(settings.config, 'USE_THEMES_FOR_SHELVES') and settings.config.USE_THEMES_FOR_SHELVES:
            # shelf_name = theme_name
            shelf_name = self.theme_composed_name

        res = {
            "id": self.id,
            "authors_repr": authors_repr,
            "collection": self.collection.capitalize() if self.collection else None,
            "created": self.created.strftime(DATE_FORMAT),  # YYYY-mm-dd
            "modified": self.modified.strftime(DATE_FORMAT),  # YYYY-mm-dd
            "data_source": self.data_source,
            "date_publication": self.date_publication.strftime(DATE_FORMAT) if self.date_publication else None,

            # Card link/url:
            "details_url": self.details_url,  # external (on data source)
            "get_absolute_url": get_absolute_url,  # internal
            "url": get_absolute_url or self.details_url,

            "distributor_repr": dist_repr,
            "dist_repr": dist_repr,
            "distributor": dist,
            "fmt": self.fmt,
            "img": self.img,
            "cover": self.cover,  # either the url, either the saved file on file system.
            "isbn": isbn,
            "model": self.__class__.__name__,  # useful to sort history.
            "places": ", ".join([p.name for p in self.places.all()]),
            "price": self.price,
            "selling_price": self.selling_price,
            # used for Sell form, when the price sold can change:
            "price_sold": self.selling_price if self.selling_price is not None else self.price,
            'price_fmt': price_fmt(self.price, currency),
            "price_discounted": self.price_discounted,
            "price_discounted_fmt": price_fmt(self.price_discounted, currency),
            "price_discounted_excl_vat": self.price_discounted_excl_vat,
            "price_discounted_excl_vat_fmt": price_fmt(self.price_discounted_excl_vat,
                                                       currency),
            "price_excl_vat": self.price_excl_vat,
            "price_excl_vat_fmt": price_fmt(self.price_excl_vat, currency),
            "currency": currency,
            "pubs_repr": pubs_repr,
            # "shelf": self.shelf.name if self.shelf else "",
            "shelf": shelf_name,
            "shelf_id": self.shelf.pk if self.shelf else None,
            "title": self.title,
            "threshold": self.threshold,
            "theme_name": theme_name,
            "theme_code": theme_code,
        }

        if in_deposits:
            res['qty_deposits'] = self.quantity_deposits()

        if with_authors:
            authors = self.authors.all()
            # comply to JS format (needs harmonization!)
            auth = [{"fields": {'name': it.name, "id": it.id}} for it in authors]
            res['authors'] = auth

        if with_publishers:
            publishers = self.publishers.all()
            # Still a bit used client side.
            pubs = [{'fields': {'name': it.name,
                                "id": it.id}} for it in publishers]
            res['publishers'] = pubs

        if with_quantity:
            res['quantity'] = self.quantity

        return res

    def get_currency(self):
        # prefer utils.card_currency(card) when possible.
        # Here, trouble with card_currency(self): 0 argument given.
        if hasattr(self, 'currency') and self.currency:
            return self.currency
        if self.data_source and 'lelivre' in self.data_source:
            return 'CHF'
        return '€'

    def get_weight_repr(self):
        "Return the weight + its unit: 400g"
        if self.weight:
            return "{} g".format(self.weight)
        return "--"

    @staticmethod
    def obj_to_list(cards, in_deposits=False, with_quantity=True,
                    with_authors=True, with_publishers=True):
        """Transform a list of Card objects to a python list.

        Used to save a search result in the session, which needs a
        serializable object, and for the api to encode to json.

        - in_deposits: bool. If true, also include the quantity of the card in deposits.

        Return: list of dicts.
        """

        return [card.to_list(in_deposits=in_deposits,
                             with_quantity=with_quantity,
                             with_authors=with_authors,
                             with_publishers=with_publishers)
                for card in cards]

    @staticmethod
    def first_cards(nb, to_list=False):
        """get the first n cards from our collection (very basic, to test)
        """
        ret = Card.objects.order_by("-created")[:nb]
        if to_list:
            ret = Card.obj_to_list(ret)
        return ret

    @staticmethod
    def cards_in_stock():
        """Return all cards in stock (will not return ones that are only in
        deposits or in lists).
        """
        return Card.objects.filter(in_stock=True)\
                           .filter(quantity__gt=0)\
                           .order_by('id')\
                           .select_related()\
                           .all()

    @staticmethod
    def search(words, card_type_id=None, distributor=None, distributor_id=None,
               to_list=False,
               publisher_id=None, place_id=None, shelf_id=None,
               deposit_id=None,
               bought=False,
               in_deposits=False,
               order_by=None,
               with_quantity=True,
               quantity_choice=None,
               price_choice=None,
               date_created=None,
               date_created_sort=None,
               page=None,
               page_size=10):
        """Search a card (by title, authors' names, ean/isbn).

        SIZE_LIMIT = 100

        - words: (list of strings) a list of key words or eans/isbns

        - card_type_id: id referencing to CardType

        - with_quantity (deprecated): if False, avoid this
          calculation. update: it *was* costly. The quantity field is now
          denormalized.

        - quantity_choice: string, one of QUANTITY_CHOICES (negative quantity, between 0 and 3, etc).
        - price_choice: string, one of PRICE_CHOICES.

        - date_created: (datetime) filter the cards by the date they were created in the stock.

        - date_created_sort: a string in "==", ">=" and "<=".

        Note that the "==" sort order works with exact datetimes. We
        currently can't search for cards that were created in a given month.

        - to_list: if True, we return a list of dicts, not Card objects.


        Pagination:
        Don't do pagination by default.
        page: page number to get.
        page_size: max elements per page.

        Returns: a 2-tuple:
        - a list of objects or a list of dicts if to_list is
        specified,
        - a dict: list of messages, pagination meta info.

        """
        isbns = []
        isbn_list_search_complete = None

        cards = []
        msgs = Messages()

        # Get all isbns, eans.
        if words:
            # Separate search terms that are isbns.
            isbns = list(filter(is_isbn, words))
            words = list(set(words) - set(isbns))

        if words:
            # Doesn't pass data validation of the view.
            head = words[0]
            # to_ascii can return None, and that's logic, but if the
            # data migration was not run, searching "iconsains=None" would error out.
            head_ascii = to_ascii(head) or head
            cards = Card.objects.filter(Q(title_ascii__icontains=head_ascii) |
                                        Q(title__contains=head) |
                                        Q(authors__name__icontains=head) |
                                        Q(authors__name_ascii__contains=head_ascii))\
                                .distinct()

            if len(words) > 1:
                for elt in words[1:]:
                    elt_ascii = to_ascii(elt) or elt
                    cards = cards.filter(Q(title_ascii__contains=elt_ascii) |
                                         Q(title__icontains=elt) |
                                         Q(authors__name__icontains=elt) |
                                         Q(authors__name_ascii__contains=elt_ascii))\
                                 .distinct()

        elif not isbns:
            cards = Card.objects.all()  # returns a QuerySets, which are lazy.

        if cards and date_created and date_created_sort:
            if date_created_sort == "<=":
                cards = cards.filter(created__lte=date_created)
            elif date_created_sort == ">=":
                cards = cards.filter(created__gte=date_created)
            elif date_created_sort == "==":
                # If the parsed date string didn't mention the day,
                # it is the first day of the month by default.
                # We can not make the difference if the user entered a day or not.
                # Therefore the "==" search only works for days.
                # For months, see the history.
                cards = cards.filter(created__month=date_created.month) \
                             .filter(created__year=date_created.year) \
                             .filter(created__day=date_created.day)
            else:
                pass

        if bought and cards:
            cards = cards.filter(in_stock=True)

        if cards and shelf_id and shelf_id not in ["0", "0"]:
            try:
                cards = cards.filter(shelf=shelf_id)
            except Exception as e:
                log.error(e)

        if cards and place_id and place_id not in ["0", "0"]:
            try:
                cards = cards.filter(placecopies__place__id=place_id)
            except Exception as e:
                log.error(e)

        if cards and deposit_id and deposit_id not in ["0", "0"]:
            try:
                cards = cards.filter(depositcopies__deposit__id=deposit_id)
            except Exception as e:
                log.error(e)

        if distributor and cards:
            cards = cards.filter(distributor__name__exact=distributor)

        if distributor_id and distributor_id not in [0, "0"] and cards:
            cards = cards.filter(distributor__id=distributor_id)

        if cards and card_type_id:
            cards = cards.filter(card_type=card_type_id)

        if cards and publisher_id:
            try:
                cards = cards.filter(publishers=publisher_id)
            except Exception as e:
                log.error("we won't search for a publisher that doesn't exist: {}".format(e))

        # Search for the requested ean(s).
        if isbns:
            try:
                cards = Card.objects.filter(isbn__in=isbns)
                if len(cards) == len(isbns):
                    isbn_list_search_complete = True
                else:
                    isbn_list_search_complete = False
            except Exception as e:
                log.error("Error searching for isbns {}: {}".format(isbns, e))
                msgs.add_error(_("Error searching for isbn ".format(isbns)))

        # Filter by quantity in stock.
        if quantity_choice and quantity_choice != "":
            # caution: values are duplicated on collectionController.ls
            if quantity_choice == "<0":
                cards = cards.filter(quantity__lt=0)
            elif quantity_choice == "0":
                cards = cards.filter(quantity=0)
            elif quantity_choice == "<=0":
                cards = cards.filter(quantity__lte=0)
            elif quantity_choice == ">0":
                cards = cards.filter(quantity__gt=0)
            elif quantity_choice == ">1":
                cards = cards.filter(quantity__gt=1)
            elif quantity_choice == ">2":
                cards = cards.filter(quantity__gt=2)
            elif quantity_choice == ">3":
                cards = cards.filter(quantity__gt=3)
            elif quantity_choice == "[1,3]":
                cards = cards.filter(quantity__gte=1).filter(quantity__lte=3)
            elif quantity_choice == "[1,5]":
                cards = cards.filter(quantity__gte=1).filter(quantity__lte=5)
            elif quantity_choice == "[3,5]":
                cards = cards.filter(quantity__gte=3).filter(quantity__lte=5)
            elif quantity_choice == "[5,10]":
                cards = cards.filter(quantity__gte=5).filter(quantity__lte=10)
            elif quantity_choice == ">10":
                cards = cards.filter(quantity__gte=10)

        if price_choice and price_choice != "":
            # caution: values are duplicated on collectionController.ls
            if price_choice == "0":
                cards = cards.filter(price=0)
            elif price_choice == "<=3":
                cards = cards.filter(price__lte=3)
            elif price_choice == "<=5":
                cards = cards.filter(price__lte=5)
            elif price_choice == "<=10":
                cards = cards.filter(price__lte=10)
            elif price_choice == "<=20":
                cards = cards.filter(price__lte=20)
            elif price_choice == "[0,5]":
                cards = cards.filter(price__gte=0).filter(price__lte=5)
            elif price_choice == "[0,10]":
                cards = cards.filter(price__gte=0).filter(price__lte=10)
            elif price_choice == "[5,10]":
                cards = cards.filter(price__gte=5).filter(price__lte=10)
            elif price_choice == ">5":
                cards = cards.filter(price__gte=5)
            elif price_choice == ">10":
                cards = cards.filter(price__gte=10)
            elif price_choice == ">20":
                cards = cards.filter(price__gte=20)

        # Sort
        if cards and order_by:
            # order_by is "-created" by default, for the first display.
            # It should be alphabetical for a custom search.
            # (it isn't set on the client)
            if distributor_id or distributor or publisher_id or\
               place_id or shelf_id:
                order_by = "title"

            if not type(cards) == list:
                # this precaution shouldn't be necessary now (fixed).
                cards = cards.order_by(order_by)

            # We must re-sort by locale, to get downcased and
            # accented letters sorted properly. See comment below and issue #122.
            if order_by != "-created":
                cards = sorted(cards, cmp=locale.strcoll, key=lambda it: it.title)

        if type(cards) == list:
            # shouldn't be necessary now (fixed).
            nb_results = len(cards)
        else:
            nb_results = cards.count()

        # Pagination
        paginator = Paginator(cards, page_size)
        if page is not None:
            try:
                cards = paginator.page(page)
            except EmptyPage:
                cards = paginator.page(paginator.num_pages)
            finally:
                cards = cards.object_list
        else:
            cards = paginator.object_list

        if to_list:
            cards = Card.obj_to_list(
                cards,
                in_deposits=in_deposits,
                with_quantity=with_quantity,
                with_authors=False,
                with_publishers=False,
            )

        meta = {
            'msgs': msgs.msgs,
            'num_pages': paginator.num_pages,
            'page': page,
            'page_size': page_size,
            'nb_results': nb_results,
            'currency': Preferences.get_default_currency(),
        }

        if isbns and len(isbns) > 1:
            meta['message'] = _("You asked for {} ISBNs. {} found.".format(len(isbns), len(cards)))
            if isbn_list_search_complete:
                meta['message_status'] = ALERT_SUCCESS
            else:
                meta['message_status'] = ALERT_WARNING

        return cards, meta

    @staticmethod
    def is_in_stock(cards):
        """Check by isbn if the given cards (dicts) are in stock.

        Return a list of dicts with new keys each:
        - "in_stock": 0/the quantity
        - "id"
        - "url": the absolute url to the card in our DB.

        Used when searching for cards on the datasource. If a result
        already exists in our DB, add the quantity and id fields.
        """
        if not cards:
            return cards

        if not type(cards) == list:
            cards = [cards]

        for card in cards:
            quantity = None
            found_id = 0
            try:
                found, _ = Card.exists(card)
                if found:
                    quantity = found.quantity
                    found_id = found.id
            except ObjectDoesNotExist:
                quantity = None
                found_id = None

            card['in_stock'] = quantity
            card['id'] = found_id
            url = reverse("card_show", args=(card['id'],))  # XXX: it switches to /en/ :(
            card['get_absolute_url'] = url
            card['url'] = url

        return cards

    @staticmethod
    def get_from_id_list(cards_id):
        """cards_id: list of card ids

        returns: a tuple Card objects, messages.
        """
        result = []
        msgs = Messages()

        for id in cards_id:
            try:
                card = Card.objects.get(id=id)
                result.append(card)
            except ObjectDoesNotExist:
                msg = _("The card of id {} doesn't exist.".format(id))
                log.debug(msg)
                msgs.add_warning(msg)
        return result, msgs.msgs

    @staticmethod
    def sell(id=None, quantity=1, place_id=None, place=None, silence=False):
        """Sell a card. Decreases its quantity in the given place.

        If it is not present anymore in the selling place (aka in its
        shelf), add it to the restocking list. If it is not present in
        stock, add it to the command list (the autocommand basket).

        This is a static method, use it like this:
        >>> Card.sell(id=<id>)

        :param int id: the id of the card to sell.
        return: a tuple (return_code, "message")

        """
        msgs = Messages()
        prefs = Preferences.prefs()
        try:
            card = Card.objects.get(id=id)

            # Get the place from where we sell it.
            place_obj = place
            if place or place_id:
                if not place and place_id not in [0, "0"]:
                    try:
                        # place_obj = card.placecopies_set.get(id=place_id)
                        place_obj = Place.objects.get(id=place_id)
                    except ObjectDoesNotExist as e:
                        if not silence:
                            log.warning('In Card.sell, can not get place of id {}: {}. Will sell on the default place.'.format(place_id, e))
                        # xxx: test here
                        place_obj = Preferences.get_default_place()
                    except Exception as e:
                        log.error('In Card.sell, error getting place of id {}: {}. Should not reach here.'.format(place_id, e))
                        return False, _("An error occured: it seems this place doesn't exist. We prefer to stop this sell.")

                # Get the intermediate table PlaceCopy, keeping the quantities.
                place_copy = None
                try:
                    place_copy, created = place_obj.placecopies_set.get_or_create(card=card)
                    if created:
                        place_copy.nb = 0
                        place_copy.save()
                except Exception as e:
                    log.error("Card.sell error filtering the place {} by id {}: {}".format(place_id, id, e))
                    return (None, MSG_INTERNAL_ERROR)  # xxx to be propagated

            else:
                # Take the first selling place this card is present in.
                if card.placecopies_set.count():
                    # XXX: get the default place
                    # fix also the undo().
                    place_copy = card.placecopies_set.filter(place__can_sell=True).first()
                    place_obj = place_copy.place
                else:
                    place_obj = prefs.get_default_place()
                    place_copy, created = place_obj.placecopies_set.get_or_create(card=card)
                    if created:
                        place_copy.nb = 0
                        place_copy.save()
                    msgs.status = ALERT_WARNING
                    msgs.add_warning(_("The card '{}' ({}) wasn't associated to any place. We had to sell it from the default place {}. This can happen if you manipulated it from lists or inventories but didn't properly add it to your stock.".format(card.title, card.id, place_obj.name)))

            place_copy.nb -= quantity
            place_copy.save()
            card.save()

        except ObjectDoesNotExist as e:
            log.warning("Requested card %s does not exist: %s" % (id, e))
            return (None, "La notice n'existe pas.")
        except Exception as e:
            log.error("Error selling a card: {}.".format(e))
            # Didn't return an error message, returned OK !
            return (None, _("Internal error, sorry."))

        # Add to the auto_command list? Depends on preferences.
        if prefs.auto_command_after_sell:
            remaining_quantity = card.quantity
            if remaining_quantity <= card.threshold:
                Basket.add_to_auto_command(card, nb=0)

        # Possibly add to the restocking list.
        if card.quantity_to_restock() > 0:
            Restocking.add_card(card)

        return msgs.status, msgs.msgs

    def sell_undo(self, quantity=1, place_id=None, place=None, deposit=None):
        """
        Do the contrary of sell(). Put the card back on the place or deposit it was sold from.
        """
        msgs = Messages()
        place_obj = place
        # deposit_obj = deposit
        if not place_obj and place_id:
            # TODO: toujours vendre depuis le lieu par défaut, filtrer par lieu par défaut, pas le first.
            place_obj = self.placecopies_set.filter(card__id=self.id).first()
        else:
            if self.placecopies_set.count() and place_obj is not None:
                place_obj = self.placecopies_set.filter(card__id=self.id, place__id=place.id).first()
            elif self.placecopies_set.count():
                place_obj = self.placecopies_set.filter(card__id=self.id).first()
            else:
                return False, {"message": _("We can not undo the sell of card {}: \
                it is not associated to any place. This shouldn't happen.").format(self.title),
                               "status": ALERT_ERROR}

        place_obj.nb = place_obj.nb + quantity
        place_obj.save()
        # TODO: add history.
        msgs.add_info("We added back {} exemplary(ies) in {}.".format(quantity, place_obj.place.name))
        self.save()

        return True, msgs.msgs

    def last_sell(self):
        """Return: the last sell datetime.
        xxx: db field for lookups ?
        """
        last_sell = None
        last_soldcard = SoldCards.objects.filter(card__id=self.id).last()
        if last_soldcard:
            last_sell = last_soldcard.created
        return last_sell

    @staticmethod
    def exists(card_dict):
        """Check if the given card already exists in the database.

        We have the same card if:
        - same isbn
        - if it has no isbn: same title, same authors and same publisher(s).

        After this check, we can add a distributor, add exemplaries, etc.

        card_dict: dictionnary

        returns: a tuple (the card object if it already exists, None oterwise / list of messages (str)).
        """
        msgs = Messages()
        # Look for the same isbn/ean
        if card_dict.get('isbn') or card_dict.get('ean'):
            isbn = card_dict.get('isbn', card_dict.get('ean'))
            clist = Card.objects.filter(isbn=isbn).first()
            return clist, msgs.msgs

        # Get the title.
        if not card_dict.get('title'):
            return None, ["Error: this card has no title."]
        clist = Card.objects.filter(title=card_dict.get('title')).all()
        no_authors, no_pubs = False, False
        if clist:
            for obj in clist:
                if card_dict.get('publishers'):
                    set_obj = set([it.name for it in obj.publishers.all()])
                    set_dict = set(card_dict.get('publishers'))
                    if not set_obj == set_dict:
                        continue

                else:
                    no_pubs = True

                if card_dict.get('authors'):
                    set_obj = set([it.name for it in obj.authors.all()])
                    set_dict = set(card_dict.get('authors'))
                    if not set_obj == set_dict:
                        continue

                else:
                    no_authors = True

                # the card passed the filter: return it.
                if not (no_authors and no_pubs):
                    return obj, msgs.msgs

            # Some cards have the same title, and not much more attributes.
            if no_authors and no_pubs:
                msgs.add_info(_("There are cards with similar titles"))
                return None, msgs.msgs  # similar titles though.

        return None, msgs.msgs

    @staticmethod
    def update_from_dict(card_obj,
                         card_dict=None,
                         authors=[],
                         distributor=None,
                         distributor_gln="",
                         publishers=[],
                         publisher_name=None):
        """
        - card_obj: Card object.
        - card_dict: dict of fields.
        - publisher_name: name of one publisher (string). We check if the card object has the same, if not we assign it to it, by creating a new publisher if required.
        - other params: objects.

        Return: the new object, saved.
        """
        assert isinstance(card_obj, models.base.Model)
        assert isinstance(card_dict, dict)
        # Update fields, except isbn (as with "else" below)
        if authors:
            # assert isinstance(authors[0], models.base.Model)
            if not isinstance(authors[0], models.base.Model):
                # log.warning("Card.update_from_dict: authors should be authors objects, we got: {}".format(authors))
                pass
            else:
                card_obj.authors = authors

        if distributor:
            if isinstance(distributor, models.base.Model):
                card_obj.distributor = distributor
            else:
                log.warning("Card.update_from_dict: distributor should be an object.")

        if distributor_gln:
            dist = None
            # Get an existing dist by GLN or create it.
            dist = Distributor.get_or_create(gln=distributor_gln)
            if dist:
                card_obj.distributor = dist

        if publishers:
            if isinstance(publishers[0], models.base.Model):
                card_obj.publishers = publishers
            else:
                log.warning("Card.update_from_dict: publishers should be a list of objects.")

        #
        elif publisher_name:
            pub_name = publisher_name.lower().strip()
            # Does the card already have this publisher?
            card_pubs = [it.name.lower().strip() for it in card_obj.publishers.all()]
            # if pub_name in card_pubs:
            #     print("-- Already the right publisher.")
            if pub_name not in card_pubs:
                # OK, we have to bind it.
                # Does a publisher of the same name exist?
                existing_pub = Publisher.objects.filter(name__iexact=pub_name).first()
                # Yes: bind it.
                if existing_pub:
                    log.debug("Replace the publisher: {} -> {}".format(card_obj.pubs_repr, existing_pub.name))
                    card_obj.publishers = [existing_pub]
                # No: create the publisher.
                else:
                    pub = Publisher(name=publisher_name)
                    pub.save()
                    card_obj.publishers = [pub]
                    log.debug("Created a new publisher: {}".format(pub))

        if card_dict.get('threshold') is not None:
            card_obj.threshold = card_dict.get('threshold')

        for field in ['title',
                      'price', 'price_bought', 'selling_price',
                      'year_published', 'date_publication', 'has_isbn',
                      'details_url', 'currency',
                      'thickness', 'height', 'width', 'weight',
                      'theme', 'presedit', 'collection']:
            if card_dict.get(field) not in [None, '', '']:
                setattr(card_obj, field, card_dict.get(field))

        if card_dict.get('isbn'):
            card_obj.isbn = card_dict.get('isbn')

        card_obj.save()
        return card_obj

    @staticmethod
    def get_or_create_from_dict(card_dict,
                                authors=[],
                                publishers=[],
                                distributor=None):
        """
        Create a new card from a dict.
        """
        assert isinstance(card_dict, dict)
        # Create the card with its simple fields.
        # Add the relationships afterwards.
        # for field, val in card_dict.items():
        #     if val in [None, '', '']:
        #         del card_dict[field]

        # We should do more data validation before this.
        # For instance, date_publication cannot be ''.
        # card_obj, created = Card.objects.get_or_create(
        #     **card_dict
        # )

        card_obj = Card(
            title=card_dict.get('title'),
            price = card_dict.get('price', 0),
            currency = card_dict.get('currency'),
            isbn = card_dict.get('isbn'),
            fmt = card_dict.get('fmt'),
            has_isbn = card_dict.get('has_isbn'),
            cover = card_dict.get('img', ""),
            details_url = card_dict.get('details_url'),
            date_publication = card_dict.get('date_publication') if card_dict.get('date_publication') else None,
            data_source = card_dict.get('data_source'),
            summary = card_dict.get('summary'),
            thickness = card_dict.get('thickness'),
            height = card_dict.get('height'),
            width = card_dict.get('width'),
            weight = card_dict.get('weight'),
            threshold = card_dict.get('threshold', THRESHOLD_DEFAULT))

        card_obj.save()

        # We can also update every field for the existing card.

        # Set the authors
        if authors:  # XXX: more tests !
            card_obj.authors = authors

        # add the distributor
        if distributor:
            card_obj.distributor = distributor

        # add many publishers
        if publishers:
            card_obj.publishers = publishers

        # add the collection
        collection = card_dict.get("collection")
        if collection:
            collection = collection.lower()
            try:
                # collection_obj, created = Collection.objects.get_or_create(name=collection)
                # card_obj.collection = collection_obj
                # Collection is not a table anymore. quickfix ensure ok
                card_obj.collection = collection
            except Exception as e:
                log.error("--- error while adding the collection: %s" % (e,))

        # add the shelf
        shelf = card_dict.get('shelf')
        shelf_id = card_dict.get('shelf_id')
        if shelf and isinstance(shelf, models.base.Model):
            card_obj.shelf = shelf
        elif shelf_id and shelf_id != "0":
            try:
                cat_obj = Shelf.objects.get(id=shelf_id)
                card_obj.shelf = cat_obj
            except Exception as e:
                log.error("error adding shelf {}: {}".format(shelf_id, e))

        # add the type of the card
        typ = "unknown"
        if card_dict.get("card_type"):
            typ = card_dict.get("card_type")

        type_obj = CardType.objects.filter(name=typ).first()
        if type_obj:
            card_obj.card_type = type_obj

        # add the publishers
        pubs = card_dict.get("publishers")
        if pubs:
            try:
                for pub in pubs:
                    if isinstance(pub, six.string_types) or isinstance(pub, six.text_type):
                        pub = pub.lower()
                        pub_obj, created = Publisher.objects.get_or_create(name=pub)
                        card_obj.publishers.add(pub_obj)

            except Exception as e:
                log.error("--- error while adding the publisher: {}".format(e))

        return card_obj

    @staticmethod
    def from_dict(card, to_list=False):
        """Add or edit a card from a dict.

        Check if it already exists in the db (the card may have no
        isbn). If so, update its secondary fields.

        Format of dict:
            title:      string
            year:       int or None
            authors:    list of authors names (list of str) or list of Author objects.
            shelf:   id (int)
            distributor: object or new name of a Distributor (deprecated: has accepted an id)
            distributor_id: id of a Distributor
            publishers: list of names of publishers (create one on the fly, like with webscraping), or list of objects
            publishers_ids: list of ids of publishers
            has_isbn:   boolean
            isbn:       str
            price:     int
            currency:  str (euro, chf)
            details_url: url (string)
            date_publication: string. Human readable date, coming from the scraped source. Gets parsed to a Date.
            card_type:  name of the type (string)
            location:   string
            in_stock:   bool
            sortkey:    string of authors in the order they appear on
                        the cover
            shelf_id:   id (int) of the shelf.
            threshold: int

        return: a tuple Card object created or existing, message (str).
        """
        if not isinstance(card, dict):
            raise TypeError("Card.from_dict expects a dict, and got a {}.".
                            format(type(card)))

        msgs = Messages()
        msg_success = _("Card saved.")  # both for creation and edit: simple message.
        # msg_exists = _("This card already exists.")

        # Unknown year is okay
        try:
            year = int(card.get('year'))
            card['year'] = date(year, 1, 1)
        except Exception:
            card['year'] = None

        # Make the card
        # Get authors or create
        card_authors = card.get('authors', [])
        if card.get('authors'):
            auts = card_authors
            if not isinstance(auts, list):
                auts = [auts]
            if isinstance(auts[0], six.string_types) or isinstance(auts[0], six.text_type):
                new_authors = []  # appending to card_authors used in the loop: infinite recursion!
                for aut in auts:
                    author, created = Author.objects.get_or_create(name=aut)
                    new_authors.append(author)
                card_authors = new_authors

        # Get and clean the ean/isbn (beware of form data)
        isbn = card.get("isbn", card.get("ean", ""))
        if isbn:
            isbn = isbn_cleanup(isbn)
            card['isbn'] = isbn

        # Get the distributor:
        # it's either already an object
        card_distributor = card.get('distributor')
        # or an id.
        if card.get('distributor_id'):
            res = Distributor.objects.filter(pk=card.get('distributor_id'))
            if res:
                card_distributor = res.first()

        # or a new name.
        if card_distributor and isinstance(card_distributor, six.string_types)\
           or isinstance(card_distributor, six.text_type)\
           or isinstance(card_distributor, int):

            if isinstance(card_distributor, int):
                # Kept the inner if logic to check old cases.
                # Hopefully we don't encounter those now.
                log.warning(_("card from_dict: we found a distributor argument with type int: this shouldn't happen, the id should be given in distributor_id. distributor gets an object or a name (str)."))

            try:
                # OK: card: edit -> card_create
                card_distributor, noop = Distributor.objects.get_or_create(name=card.get("distributor"))
            except Exception as e:
                # XXX use distributor_id and distributor
                # Fix in JS and view. But where ? :S
                # Was (at least) in cardCreateController, only used for edit now.
                # Should be OK...
                try:
                    it = card.get('distributor')
                    it_id = 1
                    if isinstance(it, six.string_types) or isinstance(it, six.text_type):
                        it_id = it
                    elif isinstance(it, dict):
                        it_id = it.get('id')
                    else:
                        log.warning("We couldn't handle the distributor of this form inside this card: {}.".format(card))
                    card_distributor = Distributor.objects.get(id=it_id)
                except Exception as e:
                    log.warning("couldn't get distributor of {}. This is not necessarily a bug.".format(card.get('distributor')))

        # Get the shelf
        card_shelf = None
        if card.get('shelf'):
            try:
                card_shelf, created = Shelf.objects.get_or_create(name=card.get('shelf'))
            except Exception as e:
                log.warning("couldn't get or create the shelf {}: {}.".format(card.get('shelf'), e))

        elif card.get('shelf_id') and not is_invalid(card.get('shelf_id')):
            try:
                card_shelf = Shelf.objects.get(id=card.get('shelf_id'))
            except Exception as e:
                log.warning("Creating/editing card: couldn't get shelf of id {}. We won't register a shelf for this card.".format(card.get('shelf_id')))

        # Get the publishers:
        card_publishers = card.pop('publishers', [])
        if card_publishers and isinstance(card_publishers[0], models.base.Model):
            pass

        elif card_publishers and (isinstance(card_publishers[0], six.string_types) or
                                  isinstance(card_publishers[0], six.text_type)):
            pubs = []
            for name in card_publishers:
                pub = Publisher.objects.filter(name__iexact=name)
                if pub:
                    pubs.append(pub.first())
                else:
                    pub = Publisher.objects.create(name=name)
                    pubs.append(pub)
            card_publishers = pubs

        elif card.get('publishers_ids'):
            card_publishers = [Publisher.objects.get(id=it) for it in card.get('publishers_ids')]  # noqa: F812 ignore "it" redefinition.

        # Get the publication date (from a human readable string)
        date_publication = None
        if card.get('date_publication') and not is_invalid(card.get('date_publication')):
            if isinstance(card.get('date_publication'), six.string_types) \
               or isinstance(card.get('date_publication'), six.text_type):
                try:
                    date_publication = dateparser.parse(card.get('date_publication'))  # also languages=['fr']
                    card['date_publication'] = date_publication
                except Exception as e:
                    log.warning("Error parsing the publication date of card {}: {}".format(card.get('title'), e))
                    card['date_publication'] = None

        # Check if the card already exists (it may not have an isbn).
        if card.get('id'):
            try:
                exists_list = Card.objects.get(id=card.get('id'))
            except ObjectDoesNotExist:
                log.error("Creating/editing card, could not find card of id {}. dict: {}".format(card.get('id'), card))
                msgs.add_error("Could not find card of id {}".format(card.get('id')))
                return None, msgs.msgs

        else:
            exists_list, _msgs = Card.exists(card)
            msgs.append(_msgs)

        default_currency = Preferences.get_default_currency()
        card['currency'] = default_currency

        #######################################################
        # Update existing card.
        #######################################################
        if exists_list:
            card_obj = Card.update_from_dict(
                exists_list,
                card_dict=card,
                authors=card_authors,
                distributor=card_distributor,
                publishers=card_publishers,
            )

        ######################################################
        # Create new card.
        ######################################################
        else:
            card_obj = Card.get_or_create_from_dict(
                card_dict=card,
                authors=card_authors,
                distributor=card_distributor,
                publishers=card_publishers,
            )

        # Update fields of new or existing card.
        # add the quantity of exemplaries: in "move" view.

        # # Add the default place (to the intermediate table).
        # try:
        #     default_place = Preferences.objects.all()[0].default_place
        #     place_copy, created = PlaceCopies.objects.get_or_create(card=card_obj, place=default_place)
        #     place_copy.nb = 1
        #     place_copy.save()
        # except Exception as e:
        #     log.error("--- error while setting the default place: %s" % (e,))

        # add the shelf
        if card_shelf:
            try:
                card_obj.shelf = card_shelf
            except Exception as e:
                log.error(e)

        # We add a card in the stock when we buy it (add it in a place).
        in_stock = False
        if 'in_stock' in card and card['in_stock']:
            in_stock = card.get('in_stock')
        try:
            card_obj.in_stock = in_stock
        except Exception as e:
            log.error('Error while setting in_stock of card {}: {}'.format(card.get('title'), e))

        if card.get('price') is not None:
            card_obj.price = float(card.get('price'))
        if card.get('price_bought') is not None:
            card_obj.price_bought = float(card.get('price_bought'))
        if card.get('selling_price') is not None:
            card_obj.selling_price = float(card.get('selling_price'))

        card_obj.save()

        card = card_obj
        if to_list:
            card = card_obj.to_dict()

        return card, [msg_success]

    def get_absolute_url(self):
        # The current user language is given from the UI and set in the api point.
        return reverse("card_show", args=(self.id,))

    def remove_card(self, place=None, movement=None):
        """
        Remove this card from a place.

        Find what's the place to remove it from, and call the method on this place.
        """
        try:
            if not place:
                place = self.places.first() or Preferences.get_default_place()
        except Exception as e:
            log.error(u"Error taking the first place of {}: {}".format(self.pk, e))
            place = Preferences.get_default_place()

        place.add_copy(self, nb=-1)
        # self.quantity -= 1
        # self.save()
        return True

    @staticmethod
    def remove_card_id(id):
        card = Card.objects.filter(id=id).first()
        return card.remove_card()

    def add_card(self, place=None, movement=None):
        """
        Add this card to a place.
        """
        try:
            if not place:
                place = self.places.first() or Preferences.get_default_place()
        except Exception as e:
            log.error(u"Error taking the first place of {}: {}".format(self.pk, e))
            place = Preferences.get_default_place()

        place.add_copy(self, is_box=True)
        return True

    @staticmethod
    def add_card_id(id):
        card = Card.objects.filter(id=id).first()
        return card.add_card()

    def display_year_published(self):
        "We only care about the year"
        return self.year_published.strftime('%Y')

    def set_sortkey(self):
        "Generate a sortkey"

        if not self.sortkey and self.authors:
            self.sortkey = ', '.join([a.name for a in self.authors.all()])
            self.save()

    def is_in_deposits(self):
        """
        Is this card in deposits ?
        Return: a boolean.
        """
        # We only look at its presence in a deposit /state/.
        # We don't have a mapping Card <-> Deposit any more, only -> DepositState.
        # We don't know here in how many deposits it is.
        return self.depositstate_set.count() > 0

    def quantity_deposits(self):
        """Quantity of this card in deposits (actually, in deposits' states).

        - Return: int
        """
        return sum(self.depositstatecopies_set.all().values_list('nb_current', flat=True))

    def quantity_selling_places(self):
        """
        Return the quantity in selling places (aka, the quantity remaining
        in the shelves, not in the stock).
        """
        return sum(self.placecopies_set.filter(place__can_sell=True).values_list('nb', flat=True))

    def quantity_boxes(self):
        """
        Get to know the boxes this card is in.

        Return: a tuple (nb, box id, box name).
        """
        res = None
        basket_copies = self.basketcopies_set.filter(basket__is_box=True)
        if basket_copies:
            res = basket_copies.values_list('nb', 'basket__id', 'basket__name')
        return res

    def quantity_reserve(self):
        """
        Return the quantity in no-selling places (aka, the stock)
        """
        return sum(self.placecopies_set.filter(place__can_sell=False).values_list('nb', flat=True))

    def quantity_to_restock(self):
        """
        Return the quantity that we can move from the stock
        place to the selling place.
        """
        if self.quantity <= 0:
            return 0
        ideal_quantity = 1 - self.quantity_selling_places()
        res = min(max(0, ideal_quantity), self.quantity_reserve())
        return res

    def quantity_to_command(self):
        """
        Quantity in the to_command list.
        """
        return Basket.auto_command_quantity_of(self)

    def get_first_deposit(self):
        names_ids = self.deposits
        if names_ids:
            return Deposit.objects.get(id=names_ids[0][1])

    @property
    def deposits(self):
        """
        Return the list of Deposits that contain or have contained this card.

        - return: a list of tuples of deposit name and id.
        """
        values_list = self.depositstatecopies_set.\
            values_list('deposit_state__deposit__name',
                        'deposit_state__deposit__id',
            ).\
            distinct()
        return values_list

    @staticmethod
    def never_sold(page=None, pagecount=20):
        # 2020-01-31 - removed from dashboard
        notsold = Card.objects.filter(in_stock=True).exclude(id__in = SoldCards.objects.all().values_list('id', flat=True))
        if page is not None:
            notsold = notsold[page:page + pagecount]
        return notsold

    @staticmethod
    def never_sold_nb():
        nb = Card.objects.filter(in_stock=True).exclude(id__in = SoldCards.objects.all().values_list('id', flat=True)).count()
        return nb

    def commands_received(self, to_list=False):
        """
        Return a list of this card's last received commands, sorted the most recent one first.
        """
        # Get command_copies objects (card, quantity) of commands *received*.
        cmd_copies = self.commandcopies_set.filter(command__date_received__isnull=False).all()
        return cmd_copies

    def commands_pending(self):
        """
        Return the pending commands (not received).
        """
        cmd_copies = self.commandcopies_set.filter(command__date_received__isnull=True).all()
        return cmd_copies


@python_2_unicode_compatible
class PlaceCopies (models.Model):
    """Copies of a card present in a place.
    """
    # This is the join table defined in Card with the "through" argument:
    # https://docs.djangoproject.com/en/1.5/topics/db/models/#intermediary-manytomany

    # so than we can add custom fields to the join.
    #: The card
    card = models.ForeignKey("Card")
    #: The place
    place = models.ForeignKey("Place")

    #: Number of copies
    nb = models.IntegerField(default=0)

    def __str__(self):
        return "%s: %i exemplaries of \"%s\"" % (self.place.name, self.nb, self.card.title)


@python_2_unicode_compatible
class Place (models.Model):
    """A place can be a selling point, a warehouse or a stand.
    """
    #: Name of this place
    name = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("name"))

    #: Copies: PlaceCopies

    #: Date of creation
    date_creation = models.DateField(auto_now_add=True, verbose_name=__("creation date"))
    #: Date of deletion
    date_deletion = models.DateField(null=True, blank=True, verbose_name=__("deletion date"))
    #: Is this place a stand ?
    is_stand = models.BooleanField(default=False, verbose_name=__("is stand?"))
    #: Is it allowed to sell books from here ?
    can_sell = models.BooleanField(default=True, verbose_name=__("can sell?"))
    #: Are we doing an inventory on it right now ?
    inventory_ongoing = models.BooleanField(default=False, verbose_name=__("inventory ongoing"))
    #: Optional comment
    comment = models.TextField(null=True, blank=True, verbose_name=__("comment"))

    class Meta:
        ordering = ("name",)
        verbose_name = __("place")
        verbose_name_plural = __("places")

    def __str__(self):
        return "{}".format(self.name)

    def get_absolute_url(self):
        prefs = Preferences.prefs()
        return "/{}/databasesearch/place/{}/".format(prefs.language if prefs.language else "en",
                                                     self.id)  # TODO: url paramaters for stock search

    @staticmethod
    def card_to_default_place(card_obj, nb=1):
        # Add the card to the default place (to the intermediate table).
        try:
            default_place = Preferences.get_default_place()
            place_copy, created = PlaceCopies.objects.get_or_create(card=card_obj, place=default_place)
            place_copy.nb += nb
            place_copy.save()
        except Exception as e:
            log.error("--- error while setting the default place: %s" % (e,))

    def move(self, dest, card, nb, create_movement=True):
        """Move the given card from this place to "dest" and create an history
        movement (unless create_movement is set to False).

        - dest: Place object
        - nb: quantity (int)

        return: Boolean

        """
        try:
            pc = self.placecopies_set.filter(card__id=card.id).first()
            pc.nb = pc.nb - nb
            pc.save()
            dest_copies = dest.placecopies_set.filter(card__id=card.id).first()
            if not dest_copies:
                dest_copies = dest.placecopies_set.create(card=card, place=dest)
                dest_copies.save()
            dest_copies.nb += nb
            dest_copies.save()
            # Delete the intermediate object when nb is 0, so a search
            # filter by this place doesn't erronously return (see card.search: we
            # filter by the place id present in placecopies).
            # That broke placecopies_set.get => used .filter() and first().
            if dest_copies.nb == 0:
                dest_copies.delete()

            if create_movement:
                mvt = history.InternalMovement(origin=self, dest=dest, card=card, nb=nb)
                mvt.save()
            return True
        except Exception as e:
            log.error(e)
            return False

    def remove(self, card, quantity=1):
        """
        Remove this card from this place, with this quantity.
        Used for example for movements out of the stock that are not sells.

        Ignore negative quantities.
        """
        # to remove many cards in a single transaction, use
        # with atomic.transaction
        if quantity >= 0:
            pc = self.placecopies_set.filter(card__id=card.id)
            # Place.move deletes the placecopies object when
            # quantity = 0, for accurate search purposes.
            if pc:
                pc = pc.first()
            else:
                pc = self.placecopies_set.create(card=card, place=self)

            pc.nb -= quantity
            pc.save()
            card.quantity = card.quantity_compute()  # update denormalized fields (like the quantity).
            card.save()

    def to_dict(self):
        # Could (should?) do with django serializers but its output is a bit too much.
        return {
            "id": self.id,
            "name": self.name,
            "date_creation": self.date_creation.isoformat(),
            "date_deletion": self.date_deletion.isoformat() if self.date_deletion else None,
            "is_stand": self.is_stand,
            "can_sell": self.can_sell,
            "inventory_ongoing": self.inventory_ongoing,
            "comment": self.comment,
        }

    def cards(self):
        """Return all cards in this place.
        To get the card and its quantity, use the PlaceCopies table."""
        cards_qties = self.placecopies_set.all()
        return [it.card for it in cards_qties]

    def add_copy(self, card, nb=1, add=True, is_box=False):
        """Adds the given number of copies (1 by default) of the given
        card to this place.

        Create an Entry movement.

        Be sure to update the card.quantity denormalized field. Saving
        a Card object is enough as it re-computes it.

        If arg "add" is False, set the quantity instead of summing it.

        - card: a card object or an id (int)
        - nb: the number of copies to add (optional).

        returns:
        - nothing

        """
        if isinstance(card, int) or isinstance(card, six.text_type) or isinstance(card, six.string_types):
            card = Card.objects.filter(id=card).first()

        assert isinstance(card, Card)

        if not isinstance(nb, int):
            # log.warning("nb '{}' is not an int: the quantity was malformed".format(nb))
            nb = 1

        try:
            place_copy, created = self.placecopies_set.get_or_create(card=card)
            if add:
                place_copy.nb += nb
            else:
                place_copy.nb = nb
            place_copy.save()

            # XXX: when a quantity reaches 0, we might want to remove it. See remove_card.

            # A card could be in the DB but only in a list
            # (basket). Now it's bought at least once.
            # Saving the card also updates the quantity field (computed from the places).
            card.in_stock = True
            if is_box:
                card.quantity += nb
            card.save()

        except Exception as e:
            log.error("Error while adding %s to the place %s" % (card.title, self.name))
            log.error(e)
            return 0

        # Add a log to the Entry history
        try:
            if nb > 0:
                history.Entry.new([card])
            elif nb < 0:
                history.OutMovement.new([card], reason=_(u"Moved to box"), typ="box")
        except Exception as e:
            log.error("Error while adding an Entry to the history for card {}:{}".format(card.id, e))

        return place_copy.nb

    def add_copies(self, cards):
        """Adds the given list of cards objects. A simple and uncomplete
        wrapper to "add_copy" for consistency. Use the latter instead.

        """
        # with transaction.atomic() ?
        start = timezone.now()
        for it in cards:
            self.add_copy(it)
        end = timezone.now()
        print("ADD_COPIES for {} cards TOOK {}".format(len(cards), end - start))
        return True

    def remove_card(self, card):
        """Remove this card from this place.
        If all went well, return True."""
        try:
            place_copy, created = self.placecopies_set.get_or_create(card=card)
            place_copy.delete()

        except Exception as e:
            log.error("Error while removing %s to the place %s" % (card.title, self.name))
            log.error(e)
            return False

        return True

    def quantities_total(self):
        """Total quantity of cards in this place.
        Return: int (None on error)
        """
        try:
            return sum(self.placecopies_set.values_list('nb', flat=True))
        except Exception as e:
            log.error("Error getting the total quantities in place {}: {}".format(self.name, e))

    def quantity_cards(self):
        return self.quantities_total()

    def quantity_titles_no_stock(self):
        """
        Quantity of titles with no more exemplary in this place (quantity lower or equal to 0).
        """
        try:
            return self.placecopies_set.filter(nb__lte=0).count()
        except Exception as e:
            log.error("Error getting the quantity of titles with no stock in place {}: {}".format(self.name, e))

    def quantity_titles_one_copy(self):
        """
        Quantity of titles that have only one exemplary left in this place.
        """
        try:
            return self.placecopies_set.filter(nb=1).count()
        except Exception as e:
            log.error("Error getting the quantity of titles with one exemplary in place {}: {}".format(self.name, e))

    def quantity_titles(self):
        """
        Total quantity of titles in this place (not exemplaries).
        """
        try:
            return self.placecopies_set.count()
        except Exception as e:
            log.error("Error getting the total of titles in place {}: {}".format(self.name, e))

    def quantity_of(self, card):
        """How many copies of this card do we have ?

        - card: a card object.
        """
        try:
            place_copies = self.placecopies_set.filter(card__id=card.id)
            if len(place_copies) > 1:
                log.error("more than 1 place_copies for a place and card {}, this shouldn't happen.".format(card))
                return -1
            if place_copies:
                return place_copies[0].nb
            else:
                return 0
        except Exception as e:
            log.error("Error getting quantity_of for card {} on place {}: {}".format(card, self, e))
            raise e

    @cached(cache=TTLCache(maxsize=1024, ttl=7200))  # 2 hours
    def cost(self):
        """
        Total cost of this place: nb of cards * their price.
        """
        try:
            res = self.placecopies_set.filter(card__price__isnull=False).\
                filter(nb__gte=1).\
                annotate(cost=ExpressionWrapper(F('nb') * F('card__price'),
                                                output_field=FloatField()))
            cost = sum([it.cost for it in res])
            return cost
        except Exception as e:
            log.error("Error getting cost of place {}: {}".format(self.name, e))
            return 0

    @cached(cache=TTLCache(maxsize=1024, ttl=7200))  # 2 hours
    def cost_excl_taxes(self):
        """
        Total cost of this place excluding taxes: nb of cards * their price
        excl taxes, which depends if the card is a book or not.
        """
        type_book = CardType.objects.filter(name="book").first()
        book_vat = Preferences.get_vat_book() / 100
        other_vat = Preferences.get_vat_other_product() / 100

        def is_book(tup):
            return tup[2] == type_book.pk or (tup[1] and tup[1].startswith('97'))

        copies = self.placecopies_set.filter(card__price__isnull=False).\
            values_list('card_id',
                        'card__isbn',
                        'card__card_type',
                        'card__price',
                        'nb')
        # start = timezone.now()
        res = 0
        # books = [it for it in copies if is_book(it)]
        # print("--- nb of books: {}".format(len(books)))
        # print("--- nb of non- books: {}".format(len(copies) - len(books)))
        for it in copies:
            price = it[-2]
            nb = it[-1]
            if price and nb > 0:
                if is_book(it):
                    res += nb * (price - price * book_vat)
                else:
                    res += nb * (price - price * other_vat)
        # print("--- summing: {}".format(res))
        # end = timezone.now()
        # print(" --- took: {}".format(end - start))
        return res

@python_2_unicode_compatible
class Preferences(models.Model):
    """
    Default preferences.
    """
    #: Name of the asso/group running this project. To appear in bills and emails.
    asso_name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True,
                                 verbose_name=__("bookshop name"))  # XXX to use in preferences
    #: What place to add the cards by default ? (we register them, then move them)
    default_place = models.OneToOneField(Place, verbose_name=__("default place"))
    #: VAT, the tax, for books.
    vat_book = models.FloatField(null=True, blank=True, default=5.50, verbose_name=__("book vat"))
    #: VAT, the tax, for other products (non books).
    vat_other_product = models.FloatField(null=True, blank=True, default=20.0, verbose_name=__("other products VAT"))
    #: the default language: en, fr, es, de.
    #: Useful for non-rest views that must set the language on the url or for UI messages.
    language = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True, verbose_name=__("language"))
    #: All other, newer preferences. They don't need to be stored in DB. Here: JSON, as text.
    #: - default_currency
    #: - sell_discounts
    others = models.TextField(null=True, blank=True)

    default_currency = "€"  # just a cached variable. XXX: explain why and where.

    default_discounts = [0, 5, 9, 20, 30]
    default_discounts_with_labels = []
    for i, it in enumerate(default_discounts):
        default_discounts_with_labels.append({'name': '{}%'.format(it),
                                              'discount': it,
                                              'id': i})

    auto_command_after_sell = models.BooleanField(blank=True, default=False, verbose_name=__("Automatically command? After a sell, if the quantity of the book gets below its minimal quantity, add the book to the list of commands."))

    class Meta:
        verbose_name = __("Preferences")

    def __str__(self):
        return "default place: {}, vat: {}".format(self.default_place.name, self.vat_book)

    def to_dict(self):
        res = {}
        res['asso_name'] = self.asso_name
        res['default_place'] = self.default_place.name
        res['default_place_id'] = self.default_place.id

        others = self.others
        if others:
            others = json.loads(others)
            res['default_currency'] = others['default_currency']
            sell_discounts = others['sell_discounts']
            sell_discounts_with_labels = [{'discount': 0,
                                           'name': '0%',
                                           'id': 0}]
            for i, it in enumerate(sell_discounts, start=1):
                sell_discounts_with_labels.append({'discount': it,
                                                   'name': '{}%'.format(it),
                                                   'id': i})
            if sell_discounts:
                res['sell_discounts'] = sell_discounts
                res['sell_discounts_with_labels'] = sell_discounts_with_labels

        else:
            res['default_currency'] = '€'
            res['sell_discounts'] = self.default_discounts
            res['sell_discounts_with_labels'] = self.default_discounts_with_labels

        return res

    @staticmethod
    def prefs():
        """
        Return a Preferences object.
        """
        prefs = Preferences.objects.first()
        # One should be created at Abelujo creation.
        if not prefs:
            place = Place.objects.first()
            if place is None:
                log.warning("We have no place in DB, but we should have one and keep one.")
                place = Place.objects.create(name="default place")
                place.save()
            prefs = Preferences.objects.create(default_place=place)
            prefs.save()

        return prefs

    @staticmethod
    def setprefs(**kwargs):
        """
        Change preferences.

        Return: tuple list of messages, status code.
        """
        # status = ALERT_SUCCESS
        msgs = Messages()
        prefs = Preferences.prefs()
        if not prefs:
            msgs.add_info(_("There is no preferences"))
            return msgs.status, msgs.msgs

        for key, val in list(kwargs.items()):
            if val is not None:
                if key == 'default_place' and not prefs.default_place == val:
                    try:
                        prefs.default_place = val
                        prefs.save()
                    except Exception as e:
                        log.error("Error while setting preferences: {}".format(e))
                        # status = ALERT_ERROR

                elif key == 'vat_book':
                    try:
                        prefs.vat_book = val
                        prefs.save()
                    except Exception as e:
                        log.error("Error setting preferences VAT: {}".format(e))
                        msgs.add_error(_("Error while setting the vat"))

                else:
                    prefs.__setattr__(key, val)
                    prefs.save()

        return msgs.status, msgs.msgs

    @staticmethod
    def get_default_place():
        """
        Return the default place object, or the first place of the DB
        (the one that should be created at the installation).
        - return: a place object.
        """
        try:
            if Preferences.objects.count():
                place = Preferences.prefs().default_place
                if place is not None:
                    return place
                else:
                    place = Place.objects.first()
                    prefs = Preferences.prefs()
                    assert place is not None
                    if place:
                        prefs.default_place = place
                        prefs.save()
                    return place
            else:
                return Place.objects.first()
        except Exception as e:
            log.warning("Could not get the default place: {}".format(e))
            return Place.objects.first()

    @staticmethod
    def get_vat_book():
        """
        Return the vat on books, as set in the preferences.
        - return: percent (float, between 0 and 100).
        """
        vat_book = 5.50
        try:
            vat = Preferences.prefs().vat_book
        except Exception:
            vat = vat_book

        if vat is not None:
            return vat
        else:
            return vat_book

    @staticmethod
    def get_vat_other_product():
        """
        Return the vat for everything else (in France, non books are taxed at 20%).
        - return: percent (float, 0 < 100)
        """
        vat_other_product = 20.0
        try:
            vat = Preferences.prefs().vat_other_product
        except Exception:
            vat = vat_other_product

        if vat is not None:
            return vat
        else:
            return vat_other_product

    @staticmethod
    def get_default_currency():
        try:
            currency = json.loads(Preferences.prefs().others)
            Preferences.default_currency = currency
            return currency.get('default_currency', '€').upper()
        except Exception:
            pass

    @staticmethod
    def price_excl_tax(price):
        """Given a price (float), return it minus the current tax.
        """
        tax = Preferences.get_vat_book()
        if tax:
            return roundfloat(price - price * tax / 100)
        return price


@python_2_unicode_compatible
class BasketCopies(TimeStampedModel):
    """Copies present in a basket (intermediate table).
    """
    card = models.ForeignKey("Card")
    basket = models.ForeignKey("Basket")
    nb = models.IntegerField(default=0)

    def __str__(self):
        return "Basket %s: %s copies of %s" % (self.basket.name, self.nb, self.card.title)

    def to_dict(self):
        """Card representation and its quantity in the basket.

        Return: a dict, with 'basket_qty'.
        """
        card = []
        try:
            card = self.card.to_dict()
            card['basket_qty'] = self.nb
            card['modified'] = self.modified.strftime(DATE_FORMAT)
        except Exception as e:
            log.error(e)

        return card

    @property
    def quantity(self):
        # should rename the arg
        return self.nb

@python_2_unicode_compatible
class Basket(models.Model):
    """A basket is a set of copies that are put in it for later use. Its
    copies can be present in the stock or not. Manipulating a basket's
    copies has no consequences on physical copies of the stock.
    """
    # This class is really similar to PlaceCopies. Do something about it.
    #: Name of the basket
    name = models.CharField(max_length=CHAR_LENGTH, verbose_name=__("name"))
    #: Type of the basket (preparation of a command, a stand, other, etc)
    basket_type = models.ForeignKey("BasketType", null=True, blank=True, verbose_name=__("basket type"))
    #: Copies in it:
    copies = models.ManyToManyField(Card, through="BasketCopies", blank=True)
    # Access the intermediate table with basketcopies_set.all(), basketcopies_set.get(card=card)
    #: Comment:
    comment = models.CharField(max_length=TEXT_LENGTH, blank=True, null=True, verbose_name=__("comment"))
    #: We can also choose a supplier for this basket.
    #: This will help when applying the basket to the stock, receiving a parcel, etc.
    distributor = models.ForeignKey(Distributor, blank=True, null=True, verbose_name=__("distributor"))
    archived = models.BooleanField(default=False, verbose_name=__("archived"))
    archived_date = models.DateField(blank=True, null=True, verbose_name=__("date archived"))

    #: Box: adding a book removes it from the stock.
    # Specially used for commands to school libraries etc.
    is_box = models.BooleanField(default=False, verbose_name=__("Behave like a box? Adding a book removes it from the stock."))

    class Meta:
        ordering = ("name",)
        verbose_name = __("Basket")

    def __str__(self):
        return "{}".format(self.name)

    def get_absolute_url(self):
        return "/baskets/##{}".format(self.id)

    def to_dict(self):
        return {"name": self.name,
                "id": self.id,
                "length": self.copies.count(),
                "comment": self.comment,
                "distributor": self.distributor.name if self.distributor else "",
                "dist_repr": self.distributor.__repr__() if self.distributor else "",
        }

    @staticmethod
    def auto_command_basket():
        """
        Return the basket used as the list of commands.
        Check its existence.
        """
        try:
            basket, created = Basket.objects.get_or_create(name="auto_command")
            return basket
        except Exception as e:
            log.error(u"Error getting or creating the basket of commands: {}".format(e))
            return None

    @staticmethod
    def auto_command_nb():
        """Return the number of cards in the auto_command basket, if any.

        (the basket may not exist in tests).
        """
        try:
            return Basket.objects.get(name="auto_command").copies.count()
        except Exception:
            return 0

    @staticmethod
    def auto_command_quantity_of(card):
        """
        Return the quantity to command of this card.
        """
        basket = Basket.objects.get(name="auto_command")
        basket_copy = basket.basketcopies_set.filter(card=card).first()
        if basket_copy:
            return basket_copy.nb
        else:
            return 0

    @staticmethod
    def auto_command_copies(dist_id=None, unicodesort=True):
        """
        Return a list of basket copies (also with their quantity in the
        basket) from the autocommand list.

        dist_id can be:
          - an id: filter by this distrubutor id.
          - 0: get all cards that don't have a distributor.
          - "all": get all cards to command.

        Return: a queryset of BasketCopies.
        """
        if dist_id is not None and dist_id not in ["all", u"all"]:
            dist_id = int(dist_id)
        try:
            basket = Basket.objects.get(name="auto_command")
            if dist_id in [0, '0', '0']:
                copies_qties = basket.basketcopies_set.\
                               filter(card__distributor_id__isnull=True)\
                               .order_by('card__title')
            elif dist_id in ["all", u"all"]:
                copies_qties = basket.basketcopies_set.all()
            elif dist_id:
                copies_qties = basket.basketcopies_set\
                                     .filter(card__distributor_id=dist_id)\
                                     .order_by("card__title")
            else:
                copies_qties = basket.basketcopies_set.all()

        except Exception as e:
            log.error(e)
            return []

        # speed up sorting by title.
        copies_qties = copies_qties.select_related()

        # Here accented letters are not sorted correctly:
        # e ... z ... é
        # I'm afraid we have to resort to Python here, even though there is an ICU SQLite extension.
        # So, sort with the locale. It also sorts correctly regarding the case:
        # E..É..d..F
        start = timezone.now()
        if unicodesort:
            copies_qties = sorted(copies_qties, cmp=locale.strcoll, key=lambda it: it.card.title)
        end = timezone.now()
        print("-- sorting took {}".format(end - start))

        return copies_qties

    @staticmethod
    def new(name=None, box=False):
        """Create a new basket.

        - name: name (str)
        - box: if True, this basket is a box.

        - Return: a 3-tuple with the new basket object (None if a pb occurs), along with the status and messages.
        """
        status = True
        msgs = Messages()
        if not name:
            msgs.add_error(_("Please provide the name of the new basket"))
            return None, status, msgs.msgs

        try:
            b_obj = Basket.objects.create(name=name, is_box=box)
            b_obj.save()
            # msg = {'level': ALERT_SUCCESS,
            # 'message': _("New basket created")}
        except Exception as e:
            log.error("Pb when trying to create a new basket: {}".format(e))
            msgs.add_error(_("We could not create a new basket. This is an internal error."))
            return None, False, msgs.msgs

        return b_obj, status, msgs.msgs

    @staticmethod
    def boxes():
        return Basket.objects.exclude(archived=True).filter(is_box=True)

    @staticmethod
    def search(pk, distributor_id=None):
        """
        Return the list of cards of this basket, filter by the given criteria.
        - pk: id of the basket to search in.

        Parameters:
        - distributor_id

        Return: a queryset (without all()).
        """
        copies = BasketCopies.objects.filter(basket_id=pk)
        if distributor_id in [0, '0', '0', -1, '-1', '-1']:
            copies = copies.filter(card__distributor__isnull=True)
        elif distributor_id in ["all", u"all"]:
            # take all.
            pass
        elif distributor_id is not None:
            copies = copies.filter(card__distributor_id=distributor_id)
        return copies

    def archive(self):
        self.archived = True
        self.archived_date = timezone.now()
        self.save()
        return True

    def add_copy(self, card, nb=1):
        """
        Adds the given card to the basket.

        If the basket is a box, remove 1 quantity from the stock.

        If no relation already exist with the card, create one.

        - nb: nb to add (1 by default)
        """
        try:
            basket_copy, created = self.basketcopies_set.get_or_create(card=card)
            if nb != 0:
                basket_copy.nb += nb
                basket_copy.save()

            # box? Remove from the stock.
            if basket_copy.basket.is_box:
                card.remove_card()
                # TODO: create movement

        except Exception as e:
            log.error("Error while adding a card to basket %s: %s" % (self.name, e))

    def set_copy(self, card=None, nb=1, card_id=None):
        """
        Set the given card's quantity.
        """
        if not card and card_id:
            try:
                card = Card.objects.get(id=card_id)
            except Exception as e:
                log.error("Basket set_copy: couldn't get card of id {}: {}".format(card_id, e))

        try:
            basket_copy, created = self.basketcopies_set.get_or_create(card=card)
            previous_nb = basket_copy.nb
            difference = previous_nb - nb

            basket_copy.nb = nb
            now = pendulum.now()
            basket_copy.modified = now
            basket_copy.save()

            # Box? Remove from the stock.
            # Because on the client side we don't distinguish a click on the upper
            # or the down arrow,
            # we don't know if this is an addition or a removal.
            # We have to check ourselves.
            # In case of a "box" list, add or remove the quantity and register a movement.
            if basket_copy.basket.is_box:
                if difference > 0:
                    card.add_card()
                elif difference < 0:
                    card.remove_card()

                # TODO: movement

        except Exception as e:
            log.error('Error while setting the cards {} quantity: {}'.format(card.id, e))

    def add_copies(self, card_ids):
        """Add the given list of card ids to this basket.

        card_ids: list of card ids (int)

        return: an alert dictionnary (level, message)
        """
        cards = Card.objects.filter(id__in=card_ids).all()
        return self.add_cards(cards)

    def add_cards(self, cards):
        """
        Add these cards to the basket.
        To add from a list of ids, use `add_copies`.

        - cards: objects

        return: an alert dictionnary (level, message)
        """
        for it in cards:
            try:
                self.add_copy(it)
            except Exception as e:
                log.error("Error while getting card of id {}: {}".format(id, e))
                return {'level': ALERT_ERROR, 'message': "Internal error"}

        return {'level': ALERT_SUCCESS, 'message': _("The cards were successfully added to the basket '{}'".format(self.name))}

    def remove_copy(self, card_id, is_box=False):
        """
        Remove the given card (id) from the basket.

        If the basket was a box, put the copies back in the stock.
        """
        status = True
        msgs = Messages()
        nb = 0
        try:
            inter_table = self.basketcopies_set.filter(card__id=card_id)
            if inter_table:
                inter_table = inter_table.first()
                nb = inter_table.nb
                inter_table.delete()
                msgs.add_success(_("The card was successfully removed from the basket"))
            else:
                log.warning("Card not found in the intermediate table when removing card {} from basket{} (this is now a warning only).".format(card_id, self.id))

            if is_box and nb:
                place = Preferences.get_default_place()
                place.add_copy(card_id, nb=nb, is_box=True)  # by saving the card, sets the quantity.
                # TODO: movement

        except ObjectDoesNotExist as e:
            log.error("Card not found when removing card {} from basket{}: {}".format(card_id, self.id, e))
            status = False
            msgs.add_error(_("Card not found"))
        except Exception as e:
            log.error("Error while trying to remove card {} from basket {}: {}".format(card_id, self.id, e))
            status = False
            msgs.add_error(_("Could not remove the card from the command basket. This is an internal error."))

        return status, msgs.msgs

    def remove_copies(self, card_ids):
        """Remove a list of card ids.
        """
        for id in card_ids:
            self.remove_copy(id)

    def empty(self):
        """
        Remove all the cards of this basket.
        """
        self.basketcopies_set.all().delete()
        return True

    def sell_basket(self, client_id=None):
        """
        Sell this basket's cards.

        - client_id

        Return: a tuple status, list of messages (dicts).
        """
        msgs = Messages()
        ids_prices_quantities = []
        try:
            copies = self.basketcopies_set.all()
            # not optimum Sell API.
            prices = copies.values_list('card__price', flat=True)
            quantities = copies.values_list('nb', flat=True)
            for i, copy in enumerate(copies):
                ids_prices_quantities.append({
                    'id': copy.card.id,
                    'price_sold': prices[i],
                    'quantity': quantities[i],
                })
            now = timezone.now()
            sell, status, alerts = Sell.sell_cards(
                ids_prices_quantities,
                date=now,
                client_id=client_id,
            )
        except Exception as e:
            msgs.add_error(u'An error occured trying to sell the books from this basket.')
            log.error("Error selling basket {}: {}".format(self.pk, e))
        return msgs.status, msgs.msgs

    def quantity(self, card=None, card_id=None):
        """Return the total quantity of copies in it, or the quantity of the given card.

        card: card object
        card_id: id (int)

        return: int.
        """
        if not card:
            return sum([it.nb for it in self.basketcopies_set.all()])
        else:
            it = card or card_id
            return self.basketcopies_set.get(card=it).nb

        return -1

    @staticmethod
    def add_to_auto_command(card, nb=1):
        """
        Add the given Card object to the basket for auto commands.

        This function is called both automatically after a sell and manually from the Card page, "add to command" button.
        """
        if isinstance(card, int) or isinstance(card, six.string_types) or isinstance(card, six.text_type):
            card = Card.objects.filter(id=card).first()
        try:
            assert isinstance(card, Card)
            basket = Basket.auto_command_basket()
            basket.add_copy(card, nb=nb)
        except ObjectDoesNotExist:
            # that's ok here, specially in tests.
            pass
        except Exception as e:
            log.error("Error while adding the card {} to the auto_command basket: {}.".format(card.id, e))
            raise e
        try:
            res = card.quantity_to_command()
        except Exception as e:
            res = -99
        return res

    def to_deposit(self, distributor=None, name=""):
        """Transform this basket to a deposit.

        Beware: the cards of have the same distributor or they'll be rejected.

        - distributor: a distributor object or id (int)
        - name: the deposit name
        - dep_type: the deposit type (see DEPOSIT_TYPES_CHOICES)

        Return: a tuple the deposit object with a list of error messages
        """
        msgs = Messages()
        if type(distributor) == int:
            try:
                distributor = Distributor.objects.get(id=distributor)
            except ObjectDoesNotExist as e:
                log.error("Basket to deposit: the given distributor of id {} doesn't exist: {}".format(distributor, e))
                return None, []

        if not distributor:
            msg = _("Basket to deposit: no distributor. Abort.")
            log.error(msg)
            msgs.add_error(msg)
            return None, msgs.msgs

        if not name:
            msg = _("Basket to deposit: no name given.")
            log.error(msg)
            msgs.add_error(msg)
            return None, msgs.msgs

        dep = Deposit(name=name)
        dep.distributor = distributor
        try:
            dep.save()
            cards_qty = self.basketcopies_set.all()
            copies = [it.card for it in cards_qty]
            qties = [it.nb for it in cards_qty]
            _status, _msgs = dep.add_copies(copies, quantities=qties)
            msgs.append(_msgs)
        except Exception as e:
            log.error("Basket to deposit: error adding copies: {}".format(e))
            msgs.add_error(_("Error adding copies"))

        return dep, msgs.msgs

    def create_return(self):
        """
        Return all the cards of this basket to their supplier (publisher, distributor).
        The cards are removed from the stock. The movement is recorded in an OutMovement.
        The basket must have a publisher or a distributor.

        The basket is archived.

        Return: a tuple Out movement, Messages object.
        """
        # The logic goes in OutMovement.
        msgs = Messages()
        if not self.distributor:
            return None, msgs.add_info(_("This basket has no distributor to "
                                          "return the cards to."))

        out = history.OutMovement.return_from_basket(self)
        msgs.add_success(_(u"Return succesfully created."))
        # Here, we return the msgs object, though earlier we return the
        # msgs.msgs list of messages. Inconsistent, but better…
        return out, msgs


@python_2_unicode_compatible
class BasketType (models.Model):
    """
    """

    name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return "{}".format(self.name)


@python_2_unicode_compatible
class ReturnBasket(Basket):
    """
    A ReturnBasket is a set of copies that will be returned to their supplier.

    When a card is added to it, that means the bookseller puts it aside his stock, so
    the card is removed from the stock. This is the difference with a regular basket.
    """

    def __str__(self):
        return "{}".format(self.name)

    def add_copy(self, card, nb=1):
        """
        Contrary to a regular basket, remove the card from the stock.
        """
        # This is the only method to override from Basket.
        # add_copies and add_cards call this method, which removes the card(s) from
        # the default place.
        try:
            basket_copy, created = self.basketcopies_set.get_or_create(card=card)
            basket_copy.nb += nb
            basket_copy.save()

            # remove from the stock.
            place = Preferences.get_default_place()
            place.remove(card, quantity=nb)
            return True

        except Exception as e:
            log.error("Error while adding a card to basket %s: %s" % (self.name, e))

    def remove_copy(self, card_id):
        """
        Remove from the basket and replace back the card in stock.
        """
        # mostly copy-pasted :/
        # because we should return the removed quantity, but this is a breaking change...
        status = True
        msgs = Messages()
        quantity = None
        try:
            inter_table = self.basketcopies_set.filter(card__id=card_id)
            if inter_table:
                inter_table = inter_table.first()

                # Re-putthe card in stock.
                quantity = inter_table.nb
                card = inter_table.card
                place = Preferences.get_default_place()
                place.add_copy(card, nb=quantity)

                inter_table.delete()
                msgs.add_success(_("The card was successfully removed from the basket"))
            else:
                log.warning("Card not found in the intermediate table when removing card {} from basket{} (this is now a warning only).".format(card_id, self.id))

        except ObjectDoesNotExist as e:
            log.error("Card not found when removing card {} from basket{}: {}".format(card_id, self.id, e))
            status = False
            msgs.add_error(_("Card not found"))
        except Exception as e:
            log.error("Error while trying to remove card {} from basket {}: {}".format(card_id, self.id, e))
            status = False
            msgs.add_error(_("Could not remove the card from the command basket. This is an internal error."))

        return status, msgs.msgs


@python_2_unicode_compatible
class Reception(Basket):

    def __str__(self):
        return "Reception {}".format(self.name)

    @staticmethod
    def ongoing():
        """
        Get or create the ongoing reception.
        """
        res = Reception.objects.filter(archived=False).first()
        if not res:
            res = Reception.objects.create()
        return res

    @staticmethod
    def validate():
        msgs = Messages()
        reception = Reception.ongoing()
        try:
            reception.archive()
        except Exception as e:
            raise e
        return True, msgs

    @staticmethod
    def copies(to_list=False):
        """
        Get the copies/quantities of the ongoing Reception.
        """
        reception = Reception.ongoing()
        copies = reception.basketcopies_set.all()
        if to_list:
            return [it.to_dict() for it in copies]
        return copies

    def add_copy(self, card_id, shelf_id=None, nb=1, set_quantity=False):
        """
        Adds the given card to the reception list AND to the stock, from its id.

        - nb: nb to add (1 by default)
        - if set_quantity is True, set it instead of adding.

        Return: a tuple status, Messages object.
        """
        MSG_NO_SHELF = _("Veuillez choisir le rayon de cette notice.")
        # MSG_DIFFERENT_SHELF = _("Attention cette notice avait déjà un rayon.")
        msgs = Messages()
        origin_qty = None  # decide if we must add or substract from the stock.
        try:
            reception = Reception.ongoing()
            basket_copy, created = self.basketcopies_set.get_or_create(basket=reception,
                                                                       card_id=card_id)
            if not set_quantity and nb != 0:
                # add
                basket_copy.nb += nb
                basket_copy.save()
            elif set_quantity and nb:
                # set
                origin_qty = basket_copy.nb
                basket_copy.nb = nb
                basket_copy.save()

            if not shelf_id and not basket_copy.card.shelf_id:
                msgs.add_info(MSG_NO_SHELF)
            elif shelf_id and not basket_copy.card.shelf_id:
                shelf_obj = Shelf.objects.filter(pk=shelf_id).first()
                if shelf_obj:
                    basket_copy.card.shelf = shelf_obj
                    basket_copy.card.save()
                else:
                    log.warning("reception.add_copy: the shelf id {} does not exist.".format(shelf_id))
                    msgs.add_error("Something went wrong")
            elif shelf_id and basket_copy.card.shelf_id and shelf_id != basket_copy.card.shelf_id:
                # shelves are different, choose.
                # msgs.add_info(MSG_DIFFERENT_SHELF)
                pass

        except Exception as e:
            log.error("Error while adding a card to the reception list %s: %s" % (self.pk, e))
            msgs.add_error("Error while adding a card to the reception list.")
            return False, msgs

        try:
            # On client side, a click on +1 or -1 (default number input widget)
            # doesn't make a difference. Do we add or substract from the stock?
            place = Preferences.get_default_place()
            if set_quantity:
                nb_difference = basket_copy.nb - origin_qty
                place.add_copy(card_id, nb=nb_difference)
            else:
                place.add_copy(card_id)

        except Exception as e:
            log.error("Error while adding a card to the stock place, from the reception %s: %s" % (self.pk, e))
            msgs.add_error(_("Something went wrong."))
            return False, msgs

        return True, msgs


@python_2_unicode_compatible
class RestockingCopies(models.Model):
    """
    Cards present in the restocking list with their quantities (intermediate table).
    """
    card = models.ForeignKey("Card", blank=True, null=True)
    restocking = models.ForeignKey("Restocking")
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return "Restocking: %s copies of %s" % (self.quantity, self.card.title)

    def to_dict(self):
        """
        Card representation and its quantity in the list.

        Return: a dict, with the added 'list_qty'.
        """
        card = []
        try:
            card = self.card.to_dict()
            card['list_qty'] = self.quantity
        except Exception as e:
            log.error(e)

        return card


class Restocking(models.Model):
    """A list of cards to move from the stock place to their shelves.

    All cards here are candidates to be moved. We can move a selection of them.
    They are taken out of this list with an InternalMovement.

    The movement procedure can detect inaccuracies in the stock. The
    stock indeed can change between the card's entry in the list and
    the moment the user does the restocking (another user might have
    done another movement).

    Likewise, the user is able to correct stock errors (s)he sees in
    the stock: if he sees that there actually remains one exemplary in
    the shelf, he can remove the card from this list.

    He must be able to set the shelf target easily.
    """
    # copies = models.OneToManyField(Card, through="RestockingCopies", blank=True)
    # Has a many-to-one relationship with RestockingCopies.
    pass

    def get_absolute_url(self):
        return "/restocking/"

    @staticmethod
    def get_or_create():
        restock = Restocking.objects.first()
        if not restock:
            restock = Restocking()
            restock.save()
        return restock

    def to_dict(self):
        return {
                "id": self.id,
                "length": self.copies.count(),
        }

    @staticmethod
    def cards():
        """
        Return the list of cards that we need to move from the stock place to the selling one.

        We must re-filter the list, it is possible that cards where moved since
        they were added to the restocking list.
        """
        restock = Restocking.get_or_create()
        copies = restock.restockingcopies_set.all()
        # cards = [it.card for it in copies]
        res = []
        for copy in copies:
            if copy.card.quantity_selling_places() <= 0:
                res.append(copy.card)
            else:
                copy.delete()

        return res

    @staticmethod
    def card_exists(pk):
        """
        Return True if this card (by id so far) exists in the Restocking list.
        """
        # XXX: not used so far, only used a bit for development.
        res = RestockingCopies.objects.filter(card_id=pk).count()
        return res > 0

    @staticmethod
    def add_card(card):
        try:
            restock = Restocking.get_or_create()
            copy, created = restock.restockingcopies_set.get_or_create(card=card)
            qty_to_restock = copy.card.quantity_to_restock()
            if qty_to_restock > 0:
                copy.quantity += qty_to_restock
                copy.save()

        except Exception as e:
            log.error("Error while adding '%s' to the list of restocking" % (card.title))
            log.error(e)
            return 0

        return qty_to_restock

    @staticmethod
    def remove_card_id(pk):
        assert isinstance(pk, (six.text_type, int))  # first type checking?!
        try:
            res = RestockingCopies.objects.filter(card_id=pk)
            if res:
                copy = res[0]
                copy.delete()
        except Exception as e:
            log.error("Error while removing the card {} from the restocking list: {}".format(pk, e))

        return True

    @staticmethod
    def remove_card(card):
        """
        Remove this card from the restocking list.
        If all went well, return True.
        """
        # TODO:
        try:
            restock = Restocking.objects.first()
            place_copy, created = restock.restockingcopies_set.get_or_create(card=card)
            place_copy.delete()

        except Exception as e:
            log.error("Error while removing %s to the restocking list" % (card.title))
            log.error(e)
            return False

        return True

    @staticmethod
    def nb_ongoing():
        """
        Total quantity of cards in the restocking list (not the number of copies to move).
        Return: int (None on error)
        """
        try:
            restock = Restocking.get_or_create()
            return restock.restockingcopies_set.count()
        except Exception as e:
            log.error("Error getting the total quantities in the restocking list: {}".format(e))

    @staticmethod
    def validate(cards=None, quantities=None):
        """
        Validate the current list: move the cards and create a movement.
        If a list of cards is given, move only these ones and leave the others.
        If a list of quantities is given, use them, otherwise use the default.
        """
        if quantities:
            assert len(cards) == len(quantities)

        restock = Restocking.get_or_create()
        if not cards:
            cards = restock.cards()

        # To create the internal movement,
        # we currently support one stock place and one selling place.
        # It could be customized for each card.
        origin = Place.objects.filter(can_sell=False).first()
        dest = Place.objects.filter(can_sell=True).first()

        for (i, card) in enumerate(cards):
            copy = restock.restockingcopies_set.filter(card=card).first()
            # filter VS get: when we re-run the script (manual
            # testing), it is possible that a card has already been
            # removed from the list and its movement created.
            if copy:
                if quantities:
                    qty = int(quantities[i])
                else:
                    qty = copy.quantity
                copy.delete()
                origin.move(dest, card, qty)

        return True


@python_2_unicode_compatible
class DepositStateCopies(models.Model):
    """For each card of the deposit state, remember:

    - the number of cards,
    - its pourcentage,
    """
    card = models.ForeignKey(Card)
    deposit_state = models.ForeignKey("DepositState")
    #: Remember sells about this card.
    sells = models.ManyToManyField("Sell")
    #: the quantity of the card at this deposit state creation.
    #: Should be equal to the nb_current of the previous one,
    #: and to nb_current + nb_sells.
    nb_initial = models.IntegerField(default=0)
    #: the current quantity of the card (at the date of the deposit state).
    nb_current = models.IntegerField(default=0)
    #: number of wanted copies.
    # nb_wanted = models.IntegerField(default=1)
    #: quantity to command to the distributor.
    # nb_to_command = models.IntegerField(default=1)
    #: quantity to return. (beware, some distributors ask a card not
    # to stay longer than a certain time in a deposit)
    nb_to_return = models.IntegerField(default=0)

    def __str__(self):
        return "card {}, initial: {}, current: {}, sells: {}, etc".format(
            self.card.id, self.nb_initial, self.nb_current, self.nb_sells)

    @property
    def nb_sells(self):
        """The number of sells since the last deposit state (*not* the number
        of copies sold).
        """
        return self.sells.count()

    @property
    def nb_cards_sold(self):
        """Re-compute the number of copies sold, with a DB query.
        It should be equal to nb_cards_sold.
        """
        total = 0
        for sell in self.sells.all():
            total += sum([it.quantity for it in sell.soldcards_set.filter(card__id=self.card_id).all()])
        return total


@python_2_unicode_compatible
class DepositState(models.Model):
    """Deposit states. We do a deposit state to know what cards have been
    sold since the last deposit state, so what sum do we need to pay to
    the distributor.

    We need to close alerts related to the cards of the deposit before
    to begin a deposit state.

    Once the deposit state is validated, it can't be modified any
    more.

    """
    deposit = models.ForeignKey("Deposit")
    # "created" could be inherited with TimeStampedModel but we want
    # it to be more precise (timezone.now())
    created = models.DateTimeField(blank=True, null=True)
    copies = models.ManyToManyField(Card, through="DepositStateCopies", blank=True)
    closed = models.DateTimeField(blank=True, null=True)
    # closed = models.DateField(default=None, blank=True, null=True)

    def __str__(self):
        ret = "{}, deposit '{}' with {} copies. Closed ? {}".format(
            self.id, self.deposit, self.copies.count(), self.closed)
        return ret

    @property
    def nb_initial(self):
        """
        Quantity at the beginning of this checkout (not at the creation of the deposit).
        """
        return self.depositstatecopies_set.aggregate(
            models.Sum('nb_initial'))['nb_initial__sum']

    @property
    def nb_current(self):
        """
        Sum all the current quantities of all cards for this deposit state.
        """
        return self.depositstatecopies_set.aggregate(
            models.Sum('nb_current'))['nb_current__sum']

    @property
    def nb_sells(self):
        """
        Sum of the Sell transactions for all the cards of this deposit state.
        (*not* the number of cards sold.)
        """
        # don't aggregate, here nb_sells isn't a field but a property.
        return sum([it.nb_sells for it in self.depositstatecopies_set.all()])

    @property
    def nb_cards_sold(self):
        """
        Number of copies sold, counting all the cards of this deposit state.
        """
        return sum([it.nb_cards_sold for it in self.depositstatecopies_set.all()])

    def quantity_of(self, card):
        """
        Return the current number of the given card in this deposit state.
        """
        depcopies = self.depositstatecopies_set.filter(card=card).all()
        if not depcopies:
            return 0
        else:
            if len(depcopies) != 1:
                log.warning("len(depcopies) != 1, this shouldn't happen.")
            return depcopies.last().nb_current

    def add_copies(self, copies, nb=1, quantities=[]):
        """Add the given list of copies objects to this deposit state.

        - copies: list of Card objects, or ids
        - quantities: list of their respective quantities (int). len(quantities) must equal len(copies).

        return: (status, msgs)

        """
        # note: use this method only at the beginning, then use add_soldcard
        msgs = Messages()
        status = True
        try:
            for (i, copy) in enumerate(copies):
                if len(quantities) == len(copies):
                    qty = quantities[i]
                else:
                    qty = nb

                if isinstance(copy, six.string_types) or isinstance(copy, six.text_type):
                    copy = Card.objects.get(id=copy)

                depositstate_copy, created = self.depositstatecopies_set.get_or_create(card=copy)
                depositstate_copy.nb_current += qty
                depositstate_copy.save()

            return status, msgs.msgs

        except Exception as e:
            log.error("Error while adding a card to the deposit state: {}".format(e))
            msgs.add_error(_("An error occured while adding a card to the deposit state."))
            return None, msgs.msgs

    def sell_card(self, card=None, nb=1, sell=None):
        """Sell the given card: decrement its quantity.

        - sell: a sell object created beforehand, to remember the sells and link to them.

        Return: tuple status / messages (list of str)
        """
        msgs = Messages()
        try:
            dscopies = self.depositstatecopies_set.filter(card__id=card.id)
        except Exception:
            msgs.add_warning(_("Error getting card {}  on this deposit state.".format(card.title)))
            return msgs.status, msgs.msgs

        if not dscopies:
            log.warning("The card {} was not found on this deposit.".format(card.title))
            msgs.add_warning(_("The card {} was not found on this deposit state.".format(card.title)))
            return msgs.status, msgs.msgs

        state_copy = dscopies[0]
        state_copy.nb_current -= nb
        # Remember the sell:
        if sell:
            state_copy.sells.add(sell)
        else:
            log.warning("You didn't specify a Sell object when selling from the deposit {}, and you should.".format(self.id))

        state_copy.save()

        return msgs.status, msgs.msgs

    def sell_undo(self, card, quantity=1):
        """
        Undo the sell of the given card for this deposit.
        Return: the current quantity in this deposit state.

        We didn't remove the sell object.
        """
        deposit_state = self.depositstatecopies_set.filter(card__id=card.id)
        deposit_state = deposit_state.last()
        deposit_state.nb_current += quantity
        deposit_state.save()
        return deposit_state.nb_current

    def card_balance(self, card_id):
        """Get the balance of the given card. For each card sold, get:
        - its current quantity,
        - the number of sells,
        - the wanted quantity,
        - etc (see DepositStateCopies)

        card_id: int

        return: a DepositStateCopies object.
        """
        try:
            states = self.depositstatecopies_set.filter(card__id=card_id)
        except Exception as e:
            log.error(e)

        if len(states) > 1:
            log.warning("The card {} has more than one entry in the intermediate table.".format(card_id))
        return states[0]

    def total_price(self):
        return self.total_cost()

    def total_cost(self):
        """
        Return the current total cost of this deposit state (not the
        initial, the current, considering nb_current).
        """
        depocopies = self.depositstatecopies_set.all()
        total_current = 0
        for it in depocopies:
            if it.card.price is not None:
                # It happened that cards have no price (missed data in scrapers).
                total_current += it.card.price * it.nb_current
        return total_current

    @property
    def total_sells(self):
        sells = self.depositstatecopies_set.first()
        if sells:
            sells = sells.sells.all()
        return sum([it.total_price_init for it in sells])

    @property
    def total_to_pay(self):
        total_sells = self.total_sells
        discount = 0
        if self.deposit.distributor and self.deposit.distributor.discount:
            discount = self.deposit.distributor.discount
        return total_sells * discount / 100 if discount else total_sells

    @property
    def margin(self):
        return self.total_sells - self.total_to_pay

    def cards_balance(self):
        """
        Get the balance of all cards of the deposit.
        """
        cards_balance = []

        for card in self.copies.all():
            cards_balance.append((card, self.card_balance(card.id)))

        return cards_balance

    def close(self):
        """
        return: a tuple status / list of messages (str).
        """
        # with alerts: check there are no ambiguous sells. To finish.
        self.closed = timezone.now()
        self.save()
        return True, []


@python_2_unicode_compatible
class Deposit(TimeStampedModel):
    """Deposits. The bookshop received copies (of many cards) from
    a distributor but didn't pay them yet.

    A bookshop can only have one deposit per card.

    On the contrary, someone acting as a publisher can also create
    deposits: it sends copies to many bookshops. Thus a card can be in
    many deposits of a type 'publisher'.

    Implementation details
    ---

    When we create the deposit, we must remember the original quantity
    of each card.

    A deposit comes with a deposit state (sometimes called
    "checkout"). A deposit has informations about cards, sometimes far
    away in time, like at its creation, or the last time we paid the
    supplier. So a deposit state stores the up to date information.

    There are two important classes to work with: Deposit and
    DepositState. Each takes count of variables for each Card in
    intermediate classes ("...Copies").

    To create a Deposit:
    - create the base object
    - add copies to it with deposit.add_copies
    - add sells with update_soldcards


    Sometimes we want to see the actual state of the deposit: how many
    cards did we sell, how many are there left, how much shall I pay
    the distributor ? The DepositState tracks those information. After
    an update(), we can call for a balance() (or directly
    checkout_balance() from a deposit).

    At a moment, we will freeze the deposit state. We can pay the
    distributor and carry on using the deposit and seeing balances.

    """
    name = models.CharField(unique=True, max_length=CHAR_LENGTH, verbose_name=__("name"))
    #: the distributor (or person) we have the copies from.
    distributor = models.ForeignKey(Distributor, blank=True, null=True, verbose_name=__("distributor"))

    #: To include cards, use add_copy/ies.

    #: type of the deposit. Some people also sent their books to a
    #: library and act like a distributor.
    deposit_type = models.CharField(choices=DEPOSIT_TYPES_CHOICES,
                                    default="fix",
                                    max_length=CHAR_LENGTH,
                                    verbose_name=__("deposit type"))

    #: in case of a deposit for a publisher, the place (client?) who
    #: we send our cards to.
    dest_place = models.ForeignKey(Place, blank=True, null=True, verbose_name=__("destination place"))
    #: due date for payment (optional)
    due_date = models.DateField(blank=True, null=True, verbose_name=__("due date"))
    #: minimal number of copies to have in stock. When not, do an action (raise an alert).
    minimal_nb_copies = models.IntegerField(blank=True, null=True, default=0,
                                            verbose_name=__("Minimun number of copies to have in stock"))
    #: auto-command when the minimal nb of copies is reached ?
    # (for now: add to the "to command" basket).
    auto_command = models.BooleanField(default=True,
                                       verbose_name=__("Automatically mark the cards to command"))
    #: Comment.
    comment = models.TextField(null=True, blank=True, verbose_name=__("comment"))

    class Meta:
        ordering = ("name",)
        verbose_name = __("deposit")

    def __str__(self):
        return "Deposit '{}' with distributor: {} (type: {})".format(
            self.name, self.distributor, self.deposit_type)

    def save(self, *args, **kwargs):
        """
        Override the save method to create the initial deposit state.
        """
        super(Deposit, self).save(*args, **kwargs)
        self.ensure_open_depostate()
        return self

    def ensure_open_depostate(self):
        """
        Ensure that we have an ongoing open DepositState.
        Return an open deposit state.
        """
        if not self.depositstate_set.count():
            depostate = DepositState.objects.create(deposit=self)
            return depostate
        last = self.depositstate_set.last()
        if last and last.closed:
            depostate = DepositState.objects.create(deposit=self)
            return depostate
        return last

    @property
    def depositstate(self):
        """
        Return the last DepositState object.
        """
        return self.depositstate_set.last()

    @property
    def ongoing_depostate(self):
        """
        Return an ongoing, open DepositState object.
        """
        return self.ensure_open_depostate()

    def copies(self):
        """
        List of cards currently in this deposit.
        """
        return self.ongoing_depostate.copies.all()

    @property
    def last_checkout_date(self):
        closed = self.depositstate_set.filter(closed__isnull=False)
        if not closed.count():
            return None
        last_closed = closed.last()
        return last_closed.closed

    @property
    def total_init_price(self):
        """Get the total value of the initial stock.
        """
        # total price of the first checkout.
        if not self.depositstate_set.count():
            return -1
        first_checkout = self.depositstate_set.first()
        return first_checkout.total_cost()

    @property
    def total_current_price(self):
        return self.total_current_cost

    @property
    def total_current_cost(self):
        depostate = self.ongoing_depostate
        return depostate.total_cost()

    @property
    def init_qty(self):
        """
        Initial quantity of cards, at the creation of the deposit.
        Return: int.
        """
        if not self.depositstate_set.count():
            return 0
        creation_depostate = self.depositstate_set.first()
        return creation_depostate.nb_current

    @property
    def checkout_nb_initial(self):
        """
        The quantity of cards at the beginning of the ongoing deposit state.
        Not the quantity at the deposit creation.
        """
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.nb_initial

    @property
    def checkout_nb_current(self):
        """
        Quantity of cards in the ongoing checkout.
        """
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.nb_current

    @property
    def checkout_nb_cards_sold(self):
        """
        Number of sells for the ongoing checkout.
        """
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.nb_cards_sold  # TODO:

    @property
    def checkout_total_sells(self):
        """
        Total of the sells of the ongoing checkout for this deposit.
        """
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.total_sells

    @property
    def checkout_total_to_pay(self):
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.total_to_pay

    @property
    def checkout_margin(self):
        """
        Margin on the sells of the current checkout.
        """
        if not self.depositstate_set.count():
            return 0
        return self.ongoing_depostate.margin

    def get_absolute_url(self):
        prefs = Preferences.prefs()
        if prefs.language:
            # should use a session.
            # The Deposits page, a django view, can't read the *current* language (on url) for now.
            translation.activate(prefs.language)

        return reverse("deposits_view", args=(self.id,))

    def to_list(self):
        return self.to_dict()

    def to_dict(self):
        ret = {
            "id": self.id,
            "name": self.name,
            "distributor": self.distributor.name if self.distributor else "",
            "due_date": self.due_date.isoformat() if self.due_date else "",
        }
        return ret

    def add_copies(self, copies, nb=1, quantities=[], **kwargs):
        """
        Add the given list of copies objects to this deposit. If their
        distributors don't match, exit. If the given copies don't
        have a distributor yet, set it.

        - copies: list of Card objects or ids.
        - quantities: list of their respective quantities (int). len(quantities) must equal len(copies).

        return: status (bool), list of messages (Message.msgs)

        """
        # TODO: check new cards aren't in another deposit already ?
        msgs = Messages()
        if not distributors_match(copies):
            msgs.add_warning(_("The cards should be all of the same supplier."))
            return False, msgs.msgs

        checkout = self.ongoing_depostate
        status, msgs = checkout.add_copies(copies, nb=nb, quantities=quantities)

        # Add a log to the Entry history.
        typ_deposit = 2
        history.Entry.new(copies, typ=typ_deposit)

        return status, msgs

    def add_copy(self, card_obj, nb=1, add=True):
        """
        Add a card object to this deposit.

        - nb (int): quantity to add
        - add (bool): if False, do not add the quantities but set them.
        """
        return self.add_copies([card_obj], nb=nb, add=add)

    def remove_card(self, card):
        """Remove this card from this deposit.
        If all went well, return True."""
        # TODO:
        raise NotImplementedError

    @staticmethod
    def from_dict(depo_dict):
        """
        Create a deposit from the given dictionnary.
        Add cards, and create an initial checkout.

        Thanks to the form validation, we are sure the deposit's name is unique.

        depo_dict: dictionnary with the required Deposit
        fields. Copies and Distributor are objects.
        - copies: a list of Card objects
        - quantities: a list of their respective quantities (int)

        returns: a tuple with: the new Deposit object, a Messages object.
        """
        msgs = Messages()

        copies_to_add = depo_dict.pop('copies')
        qties = []
        if 'quantities' in depo_dict:
            qties = depo_dict.pop('quantities', [])

        if 'dest_place' in depo_dict:
            dest_place_id = depo_dict.pop('dest_place')

        if depo_dict.get("auto_command") == "true":
            depo_dict["auto_command"] = True

        if depo_dict.get('due_date') == 'undefined':
            depo_dict['due_date'] = None

        # TODO: If any that copies don't belong to that distributor: fail.
        # *before* we create the deposit.

        # TODO: Check the cards are not already in a deposit. Allowed for a deposit of type publisher.

        # Normal case.
        # Check name exists.
        if Deposit.objects.filter(name=depo_dict['name']):
            msgs.add_error(_("A deposit of that name already exists."))
            return None, msgs

        # Create the deposit.
        try:
            dep = Deposit.objects.create(**depo_dict)
        except Exception as e:
            log.error("Adding a Deposit from_dict error ! {}".format(e))
            msgs.add_error(_("internal error, sorry !"))
            return None, msgs

        # Add copies.
        try:
            _status, _msgs = dep.add_copies(copies_to_add, quantities=qties)
            msgs.append(_msgs)
            msgs.add_success(_("The deposit was successfully created."))
        except Exception as e:
            log.error("Adding a Deposit from_dict error ! {}".format(e))
            # Delete previously created deposit (we want an atomic operation).
            dep.delete()
            msgs.add_error(_("internal error, sorry !"))
            return dep, msgs

        # Create our initial deposit state.
        dep.checkout_create()

        # Link to the destination place, if any.
        if dep and dest_place_id:
            try:
                dep.dest_place = Place.objects.get(id=dest_place_id)
                dep.save()
            except Exception as e:
                log.error("Error adding a Deposit from dict: {}".format(e))
                msgs.add_error(_("Error adding a deposit"))

        return dep, msgs

    def sell_card(self, card=None, card_id=None, nb=1, sell=None, silence=False):
        """Sell a card from this deposit state: decrement its quantity,
        register the sell object.

        Return a tuple: a status (bool) and a list of messages (str).
        """
        msgs = Messages()
        if not (card or card_id):
            msgs.add_warning(_("Please provide a card or a card id."))
            return msgs.status, msgs.msgs

        if card_id:
            try:
                card = Card.objects.get(id=card_id)
            except Exception as e:
                if not silence:
                    log.error("Exception while getting card of id {}: {}".format(card_id, e))
                msgs.add_error(_("The card of id {} does not exist is this deposit.".format(card_id)))
                return msgs.status, msgs.msgs

        if card:
            co = self.ongoing_depostate
            co.sell_card(card=card, sell=sell, nb=nb)
            return msgs.status, msgs.msgs

        else:
            return None, []

    def sell_undo(self, card=None, quantity=1):
        """
        Undo the sell, put the exemplary back.
        """
        msgs = Messages()
        try:
            state = self.ongoing_depostate
            state.sell_undo(card=card, quantity=quantity)

        except Exception as e:
            log.error("Error undoing the sell of card {} for deposit {}: {}".format(card, self.id, e))
            msgs.add_error(_("Error undoing the sell of card '{}' for deposit {}".format(card.title, self.name)))
            return msgs.status, msgs.msgs

        return msgs.status, msgs.msgs

    def quantity_of(self, card):
        """
        How many copies of this card do we have in the current deposit state ?

        - card: a card object.

        Return: int
        """
        checkout = self.ongoing_depostate
        return checkout.quantity_of(card)

    def nb_alerts(self):
        """Is the distributor of this deposit concerned by open alerts ? If
        so, we can not start a deposit checkout.

        Return: integer, the number of alerts.
        """
        raise NotImplementedError

    def checkout_create(self):
        """
        Do a deposit checkout:
        - register it
        - record all the cards of the deposit that have been sold since the last checkout,
        [- if there are alerts (ambiguous sold cards): don't close it]

        Close it manually.

        return: tuple (DepositState object or None, list of messages (str))
        """
        # There should be always an ongoing, open deposit state.
        # Create a checkout = close the current one, register what should be,
        # open a new one and report the current quantities.
        # We should find sells that are related to this deposit.
        # Or, we should always say that we sell from a deposit: simpler.
        co = self.ongoing_depostate
        co.close()
        new = DepositState.objects.create(deposit=self)
        # Report the current cards and quantities from the old to the new one.
        for it in co.depositstatecopies_set.all():
            ds, created = new.depositstatecopies_set.get_or_create(card=it.card)
            ds.nb_current = it.nb_current
            ds.nb_initial = it.nb_current
            ds.save()
        return new, []

    def checkout_balance(self):
        """
        Get the balance of the cards of the ongoing checkout.

        return: depositstate.cards_balance(), i.e. a list.
        """
        depostate = self.ongoing_depostate
        return depostate.cards_balance()


@python_2_unicode_compatible
class SoldCards(TimeStampedModel):
    card = models.ForeignKey(Card)
    sell = models.ForeignKey("Sell")
    #: Number of this card sold:
    quantity = models.IntegerField(default=0)
    #: Initial price
    price_init = models.FloatField(default=DEFAULT_PRICE)
    #: Price sold:
    price_sold = models.FloatField(default=DEFAULT_PRICE)
    #: The decision to sell from the stock or the card's deposit is made for each card,
    # not each sell (that includes other cards).
    deposit = models.ForeignKey("Deposit", blank=True, null=True, verbose_name=__("deposit"))
    #: Sometimes we want to register the sell action, but not count it in the total revenue.
    ignore_for_revenue = models.BooleanField(default=False, blank=True, verbose_name=__("ignore when counting the revenue?"))

    def __str__(self):
        ret = "card sold id {}, {} sold at price {}".format(self.card.id, self.quantity, self.price_sold)
        return ret

    def to_dict(self):
        return {"card_id": self.card.id,
                "card": Card.to_dict(self.card),
                "created": self.created.strftime(DATE_FORMAT),
                "quantity": self.quantity,
                "price_init": self.price_init,
                "price_sold": self.price_sold,
                "price_sold_excl_tax": Preferences.price_excl_tax(self.price_sold),
                "sell_id": self.sell.id,
                "soldcard_id": self.id,
               }

    def to_list(self):
        return self.to_dict()

    def price_sold_fmt(self):
        return price_fmt(self.price_sold, card_currency(self.card))

    def price_init_fmt(self):
        return price_fmt(self.price_init, card_currency(self.card))

    @staticmethod
    def undo(pk):
        """
        Undo the sell linked to this soldcard: add it to the stock again.

        Return:
        - status, list of messages.
        """
        msgs = Messages()
        status = True
        try:
            soldcard = SoldCards.objects.get(id=pk)
        except ObjectDoesNotExist as e:
            msgs.add_error('Error while trying to get soldcard n° {}: {}'.format(pk, e))
            log.error(msgs.msgs)
            return False, msgs.msgs

        try:
            # Called by the api, to undo the sell of only one book,
            # instead of calling Sell.undo to undo all of it.
            if soldcard.sell.canceled:
                return True, [{"message": "This sell was already canceled.",
                              "level": ALERT_WARNING}]

            status, _msgs = soldcard.card.sell_undo(quantity=soldcard.quantity,
                                                    place=soldcard.sell.place,
                                                    deposit=soldcard.sell.deposit)
            soldcard.sell.canceled = True
            soldcard.sell.save()
            msgs.append(_msgs)
        except Exception as e:
            msg = 'Error while undoing the soldcard {}: {}'.format(pk, e)
            msgs.add_error(msg)
            log.error(msg)
            status = False

        # We keep the transaction visible, we don't delete the soldcard.
        # Instead, it must appear as a new entry.

        msgs.add_success(_("Operation successful"))
        return status, msgs.msgs

def can_sell_from_deposit(card):
    """
    If the card is in stock, sell it. Otherwise, sell from its deposit.
    """
    return (not card.quantity > 0) and card.deposits


@python_2_unicode_compatible
class Sell(models.Model):
    """A sell represents a set of one or more cards that are sold:
    - at the same time,
    - under the same payment,
    - where the price sold can be different from the card's original price,
    - to one client.
    """
    created = models.DateTimeField()
    copies = models.ManyToManyField(Card, through="SoldCards", blank=True)
    payment = models.CharField(choices=PAYMENT_CHOICES,  # for easy customization: no need of a DB table.
                               default=PAYMENT_CHOICES[0],
                               max_length=CHAR_LENGTH,
                               blank=True, null=True,
                               verbose_name=__("payment"))
    #: Second payment method (optional).
    payment_2 = models.CharField(choices=PAYMENT_CHOICES,
                               default="0",
                               max_length=CHAR_LENGTH,
                               blank=True, null=True,
                               verbose_name=__("payment"))

    #: In case of several payment methods, say how much for each of them.
    total_payment_1 = models.FloatField(blank=True, null=True)
    total_payment_2 = models.FloatField(blank=True, null=True)

    #: The total for revenue does not count coupons and the like.
    #: It only counts the books that were effectively paid.
    total_for_revenue = models.FloatField(default=0, blank=True, null=True)

    #: We can choose to sell from a specific place.
    place = models.ForeignKey("Place", blank=True, null=True, verbose_name=__("place"))
    #: We can also choose to sell from a specific deposit.
    deposit = models.ForeignKey("Deposit", blank=True, null=True, verbose_name=__("deposit"))
    #: If True, this sell was already canceled. It can not be undone twice.
    canceled = models.BooleanField(default=False, blank=True, verbose_name=__("canceled"))

    #: The client who bought those books (optional).
    client = models.ForeignKey("Client", blank=True, null=True, verbose_name=__("client"))

    class Meta:
        verbose_name = __("sell")

    def __str__(self):
        return "Sell {} of {} copies at {}.".format(self.id,
                                                     self.soldcards_set.count(),
                                                     self.created)

    @property
    def total_price_sold(self):
        total = 0
        for card in self.soldcards_set.all():
            total += card.price_sold * card.quantity
        return total

    @property
    def total_price_sold_fmt(self):
        total = self.total_price_sold
        return price_fmt(total, Preferences.get_default_currency())

    @property
    def total_price_init(self):
        total = 0
        for card in self.soldcards_set.all():
            total += card.price_init * card.quantity
        return total

    def get_absolute_url(self):
        return reverse("sell_details", args=(self.id,))

    @staticmethod
    def search(card_id=None, date_min=None, count=False, date_max=None,
               distributor_id=None,
               deposit_id=None,
               year=None,
               month=None,
               day=None,
               with_total_price_sold=None,
               page=None,
               page_size=None,
               sortby=None,
               sortorder=0,  # "-"
               to_list=False):
        """Search for the given card id in sells more recent than "date_min".

        - card_id: int. If not given, searches in all.
        - date_min: date obj
        - date_max: date obj
        - count: if True, only return the count() of the result, not the result list.
        - year, month: ints (month in 1..12)
        - distributor_id: int.
        - with_total_price_sold: if True, sum the prices sold (x their quantity).

        Pagination:
        - page: int

        Sorting results:
        - sortby: a field name (str) such as "sell__id", "created", "price" and "title".
        - sortorder: 0 (default) or 1 (descending).

        return: a dict with keys `total` (int) and `data` (a list of sortcard objects).
        """
        sells = []
        if page is not None:
            page = int(page)
        if page_size is not None:
            page_size = int(page_size)

        try:
            if card_id:
                sells = SoldCards.objects.filter(card__id=card_id)
            else:
                sells = SoldCards.objects.all()

            sells = sells.exclude(sell__canceled=True)

            if year:
                year = int(year)
                sells = sells.filter(created__year=year)

            if month:
                month = int(month)
                sells = sells.filter(created__month=month)

            if day:
                day = int(day)
                sells = sells.filter(created__day=day)

            # by Django 1.9 we can chain created__month__gt (new: __gt).
            if date_min:
                # dates must be timezone.now() for precision.
                sells = sells.filter(created__gt=date_min)
            if date_max:
                sells = sells.filter(created__lt=date_max)

            if distributor_id:
                soldcards = sells.filter(card__distributor_id=distributor_id)
                sells = soldcards

            if deposit_id:
                sells = sells.filter(sell__deposit_id=deposit_id)

        except Exception as e:
            log.error("search for sells of card id {}: {}".format(card_id, e))
        if count:
            return sells.count()

        # Sorting.
        sortsign = "-"
        if sortorder in [0, "0", "0"]:
            sortsign = "-"
        else:
            sortsign = ""
        if sortby in [None, ""]:
            sells = sells.order_by(sortsign + "created")
        elif sortby == "sell__id":
            sells = sells.order_by("-sell__id")  # TODO:
        elif sortby == "created":
            sells = sells.order_by(sortsign + "created")
        elif "price" in sortby:
            sells = sells.order_by(sortsign + "price_sold")
        elif "title" in sortby:
            sells = sells.order_by(sortsign + "card__title")
        else:
            log.warning("Warning sorting Sell.search: uncaught case with sortby {} and sortorder {}".format(sortby, sortorder))

        # Totals.
        # nb_sells = sells.count()  # = nb of articles sold, != nb sells (passages en caisse).
        book_type = CardType.objects.filter(name='book').first()
        nb_sells = sells.values('sell_id').distinct().count()
        nb_books_sells = sells.filter(card__card_type=book_type).values('sell_id').distinct().count()
        # nb_cards_sold = sum([it.quantity for it in sells])
        nb_cards_sold = sum(sells.filter(quantity__gt=0).values_list('quantity', flat=True))
        nb_cards_returned = sum(sells.filter(quantity__lt=0).values_list('quantity', flat=True))
        total_sells = sum(sells.values_list('quantity', flat=True))

        type_book = CardType.objects.filter(name="book").first()

        total_price_sold = None
        total_price_sold_books = None
        total_price_sold_not_books = None
        sell_mean = None
        books_sell_mean = 0
        sold_books = []
        nb_books_sold = 0   # nb of copies
        not_books = []
        if with_total_price_sold:
            # Ignore coupons, gifts, and others in the total revenue.
            # Total for the cash register: count sells and returns.
            sells_for_revenue = sells.exclude(ignore_for_revenue=True)
            # Total for mean sell: count sells only, not returns.
            # We consider that a return or an exchange should not lower the mean sell.
            sells_for_mean = sells.filter(quantity__gt=0).exclude(ignore_for_revenue=True)
            # total_price_sold = sum([it[0] * it[1] for it in sells_for_revenue.values_list('quantity', 'price_sold')])

            # Count VATs separately.
            sells_for_revenue_values = sells_for_revenue.values_list('quantity', 'price_sold', 'card__card_type', 'card__isbn', 'card__card_type__name')
            # Filter books.
            # Normally, they are of type "book", but I observe it is not always the case. Why?
            sold_books = [it for it in sells_for_revenue_values
                          if (it[2] and it[2] == type_book.pk) or
                          (it[3] and it[3].startswith('97'))]
            nb_books_sold = len(sold_books)
            total_price_sold_books = sum([it[0] * it[1] for it in sold_books])
            # values_not_books = [it for it in sells_for_revenue_values if it[2] != type_book.pk and not it[3].startswith('97')]
            # XXX: 2021/01/15: shipped new management script to clean up types and
            # fixed the datasources to return the correct type.
            # This should allow to rely on card_type.
            not_books = [it for it in sells_for_revenue_values
                         if (it[2] and it[2] != type_book.pk) and
                         (not it[3] or
                          (it[3] and not it[3].startswith('97')))]
            not_books += [it for it in sells_for_revenue_values
                          if it[2] is None]
            total_price_sold_not_books = sum([it[0] * it[1] for it in not_books])
            total_price_sold = total_price_sold_books + total_price_sold_not_books
            total_sells_for_mean = sum([it[0] * it[1] for it in sells_for_mean.values_list('quantity', 'price_sold')])
            if total_sells_for_mean:
                sell_mean = total_sells_for_mean / nb_cards_sold
            books_sell_mean = 0
            if sold_books:
                books_sell_mean = total_price_sold_books / nb_books_sold

        # Pagination.
        if page is not None and page_size is not None:
            try:
                sells = sells[page_size * (page - 1):page_size * page]
            except IndexError:
                log.warning("Sells pagination: index error.")
                sells = []

        # select_related: pre-populate data to save later DB queries.
        # Especially for history download to CSV.
        sells = sells.select_related()  # cache all 1-1 1-n relationships.

        if to_list:
            sells = [it.to_list() for it in sells]

        default_currency = Preferences.get_default_currency()
        return {"data": sells,
                "not_books": not_books,
                "nb_sells": nb_sells,  # within search criteria
                "nb_cards_sold": nb_cards_sold,
                "nb_books_sold": nb_books_sold,
                "nb_books_sells": nb_books_sells,
                "nb_cards_returned": - nb_cards_returned,
                "total_sells": total_sells,  # total
                "total_sells_fmt": price_fmt(total_sells, default_currency),  # total
                "total_price_sold": total_price_sold,
                "total_price_sold_books": total_price_sold_books,
                "total_price_sold_books_fmt": price_fmt(total_price_sold_books, default_currency),
                "total_price_sold_not_books": total_price_sold_not_books,
                "total_price_sold_not_books_fmt": price_fmt(total_price_sold_not_books, default_currency),
                "total_price_sold_fmt": price_fmt(total_price_sold, default_currency),
                "sell_mean": sell_mean,
                "sell_mean_fmt": price_fmt(sell_mean, default_currency),
                "books_sell_mean": books_sell_mean,
                }

    @staticmethod
    def count_client_soldcards(client):
        """
        Return the number of cards sold to this client.
        """
        # this method in the users.py file would
        assert isinstance(client, models.base.Model)
        return SoldCards.objects.filter(sell__client=client).count()

    def to_list(self):
        """Return this object as a python list, ready to be serialized or
        json-ified."""
        default_currency = Preferences.get_default_currency()
        cards_sold = [it.to_dict() for it in self.soldcards_set.all()]
        total_copies_sold = sum([it['quantity'] for it in cards_sold])
        ret = {
            "id": self.id,
            "created": self.created.strftime(DATE_FORMAT),  # YYYY-mm-dd
            "cards": cards_sold,
            "place_id": self.place.id if self.place else None,
            "deposit_id": self.deposit.id if self.deposit else None,
            "total_copies_sold": total_copies_sold,
            # "payment": self.payment,
            "total_price_init": self.total_price_init,
            "total_price_init_fmt": price_fmt(self.total_price_init, default_currency),
            "total_price_sold": self.total_price_sold,
            "total_price_sold_fmt": price_fmt(self.total_price_sold, default_currency),
            "details_url": "/admin/search/{}/{}".format(self.__class__.__name__.lower(), self.id),
            "model": self.__class__.__name__,
        }

        return ret

    @staticmethod
    def sells_of_month(year=None, month=None, publisher_id=None, distributor_id=None):
        assert year
        assert month
        assert isinstance(month, int)

        sells = SoldCards.objects.exclude(sell__canceled=True)

        sells = sells.filter(created__year=year).filter(created__month=month)
        if publisher_id is not None:
            sells = sells.filter(card__publishers__id=publisher_id)
        if distributor_id is not None:
            sells = sells.filter(card__distributor_id=distributor_id)
        sells = sells.order_by('card__title')
        return sells

    @staticmethod
    def stat_days_of_month(month=None, year=None, sortby=None, sortorder=None):
        assert year
        assert month
        assert isinstance(month, int)
        default_currency = Preferences.get_default_currency()
        soldcards = SoldCards.objects.exclude(sell__canceled=True)
        soldcards = soldcards.filter(created__year=year).filter(created__month=month)
        soldcards.order_by("created")
        nb_sells = soldcards.values('sell_id').distinct().count()
        now = timezone.now()
        last_day = 31
        if now.month == month and now.year == year:
            last_day = now.day
        else:
            _, last_day = calendar.monthrange(year, month)
        sells_per_day = []
        sells_this_day = []
        total_price_sold = 0
        total_cards_sold = 0
        TWO_DIGITS_SPEC = '0>2'
        YMD = '%Y-%m-%d'
        all_sells_days = soldcards.values_list('quantity', 'price_sold',
                                               'ignore_for_revenue',  # => bool
                                               'created')  # => datetime
        for day in range(1, last_day + 1):
            date = "{}-{}-{}".format(year,
                                     format(month, TWO_DIGITS_SPEC),
                                     format(day, TWO_DIGITS_SPEC))
            date_obj = datetime.datetime.strptime(date, YMD)
            # sells_this_day = soldcards.filter(created__day=day)
            sells_this_day = [it for it in all_sells_days if it[-1].day == day]
            # cards_sold = sum(sells_this_day.values_list('quantity', flat=True))
            cards_sold = sum([it[0] for it in sells_this_day])
            total_cards_sold += cards_sold

            # Ignore coupons, gifts, and others in the total revenue.
            sells_for_revenue = [it for it in sells_this_day if it[2] is not True]
            values = [(it[0], it[1]) for it in sells_for_revenue]
            total = sum([it[0] * it[1] for it in values])
            sells_per_day.append({'date': date,
                                  'date_obj': date_obj,
                                  'weekday': date_obj.weekday(),
                                  'nb_cards_sold': cards_sold,
                                  'total_price_sold': total,
                                  'total_price_sold_fmt': price_fmt(total, default_currency),
            })
            total_price_sold += total

        # Best sells per card type.
        best_sells = get_best_sells(soldcards)

        sell_mean = 0
        if total_cards_sold:
            sell_mean = total_price_sold / total_cards_sold
        return {'total_price_sold': total_price_sold,
                'total_price_sold_fmt': price_fmt(total_price_sold, default_currency),
                'total_cards_sold': total_cards_sold,
                'sell_mean': sell_mean,
                'sell_mean_fmt': price_fmt(sell_mean, default_currency),
                'nb_sells': nb_sells,
                'best_sells': best_sells,
                'data': sells_per_day}

    @staticmethod
    def history_suppliers(year=None, month=None):
        """
        Information on what to pay to distributors and publishers.

        This does NOT return the full list of sells for publishers, since we don't want
        one book to appear both on the distributors and publishers side.

        Return: a dict with keys
        - publishers_data
        - distributors_data
        """
        assert year
        assert month
        default_currency = Preferences.get_default_currency()
        sells = Sell.sells_of_month(month=month, year=year)
        # Consider sells of distributors.
        sells_with_distributor = sells.filter(card__distributor__isnull=False)
        # and then the *remaining* sells for publishers.
        sells_with_publishers = sells.exclude(card__distributor__isnull=False)\
                                     .filter(card__publishers__isnull=False)
        # without any pub or dist:
        # sells_without_supplier = sells.exclude(card__publishers__isnull=False)\
        #                              .exclude(card__distributor__isnull=False)

        current_distributors = []
        if sells_with_distributor:
            current_distributors = sells_with_distributor.values_list('card__distributor__name', 'card__distributor__id').distinct()  # distinct has no effect?!
            current_distributors = list(set(current_distributors))
        current_publishers = []
        if sells_with_publishers:
            current_publishers = sells_with_publishers.values_list('card__publishers__name', 'card__publishers__id').distinct()
            current_publishers = list(set(current_publishers))

        # distinct('card__distributor__id')  # not supported on SQLite.

        publishers_data = []
        for name, pk in current_publishers:
            data = {}
            data['publisher'] = (name, pk)
            pub_sells = sells_with_publishers.filter(card__publishers__id=pk)
            data['sells'] = pub_sells
            cards_sold = pub_sells.values_list('quantity', flat=True)
            nb_cards_sold = sum(cards_sold)
            data['nb_cards_sold'] = nb_cards_sold
            prices_sold = pub_sells.values_list('price_sold', flat=True)
            public_prices = pub_sells.values_list('price_init', flat=True)
            assert len(cards_sold) == len(prices_sold)
            total = sum([cards_sold[i] * prices_sold[i] for i in range(len(prices_sold))])
            data['total'] = total
            data['total_fmt'] = price_fmt(total, default_currency)
            total_public_price = sum([public_prices[i] * cards_sold[i] for i in range(len(cards_sold))])
            data['total_public_price'] = total_public_price
            data['total_public_price_fmt'] = price_fmt(total_public_price, default_currency)
            publishers_data.append(data)

        publishers_data = sorted(publishers_data, key=lambda it: it['publisher'][0])  # sort by name

        distributors_data = []
        for name, pk in current_distributors:
            data = {}
            data['distributor'] = (name, pk)
            pub_sells = sells_with_distributor.filter(card__distributor__id=pk)
            data['sells'] = pub_sells
            cards_sold = pub_sells.values_list('quantity', flat=True)
            nb_cards_sold = sum(cards_sold)
            data['nb_cards_sold'] = nb_cards_sold
            prices_sold = pub_sells.values_list('price_sold', flat=True)
            public_prices = pub_sells.values_list('price_init', flat=True)
            assert len(cards_sold) == len(prices_sold) == len(public_prices)
            total = sum([cards_sold[i] * prices_sold[i] for i in range(len(prices_sold))])
            data['total'] = total
            data['total_fmt'] = price_fmt(total, default_currency)
            total_public_price = sum([public_prices[i] * cards_sold[i] for i in range(len(cards_sold))])
            data['total_public_price'] = total_public_price
            data['total_public_price_fmt'] = price_fmt(total_public_price, default_currency)
            distributors_data.append(data)

        distributors_data = sorted(distributors_data, key=lambda it: it['distributor'][0])  # sort by name

        return {'distributors_data': distributors_data,
                'publishers_data': publishers_data, }

    @staticmethod
    def sell_card(card, nb=1, **kwargs):
        """Sell a Card. Simple wrapper to Sell.sell_cards.
        """
        return Sell.sell_cards(None, cards=[card], **kwargs)

    @staticmethod
    def sell_cards(ids_prices_nb, date=None,
                   payment=None,
                   payment_2=None,
                   cards=[],
                   place_id=None, place=None,
                   deposit_id=None, deposit=None,  # XXX: deprecated since 2020-07-09
                   client=None, client_id=None,
                   total_payment_1=0,
                   total_payment_2=0,
                   silence=False):
        """ids_prices_nb: list of dict {"id", "price sold", "quantity" to sell}.

        The default of "price_sold" is the card's price, the default
        quantity is 1. No error is returned, only a log (it's supposed
        not to happen, to be checked before calling this method).

        We accept 2 payment methods.

        - cards: can be used as a shortcut to write tests. Price and quantity will be default.
        - date: a timezone or a str (from javascript) which complies to the DATE_FORMAT,
          or a timezone.datetime object.
        - place_id: int

        return: a 3-tuple (the Sell object, the global status, a list of messages).

        """
        alerts = []  # error messages
        status = ALERT_SUCCESS
        cards_obj = []
        sell = None

        TEST_DEFAULT_QUANTITY = 1
        if cards:
            ids_prices_nb = []
            for it in cards:
                ids_prices_nb.append({'id': it.id, 'price': it.price, "quantity": TEST_DEFAULT_QUANTITY})

        if not ids_prices_nb:
            if not silence:
                log.warning("Sell: no cards are passed on. That shouldn't happen.")
            status = ALERT_WARNING
            return sell, status, alerts

        if not date:
            date = timezone.now()
        else:
            # create a timezone aware date
            if isinstance(date, six.string_types) or isinstance(date, six.text_type):
                date = datetime.datetime.strptime(date, DATE_FORMAT)
                date = pytz.utc.localize(date, pytz.UTC)

        # Get the deposit we sell from (optional).
        deposit_obj = deposit
        # Here, check if a deposit was given as argument.
        # Check the deposit of each card a bit later.
        if not deposit_obj and deposit_id and deposit_id not in [0, "0"]:
            log.warning("the use of deposit and deposit_id arguments to sell was deprecated. We guess it smartly now.")

        # Get the place we sell from (optional).
        place_obj = place
        if not place_obj and place_id and place_id:
            try:
                place_obj = Place.objects.get(id=place_id)
            except ObjectDoesNotExist as e:
                log.error("Registering a Sell, couldn't get place of id {}.".format(place_id, e))
        elif not place_obj:
            place_obj = Preferences.get_default_place()

        # Register the client (optional).
        if client_id:
            client = Client.objects.filter(id=client_id).first()

        # The revenue of the sell does not count coupons, it only counts
        # effective payments.
        total_for_revenue = 0
        if not ignore_payment_for_revenue(payment):
            total_for_revenue += total_payment_1
        if not ignore_payment_for_revenue(payment_2):
            total_for_revenue += total_payment_2

        # Create the Sell object.
        try:
            sell = Sell(created=date,
                        payment=payment,
                        payment_2=payment_2,
                        total_payment_1=total_payment_1,
                        total_payment_2=total_payment_2,
                        total_for_revenue=total_for_revenue,
                        place=place_obj,
                        client=client)
            sell.save()

        except Exception as e:
            status = ALERT_ERROR
            alerts.append({"message": "Ooops, we couldn't sell anything :S",
                           "level": ALERT_ERROR})
            log.error("Error on creating Sell object: {}".format(e))
            return None, status, "Error registering the sell"

        # Decrement cards quantities from their place or deposit.
        # A quantity < 0 is a return (or reimboursement).
        for it in ids_prices_nb:
            # "sell" a card.
            id = it.get("id")
            quantity = it.get("quantity", 1)
            if not id:
                log.error("Error: id {} shouldn't be None.".format(id))
            card = Card.objects.get(id=id)
            cards_obj.append(card)

            # Check each card if it is in a deposit.
            deposit_obj = None

            try:
                # Either sell from a deposit.
                # Check if the card is registered in a deposit.
                # However, if it is also in stock, sell the one in stock.
                if can_sell_from_deposit(card):
                    deposit_obj = card.get_first_deposit()
                    card.deposit_obj = deposit_obj

                if deposit_obj:
                    status, alerts = deposit_obj.sell_card(card_id=id,
                                                           sell=sell,
                                                           nb=quantity)

                # either sell from a place or the default (selling) place.
                # A quantity < 0 gets added back.
                else:
                    status, alerts = Card.sell(id=id, quantity=quantity, place=place_obj)

            except ObjectDoesNotExist:
                msg = "Error: the card of id {} doesn't exist.".format(id)
                log.error(msg)
                alerts.append({"level": ALERT_ERROR, "message": msg})
                status = ALERT_WARNING
                sell.delete()
                return None, status, msg
            except Exception as e:
                msg = "Error selling card {}: {}".format(id, e)
                log.error(msg)
                status = ALERT_ERROR
                sell.delete()
                return None, status, msg

        #
        # Add the cards and their attributes in the Sell.
        #
        for i, card in enumerate(cards_obj):
            price_sold = ids_prices_nb[i].get("price_sold", card.price)
            if not price_sold:
                msg = "We can not sell the card '{}' because it has no sell price and no original price. Please specify the price in the form.".format(card.title)
                if not silence:
                    log.error(msg)
                alerts.append({"message": msg,
                               "level": ALERT_WARNING, })
                status = ALERT_WARNING
                continue
            quantity = ids_prices_nb[i].get("quantity", 1)

            try:
                if not card.price:
                    # This can happen with a broken parser.
                    log.warning("The card {} has no price and this shouldn't happen. Setting it to 0 to be able to sell it.".format(card.id))
                    card.price = 0

                # If it's a coupon or a gift, don't count it for the total revenue.
                ignore_for_revenue = ignore_payment_for_revenue(payment)
                if payment_2 is not None:
                    ignore_for_revenue = ignore_for_revenue and ignore_payment_for_revenue(payment_2)

                sold = sell.soldcards_set.create(card=card,
                                                 price_sold=price_sold,
                                                 price_init=card.price,
                                                 quantity=quantity,
                                                 ignore_for_revenue=ignore_for_revenue,
                                                 deposit=getattr(card, 'deposit_obj', None))
                sold.created = date
                sold.save()
            except Exception as e:
                alerts.append({"message": _("Warning: we couldn't sell {}.".format(card.id)),
                               "level": ALERT_WARNING})
                log.error("Error on adding the card {} to the sell {}: {}".format(card.id,
                                                                                   sell.id,
                                                                                   e))
                status = ALERT_ERROR

        # XXX: misleading names: alerts (messages) and Alert.
        if not alerts:
            alerts.append({"message": _("Sell successfull."),
                           "level": ALERT_SUCCESS})

        return (sell, status, alerts)

    def get_soldcard(self, card_id):
        """Get informations about this card that was sold: how many, how much etc.
        """
        if not card_id:
            return None

        return self.soldcards_set.filter(card__id=card_id)

    @staticmethod
    def sell_undo(sell_id):
        status = False
        msgs = Messages()
        try:
            sell = Sell.objects.get(id=sell_id)
            status, msgs = sell.undo()
        except Exception as e:
            log.error("Error while trying to undo sell id {}: {}".format(sell_id, e))
            msgs.add_error(_("Error while undoing sell {}".format(sell_id)))

        return status, msgs

    def undo(self):
        """Undo:
        - add the necessary quantity to the right place or deposit.
        - create a new entry, for the history.
        - we do not undo alerts here
        """
        if self.canceled:
            return True, [{"message": "This sell was already canceled.",
                          "level": ALERT_WARNING}]

        status = True
        msgs = Messages()
        cards = []
        for soldcard in self.soldcards_set.all():
            card_obj = soldcard.card
            cards.append(card_obj)
            qty = soldcard.quantity
            try:
                # undo for deposit
                if soldcard.deposit:
                    status, _msgs = soldcard.deposit.sell_undo(card=card_obj, quantity=qty)
                else:
                    status, _msgs = card_obj.sell_undo(quantity=qty, place=self.place)
                msgs.append(_msgs)
            except Exception as e:
                msgs.add_error(_("Error while undoing sell {}.".format(self.id)))
                log.error("Error while undoing sell {}: {}".format(self.id, e))
                status = False

        # Add a log to the Entry history
        if status:
            # We can undo a Sell only once.
            self.canceled = True
            self.save()

            reason = "canceled sell n°{} of {}".format(self.id, self.created.strftime(DATE_FORMAT))
            try:
                history.Entry.new(cards, payment=4, reason=reason)  # 4: canceled sell
            except Exception as e:
                log.error("Error while adding an Entry to the history for card {}:{}".format(self.id, e))
                status = False

            msgs.add_success(_("Sell {} canceled with success.").format(self.id))

        return status, msgs.msgs

    @staticmethod
    def history(to_list=True):
        """
        """
        raise DeprecationWarning("Unused method. Use Sell.search and Entry.search instead.")


def getHistory(**kwargs):
    raise DeprecationWarning("Unused method.")


@python_2_unicode_compatible
class Alert(models.Model):
    """An alert stores the information that a Sell is ambiguous. That
    happens when we want to sell a card and it has at least one
    exemplary in (at least) one deposit AND it also has exemplaries
    not in deposits. We need to ask the user which exemplary to sell.
    """
    card = models.ForeignKey("Card")
    deposits = models.ManyToManyField(Deposit, blank=True)
    date_creation = models.DateField(auto_now_add=True)
    date_resolution = models.DateField(null=True, blank=True)
    resolution_auto = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return "alert for card {}, created {}".format(self.card.id, self.date_creation)

    def get_absolute_url(self):
        # return reverse("sell_view", args=(self.id,))
        return "not_implemented"  # TODO: view a sell

    def obj_to_list(self):
        resolution = self.date_resolution
        if resolution:
            resolution = resolution.strftime(DATE_FORMAT)
        res = {
            "card": self.card.to_list(),
            "date_creation": self.date_creation.strftime(DATE_FORMAT),
            "date_resolution": resolution,
            "deposits": [dep.to_list() for dep in self.deposits.all()],
            "deposits_repr": ", ".join(dep.name for dep in self.deposits.all()),
        }
        return res

    @staticmethod
    def get_alerts(to_list=False):
        """Get all the alerts.

        Return: a 3-tuple (list of alerts, status, list of messages).
        """
        alerts = Alert.objects.all().order_by("-date_creation")
        # todo: the alert may be resolved if we sold the remaining copies.
        msgs = Messages()
        status = ALERT_SUCCESS
        if to_list:
            alerts = [alert.obj_to_list() for alert in alerts]
        return (alerts, status, msgs.msgs)

    def add_deposits_of_card(self, card):
        for it in card.deposit_set.all():
            self.deposits.add(it)

class InventoryCopiesBase(models.Model):
    """The list of cards of an inventory, plus other information:
    - the quantity of them in this inventory.
    """
    card = models.ForeignKey(Card)
    #: How many copies of it did we find in our stock ?
    quantity = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def to_dict(self):
        return {
            "card": self.card.to_dict(),
            "quantity": self.quantity,
        }


@python_2_unicode_compatible
class InventoryCopies(InventoryCopiesBase):
    # we inherit card and quantity.
    inventory = models.ForeignKey("Inventory")

    def __str__(self):
        return "Inventory %s: %s copies of card %s, id %s" % (self.inventory.id,
                                                               self.quantity,
                                                               self.card.title,
                                                               self.card.id)


class InventoryBase(TimeStampedModel):
    """An inventory can happen for a place or a shelf. Once we begin it we
    can't manipulate the stock from there (at least in the specs, not
    yet). We list the copies we have in stock, and enter the missing
    ones.

    InventoryBase shares fields for other inventorie classes. This
    helps to distinguish, in the code and in the DB, inventories of
    different objects. For example, doing the inventory of a shelf or
    of a command's parcel we just received is the same process, but is
    a different thing for the user. Now they are in two different DB
    tables.
    """
    # By TimeStampedModel, we get "created" and "modified".
    #: Closed or still active ?
    closed = models.DateTimeField(blank=True, null=True)
    #: An archived inventory was closed, applied or not.
    # This status is necessary so that we can list all the inventories
    # we are currently working on. We can see that some are applied (the check mark),
    # others are not.
    archived = models.BooleanField(default=False)
    #: Did we apply it ?
    applied = models.BooleanField(default=False)

    class Meta:
        # this class isn't a DB table by itself. It just shares some
        # fields. No DB change inplied.
        abstract = True

    @property
    def copies_set(self):
        """
        The reference to the intermediate table, like inventorycopies_set.
        For an InventoryCommand, will be inventorycommandcopies_set.
        Goal: have generic methods, like state().

        Return: an object.
        """
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    def get_absolute_url(self):
        raise NotImplementedError

    @staticmethod
    def open_inventories():
        return Inventory.objects.exclude(archived=True).all()

    def _orig_cards_qty(self):
        """Return the number of copies to inventory (the ones in the original
        shelf, place, etc.
        """
        raise NotImplementedError

    def nb_copies(self):
        """How many exemplaries in total.
        """
        return sum(self.copies_set.all().values_list('quantity', flat=True))

    def nb_cards(self):
        """Return the quantity of cards in it.

        - return: int
        """
        return self.inventorycopies_set.count() or 0

    def value(self, discount=False):
        """Total value. Sum of public prices of all books in this inventory.

        Return: a float, rounded to two decimals.
        """
        def card_price(card, discount=False):
            if card and card.price is not None:
                if discount:
                    return card.price_discounted
                else:
                    return card.price
            return 0

        ret = sum([card_price(it.card, discount=discount) * it.quantity for it in
                   self.inventorycopies_set.select_related('card').all()])
        ret = roundfloat(ret)
        return ret

    def to_dict(self, details=False):
        """Return a dict ready to be serialized. Simplest form: id and name.

        - details: if True, return also information about its state:
        applied, closed, created, nb of cards and copies, proress, value.
        """
        ret = {
            "id": self.id,
            "name": self.name,
            "get_absolute_url": self.get_absolute_url(),
        }

        if details:
            ret["applied"] = self.applied
            ret["closed"] = self.closed.strftime(DATE_FORMAT) if self.closed else ""
            ret["created"] = self.created.strftime(DATE_FORMAT) if self.created else ""
            ret["nb_cards"] = self.nb_cards()
            ret["nb_copies"] = self.nb_copies()
            ret["value"] = self.value()
            ret["value_fmt"] = price_fmt(self.value(), Preferences.get_default_currency())

        return ret

    def state(self, page=1, page_size=PAGE_SIZE):
        """
        Get the current state:
        - list of copies already inventoried and their quantities,
        - list of copies not found te be searched for (and their quantities)
        - total value of the inventory
        - total value with discount
        """
        default_currency = Preferences.get_default_currency()
        all_copies = self.copies_set.order_by("card__title").all()
        nb_cards = all_copies.count()
        nb_copies = self.nb_copies()

        total_value = self.value()

        paginator = Paginator(all_copies, page_size)
        if page is not None:
            try:
                copies = paginator.page(page)
            except EmptyPage:
                copies = paginator.page(paginator.num_pages)
            finally:
                copies = copies.object_list
        else:
            copies = paginator.object_list

        copies = [it.to_dict() for it in copies]

        meta = {
            'nb_results': nb_cards,
            'num_pages': paginator.num_pages,
            'currency': default_currency,
        }
        inv_name = ""
        shelf_dict, place_dict, basket_dict, pub_dict = ({}, {}, {}, {})
        # orig_cards_qty = self._orig_cards_qty()
        if hasattr(self, "shelf") and self.shelf:
            shelf_dict = self.shelf.to_dict()
            inv_name = self.shelf.name
        elif hasattr(self, "place") and self.place:
            place_dict = self.place.to_dict()
            inv_name = self.place.name
        elif hasattr(self, "publisher") and self.publisher:
            pub_dict = self.publisher.to_dict()
            inv_name = self.publisher.name
        elif hasattr(self, "basket") and self.basket:
            basket_dict = self.basket.to_dict()
            inv_name = self.basket.name
        else:
            log.error("Inventory of a shelf, place or basket ? We don't know. That shouldn't happen !")

        state = {
            "copies": copies,
            "inv_name": inv_name,
            "nb_cards": nb_cards,
            "nb_copies": nb_copies,
            "total_value": total_value,
            "total_value_fmt": price_fmt(total_value, default_currency),
            "shelf": shelf_dict,
            "place": place_dict,
            "basket": basket_dict,
            "publisher": pub_dict,
            "meta": meta,
        }

        return state

    def add_copy(self, copy, nb=1, add=True):
        """copy: a Card object.

        Add the quantities only if 'add' is True (the clientside may
        ask to *set* the quantity, not add them).

        """
        if isinstance(nb, six.string_types) or isinstance(nb, six.text_type):
            nb = int(nb)
        try:
            inv_copies, created = self.copies_set.get_or_create(card=copy)
            if add:
                inv_copies.quantity += nb
            else:
                inv_copies.quantity = nb
            inv_copies.save()
        except Exception as e:
            log.error(e)
            return None

        return inv_copies.quantity

    def update_copies(self, cards_qties):
        """
        Update the cards of this inventory.
        Add missing ones and update the quantities

        - cards_qties: list of BasketCopies, with a card and a quantity field.
        """
        for it in cards_qties:
            self.add_copy(it.card, nb=it.quantity, add=False)

    def remove_card(self, card_id):
        """
        - return: status (bool)
        """
        try:
            inv_copies = self.copies_set.get(card__id=card_id)
            inv_copies.delete()

        except Exception as e:
            log.error(e)
            return False

        return True

    def add_pairs(self, pairs, add=False):
        """Save the given copies.

        - pairs: list of pairs (lists) with an id and its quantity
        - add: bool. If True, add the quantities. If False, just set it (client side need).

        return: tuple status, messages
        """
        status = "success"
        msgs = Messages()
        for pair in pairs:
            if not pair:
                # beware void lists
                continue
            id, qty = pair
            try:
                card = Card.objects.get(id=id)
                if qty in ["null", "null", "undefined", "undefined"]:
                    log.warning("updating inventory: got qty of null or undefined. {}".format(pairs))
                    qty = 0
                else:
                    qty = int(qty)
                self.add_copy(card, nb=qty, add=add)
            except Exception as e:
                log.error(e)
                msgs.add_error(_("Internal error, sorry !"))
                status = "error"
                return None, msgs.msgs

            if hasattr(self, "shelf") and self.shelf:
                card.shelf = self.shelf
                card.save()

        return (status, msgs.msgs)

    @staticmethod
    def diff_inventory(pk, **kwargs):
        try:
            obj = Inventory.objects.get(id=pk)
            return obj.diff(**kwargs)
        except Exception as e:
            log.error("Error getting inventory: {}".format(e))
            return None

    def diff(self, to_dict=False):
        """Diff the inventory's state with the database: get
        - which cards are ok,
        - which ones are missing from the inventory,
        - which are missing from the
        database,
        - which are in the database but with the wrong quantity.

        - return a tuple with the diff, the object name, total copies in the inv, total in stock.

        """
        d_stock = None
        inv_cards_set = self.copies_set.all()
        obj_name = ""
        if hasattr(self, "shelf") and self.shelf:
            d_stock = self.shelf.cards_set()
            obj_name = self.shelf.name
        elif hasattr(self, "place") and self.place:
            stock_cards_set = self.place.placecopies_set.select_related('card').all()
            obj_name = self.place.name
        elif hasattr(self, "basket") and self.basket:
            stock_cards_set = self.basket.basketcopies_set.all()
            obj_name = self.basket.name
        elif hasattr(self, "publisher") and self.publisher:
            cards = self.publisher.card_set.all()
            d_stock = {it.id: {'card': it, 'quantity': it.quantity} for it in cards}
            obj_name = self.publisher.name
        elif hasattr(self, "command") and self.command:
            cards = self.command.commandcopies_set.all()
            obj_name = self.command.title
            stock_cards_set = self.command.commandcopies_set.all()
        else:
            log.error("An inventory without place nor shelf nor basket nor publisher nor command... that shouldn't happen.")

        # Cards of the inventory:
        d_inv = {it.card.id: {'card': it.card, 'quantity': it.quantity} for it in inv_cards_set}
        # Total copies inventoried
        total_copies_in_inv = sum([it.quantity for it in inv_cards_set.all()])
        # Cards of the stock (the reference)
        if d_stock is None:
            d_stock = {it.card.id: {'card': it.card, 'quantity': it.nb} for it in stock_cards_set}
        total_copies_in_stock = sum([it['quantity'] for _, it in list(d_stock.items())])

        # cards in stock but not in the inventory:
        in_stock = list(set(d_stock) - set(d_inv))  # list of ids
        in_stock = {it: d_stock[it] for it in in_stock}

        # cards in the inventory but not in stoc:
        in_inv = list(set(d_inv) - set(d_stock))
        in_inv = {it: d_inv[it] for it in in_inv}

        # Difference of quantities:
        # diff = quantity original - quantity found in inventory
        d_diff = {}  # its quantity is: "how many the inventory has more or less compared with the stock"
        for id, val in list(d_inv.items()):
            d_diff[id] = {}
            d_diff[id]['in_orig'] = True  # i.e. in place/basket of origin, we get the diff from
            d_diff[id]['in_inv'] = True
            d_diff[id]['inv'] = val['quantity']
            d_diff[id]['card'] = val['card']
            if d_stock.get(id):
                d_diff[id]['diff'] = d_stock[id]['quantity'] - val['quantity']
                d_diff[id]['stock'] = d_stock[id]['quantity']
                d_stock[id]['inv'] = val['quantity']

            else:
                d_diff[id]['in_orig'] = False
                d_diff[id]['stock'] = 0
                d_diff[id]['diff'] = d_inv[id]['quantity']

        # Add the cards in the inv but not in the origin
        for id, val in list(d_stock.items()):
            if not d_inv.get(id):
                d_diff[id] = {'in_inv': False,
                              'in_orig': True,
                              'card': val['card'],
                              'stock': val['quantity'],
                              'inv': 0,
                              'diff': val['quantity'],
                             }
        # we must have all cards in d_dif and all info.

        if to_dict:
            # Update each sub-dict in place, to replace the card obj with its to_dict.
            d_diff = {key: update_in(val, ['card'], lambda copy: copy.to_dict()) for key, val in list(d_diff.items())}

        return d_diff, obj_name, total_copies_in_inv, total_copies_in_stock

    def archive(self):
        """
        Archive and close this inventory.
        """
        self.closed = timezone.now()
        self.archived = True
        self.save()

    def reopen(self):
        """
        Re-open this inventory.
        """
        self.closed = None
        self.archived = False
        self.applied = False
        self.save()

    @staticmethod
    def apply_inventory(pk):
        raise NotImplementedError

    def apply(self, add_qty=False, deposit_obj=None):
        """Apply this inventory to the stock. Changes each card's quantity of
        the needed place and closes the inventory.

        When called from the UI, this action needs the asynchronous task queue (see make
        taskqueue). It can be slow with non-small card lists.

        Return: a tuple status (bool), alerts (list of dicts with a level and a message).
        """
        if self.applied or (self.closed is not None and self.closed):
            return False, [{"level": ALERT_WARNING, "message": _("This inventory is already closed, you can't apply it again.")}]

        # Choose where to apply this inventory.
        if deposit_obj:
            place_or_deposit = deposit_obj
        elif hasattr(self, "place") and self.place:
            place_or_deposit = self.place
        else:
            # xxx use get_default_place ?
            # TODO: when inventoring a shelf, also choose a place !
            place_or_deposit = Preferences.get_default_place()

        # Shall we set the quantities of these cards in the stock or sum them to the existing ?
        # By default, we set them.
        add_qty = False
        # But a basket didn't touch the stock, so we want to add this basket to it.
        if hasattr(self, "basket") and self.basket:
            add_qty = True

        # In addition, if we work from a basket and it has an associated distributor,
        # we must set the cards' distributor to it.
        # XXX: check that there is no card with another distributor ?
        if hasattr(self, "basket") and self.basket and self.basket.distributor:
            # When receiving a command, we must update the distributor
            # of the cards of the command, and of the basket (which is
            # maybe empty, or may contain other cards).
            cards = self.copies.all()
            if self.basket.copies:  # optim.
                cards = list(set(self.copies.all()) | set(self.basket.copies.all()))
            self.basket.distributor.set_distributor(cards)

        # The inventory has inventoried cards: self.copies_set.all()
        # We must not forget cards that were not inventoried but must be set to 0.
        all_copies = []  # list of Card objects.
        if hasattr(self, "place") and self.place:
            all_copies = self.place.cards()
        elif hasattr(self, "basket") and self.basket:
            # In the case of receiving a command, we don't want to
            # reset the missing ones to 0.
            pass
        elif hasattr(self, "shelf") and self.shelf:
            all_copies = self.shelf.cards()
        elif hasattr(self, "publisher") and self.publisher:
            all_copies = self.publisher.card_set.all()
        elif hasattr(self, "command") and self.command:
            all_copies = self.command.copies.all()
        else:
            log.error("Applying inventory {}, getting all cards: missing implementation.".format(self.id))
            raise NotImplementedError
        # We get the cards not inventoried, but present in the original place/shelf.
        missing_copies = list(set(all_copies) - set(self.copies.all()))

        # Now we apply to the stock:
        try:
            for card_qty in self.copies_set.all():
                place_or_deposit.add_copy(card_qty.card, nb=card_qty.quantity, add=add_qty)
                card_qty.card.in_stock = True
                card_qty.card.save()

        except Exception as e:
            log.error("Error while applying the inventory {} to {}: {}"
                      .format(self.id, place_or_deposit, e))
            return False, [{"level": ALERT_ERROR, "message": _("There was an internal error, sorry !")}]

        # And we remove the remaining cards.
        try:
            for card in missing_copies:
                place_or_deposit.remove_card(card)
                # xxx: shall we mark in_stock to False ? It depends on their quantity in other places.
        except Exception as e:
            log.error("Error while applying the 'missing' cards of the inventory {} to {}: {}"
                      .format(self.id, place_or_deposit, e))
            return False, [{"level": ALERT_ERROR, "message": _("There was an internal error, sorry !")}]

        self.closed = timezone.now()
        self.applied = True
        self.save()

        return True, [{"level": ALERT_SUCCESS, "message": _("The inventory got succesfully applied to your stock.")}]


@python_2_unicode_compatible
class Inventory(InventoryBase):
    """
    We can do inventories of baskets, publishers, places, shelves.
    """
    #: List of cards and their quantities already "inventored".
    #: We must also consider (set to 0) the cards that are from the original shelf or place
    #: but were not inventoried.
    copies = models.ManyToManyField(Card, through="InventoryCopies", blank=True)
    #: We can do the inventory of a shelf.
    # XXX: use InventoryBase now that we have it.
    shelf = models.ForeignKey("Shelf", blank=True, null=True, verbose_name=__("shelf"))
    #: we can also do the inventory of a whole place.
    place = models.ForeignKey("Place", blank=True, null=True, verbose_name=__("place"))
    #: we can also do the inventory of publishers
    publisher = models.ForeignKey("publisher", blank=True, null=True, verbose_name=__("publisher"))
    #: At last, we can also do "inventories" of baskets, meaning we compare it
    # with a newly received command, or a pack of cards returned.
    basket = models.ForeignKey("Basket", blank=True, null=True, verbose_name=__("basket"))

    class Meta:
        verbose_name = __("Inventory")
        verbose_name_plural = __("Inventories")

    def __str__(self):
        inv_obj = self.shelf or self.place or self.basket or self.publisher
        return "{}: {}".format(self.id, inv_obj.name)

    @property
    def copies_set(self):
        return self.inventorycopies_set

    @property
    def name(self):
        name = ""
        if self.place:
            name = self.place.name
        elif self.basket:
            name = self.basket.name
        elif self.publisher:
            name = self.publisher.name
        elif self.shelf:
            name = self.shelf.name

        return name

    def get_absolute_url(self):
        return reverse('inventory_view', args=(self.id,))

    def _orig_cards_qty(self):
        """Return the number of copies to inventory (the ones in the original
        shelf, place, etc.
        """
        cards_qty = 0
        if self.shelf:
            cards_qty = self.shelf.cards_qty
        elif self.place:
            cards_qty = self.place.placecopies_set.count()
        elif self.publisher:
            cards_qty = self.publisher.card_set.count()
        elif self.basket:
            cards_qty = self.basket.basketcopies_set.count()
        else:
            log.error("We are not doing the inventory of a shelf, a place, a basket or a publisher, so what ?")

        return cards_qty

    @staticmethod
    def apply_inventory(pk):
        inv = Inventory.objects.get(id=pk)
        return inv.apply()

def do_inventory_apply(pk):
    Inventory.apply_inventory(pk)


def shelf_age_sort_key(it):
    """

    -it: a card object

    Return: a dict of lists with card objects. The keys (0,…4) represent days intervals.

    """
    it = (timezone.now() - (it.last_sell() or it.created)).days
    if it <= 91:  # 3 months
        return 0
    elif it <= 182:  # 6 months
        return 1
    elif it <= 365:
        return 2
    elif it <= 547:  # 18 months
        return 3
    elif it <= 730:  # 24 months
        return 4
    else:
        return 5

def get_total_cost():
    """Calculate the total cost of My Stock.
    """
    try:
        price_qties = [(it.price, it.quantity) for it in Card.objects.all()]
        price_qties = [it for it in price_qties if it[0] is not None]
        total_cost = sum([it[0] * it[1] for it in price_qties])
        return total_cost
    except Exception as e:
        log.error("Error calculating the total cost of the stock: {}".format(e))


class Stats(object):

    @staticmethod
    def stock(to_json=False):
        """Simple figures about our stock:
        - how many products
        - how many titles
        - how many titles (copies)
        - how many books (cards)
        - value of the stock
        # - value of the stock, excl. vat
        - idem for stock in deposits

        return: a dict by default, a json if to_json is set to True.

        """
        default_currency = Preferences.get_default_currency()
        places = Place.objects.all()
        # default_place = Preferences.get_default_place()
        # XXX: Everything below needs unit tests.
        type_book = CardType.objects.get(name="book")
        type_unknown = CardType.objects.get(name="unknown")
        res = {}
        nb_cards = Card.quantities_total()
        nb_not_books = Card.objects.filter(in_stock=True).exclude(card_type=type_book).count()
        # label: needed for graph creation in js.
        res['nb_titles'] = {'label': _("Number of book titles"),
                            'value': Card.objects.filter(in_stock=True).
                            filter(card_type=type_book).count()}
        res['nb_cards'] = {'label': _("Number of books"),
                           'value': nb_cards}
        res['nb_products'] = {'label': _("Number of products"),
                              'value': nb_cards + nb_not_books}
        res['nb_unknown'] = {'label': _("Number of products of unknown type"),
                             'value': Card.objects.filter(card_type=type_unknown).count()}
        # the ones we bought
        # impossible atm
        res['nb_bought'] = {'label': "",
                            'value': "<soon>"}

        # Cleanlyness: nb of cards with stock <= 0

        res['nb_cards_no_stock'] = {'label': _("Number of titles with no copy"),
                                    # 'value': Card.objects.filter(quantity__lte=0).count()}
                                    'value': sum([it.quantity_titles_no_stock() for it in places])}
        res['nb_cards_one_copy'] = {'label': _("Number of titles with one copy"),
                                    # 'value': Card.objects.filter(quantity=1).count()}
                                    'value': sum([it.quantity_titles_one_copy() for it in places])}

        # Stock of deposits
        in_deposits = 0
        deposits_cost = 0.0
        for dep in Deposit.objects.all():
            balance = dep.checkout_balance()
            for card_tuple in balance:
                if card_tuple[0].price is not None:
                    deposits_cost += card_tuple[0].price
                else:
                    deposits_cost += 0
                nb_current = card_tuple[1].nb_current
                if nb_current > 0:
                    in_deposits += nb_current

        res['in_deposits'] = {'label': _("Number of books in deposits"),
                              'value': in_deposits}
        # xxx: percentage cards we bought / in deposit / in both

        # Cost
        res['deposits_cost'] = {'label': _("Total cost of the books in deposits"),
                                'value': deposits_cost,
                                'value_fmt': price_fmt(deposits_cost, default_currency),
        }

        try:
            total_cost = sum([it.cost() for it in places])
            res['total_cost'] = {'label': _("Total cost of the stock"),
                                 # Round the float... or just {:.2f}.format.
                                 'value': roundfloat(total_cost),
                                 'value_fmt': price_fmt(roundfloat(total_cost), default_currency),
            }
            # The same, excluding vat.
            # XXX: to redo.
            # xxx: all Cards will not be books.
            total_cost_excl_tax = sum([it.cost_excl_taxes() for it in places])
            res['total_cost_excl_tax'] = {'label': _("Total cost of the stock, excl. tax"),
                                          'value': total_cost_excl_tax,
                                          'value_fmt': price_fmt(total_cost_excl_tax, default_currency),
            }

        except Exception as e:
            log.error("Error with total_cost: {}".format(e))

        # Next appointments
        # xxx: transform to strings and associate with the deposit.
        # dates = [it.due_date for it in Deposit.objects.order_by("due_date").all()]
        res['next_deposits_dates'] = {'label': _('next appointments'),
                                      # 'value': dates}
                                      'value': "<soon>"}

        if to_json:
            res = json.dumps(res)

        return res

    @staticmethod
    def sells_month(limit=10, year=None, month=None):
        """Best sells of the current month, total revenue, total nb of cards
        sold, average sell.
        - year, month (int, month must be in [1..12]). If not, current year, and current month.

        Return: a dict {
            "best_sells": list of cards, max length "limit",
            "revenue": total revenue (float)
            "nb_sells" (int): the number of sell transactions
            "nb_cards_sold" (int): the number of copies sold
            "mean": mean of sells (float),
            }
        """
        default_currency = Preferences.get_default_currency()
        # Get the sells since the beginning of the given month
        start_time = timezone.now()
        if year is None:
            year = start_time.year
        if month is not None:
            month = int(month)
            assert month, int
            start_time = timezone.datetime(year=year, month=month, day=1)
        else:
            month = start_time.month

        soldcards = SoldCards.objects.exclude(sell__canceled=True).filter(created__year=year).filter(created__month=month)
        price_qties = soldcards.values_list('price_sold', 'quantity')
        revenue = sum([it[0] * it[1] for it in price_qties])
        revenue = roundfloat(revenue) if revenue else 0
        # Count the total revenue
        nb_sells = soldcards.values('sell_id').distinct().count()
        nb_cards_sold = sum(soldcards.values_list('quantity', flat=True))

        # Average sell
        sell_mean = None
        if nb_sells:
            sell_mean = revenue / nb_sells
            sell_mean = roundfloat(sell_mean)

        to_ret = {
            "revenue": revenue,
            "revenue_fmt": price_fmt(revenue, default_currency),
            "nb_sells": nb_sells,
            "nb_cards_sold": nb_cards_sold,
            "mean": sell_mean,
            "mean_fmt": price_fmt(sell_mean, default_currency),
            # nb of sells
        }

        return to_ret

    @staticmethod
    def entries_month():
        """
        """
        now = timezone.now()
        month_beg = now - timezone.timedelta(days=now.day - 1)
        res = history.Entry.objects.filter(created__gt=month_beg)
        res = [it.to_dict() for it in res]
        nb = sum([it.entrycopies_set.count() for it in res])
        return {"cards": res,
                "total": nb}

    @staticmethod
    def _shelf_age(shelf_id):
        shelf_name = None
        try:
            shelf = Shelf.objects.get(id=shelf_id)
            shelf_name = shelf.name
        except Exception as e:
            log.error("No shelf with id {}: {}".format(shelf_id, e))
            return None

        hcards = Card.objects.filter(shelf__name=shelf_name)
        stats = groupby(shelf_age_sort_key, hcards)

        # Have a dict with all keys (easier for plotting charts)
        for key in range(6):
            if key not in stats:
                stats[key] = []

        # to dict
        stats = valmap(lambda its: [it.to_dict() for it in its], stats)

        return stats

    @staticmethod
    def stock_age(shelf_id):
        # 2020-01-31 removed from dashboard.
        return Stats._shelf_age(shelf_id)

@python_2_unicode_compatible
class CommandCopies(TimeStampedModel):
    """Intermediate table between a Command and its Cards. Records the
    number of exemplaries for each card.
    """
    card = models.ForeignKey("Card")
    command = models.ForeignKey("Command")
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return "Command for card {}".format(self.card.pk)

    @property
    def qty(self):
        return self.quantity

    @property
    def nb(self):
        return self.quantity

    @property
    def value_inctaxes(self):
        try:
            return self.card.price * self.quantity
        except Exception as e:
            log.error("Error getting price for value: {}".format(e))
            return 0

    @property
    def value(self):
        try:
            return self.card.price_discounted * self.quantity
        except Exception as e:
            log.error("Error getting discounted value: {}".format(e))
            return 0

    # def __str__(self):
        # pass

    # def to_dict(self):
        # pass

class InventoryCommandCopies(InventoryCopiesBase):
    # we inherit card and quantity.
    inventory = models.ForeignKey("InventoryCommand")


class InventoryCommand(InventoryBase):
    #: List of cards and their quantities already "inventoried".
    copies = models.ManyToManyField(Card, through="InventoryCommandCopies", blank=True)

    @property
    def copies_set(self):
        return self.inventorycommandcopies_set

    @property
    def name(self):
        return self.command.name

    def get_absolute_url(self):
        self.command.get_absolute_url()

    def _orig_cards_qty(self):
        # the nb of copies to inventory (the ones in the original place).
        cards_qty = self.command.commandcopies_set.count()
        return cards_qty

    def state(self):
        copies = [it.to_dict() for it in self.copies_set.all()]
        nb_cards = len(copies)
        nb_copies = self.nb_copies()
        inv_name = ""
        # orig_cards_qty = self._orig_cards_qty()
        inv_name = self.command.title
        inv_dict = self.to_dict()

        return {
            "copies": copies,
            "inv_name": inv_name,
            "nb_cards": nb_cards,
            "nb_copies": nb_copies,
            "object": inv_dict,
            "command": inv_dict,
        }

    @staticmethod
    def apply_inventory(pk, add_qty=True):
        inv = InventoryCommand.objects.get(id=pk)
        return inv.apply(add_qty=add_qty)

def do_command_apply(pk):
    InventoryCommand.apply_inventory(pk)

@python_2_unicode_compatible
class Command(TimeStampedModel):
    """A command records that some cards were ordered to a supplier.
    We have to track when we receive the command and when we pay.
    """

    #: Name
    name = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True, verbose_name=__("name"))
    #: Command to supplier: a publisher or a distributor (see `supplier`).
    publisher = models.ForeignKey("Publisher", blank=True, null=True, verbose_name=__("publisher"))
    distributor = models.ForeignKey("Distributor", blank=True, null=True, verbose_name=__("distributor"))
    #: Copies in it:
    copies = models.ManyToManyField(Card, through="CommandCopies", blank=True)
    #: Date of reception. To check if the command was received, use the received property.
    date_received = models.DateTimeField(blank=True, null=True, verbose_name=__("date received"))
    #: Date of reception of the bill from the supplier. See also the `bill_received` property
    date_bill_received = models.DateTimeField(blank=True, null=True,
                                              verbose_name=__("date bill received"))
    #: When did we send the payment ? See also `payment_sent`.
    date_payment_sent = models.DateTimeField(blank=True, null=True,
                                             verbose_name=__("date payment sent"))
    #: When did the supplier accept the payment ? See also `paid`.
    date_paid = models.DateTimeField(blank=True, null=True,
                                     verbose_name=__("date paid"))
    #: Inventory of the parcel we received, to check its content.
    inventory = models.OneToOneField('InventoryCommand', blank=True, null=True,
                                     verbose_name=__("inventory"))
    #: Short comment
    comment = models.TextField(blank=True, null=True, verbose_name=__("comment"))

    class Meta:
        verbose_name = __("Command")

    def get_absolute_url(self):
        return reverse("commands_view", args=(self.id,))

    def __str__(self):
        return "command {} for {}".format(self.id, self.supplier_name)

    def to_list(self):
        date_received = ""
        date_bill_received = ""
        date_payment_sent = ""
        date_paid = ""
        if self.date_received:
            date_received = self.date_received.strftime(DATE_FORMAT)
        if self.date_bill_received:
            date_bill_received = self.date_bill_received.strftime(DATE_FORMAT)
        if self.date_payment_sent:
            date_payment_sent = self.date_payment_sent.strftime(DATE_FORMAT)
        if self.date_paid:
            date_paid = self.date_paid.strftime(DATE_FORMAT)

        return {
            'id': self.id,
            'name': self.name,
            'created': self.created.strftime(DATE_FORMAT),
            'distributor_name': self.distributor.name if self.distributor else _("NO SUPPLIER"),
            'distributor_id': self.distributor.id if self.distributor else 0,
            'nb_copies': self.copies.count(),
            'date_received': date_received,
            'date_bill_received': date_bill_received,
            'date_paid': date_paid,
            'date_payment_sent': date_payment_sent,
        }

    @property
    def supplier(self):
        """
        """
        return self.publisher or self.distributor

    @property
    def supplier_id(self):
        if self.publisher:
            return self.publisher.id
        elif self.distributor:
            return self.distributor.id
        return None

    @property
    def supplier_name(self):
        """Return the publisher or distributor name (str).
        """
        if self.publisher:
            return self.publisher.name
        elif self.distributor:
            return self.distributor.name
        return None

    @property
    def received(self):
        """Was this command received ?
        Return: boolean.
        """
        return self.date_received is not None

    @property
    def received_delta(self):
        """
        Delta, in days, between the date we sent it (created) and received it.
        """
        diff = ""
        if self.created and self.date_received:
            created = pendulum.instance(self.created)
            received = pendulum.instance(self.date_received)
            diff = created.diff(received).in_days()

        return diff

    @property
    def paid_delta(self):
        """
        Delta, in days, between the creation and the day it was paid (thus finished).
        """
        diff = ""
        if self.created and self.date_paid:
            created = pendulum.instance(self.created)
            paid = pendulum.instance(self.date_paid)
            diff = created.diff(paid).in_days()
        return diff

    @property
    def date_received_label(self):
        """See other _label property below.
        """
        return self.date_received or ""

    @property
    def date_bill_received_label(self):
        # btw, no much need of refactoring with one date_label(label)
        # method and getattr, because we can't pass arguments in
        # templates.
        return self.date_bill_received or ""

    @property
    def date_payment_sent_label(self):
        """
        Return the date or "", for UI.
        """
        return self.date_payment_sent or ""

    @property
    def bill_received(self):
        """Did we receive the bill, from the supplier ?
        Return: boolea
        """
        return self.date_bill_received is not None

    @property
    def payment_sent(self):
        return self.date_payment_sent is not None

    @property
    def paid(self):
        return self.date_paid is not None

    @property
    def date_paid_label(self):
        """Helps the UI to not display "None" (django template).
        Return: date object or "".
        """
        return self.date_paid or ""

    @property
    def title(self):
        """
        Used for example in the inventory UI title.
        """
        return _("command #{} - {}").format(self.id, self.supplier_name)

    @staticmethod
    def ongoing(to_dict=None):
        """
        Return a queryset of ongoing commands (to be more defined).
        Return: a queryset, so to apply .all() or .count().
        """
        # XXX: fix return type.
        res = Command.objects.filter(date_paid__isnull=True).filter(date_received__isnull=True)
        if res and to_dict:
            # return [it.to_dict() for it in res]  # f* to_dict returns null O_o
            return [it.to_list() for it in res]
        return res

    @staticmethod
    def nb_ongoing():
        """Return: int.
        """
        return Command.ongoing().count()

    def nb_copies(self):
        """Return the number of copies of this command.
        """
        try:
            return sum([it.quantity for it in self.commandcopies_set.all()])
        except Exception:
            return None

    def total_value_inctaxes(self):
        try:
            return sum([it.value_inctaxes for it in self.commandcopies_set.all()])
        except Exception:
            return None

    def total_value(self):
        try:
            return sum([it.value for it in self.commandcopies_set.all()])
        except Exception:
            return None

    def to_dict(self):
        # Use the serializer in drfserializers.py.
        pass

    def add_copy(self, card_obj, card_id=None, nb=1):
        """Add a given card object to the command.

        Return: a tuple quantity of the card, a dict of Messages (status, list of messages).
        """
        msgs = Messages()

        if not (card_obj or card_id):
            msgs.add_error("Adding a copy to a command without giving a card. Abort.")
            return msgs.status, msgs.msgs

        if card_obj and not card_id:
            card_id = card_obj.id

        try:
            cmdcopy, created = self.commandcopies_set.get_or_create(card_id=card_id)
            cmdcopy.quantity += nb
            cmdcopy.save()
        except Exception as e:
            log.error('Error while adding card {} to command {}: {}'.format(card_id,
                                                                            self.id,
                                                                            e))
            msgs.add_error("An error occured while adding the card {} to the command.".format(card_id))
            return False, msgs

        return cmdcopy.quantity, msgs

    @staticmethod
    def new_command(ids_qties=None, distributor_id=None):
        """Create a command, remove the cards from the ToCommand list.

        A command is linked to a distributor.
        If you are used to work with publishers, then create a distributor with the same name.

        Return: the new Command object, with a Messages dict.
        """
        msgs = Messages()

        # We must have a distributor.
        dist_obj = None
        if distributor_id is None:
            msgs.add_error("Please provide a distributor for the new command.")
            return None, msgs

        elif distributor_id and distributor_id not in BAD_IDS:
            dist_obj = Distributor.objects.get(id=distributor_id)

        cmd = Command()
        cmd.save()
        ids_qties = [it for it in ids_qties if not (not it)]
        if not ids_qties:
            msgs.add_error("Creating a command with no card ids. Abort.")
            return None, msgs

        # Here we create a new one: we can bulk_create it.
        CommandCopies.objects.bulk_create([
            CommandCopies(card_id=it[0],
                          command_id=cmd.id,
                          quantity=it[1])
            for it in ids_qties])

        # Register the (optional) supplier.
        if dist_obj:
            cmd.distributor = dist_obj
            cmd.save()

        # Remove the given cards from the AutoCommand basket.
        ids = [it[0] for it in ids_qties]
        tocmd = Basket.auto_command_basket()
        tocmd.basketcopies_set.filter(card_id__in=ids).delete()

        return cmd, msgs

    @staticmethod
    def update_date_attr(cmd_id, label, date):
        """
        Update the given attr with val.

        - cmd_id: id (int or str)
        - label: str
        - date: str in right format (see commons.DATE_FORMAT).

        return: Messages object.
        """
        msgs = Messages()
        try:
            date = datetime.datetime.strptime(date, DATE_FORMAT)
        except ValueError as e:
            log.warning("commands update: error on date format: {}".format(e))
            return msgs.add_error("Date format is not valid.")

        try:
            cmd_obj = Command.objects.get(id=cmd_id)
        except ObjectDoesNotExist as e:
            return msgs.add_error("The queried command does not exist.")

        if label not in dir(cmd_obj):
            return msgs.add_error("The date to change doesn't seem to exist.")

        # At last, update the attribute.
        try:
            setattr(cmd_obj, label, date)
            cmd_obj.save()
        except Exception as e:
            log.error("Error updating command {} with attribute {} and value {}: {}".format(
                cmd_id, label, date, e))
            return msgs.add_error("Internal error.")

        msgs.add_success(_("Command updated succesfully."))
        return msgs

    def get_inventory(self):
        """
        Create an inventory of the parcel (to check its content) if it doesn't exist.
        """

        if not self.inventory:
            inv = InventoryCommand()
            inv.save()
            self.inventory = inv
            self.save()

        return self.inventory
