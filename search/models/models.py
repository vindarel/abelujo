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

import datetime
import json
import logging
import operator
from datetime import date
from textwrap import dedent

import pytz
from toolz.dicttoolz import update_in
from toolz.dicttoolz import valmap
from toolz.itertoolz import groupby

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.http import quote
from django.utils.translation import ugettext as _
from search.models import history
from search.models.common import ALERT_ERROR
from search.models.common import ALERT_SUCCESS
from search.models.common import ALERT_WARNING
from search.models.common import DATE_FORMAT
from search.models.common import PAYMENT_CHOICES
from search.models.common import TimeStampedModel
from search.models.utils import is_isbn
from search.models.utils import isbn_cleanup
from search.models.utils import roundfloat

CHAR_LENGTH = 200
TEXT_LENGTH = 10000
PAGE_SIZE = 50
#: Date format used to jsonify dates, used by angular-ui (datepicker)
# and the ui in general (datejs).
DEFAULT_PRICE = 0

log = logging.getLogger(__name__)

DEPOSIT_TYPES_CHOICES = [
    ("Dépôt de libraire", (
        ("lib", "dépôt de libraire"),
        ("fix", "dépôt fixe"),
      )),
    ("Dépôt de distributeur", (
        ("dist", "dépôt de distributeur"),
    )),
    ]


class Author(TimeStampedModel):
    name = models.CharField(unique=True, max_length=200)

    class Meta:
        ordering = ('name',)
        app_label = "search"

    def __unicode__(self):
        return u"{}".format(self.name)

    @staticmethod
    def search(query):
        """Search for names containing "query", return a python list.
        """
        try:
            data = Author.objects.filter(name__icontains=query)
        except Exception as e:
            log.error("Author.search error: {}".format(e))
            data = [
                {"alerts": {"level": ALERT_ERROR,
                            "message": "error while searching for authors"}}
            ]

        # data = [auth.to_list() for auth in data]
        return data


class Distributor(TimeStampedModel):
    """The entity that distributes the copies (a publisher can be a
    distributor).
    """

    name = models.CharField(max_length=CHAR_LENGTH)
    #: The discount (in %). When we pay the distributor we keep the amount of
    # the discount.
    discount = models.IntegerField(default=0, null=True, blank=True)
    #: Star the distributors to give precendence to our favourite ones.
    stars = models.IntegerField(default=0, null=True, blank=True)
    #: Contact: email adress. To complete, create a Contact class.
    email = models.EmailField(null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"{}".format(self.name)

    def get_absolute_url(self):
        return "/admin/search/{}/{}".format(self.__class__.__name__.lower(),
                                            self.id)

    def __repr__(self):
        """Representation for json/javascript.
        """
        return "{} ({} %)".format(self.name, self.discount)

    def to_list(self):
        return {
            "id": self.id,
            "name": self.name,
            "discount": self.discount,
            "stars": self.stars,
            "email": self.email,
            "repr": self.__repr__(),
        }

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


class Publisher (models.Model):
    """The publisher of the card.
    """

    #: Name of the publisher
    name = models.CharField(max_length=CHAR_LENGTH)
    #: ISBN of the publisher
    isbn = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: Contact address (to put in own table)
    address = models.TextField(null=True, blank=True)
    #: Optional comment
    comment = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("name",)
        app_label = "search"

    def __unicode__(self):
        return u"{}, {}".format(self.id, self.name)

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

class Collection (models.Model):
    """A collection (or sub-collection) of books.

    A collection is a set of cards gathered under a common title,
    chosen by the publisher.
    """

    #: Name of the collection
    name = models.CharField(max_length=200)
    #: Is it an ordered collection ?
    ordered = models.IntegerField(null=True, blank=True)
    #: Parent collection. A null field means this collection is not
    # the sub-collection of another one.
    parent = models.ForeignKey("Collection", null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"{}".format(self.name)

class Shelf(models.Model):
    """Shelves are categories for cards, but they have a physical location
    in the bookstore.

    - ...

    For now, a Card has only one shelf.

    """
    class Meta:
        app_label = "search"

    #: Name of the shelf
    name = models.CharField(max_length=CHAR_LENGTH)

    def __unicode__(self):
        #idea: show the nb of cards with that category.
        return u"{}".format(self.name)

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

class CardType(models.Model):
    """The type of a card: a book, a CD, a t-shirt, a DVD,…
    """
    name = models.CharField(max_length=100, null=True)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return u"{}".format(self.name)

    @staticmethod
    def search(query):
        if not query:
            query=""
        if query == "":
            log.info("CardType: we return everything")
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


class Card(TimeStampedModel):
    """A Card represents a book, a CD, a t-shirt, etc. This isn't the
    physical object.
    """

    #: Title:
    title = models.CharField(max_length=CHAR_LENGTH)
    #: type of the card, if specified (book, CD, tshirt, …)
    card_type = models.ForeignKey(CardType, blank=True, null=True)
    #: ean/isbn (mandatory). For db queries, use isbn, otherwise "ean" points to the isbn.
    isbn = models.CharField(max_length=99, null=True, blank=True)
    #: Maybe this card doesn't have an isbn. It's good to know it isn't missing.
    has_isbn = models.NullBooleanField(default=True, blank=True, null=True)
    sortkey = models.TextField('Authors', blank=True)
    authors = models.ManyToManyField(Author)
    price = models.FloatField(null=True, blank=True, default=0.0)
    #: price_sold is only used to generate an angular form, it is not
    #: stored here in the db.
    price_sold = models.FloatField(null=True, blank=True)
    #: The current quantity of this card in Places. It is equal to the sum of quantities in each place.
    # It may seem redundant but it's needed for effective queries.
    quantity = models.IntegerField(null=True, blank=True, default=0)
    #: The minimal quantity we want to always have in stock:
    threshold = models.IntegerField(blank=True, null=True, default=1)
    #: Publisher of the card:
    publishers = models.ManyToManyField(Publisher, blank=True)
    year_published = models.DateField(blank=True, null=True)
    #: Distributor:
    distributor = models.ForeignKey("Distributor", blank=True, null=True)
    #: Collection
    collection = models.ForeignKey(Collection, blank=True, null=True)
    #: Shelf (for now, only one shelf).
    shelf = models.ForeignKey("Shelf", blank=True, null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    #: the places were we can find this card (and how many).
    places = models.ManyToManyField("Place", through="PlaceCopies", blank=True)
    #: when and how this card was sold: sells (see the Sell table).
    #: an url to show a thumbnail of the cover:
    img = models.URLField(null=True, blank=True)
    #: the internet source from which we got the card's informations
    data_source = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: link to the card's data source
    details_url = models.URLField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: the summary (of the back cover)
    summary = models.TextField(null=True, blank=True)
    #: a user's comment
    comment = models.TextField(blank=True)
    #: Did we buy this card once, or did we register it only to use in
    #: lists (baskets), without buying it ?
    in_stock = models.BooleanField(default=True)

    @property
    def ean(self):
        """Can't be used in queries, use isbn.
        """
        return self.isbn

    def save(self, *args, **kwargs):
        """We override the save method in order to copy the price to
        price_sold. We want it to initialize the angular form.
        """
        # https://docs.djangoproject.com/en/1.8/topics/db/models/#overriding-model-methods
        self.price_sold = self.price
        super(Card, self).save(*args, **kwargs)

    class Meta:
        app_label = "search"
        ordering = ('sortkey', 'year_published', 'title')

    def __unicode__(self):
        """To pretty print a list of cards, see models.utils.ppcard.
        """
        MAX_LENGTH = 15
        authors = self.authors.all()
        authors = authors[0].name if authors else ""
        publishers = ", ".join([pub.name for pub in self.publishers.all()])
        if len(publishers) > MAX_LENGTH:
            publishers = publishers[0:MAX_LENGTH] + "..."
        distributor = self.distributor.name if self.distributor else _("none")
        return u"{}:{}, {}, editor: {}, distributor: {}".format(self.id, self.title, authors, publishers, distributor)

    def display_authors(self):
        return u', '.join([a.name for a in self.authors.all()])

    def getAuthorsString(self):
        """returns a string with the list of authors.
        It is called from the templates so can't take any arg.
        """
        return "; ".join([aut.name for aut in self.authors.all()])

    def quantity_compute(self):
        """Return the quantity of this card in all places (not deposits).

        Utility function, primarily used for a data migration. Use the
        Card.quantity field to query the db.

        return: int
        """
        quantity = 0
        if self.placecopies_set.count():
            quantity = sum([pl.nb for pl in self.placecopies_set.all()])
        return quantity

    @staticmethod
    def quantities_to_zero():
        """Set all cards' quantity to zero. Only for admin purposes.
        """
        for place_copy in PlaceCopies.objects.all():
            place_copy.quantity_set(0)

    @staticmethod
    def quantities_total():
        """Total of quantities for all cards in this stock (for tests).
        Return: int (None on error)
        """
        try:
            return sum([it.quantities_total() for it in Place.objects.all()])
        except Exception as e:
            log.error("Error while getting the total quantities of all cards: {}".format(e))

    def quantity_to_zero(self):
        """Set the quantity of this card to zero. This is needed sometimes for
        admin purposes.
        """
        for pc in self.placecopies_set.all():
            pc.quantity_set(0)

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

    def to_dict(self):
        return self.to_list()

    @property
    def pubs_repr(self):
        """Coma-separated str representation of this card's publishers.
        May need truncating ?

        Return: str
        """
        publishers = self.publishers.all()
        pubs_repr = ", ".join(it.name for it in publishers)
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

    def to_list(self):
        authors = self.authors.all()
        # comply to JS format (needs harmonization!)
        auth = [{"fields": {'name': it.name}} for it in authors]
        authors_repr = self.authors_repr
        publishers = self.publishers.all()
        pubs = [{'fields': {'name': it.name}} for it in publishers]
        pubs_repr = self.pubs_repr

        if self.distributor:
            dist = self.distributor.to_list()
        else:
            dist = {}

        try:
            get_absolute_url = self.get_absolute_url()
        except Exception as e:
            log.error(e)
            get_absolute_url = ""

        res = {
            "id": self.id,
            "ambiguous_sell": self.ambiguous_sell(),
            "authors": auth,
            "authors_repr": authors_repr,
            "collection": self.collection.name.capitalize() if self.collection else None,
            "created": self.created.strftime(DATE_FORMAT), #YYYY-mm-dd
            "data_source": self.data_source,
            "details_url": self.details_url,
            "distributor": dist,
            "isbn": self.isbn,
            "get_absolute_url": get_absolute_url,
            "img": self.img,
            "isbn": self.isbn if self.isbn else u"",
            "model": self.__class__.__name__, # useful to sort history.
            "places": ", ".join([p.name for p in self.places.all()]),
            "price": self.price,
            "price_sold": self.price_sold,
            # "publishers": ", ".join([p.name.capitalize() for p in self.publishers.all()]),
            "publishers": pubs,
            "pubs_repr": pubs_repr,
            "quantity": self.quantity,
            "shelf": self.shelf.name if self.shelf else "",
            "title": self.title,
            "threshold": self.threshold,
        }
        return res

    @staticmethod
    def obj_to_list(cards):
        """Transform a list of Card objects to a python list.

        Used to save a search result in the session, which needs a
        serializable object, and for the api to encode to json.
        TODO: https://docs.djangoproject.com/en/1.6/topics/serialization/
        """

        return [card.to_list() for card in cards]

    @staticmethod
    def first_cards(nb, to_list=False):
        """get the first n cards from our collection (very basic, to test)
        """
        ret = Card.objects.order_by("-created")[:nb]
        if to_list:
            ret = Card.obj_to_list(ret)
        return ret

    @staticmethod
    def search(words, card_type_id=None, distributor=None, distributor_id=None,
               to_list=False,
               publisher_id=None, place_id=None, shelf_id=None,
               bought=False, order_by=None):
        """Search a card (by title, authors' names, ean/isbn).

        SIZE_LIMIT = 100

        - words: (list of strings) a list of key words or eans/isbns

        - card_type_id: id referencing to CardType

        - to_list: if True, we return a list of dicts, not Card
          objects. Used to store the search result into the session,
          which doesn't know how to store Card objects.

        returns: a 2-tuple: a list of objects or a list of dicts if to_list is
        specified, and a list of messages.
        """
        SIZE_LIMIT = 10 #TODO: pagination
        isbns = []
        cards = []
        msgs = []

        # Get all isbns, eans.
        if words:
            # Separate search terms that are isbns.
            isbns = filter(is_isbn, words)
            words = list(set(words) - set(isbns))

        if words:
            # Doesn't pass data validation of the view.
            head = words[0]
            cards = Card.objects.filter(Q(title__icontains=head) |
                                        Q(authors__name__icontains=head))

            if len(words) > 1:
                for elt in words[1:]:
                    cards = cards.filter(Q(title__icontains=elt)|
                                         Q(authors__name__icontains=elt))

        elif not isbns:
            cards = Card.objects.all()  # returns a QuerySets, which are lazy.

        if bought and cards:
            cards = cards.filter(in_stock=True)

        if cards and shelf_id:
            try:
                cards = cards.filter(shelf=shelf_id)
            except Exception as e:
                log.error(e)

        if cards and place_id:
            try:
                cards = cards.filter(placecopies__place__id=place_id)
            except Exception as e:
                log.error(e)

        if distributor and cards:
            cards = cards.filter(distributor__name__exact=distributor)

        if distributor_id and cards:
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
            for isbn in isbns:
                try:
                    card = Card.objects.get(isbn=isbn)
                    cards.append(card)
                except Exception as e:
                    log.error("Error searching for isbn {}: {}".format(isbn, e))
                    msgs.append({'level': 'error',
                                 'message': e})

        # Sort
        if order_by:
            cards = cards.order_by(order_by)

        # Pagination
        paginator = Paginator(cards, SIZE_LIMIT)
        page = 1
        try:
            cards = paginator.page(page)
        except EmptyPage:
            cards = paginator.page(paginator.num_page)
        finally:
            cards = cards.object_list

        if to_list:
            cards = Card.obj_to_list(cards)

        return cards, msgs

    @staticmethod
    def is_in_stock(cards):
        """Check by isbn if the given cards (dicts) are in stock.

        Return a list of dicts with new keys each:
        - "in_stock": 0/the quantity
        - "id"
        """
        if not cards:
            return cards

        quantity = None
        found_id = 0
        for card in cards:
            try:
                found, _ = Card.exists(card)
                if type(found) == list:
                    found = found[0]
                if found:
                    quantity = found.quantity
                    found_id = found.id
            except ObjectDoesNotExist:
                quantity = None
                found_id = None

            card['in_stock'] = quantity
            card['id'] = found_id

        return cards


    @staticmethod
    def get_from_id_list(cards_id):
        """cards_id: list of card ids

        returns: a tuple Card objects, messages.
        """
        result = []
        msgs = []

        for id in cards_id:
            try:
                card = Card.objects.get(id=id)
                result.append(card)
            except ObjectDoesNotExist:
                msg = "the card of id {} doesn't exist.".format(id)
                log.debug(msg)
                msgs.append({"level": messages.WARNING, "message": msg})
        return result, msgs

    @staticmethod
    def sell(id=None, quantity=1, place_id=None):
        """Sell a card. Decreases its quantity in the given place.

        This is a static method, use it like this:
        >>> Card.sell(id=<id>)

        :param int id: the id of the card to sell.
        return: a tuple (return_code, "message")
        """
        # Why use a static method ? Because from the view, we get back
        # an id and not a Card object. Why ? Because we want to store
        # list of cards into the session, and we can't serialize Card
        # objects as is, so we use lists of dicts (that we prefer over
        # django serialization).
        try:
            card = Card.objects.get(id=id)

            # Get the place from where we sell it.
            if place_id:
                place_obj = card.placecopies_set.get(id=place_id)
            else:
                if card.placecopies_set.count():
                    # XXX: get the default place
                    # fix also the undo().
                    log.warning("selling: select the place: to finish")
                    place_obj = card.placecopies_set.first()
                else:
                    return False, "We can not sell card {}: it is not associated with any place.".format(card.title)

            place_obj.nb = place_obj.nb - quantity
            place_obj.save()
            card.quantity = card.quantity - quantity
            card.save()
        except ObjectDoesNotExist as e:
            log.warning(u"Requested card %s does not exist: %s" % (id, e))
            return (None, "La notice n'existe pas.")
        except Exception as e:
            log.error(u"Error selling a card: {}.".format(e))

        if card.quantity <= 0:
            Basket.add_to_auto_command(card)

        return (True, "")

    def sell_undo(self, quantity=1, place_id=None):
        """Do the contrary of sell().

        todo: manage the places we sell from correctly.
        """
        msgs = []
        if place_id:
            place_obj = self.placecopies_set.get(id=place_id)
        else:
            # same warning as sell()
            if self.placecopies_set.count():
                place_obj = self.placecopies_set.first()
            else:
                return False, {"message": _(u"We can not undo the sell of card {}: \
                it is not associated to any place. This shouldn't happen.").format(self.title),
                               "status": ALERT_ERROR}
                # let's take the default place
                # place_obj = Place.objects.first()
                # msgs.append(u"No place was specified for '{}'. Let's take {}".format(self.title, place_obj.name))

        place_obj.nb = place_obj.nb + quantity
        place_obj.save()
        self.quantity = self.quantity + quantity
        self.save()

        return True, msgs

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
        msgs = []
        # Look for the same isbn/ean
        if card_dict.get('isbn') or card_dict.get('ean'):
            isbn = card_dict.get('isbn', card_dict.get('ean'))
            clist = Card.objects.filter(isbn=isbn).first()
            if clist:
                return clist, msgs

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
                    return obj, msgs

            # Some cards have the same title, and not much more attributes.
            if no_authors and no_pubs:
                return clist, msgs

        return None, msgs

    @staticmethod
    def from_dict(card, to_list=False):
        """Add a card from a dict.

        Check if it already exists in the db (the card may have no
        isbn). If so, update its secondary fields.

        Format of dict:
            title:      string
            year:       int or None
            authors:    list of authors names (list of str) or list of Author objects.
            shelf:   id (int)
            distributor: id of a Distributor
            publishers: list of names of publishers (create one on the fly, like with webscraping)
            publishers_ids: list of ids of publishers
            has_isbn:   boolean
            isbn:       str
            details_url: url (string)
            card_type:  name of the type (string)
            location:   string
            in_stock:   bool
            sortkey:    string of authors in the order they appear on
                        the cover
            origkey:    (optional) original key, like an ISBN, or if
                        converting from another system


        return: a tuple Card objec created or existing, message (str).

        """

        msg_success = _("The card was created successfully.")
        msg_exists = _("This card already exists.")

        # Unknown years is okay
        year = card.get('year', None)
        try:
            int(year)
            year = date(year, 1, 1)
        except Exception:
            year = None

        # Make the card
        # Get authors or create
        card_authors = []
        if card.get('authors'):
            auts = card.get('authors')
            if type(auts) != type([]):
                auts = [auts]
            if type(auts[0]) in [type("string"), type(u"unicode-str")]:
                for aut in auts:
                    author, created = Author.objects.get_or_create(name=aut)
                    card_authors.append(author)
            else:
                # We already have objects.
                card_authors = card["authors"]
        else:
            log.warning(u"this card has no authors (ok for a CD): %s" % card.get('title'))

        # Get and clean the ean/isbn (beware of form data)
        isbn = card.get("isbn", card.get("ean", ""))
        if isbn:
            isbn = isbn_cleanup(isbn)

        # Get the distributor:
        card_distributor=None
        if card.get("distributor"):
            try:
                card_distributor = Distributor.objects.get(id=card.get("distributor"))
            except Exception as e:
                # XXX use distributor_id and distributor
                try:
                    card_distributor = Distributor.objects.get(name=card.get("distributor"))
                except Exception as e:
                    log.warning("couldn't get distributor {}. This is not necessarily a bug.".format(card.get('distributor')))

        # Get the shelf
        card_shelf = None
        if card.get('shelf'):
            try:
                card_shelf, created = Shelf.objects.get_or_create(name=card.get('shelf'))
            except Exception as e:
                log.warning("couldn't get or create the shelf {}.".format(card.get('shelf')))

        # Get the publishers:
        card_publishers = []
        if card.get("publishers_ids"):
            card_publishers = [Publisher.objects.get(id=it) for it in card.get("publishers_ids")]

        # Check if the card already exists (it may not have an isbn).
        exists_list, _msgs = Card.exists(card)
        created = False
        if exists_list:
            card_obj = exists_list
            # Update fields, except isbn (as with "else" below)
            card_obj.distributor = card_distributor
            card_obj.save()

            card_obj.isbn = isbn
            card_obj.save()

        else:
            # Create the card with its simple fields.
            # Add the relationships afterwards.
            card_obj, created = Card.objects.get_or_create(
                title=card.get('title'),
                year_published=year,
                price = card.get('price',  0),
                price_sold = card.get('price_sold',  0),
                isbn = isbn,
                has_isbn = card.get('has_isbn'),
                img = card.get('img', ""),
                details_url = card.get('details_url'),
                data_source = card.get('data_source'),
                summary = card.get('summary'),
            )

            #TODO: we can also update every field for the existing card.

            # add the authors
            if card_authors:  # TODO: more tests !
                card_obj.authors.add(*card_authors)
                card_obj.save()

            # add the distributor
            if card_distributor:
                card_obj.distributor = card_distributor
                card_obj.save()

            # add many publishers
            if card_publishers:
                card_obj.publishers.add(*card_publishers)

            # add the collection
            collection = card.get("collection")
            if collection:
                collection = collection.lower()
                try:
                    collection_obj, created = Collection.objects.get_or_create(name=collection)
                    card_obj.collection = collection_obj
                    card_obj.save()
                    if created:
                        log.debug("--- new collection created: %s" % (collection,))
                except Exception as e:
                    log.error(u"--- error while adding the collection: %s" % (e,))

            # add the shelf
            shelf_id = card.get('shelf_id')
            if shelf_id and shelf_id != "0":
                try:
                    cat_obj = Shelf.objects.get(id=shelf_id)
                    card_obj.shelf = cat_obj
                    card_obj.save()
                except Exception as e:
                    log.error("error adding shelf {}: {}".format(shelf_id, e))

            # add the type of the card
            typ = "unknown"
            if card.get("card_type"):
                typ = card.get("card_type")

            try:
                type_obj = CardType.objects.get(name=typ)
            except Exception as e:
                type_obj = CardType.objects.filter(name="unknown")[0]

            card_obj.card_type = type_obj
            card_obj.save()

            # add the publishers
            pubs = card.get("publishers")
            if pubs:
                try:
                    for pub in pubs:
                        pub = pub.lower()
                        pub_obj, created = Publisher.objects.get_or_create(name=pub)
                        card_obj.publishers.add(pub_obj)
                        if created:
                            log.debug("--- new publisher created: %s" % (pub,))

                    card_obj.save()
                except Exception, e:
                    log.error(u"--- error while adding the publisher: %s" % (e,))

        # Update fields of new or existing card.
        # add the quantity of exemplaries: in "move" view.

        # # Add the default place (to the intermediate table).
        # try:
        #     default_place = Preferences.objects.all()[0].default_place
        #     place_copy, created = PlaceCopies.objects.get_or_create(card=card_obj, place=default_place)
        #     place_copy.nb = 1
        #     place_copy.save()
        # except Exception, e:
        #     log.error(u"--- error while setting the default place: %s" % (e,))

        # add the shelf
        if card_shelf:
            try:
                card_obj.shelf = card_shelf
                card_obj.save()
            except Exception as e:
                log.error(e)

        # We add a card in the stock when we buy it (add it in a place).
        in_stock = False
        if card.has_key('in_stock') and card['in_stock']:
            in_stock = card.get('in_stock')
        try:
            card_obj.in_stock = in_stock
            card_obj.save()
        except Exception as e:
            log.error('Error while setting in_stock of card {}: {}'.format(card.get('title'), e))

        card = card_obj
        if to_list:
            card = card_obj.to_dict()

        return card, [msg_success]

    def get_absolute_url(self):
        return reverse("card_show", args=(self.id,))

    def display_year_published(self):
        "We only care about the year"
        return self.year_published.strftime(u'%Y')

    def set_sortkey(self):
        "Generate a sortkey"

        if not self.sortkey and self.authors:
            self.sortkey = ', '.join([a.name for a in self.authors.all()])
            self.save()

    def is_in_deposits(self):
        return self.deposit_set.count() > 0

    def quantity_deposits(self):
        """Only the original quantity. Use a deposit.balance() for the
        accureta number.

        """
        # XXX not accurate. Dig in depositstates' nb_current
        return sum([it.nb for it in self.depositcopies_set.all()])

    def ambiguous_sell(self):
        in_deposits = self.quantity_deposits() # XXX not accurate TODO:
        log.info("quantity in deposits: {} in total: {}".format(in_deposits, self.quantity))
        return self.is_in_deposits() and (in_deposits > 0) and (self.quantity > in_deposits)

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

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return u"%s: %i exemplaries of \"%s\"" % (self.place.name, self.nb, self.card.title)

    def quantity_set(self, nb):
        """Set this card's quantity in this place to nb (int).

        (Normally, use Place.add_copy or add_copies or sell
        copies. This method is here for admin purposes only.)
        """
        try:
            self.nb = nb
            self.save()
            self.card.quantity = nb
            self.card.save()

        except Exception as e:
            log.error("Error while setting the card {}'s quantity: {}".format(self.card.id, e))

class Place (models.Model):
    """A place can be a selling point, a warehouse or a stand.
    """
    #: Name of this place
    name = models.CharField(max_length=CHAR_LENGTH)

    #: Copies: PlaceCopies

    #: Date of creation
    date_creation = models.DateField(auto_now_add=True)

    #: Date of deletion
    date_deletion = models.DateField(null=True, blank=True)

    #: Is this place a stand ?
    is_stand = models.BooleanField(default=False)

    #: Is it allowed to sell books from here ?
    can_sell = models.BooleanField(default=True)

    #: Are we doing an inventory on it right now ?
    inventory_ongoing = models.BooleanField(default=False)

    #: Optional comment
    comment = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"{}".format(self.name)

    @staticmethod
    def card_to_default_place(card_obj, nb=1):
        # Add the card to the default place (to the intermediate table).
        try:
            default_place = Preferences.objects.all()[0].default_place
            place_copy, created = PlaceCopies.objects.get_or_create(card=card_obj, place=default_place)
            place_copy.nb += nb
            place_copy.save()
        except Exception, e:
            log.error(u"--- error while setting the default place: %s" % (e,))

    def move(self, dest, card, nb):
        """Move the given card from this place to "dest" and create an history
        movement.

        - dest: Place object
        - nb: quantity (int)

        return: Boolean

        """
        try:
            pc = self.placecopies_set.filter(card__id=card.id).first()
            pc.nb = pc.nb - nb
            pc.save()
            dest_copies = dest.placecopies_set.filter(card__id=card.id).first()
            dest_copies.nb += nb
            dest_copies.save()
            mvt = history.InternalMovement(origin=self, dest=dest, card=card, nb=nb)
            mvt.save()
            return True
        except Exception as e:
            log.error(e)
            return False

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

    def add_copy(self, card, nb=1, add=True):
        """Adds the given number of copies (1 by default) of the given
        car to this place.

        - card: a card object
        - nb: the number of copies to add (optional).

        returns:
        - nothing

        """
        if not type(nb) == type(1):
            # log.warning("nb '{}' is not an int: the quantity was malformed".format(nb))
            nb = 1

        try:
            place_copy, created = self.placecopies_set.get_or_create(card=card)
            if add:
                place_copy.nb += nb
            else:
                place_copy.nb = nb
            place_copy.save()

            # Keep in sync the card's quantity field.
            card.quantity += nb
            card.save()

            # A card could be in the DB but only in a list
            # (basket). Now it's bought at least once.
            card.in_stock = True
            card.save()

        except Exception,e:
            log.error(u"Error while adding %s to the place %s" % (card.title, self.name))
            log.error(e)
            return 0

        # Add a log to the Entry history
        try:
            history.Entry.new([card])
        except Exception as e:
            log.error(u"Error while adding an Entry to the history for card {}:{}".format(card.id, e))

        return place_copy.nb

    def quantities_total(self):
        """Total quantity of cards in this place.
        Return: int (None on error)
        """
        try:
            return sum([it.nb for it in self.placecopies_set.all()])
        except Exception as e:
            log.error("Error getting the total quantities in place {}: {}".format(self.name, e))

    def quantity_of(self, card):
        """How many copies of this card do we have ?
        """
        try:
            place_copies = self.placecopies_set.filter(card__id=card.id).first()
            return place_copies.nb
        except Exception as e:
            log.error(e)
            return None

    def add_copies(self, cards):
        """Adds the given list of cards objects. A simple and uncomplete
        wrapper to "add_copy" for consistency. Use the latter instead.

        """
        for it in cards:
            self.add_copy(it)


class Preferences(models.Model):
    """
    Default preferences.
    """
    #: What place to add the cards by default ? (we register them, then move them)
    default_place = models.OneToOneField(Place)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return u"default place: %s" % (self.default_place.name,)

class BasketCopies(models.Model):
    """Copies present in a basket (intermediate table).
    """
    card = models.ForeignKey("Card")
    basket = models.ForeignKey("Basket")
    nb = models.IntegerField(default=0)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return u"Basket %s: %s copies of %s" % (self.basket.name, self.nb, self.card.title)

    def to_dict(self):
        """Card representation and its quantity in the basket.

        Return: a dict, with 'basket_qty'.
        """
        card = []
        try:
            card = self.card.to_dict()
            card['basket_qty'] = self.nb
        except Exception as e:
            log.error(e)

        return card


class Basket(models.Model):
    """A basket is a set of copies that are put in it for later use. Its
    copies can be present in the stock or not. To mix with a basket's
    copies doesn't mean mixing with physical copies of the stock.
    """
    # This class is really similar to PlaceCopies. Do something about it.
    #: Name of the basket
    name = models.CharField(max_length=CHAR_LENGTH)
    #: Short description
    descrition = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True)
    #: Type of the basket (preparation of a command, a stand, other, etc)
    basket_type = models.ForeignKey("BasketType", null=True, blank=True)
    #: Copies in it:
    copies = models.ManyToManyField(Card, through="BasketCopies", blank=True)
    # Access the intermediate table with basketcopies_set.all(), basketcopies_set.get(card=card)
    #: Comment:
    comment = models.CharField(max_length=TEXT_LENGTH, blank=True, null=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"{}".format(self.name)

    def to_dict(self):
        return {"name": self.name,
                "id": self.id,
                "length": self.copies.count(),
                "comment": self.comment,
                }

    @staticmethod
    def auto_command_nb():
        """Return the number of cards in the auto_command basket, if any.

        (the basket may not exist in tests).
        """
        try:
            return Basket.objects.get(name="auto_command").copies.count()
        except:
            return 0

    @staticmethod
    def new(name=None):
        """Create a new basket.

        - name: name (str)

        - Return: a 3-tuple with the new basket object (None if a pb occurs), along with the status and messages.
        """
        status = True
        msgs = []
        if not name:
            msg = {'level': ALERT_ERROR,
                   'message': _("Please provide the name of the new basket")}
            status = False
            return None, status, msgs.append(msg)

        try:
            b_obj = Basket.objects.create(name=name)
            b_obj.save()
            msg = {'level': ALERT_SUCCESS,
                   'message': _("New basket created")}
        except Exception as e:
            log.error("Pb when trying to create a new basket: {}".format(e))
            msgs.append({"level": ALERT_ERROR,
                         "message": _("We could not create a new basket. This is an internal error.")})
            return None, False, msgs

        msgs += msg
        return b_obj, status, msgs

    def add_copy(self, card, nb=1):
        """Adds the given card to the basket.

        If no relation already exist with the card, create one.

        nb: nb to add (1 by default)
        """
        try:
            basket_copy, created = self.basketcopies_set.get_or_create(card=card)
            basket_copy.nb += nb
            basket_copy.save()
        except Exception as e:
            log.error(u"Error while adding a card to basket %s: %s" % (self.name,e))

    def add_copies(self, card_ids):
        """Add the given list of card ids to this basket.

        card_ids: list of card ids (int)

        return: an alert dictionnary (level, message)
        """
        for id in card_ids:
            try:
                card = Card.objects.get(id=id)
                self.add_copy(card)
            except Exception as e:
                log.error(u"Error while getting card of id {}: {}".format(id, e))
                return {'level': ALERT_ERROR, 'message': "Internal error"}

        return {'level': ALERT_SUCCESS, 'message':_(u"The cards were successfully added to the basket '{}'".format(self.name))}

    def remove_copy(self, card_id):
        """Remove the given card (id) from the basket.
        """
        status = True
        msgs = []
        msg = ""
        try:
            inter_table = self.basketcopies_set.filter(card__id=card_id).get()
            inter_table.delete()
            msgs.append({"level": ALERT_SUCCESS,
                         "message":_(u"The card was successfully removed from the basket")})
        except ObjectDoesNotExist as e:
            log.error(u"Card not found when removing card {} from basket{}: {}".format(card_id, self.id, e))
            status = False
            msg = {"level": ALERT_ERROR,
                   "message": _(u"Card not found")}
        except Exception as e:
            log.error(u"Error while trying to remove card {} from basket {}: {}".format(card_id, self.id, e))
            status = False
            msg = {"level": ALERT_ERROR,
                   "message":_(u"Could not remove the card from the command basket. This is an internal error.")}

        msgs.append(msg)
        return status, msgs

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
    def add_to_auto_command(card):
        """Add the given Card object to the basket for auto commands.
        """
        try:
            Basket.objects.get(name="auto_command").add_copy(card)
        except Exception as e:
            log.error(u"Error while adding the card {} to the auto_command basket: {}.".format(card.id, e))

    def to_deposit(self, distributor=None, name=""):
        """Transform this basket to a deposit.

        Beware: the cards of have the same distributor or they'll be rejected.

        - distributor: a distributor object or id (int)
        - name: the deposit name
        - dep_type: the deposit type (see DEPOSIT_TYPES_CHOICES)

        Return: a tuple the deposit object with a list of error messages
        """
        msgs = []
        if type(distributor) == int:
            try:
                distributor = Distributor.objects.get(id=distributor)
            except ObjectDoesNotExist as e:
                log.error("Basket to deposit: the given distributor of id {} doesn't exist: {}".format(distributor, e))
                return None

        if not distributor:
            msg = "Basket to deposit: no distributor. Abort."
            log.error(msg)
            return None, [msg]

        if not name:
            msg = "Basket to deposit: no name given."
            log.error(msg)
            return None, [msg]

        dep = Deposit(name=name)
        dep.distributor = distributor
        try:
            dep.save()
            msgs = dep.add_copies(self.copies.all())
            msgs += msgs
        except Exception as e:
            log.error("Basket to deposit: error adding copies: {}".format(e))
            msgs.append(e)

        return dep, msgs


class BasketType (models.Model):
    """
    """

    name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"{}".format(self.name)

class DepositStateCopies(models.Model):
    """For each card of the deposit state, remember:

    - the number of cards,
    - its pourcentage,
    """
    class Meta:
        app_label = "search"

    card = models.ForeignKey(Card)
    deposit_state = models.ForeignKey("DepositState")
    sells = models.ManyToManyField("Sell")
    #: the current quantity of the card (at the date of the deposit state).
    nb_current = models.IntegerField(default=0)
    #: number of wanted copies.
    # nb_wanted = models.IntegerField(default=1)
    #: quantity to command to the distributor.
    # nb_to_command = models.IntegerField(default=1)
    #: quantity to return. (beware, some distributors ask a card not
    # to stay longer than a certain time in a deposit)
    nb_to_return = models.IntegerField(default=0)

    def __unicode__(self):
        return u"card {}, initial: {}, current: {}, sells: {}, etc".format(
            self.card.id, self.nb_initial, self.nb_current, self.nb_sells)

    @property
    def nb_sells(self):
        """the quantity of sold cards since the last deposit state.
        """
        return self.sells.count()

    @property
    def nb_initial(self):
        """the initial number of that card in stock: current + nb of sells
        """
        return self.nb_current + self.nb_sells

    @property
    def nb_to_command(self):
        """nb of this card to command: the quantity missing to reach the number wanted.
        """
        return self.nb_wanted - self.nb_current

    @property
    def nb_wanted(self):
        try:
            ret = self.deposit_state.deposit.depositcopies_set.filter(card__id=2)
        except Exception as e:
            log.error(e)
            return -1

        if len(ret) > 1:
            log.warning("a deposit has not a unique result for the intermediate table of a card")
        return ret[0].threshold

    def add_sells(self, sells):
        for sell in sells:
            try:
                self.sells.add(sell)
            except Exception as e:
                log.error("adding sells to {}: ".format(self.id), e)


class DepositState(models.Model):
    """Deposit states. We do a deposit state to know what cards have been
    sold since the last deposit state, so what sum do we need to pay to
    the distributor.

    We need to close alerts related to the cards of the deposit before
    to begin a deposit state.

    Once the deposit state is validated, it can't be modified any
    more.

    """

    class Meta:
        app_label = "search"

    deposit = models.ForeignKey("Deposit")
    # "created" could be inherited with TimeStampedModel but we want
    # it to be more precise (timezone.now())
    created = models.DateTimeField(blank=True, null=True)
    copies = models.ManyToManyField(Card, through="DepositStateCopies", blank=True)
    closed = models.DateTimeField(blank=True, null=True)
    # closed = models.DateField(default=None, blank=True, null=True)

    def __unicode__(self):
        ret = u"{}, deposit '{}' with {} copies. Closed ? {}".format(
            self.id, self.deposit, self.copies.count(), self.closed)
        return ret

    @property
    def ambiguous(self):
        for card in self.copies.all():
            if card.ambiguous_sell():
                return True
        return False

    @staticmethod
    def existing(deposit):
        """Get the existing deposit state of the given deposit.

        Return: a DepositState object, None if there isn't or if it isn't closed.
        """
        try:
            ex = DepositState.objects.filter(deposit=deposit).order_by("created").last()
        except Exception as e:
            log.debug(e)
            return None

        return ex

    def add_copies(self, copies, nb=1, quantities=[]):
        """Add the given list of copies objects to this deposit state.

        - copies: list of Card objects, or ids
        - quantities: list of their respective quantities (int). len(quantities) must equal len(copies).

        return: (status, msgs)

        """
        # note: use this method only at the beginning, then use add_soldcard
        msgs = []
        status = True
        try:
            for (i, copy) in enumerate(copies):
                if len(quantities) == len(copies):
                    qty = quantities[i]
                else:
                    qty = nb

                if type(copy) == type('str'):
                    copy = Card.objects.get(id=copy)

                depositstate_copy, created = self.depositstatecopies_set.get_or_create(card=copy)
                depositstate_copy.nb_current += qty
                depositstate_copy.save()

            return status, msgs

        except Exception as e:
            log.error(u"Error while adding a card to the deposit state: {}".format(e))
            msgs.append({'level': messages.ERROR,
                                'message': _("An error occured while adding a card to the deposit state.")})
            return None, msgs

    def add_soldcards(self, cards_sells):
        """Add cards to this deposit state.
        Updates the sells if the card is already registered.

        - card_sells: list of dicts to associate a card to a list of sells:
            "card": card object, "sells": list of Sell objects of this card.
        """
        if self.closed:
            log.debug("This deposit state is closed.")
            return False, [_("This deposit state is closed ! We won't update it, sorry.")]

        msgs = []
        try:
            for it in cards_sells:
                card = it.get('card')
                sells = it.get('sells')
                depostate_copy, created = self.depositstatecopies_set.get_or_create(card=card)
                if created:
                    depostate_copy.save()
                # Keep sells that are not already registered
                ids = [it.id for it in depostate_copy.sells.all()]
                to_add = filter(lambda it: it.id not in ids, sells)
                depostate_copy.add_sells(to_add)
                depostate_copy.nb_current -= len(to_add)
                depostate_copy.nb_to_return = -1 #TODO: see DepositCopies due_date
                depostate_copy.save()

        except Exception as e:
            log.error(u"adding cards to the DepositState: {}".format(e))
            return msgs.append({'level': messages.ERROR,
                                'message': _("Wooops, an error occured while adding a card to the deposit. That shouldn't happen !")})

        return True, msgs

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

    def balance(self):
        """Get the balance of all cards of the deposit.

        return: a dict.
        "cards": a dict: the card id, value: a DepositStateCopies object.
        "total": a dict with: total_price_init, total_price_sold, discount, total_to_pay, margin.
        """
        balance = {"cards": [],
                   "total": {}}
        for card in self.copies.all():
            balance["cards"].append((card, self.card_balance(card.id)))
            depostate = self.depositstatecopies_set.first()
            sells = depostate.sells.all()
            total_price_init = sum([it.total_price_init for it in sells])
            balance["total"]["total_price_init"] = total_price_init
            total_price_sold = sum([it.total_price_sold for it in sells])
            discount = self.deposit.distributor.discount
            total_to_pay = total_price_init * discount / 100 if discount else total_price_sold
            balance["total"]["total_to_pay"] = total_to_pay
            balance["total"]["discount"] = discount
            balance["total"]["total_price_sold"] = total_price_sold
            balance["total"]["margin"] = total_price_sold - total_to_pay

        return balance

    def update(self):
        """Update the cards associated and their corresponding sells.

        return: self, the updated DepositState object
        """
        sold_cards = []
        for card in self.deposit.copies.all():
            sells = Sell.search(card_id=card.id, date_min=self.created).all()
            sold_cards.append({"card": card, "sells": sells})

        self.add_soldcards(sold_cards)
        return self

    def close(self):
        """
        return: a tuple status / list of messages (str).
        """
        if not self.ambiguous:
            self.closed = timezone.now()
            self.save()
            return True, []
        else:
            return False, [_("The deposit state can not be closed. There are conflicting sells.")]

class DepositCopies(TimeStampedModel):
    """doc
    """
    class Meta:
        app_label = "search"
        # ordering = ("name",)

    card = models.ForeignKey(Card)
    deposit = models.ForeignKey("Deposit")
    #: Number of copies now present in the stock.
    nb = models.IntegerField(default=0)
    #: Minimum of copies we want to have.
    threshold = models.IntegerField(blank=True, null=True, default=1)

    def __unicode__(self):
        return u"card {}, deposit {}, nb {}".format(self.card.id,
                                                    self.deposit.id,
                                                    self.nb)

class Deposit(TimeStampedModel):
    """Deposits. The bookshop received copies (of many cards) from
    a distributor but didn't pay them yet.

    Implementation details
    ---

    When we create the deposit, we must remember the original quantity
    of each card.

    There are two important classes to work with: Deposit and
    DepositState. Each take count of variables for each Card in
    intermediate classes ("...Copies").

    To create a Deposit:
    - create the base object
    - add copies to it with deposit.add_copies
    - add sells with add_soldcards


    Sometimes we want to see the actual state of the deposit: how many
    cards did we sell, how many are there left, how much shall I pay
    the distributor ? The DepositState tracks those information. After
    an update(), we can call for a balance() (or directly
    checkout_balance() from a deposit).

    At a moment, we will freeze the deposit state. We can pay the
    distributor and carry on using the deposit and seeing balances.

    """
    name = models.CharField(unique=True, max_length=CHAR_LENGTH)
    #: the distributor (or person) we have the copies from.
    distributor = models.ForeignKey(Distributor, blank=True, null=True)
    #: the cards to include in this deposit, with their nb of copies.
    copies = models.ManyToManyField(Card, through="DepositCopies", blank=True)

    #: type of the deposit. Some people also sent their books to a
    #: library and act like a distributor.
    deposit_type = models.CharField(choices=DEPOSIT_TYPES_CHOICES,
                                    default="fix",
                                    max_length=CHAR_LENGTH)

    #: in case of a deposit for a publisher, the place (client?) who
    #: we send our cards to.
    dest_place = models.ForeignKey(Place, blank=True, null=True)
    #: due date for payment (optional)
    due_date = models.DateField(blank=True, null=True)
    #: minimal number of copies to have in stock. When not, do an action (raise an alert).
    minimal_nb_copies = models.IntegerField(blank=True, null=True, default=0,
                                        verbose_name="Nombre minimun d'exemplaires")
    #: auto-command when the minimal nb of copies is reached ?
    # (for now: add to the "to command" basket).
    auto_command = models.BooleanField(default=True, verbose_name="Automatiquement marquer les fiches à commander")


    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return u"Deposit '{}' with distributor: {} (type: {})".format(
            self.name, self.distributor, self.deposit_type)

    @property
    def last_checkout_date(self):
        obj = self.last_checkout()
        if obj:
            return obj.created

        return None

    @property
    def total_init_price(self):
        """Get the total value of the initial stock.
        """
        res = "undefined"
        try:
            res = sum([it.card.price for it in self.depositcopies_set.all()])
        except Exception as e:
            log.error(e)

        return res

    @property
    def init_qty(self):
        #XXX: qty of copies
        #XXX: use decorator to encapsulate exception.
        res = "undefined"
        try:
            res = sum([it.nb for it in self.depositcopies_set.all()])
        except Exception as e:
            log.error(e)

        return res

    def get_absolute_url(self):
        return self.id
        # return quote(self.name)

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

    @staticmethod
    def filter_copies(copies, distributor):
        """Filter out the copies that don't have this distributor.

        Return the list of copies, filtered.
        """
        MSG_CARD_DIFFERENT_DIST = dedent(u"""Attention: la notice \"%s\" n'a pas
            été ajoutée au dépôt car elle n'a pas
            le même distributeur (\"%s\" au lieu de \"%s\).""")
        filtered = []
        msgs = []
        for copy in copies:
            if copy.distributor and (copy.distributor.name == distributor):
                filtered.append(copy)
            else:
                cur_dist = copy.distributor.name if copy.distributor else _(u"none")
                msgs.append({'level': messages.WARNING,
                             'message': MSG_CARD_DIFFERENT_DIST %
                             (copy.title, cur_dist, distributor)})

        return filtered, msgs

    @staticmethod
    def next_due_dates(to_list=False, count=None):
        """What are the deposits we have to pay soon ?

        - count: number of results to return, all by default.
        - to_list: if True, return a python list of dicts, not Deposit objects

        return: a list of Deposit objects, or a list of dict.
        """
        today = datetime.date.today()
        next = Deposit.objects.filter(due_date__gt=today).order_by('due_date')

        if count:
            next = next[:count]
        else:
            next = next.all()

        if to_list:
            next = [it.to_dict() for it in next]

        return next

    def add_copies(self, copies, nb=1, quantities=[]):
        """Add the given list of copies objects to this deposit. If their
        distributors don't match, exit. If the given copies don't
        have a distributor yet, set it.

        - copies: list of Card objects or ids.
        - quantities: list of their respective quantities (int). len(quantities) must equal len(copies).

        return: []

        """
        msgs = []
        try:
            for (i, copy) in enumerate(copies):
                if type(copy) == type('str'):
                    copy = Card.objects.get(id=copy)

                if not copy.distributor:
                    # No distributor ? Ok, you receive this one.
                    copy.distributor = self.distributor
                    copy.save

                if copy.distributor and (copy.distributor.name == self.distributor.name):
                    if len(quantities) == len(copies):
                        qty = quantities[i]
                    else:
                        qty = nb
                    deposit_copy, created = self.depositcopies_set.get_or_create(card=copy)
                    if created:
                        deposit_copy.nb = qty
                        deposit_copy.save()
                    else:
                        # Update the ongoing checkout
                        checkout = self.checkout_current()
                        checkout.add_copies(copies, quantities=quantities)

                else:
                    msg = u"Error: the distributor of card \"{}\" do not match the one of the deposit: {} and {}.".\
                          format(copy.title, copy.distributor.name, self.distributor.name)
                    log.error(msg + u"We should have filtered the copies before.")
                    msgs.append(msg)

            return msgs

        except Exception as e:
            log.error(u"Error while adding a card to the deposit: {}".format(e))
            return msgs.append({'level': messages.ERROR,
                                'message': _("Wooops, an error occured while adding a card to the deposit. That shouldn't happen !")})

    def add_copy(self, card_obj, nb=1):
        """Add a card object to this deposit.
        """
        self.add_copies([card_obj], nb=nb)

    @staticmethod
    def get_from_kw(**kwargs):
        """Return a list of deposits.

        No arguments: return all.
        """
        return Deposit.objects.order_by("name")

    @staticmethod
    def from_dict(depo_dict):
        """Creates a deposit from the given dictionnary.

        Thanks to the form validation, we are sure the deposit's name is unique.

        depo_dict: dictionnary with the required Deposit
        fields. Copies and Distributor are objects.
        - copies: a list of Card objects
        - quantities: a list of their respective quantities (int)

        returns: a 2-tuple status, list of messages. The messages are dictionnaries:
            - level: STATUS_{SUCCESS, ERROR, WARNING}
            - message: string

        """
        msgs = []
        status = ALERT_SUCCESS
        dep = None
        copies = depo_dict.pop('copies')  # add the copies after deposit creation.
        copies_to_add, msgs = Deposit.filter_copies(copies, depo_dict["distributor"].name)

        # Check the cards are not already in a deposit.
        for copy in copies_to_add:
            copy_depos = copy.deposit_set.all()
            if copy_depos:
                message=_(dedent(u"""Hey ! We won't create this deposit
                because the card '{}' is already in the
                deposit '{}'""".format(
                    copy.title, copy_depos[0].name)))
                if len(copy_depos) > 1:
                    message += " (and {} others)".format(len(copy_depos) - 1)
                message += "."
                msgs.append(dict(level=messages.INFO, message=message))

                return ALERT_ERROR, msgs

        # Normal case.
        dest_place_id = None
        if depo_dict.get("dest_place"):
            dest_place_id = depo_dict.pop('dest_place')
        if depo_dict.get("auto_command") == "true":
            depo_dict["auto_command"] = True  # TODO: form validation beforehand.
        try:
            qties = depo_dict.pop('quantities', [])
            dep = Deposit.objects.create(**depo_dict)
            msgs += dep.add_copies(copies_to_add, quantities=qties)
            msgs.append({'level': "success",
                            'message':_("The deposit was successfully created.")})
        except Exception as e:
            log.error(u"Adding a Deposit from_dict error ! {}".format(e))
            return ALERT_ERROR, msgs.append({'level': "danger",
                                              'message': e})

        # Link to the destination place, if any.
        if dep and dest_place_id:
            try:
                dep.dest_place = Place.objects.get(id=dest_place_id)
                dep.save()
            except Exception as e:
                log.error(u"{}".format(e))

        return status, msgs

    def nb_alerts(self):
        """Is the distributor of this deposit concerned by open alerts ? If
        so, we can not start a deposit checkout.

        Return: integer, the number of alerts.
        """
        try:
            alerts_found = Alert.objects.filter(deposits__name=self.name).count()
        except ObjectDoesNotExist as e:
            log.error("Error looking for alerts of deposit {}: {}".format(self.name, e))
        return alerts_found

    def checkout_current(self):
        """
        return: a DepositState object.
        """
        checkout = self.last_checkout()
        if not checkout:
            checkout, msgs = self.checkout_create()

        return checkout

    def last_checkout(self):
        """Return the last checkout at which we did the last checkout of this
        deposit.

        return: a depositstate object.

        """
        try:
            last_checkout_obj = self.depositstate_set.order_by("created").last()
        except ObjectDoesNotExist as e:
            log.error("Error looking for DepositState of {}: {}".format(self.name, e))
            return None

        return last_checkout_obj

    def checkout_create(self):
        """Do a deposit checkout:
        - register it
        - record all the cards of the deposit that have been sold since the last checkout,
        - if there are alerts (ambiguous sold cards): don't close it

        Close it manually.

        return: tuple (DepositState object or None, list of messages (str))
        """

        msgs = []
        cur_depostate = DepositState.existing(self)
        if cur_depostate and not cur_depostate.closed:
            log.debug("a depositState already exists and is not closed.")
            return None, [_("Hey oh, a deposit state for this deposit already exists. \
            Please close it before opening a new one.")]

        last_checkout = self.last_checkout()

        sold_cards = [] # list of dict card, list of sell objects
        # Register the cards associated with the deposit at that time
        # and their corresponding sells.
        now = timezone.now()
        checkout = DepositState(deposit=self, created=now)
        checkout.save()
        for card in self.copies.all():
            sells = Sell.search(card_id=card.id, date_min=now).all() # few chances we sell cards between now() and now
            sold_cards.append({"card": card, "sells": sells})

        quantities = []
        if last_checkout:
            # Get the previous quantities of the cards.
            balance = last_checkout.balance()
            for card_tuple in balance['cards']:
                # card_obj = card_tuple[0]
                depostate_copy = card_tuple[1]
                nb_current = depostate_copy.nb_current
                quantities.append(nb_current)
        else:
            # Initialize the checkout with the initial values.
            dep_copies = self.depositcopies_set.all()
            for it in dep_copies:
                quantities.append(it.nb)

        status, msgs = checkout.add_copies(self.copies.all(), quantities=quantities)
        if sold_cards:
            checkout.add_soldcards(sold_cards)
        else:
            msgs.append(_("No cards were sold since the last deposit state."))

        return checkout, msgs

    def checkout_balance(self):
        """Get the balance of the ongoing checkout.

        return: depositstate.balance(), i.e. a dict.
        """
        state = self.last_checkout()
        if not state or state.closed:
            state, _ = self.checkout_create()

        return state.balance()

    def checkout_close(self):
        """Close this state of the deposit (before to pay the
        distributor).

        The following checkouts will start from this date.
        """
        state = self.last_checkout()
        closed, msg = state.close()
        state.save()
        return (closed, msg)


class SoldCards(TimeStampedModel):

    class Meta:
        app_label = "search"

    card = models.ForeignKey(Card)
    sell = models.ForeignKey("Sell")
    #: Number of this card sold:
    quantity = models.IntegerField(default=0)
    #: Initial price
    price_init = models.FloatField(default=DEFAULT_PRICE)
    #: Price sold:
    price_sold = models.FloatField(default=DEFAULT_PRICE)

    def __unicode__(self):
        ret = u"card id {}, {} sold at price {}".format(self.card.id, self.quantity, self.price_sold)
        return ret

    def to_dict(self):
        return {"card_id": self.card.id,
                "card": Card.to_dict(self.card),
                "quantity": self.quantity,
                "price_init": self.price_init,
                "price_sold": self.price_sold,
                }

class Sell(models.Model):
    """A sell represents a set of one or more cards that are sold:
    - at the same time,
    - under the same payment,
    - where the price sold can be different from the card's original price,
    - to one client.

    The fact to sell a card can raise an alert, like if we have a copy
    in a deposit and another not, we'll have to choose which copy to
    sell. This can be done later on.

    See "alerts": http://ruche.eu.org/wiki/Specifications_fonctionnelles#Alerte
    """

    class Meta:
        app_label = "search"

    created = models.DateTimeField()
    copies = models.ManyToManyField(Card, through="SoldCards", blank=True)
    payment = models.CharField(choices=PAYMENT_CHOICES, #XXX: table
                               default=PAYMENT_CHOICES[0],
                               max_length=CHAR_LENGTH,
                               blank=True, null=True)
    #: If True, this sell was already canceled. It can not be undone twice.
    canceled = models.BooleanField(default=False, blank=True)

    # alerts
    # client

    def __unicode__(self):
        return u"Sell {} of {} copies at {}.".format(self.id,
                                                     self.soldcards_set.count(),
                                                     self.created)
    @property
    def total_price_sold(self):
        total = 0
        for card in self.soldcards_set.all():
            total += card.price_sold * card.quantity
        return total

    @property
    def total_price_init(self):
        total = 0
        for card in self.soldcards_set.all():
            total += card.price_init * card.quantity
        return total

    def get_absolute_url(self):
        return reverse("sell_details", args=(self.id,))

    @staticmethod
    def search(card_id=None, date_min=None, count=False):
        """Search for the given card id in sells more recent than "date_min".

        - card_id: int. If not given, searches in all.
        - date_min: date obj
        - count: if True, only return the count() of the result, not the result list.

        return: a list of Sell objects.
        """
        sells = []
        try:
            if card_id:
                sells = Sell.objects.filter(copies__id=card_id)
            else:
                sells = Sell.objects.all()
            if date_min:
                # dates must be timezone.now() for precision.
                sells = sells.filter(created__gt=date_min)
        except Exception as e:
            log.error("search for sells of card id {}: ".format(card_id), e)
            return sells

        if count:
            return sells.count()

        return sells.all()

    @staticmethod
    def nb_card_sold_in_sells(sells, card):
        """We may have a list of sells in which one card was sold, among
        others. Now we want to know how many of this given card were sold.

        - sells: list of Sell objects
        - card: Card object

        return: int

        """
        return sum([len(se.soldcards_set.filter(card__id=card.id)) for se in sells])

    def to_list(self):
        """Return this object as a python list, ready to be serialized or
        json-ified."""
        cards_sold = [it.to_dict() for it in self.soldcards_set.all()]
        total_copies_sold = sum([it['quantity'] for it in cards_sold])
        ret = {
            "id": self.id,
            "created": self.created.strftime(DATE_FORMAT), #YYYY-mm-dd
            "cards": cards_sold,
            "total_copies_sold": total_copies_sold,
            # "payment": self.payment,
            "total_price_init": self.total_price_init,
            "total_price_sold": self.total_price_sold,
            "details_url": "/admin/search/{}/{}".format(self.__class__.__name__.lower(), self.id),
            "model": self.__class__.__name__,
            }

        return ret

    @staticmethod
    def sell_card(card, nb=1):
        """Sell a Card. Simple wrapper to Sell.sell_cards.
        """
        return Sell.sell_cards(None, cards=[card])

    @staticmethod
    def sell_cards(ids_prices_nb, date=None, payment=None, cards=[]):
        """ids_prices_nb: list of dict {"id", "price sold", "quantity" to sell}.

        The default of "price_sold" is the card's price, the default
        quantity is 1. No error is returned, only a log (it's supposed
        not to happen, to be checked before calling this method).

        - cards: can be used as a shortcut to write tests. Price and quantity will be default.
        - date: a str (from javascript) which complies to the DATE_FORMAT,
          or a timezone.datetime object.

        return: a 3-tuple (the Sell object, the global status, a list of messages).

        """
        alerts = [] # error messages
        status = ALERT_SUCCESS
        cards_obj = []
        sell = None

        TEST_DEFAULT_QUANTITY = 1
        if cards:
            ids_prices_nb = []
            for it in cards:
                ids_prices_nb.append({'id': it.id, 'price': it.price, "quantity": TEST_DEFAULT_QUANTITY})

        if not ids_prices_nb:
            log.warning(u"Sell: no cards are passed on. That shouldn't happen.")
            status = ALERT_WARNING
            return sell, status, alerts

        if not date:
            date = timezone.now()
        else:
            # create a timezone aware date
            if type(date) == type('str'):
                date = datetime.datetime.strptime(date, DATE_FORMAT)
                date = pytz.utc.localize(date, pytz.UTC)

        for it in ids_prices_nb:
            # "sell" a card.
            id = it.get("id")
            quantity = it.get("quantity", 1)
            if not id:
                log.error(u"Error: id {} shouldn't be None.".format(id))
            card = Card.objects.get(id=id)
            cards_obj.append(card)

            # Create an alert ?
            if card.ambiguous_sell():
                alert = Alert(card=card); alert.save()
                alert.add_deposits_of_card(card)
                #TODO: ajouter les messages pour la UI
                # msgs.append
                log.info(u"Alert created for card {}".format(card.title))

            try:
                Card.sell(id=id, quantity=quantity)
            except ObjectDoesNotExist:
                msg = u"Error: the card of id {} doesn't exist.".format(id)
                log.error(msg)
                alerts.append({"level": ALERT_ERROR, "message": msg})
                status = ALERT_WARNING

        # Create the Sell.
        try:
            sell = Sell(created=date, payment=payment)
            sell.save()
        except Exception as e:
            status = ALERT_ERROR
            alerts.append({"message": "Ooops, we couldn't sell anything :S",
                           "level": ALERT_ERROR})
            log.error(u"Error on creating Sell object: {}".format(e))

        # Add the cards and their attributes.
        for i, card in enumerate(cards_obj):
            price_sold = ids_prices_nb[i].get("price_sold", card.price)
            if not price_sold:
                msg = u"We can not sell the card '{}' because the price_sold wasn't set and the card's price is None.".format(card.title)
                log.error(msg)
                alerts.append({"message": msg,
                               "level": ALERT_WARNING,})
                status = ALERT_WARNING
                continue
            quantity = ids_prices_nb[i].get("quantity", 1)

            try:
                log.info(u"Selling {} copies of {} at {}.".format(quantity, card.__unicode__(), price_sold))
                sold = sell.soldcards_set.create(card=card,
                                                 price_sold=price_sold,
                                                 price_init=card.price,
                                                 quantity=quantity)
                sold.save()
            except Exception as e:
                alerts.append({"message": _(u"Warning: we couldn't sell {}.".format(card.id)),
                              "level": ALERT_WARNING})
                log.error(u"Error on adding the card {} to the sell {}: {}".format(card.id,
                                                                                   sell.id,
                                                                                   e))
                status = ALERT_ERROR

        # XXX: misleading names: alerts (messages) and Alert.
        if not alerts:
            alerts.append({"message": _(u"Sell successfull."),
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
        msgs = []
        try:
            sell = Sell.objects.get(id=sell_id)
            status, msgs = sell.undo()
        except Exception as e:
            log.error(u"Error while trying to undo sell id {}: {}".format(sell_id, e))
            msgs.append({"message": u"Error while undoing sell {}".format(sell_id), "level": ALERT_ERROR})

        return status, msgs

    def undo(self):
        """Undo:
        - add the necessary quantity to the right place
        - create a new entry, for the history.
        - we do not undo alerts here

        todo: manage the places we sell from.
        """
        if self.canceled:
            return True, {"message": u"This sell was already canceled.",
                          "level": ALERT_WARNING}

        status = True
        msgs = []
        cards = []
        for soldcard in self.soldcards_set.all():
            card_obj = soldcard.card
            cards.append(card_obj)
            qty = soldcard.quantity
            try:
                status, msgs = card_obj.sell_undo(quantity=qty, place_id=None)
            except Exception as e:
                msgs.append(u"Error while undoing sell {}.".format(self.id))
                log.error(u"Error while undoing sell {}: {}".format(self.id, e))
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
                log.error(u"Error while adding an Entry to the history for card {}:{}".format(self.id, e))
                status = False

            msgs.append({"message": _(u"Sell {} canceled with success.").format(self.id),
                         "level": ALERT_SUCCESS})
            log.debug(u"Sell {} canceled".format(self.id))

        return status, msgs

    @staticmethod
    def history(to_list=True):
        """
        """
        alerts = []
        sells = Sell.objects.order_by("-created")[:PAGE_SIZE]
        if to_list:
            sells = [it.to_list() for it in sells]
        return sells, ALERT_SUCCESS, alerts

def getHistory(to_list=False, sells_only=False):
    """return the last sells, card creations and movements.

    With pagination.

    returns: a tuple: (list of Sell or Card as dicts, status, alerts).
    """
    alerts = []
    sells = Sell.objects.order_by("-created")[:PAGE_SIZE]
    sells = [it.to_list() for it in sells]
    entries = history.Entry.objects.order_by("-created")[:PAGE_SIZE]
    entries = [it.to_list() for it in entries]
    moves = history.InternalMovement.objects.order_by("-created")[:PAGE_SIZE]
    moves = [it.to_dict() for it in moves]
    if sells_only:
        toret = entries
    else:
        toret = sells + entries + moves
    toret.sort(key= lambda it: it['created'], reverse=True)
    return toret, ALERT_SUCCESS, alerts


class Alert(models.Model):
    """An alert stores the information that a Sell is ambiguous. That
    happens when we want to sell a card and it has at least one
    exemplary in (at least) one deposit AND it also has exemplaries
    not in deposits. We need to ask the user which exemplary to sell.
    """

    class Meta:
        app_label = "search"

    card = models.ForeignKey("Card")
    deposits = models.ManyToManyField(Deposit, blank=True)
    date_creation = models.DateField(auto_now_add=True)
    date_resolution = models.DateField(null=True, blank=True)
    resolution_auto = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u"alert for card {}, created {}".format(self.card.id, self.date_creation)

    def get_absolute_url(self):
        # return reverse("sell_view", args=(self.id,))
        return "not_implemented" #TODO: view a sell

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
        msgs = []
        status = ALERT_SUCCESS
        if to_list:
            alerts = [alert.obj_to_list() for alert in alerts]
        return (alerts, status, msgs)

    def add_deposits_of_card(self, card):
        for it in card.deposit_set.all():
            self.deposits.add(it)

class InventoryCopies(models.Model):
    """The list of cards of an inventory, plus other information:
    - the quantity of them
    """

    class Meta:
        app_label = "search"

    card = models.ForeignKey(Card)
    inventory = models.ForeignKey("Inventory")
    #: How many copies of it did we find in our stock ?
    quantity = models.IntegerField(default=0)

    def __unicode__(self):
        return u"Inventory %s: %s copies of card %s, id %s" % (self.inventory.id,
                                                   self.quantity,
                                                   self.card.title,
                                                   self.card.id)

    def to_dict(self):
        return {
            "card": self.card.to_dict(),
            "quantity": self.quantity,
            }

class Inventory(TimeStampedModel):
    """An inventory can happen for a place or a shelf. Once we begin it we
    can't manipulate the stock from there. We list the copies we have in
    stock, and enter the missing ones.
    """

    class Meta:
        app_label = "search"

    #: List of cards and their quantities already "inventored".
    copies = models.ManyToManyField(Card, through="InventoryCopies", blank=True)
    #: We can do the inventory of a shelf.
    shelf = models.ForeignKey("Shelf", blank=True, null=True)
    #: we can also do the inventory of a whole place.
    place = models.ForeignKey("Place", blank=True, null=True)
    #: we can also do the inventory of publishers
    publisher = models.ForeignKey("publisher", blank=True, null=True)
    #: At last, we can also do "inventories" of baskets, meaning we compare it
    # with a newly received command, or a pack of cards returned.
    basket = models.ForeignKey("Basket", blank=True, null=True)
    #: Closed or still active ?
    closed = models.BooleanField(default=False)

    def __unicode__(self):
        inv_obj = self.shelf or self.place or self.basket or self.publisher
        return u"{}: {}".format(self.id, inv_obj.name)

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

    def to_dict(self):
        ret = {
            "id": self.id,
            "name": self.name,
            }
        return ret

    def add_copy(self, copy, nb=1, add=True):
        """copy: a Card object.

        Add the quantities only if 'add' is True (the clientside may
        ask to *set* the quantity, not add them).

        """
        if type(nb) == type("str"):
            nb = int(nb)
        try:
            inv_copies, created = self.inventorycopies_set.get_or_create(card=copy)
            if add:
                inv_copies.quantity += nb
            else:
                inv_copies.quantity = nb
            inv_copies.save()
        except Exception as e:
            log.error(e)
            return None

        return inv_copies.quantity

    def remove_card(self, card_id):
        """

        - return: status (bool)
        """
        try:
            inv_copies = self.inventorycopies_set.get(card__id=card_id)
            inv_copies.delete()

        except Exception as e:
            log.error(e)
            return False

        return True

    def progress(self):
        """Return the percentage of progress (int < 100).
        """
        done_qty = self.inventorycopies_set.count()
        orig_qty = self._orig_cards_qty()

        progress = 0
        if orig_qty:
            progress = done_qty / float(orig_qty) * 100
        elif done_qty:
            progress = 100

        return roundfloat(progress)

    def quantity(self):
        """Return the quantity of copies in it.

        - return: int
        """
        return self.inventorycopies_set.count() or 0

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

    def state(self):
        """Get the current state:
        - list of copies already inventored and their quantities,
        - list of copies not found te be searched for (and their quantities)

        """
        copies = [it.to_dict() for it in self.inventorycopies_set.all()]
        total = len(copies)
        inv_name = ""
        shelf_dict, place_dict, basket_dict, pub_dict = ({}, {}, {}, {})
        orig_cards_qty = self._orig_cards_qty()
        missing = orig_cards_qty - total
        if self.shelf:
            shelf_dict = self.shelf.to_dict()
            inv_name = self.shelf.name
        elif self.place:
            place_dict = self.place.to_dict()
            inv_name = self.place.name
        elif self.publisher:
            pub_dict = self.publisher.to_dict()
            inv_name = self.publisher.name
        elif self.basket:
            basket_dict = self.basket.to_dict()
            inv_name = self.basket.name
        else:
            log.error("Inventory of a shelf, place or basket ? We don't know. That shouldn't happen !")

        state = {
            "copies": copies,
            "inv_name": inv_name,
            "total_copies": total,
            "total_missing": missing,
            "shelf": shelf_dict,
            "place": place_dict,
            "basket": basket_dict,
            "publisher": pub_dict,
        }

        return state

    @staticmethod
    def diff_inventory(pk, **kwargs):
        try:
            obj = Inventory.objects.get(id=pk)
            return obj.diff(**kwargs)
        except Exception as e:
            log.error(u"Error getting inventory: {}".format(e))
            return None

    def diff(self, to_dict=False):
        """Diff the inventory's state with the database: get
        - which cards are
        ok,
        - which ones are missing from the inventory,
        - which are missing from the
        database,
        - which are in the database but with the wrong quantity.

        - return a tuple with the diff, the object name, total copies in the inv, total in stock.

        """
        d_stock = None
        inv_cards_set = self.inventorycopies_set.all()
        obj_name = ""
        if self.shelf:
            d_stock = self.shelf.cards_set()
            obj_name = self.shelf.name
        elif self.place:
            stock_cards_set = self.place.placecopies_set.all()
            obj_name = self.place.name
        elif self.basket:
            stock_cards_set = self.basket.basketcopies_set.all()
            obj_name = self.basket.name
        elif self.publisher:
            cards = self.publisher.card_set.all()
            d_stock = {it.id: {'card': it, 'quantity': it.quantity} for it in cards}
            obj_name = self.publisher.name
        else:
            log.error("An inventory without place nor shelf nor basket nor publisher... that shouldn't happen.")

        # Cards of the inventory:
        d_inv = {it.card.id: {'card': it.card, 'quantity': it.quantity} for it in inv_cards_set}
        # Total copies inventoried
        total_copies_in_inv = sum([it.quantity for it in inv_cards_set.all()])
        # Cards of the stock (the reference)
        if d_stock is None:
            d_stock = {it.card.id: {'card': it.card, 'quantity': it.nb} for it in stock_cards_set}
        total_copies_in_stock = sum([it['quantity'] for _, it in d_stock.iteritems()])

        # cards in stock but not in the inventory:
        in_stock = list(set(d_stock) - set(d_inv)) # list of ids
        in_stock = {it: d_stock[it] for it in in_stock}

        # cards in the inventory but not in stoc:
        in_inv = list(set(d_inv) - set(d_stock))
        in_inv = {it: d_inv[it] for it in in_inv}

        # Difference of quantities:
        # diff = quantity original - quantity found in inventory
        d_diff = {} # its quantity is: "how many the inventory has more or less compared with the stock"
        for id, val in d_inv.iteritems():
            d_diff[id] = {}
            d_diff[id]['in_orig'] = True # i.e. in place/basket of origin, we get the diff from
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
        for id, val in d_stock.iteritems():
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
            d_diff = {key: update_in(val, ['card'], lambda copy: copy.to_dict()) for key, val in d_diff.iteritems()}

        return d_diff, obj_name, total_copies_in_inv, total_copies_in_stock

    def add_pairs(self, pairs, add=False):
        """Save the given copies.

        - pairs: list of pairs (lists) with an id and its quantity
        - add: bool. If True, add the quantities. If False, just set it (client side need).

        return: tuple status, messages
        """
        status = "success"
        msgs = []
        for pair in pairs:
            if not pair:
                # beware void lists
                continue
            id, qty = pair
            try:
                card = Card.objects.get(id=id)
                self.add_copy(card, nb=int(qty), add=add)
            except Exception as e:
                log.error(e)
                msgs.append(e)
                status = "error"
                return None

            if self.shelf:
                card.shelf = self.shelf
                card.save()

        return (status, msgs)

def shelf_age_sort_key(it):
    """

    -it: a card object

    Return: a dict of lists with card objects. The keys (0,…4) represent days intervals.

    """
    it = ( timezone.now() - ( it.last_sell() or it.created ) ).days
    if it <= 91: # 3 months
        return 0
    elif it <= 182: # 6 months
        return 1
    elif it <= 365:
        return 2
    elif it <= 547: # 18 months
        return 3
    elif it <= 730: # 24 months
        return 4
    else:
        return 5

class Stats(object):

    class Meta:
        app_label = "search"

    def stock(self, to_json=False):
        """Simple figures about our stock:
        - how many cards
        - how many exemplaries
        - cost of the stock
        - idem for stock in deposits

        return: a dict by default, a json if to_json is set to True.

        Everything below needs unit tests.
        """
        type_book = CardType.objects.get(name="book")
        type_unknown = CardType.objects.get(name="unknown")
        res = {}
        res['nb_cards'] = {'label': "",
                           'value': Card.objects.count()}
        res['nb_books'] = {'label': "",
                           'value': Card.objects.filter(card_type=type_book).count()}
        res['nb_unknown'] = {'label': "",
                             'value': Card.objects.filter(card_type=type_unknown).count()}
        # the ones we bought
        # impossible atm
        res['nb_bought'] = {'label': "",
                            'value': "<soon>"}

        # Cleanlyness: nb of cards with stock <= 0
        res['nb_cards_no_stock'] = {'label': "",
                                    'value': Card.objects.filter(quantity__lte=0).count()}
        res['nb_cards_one_copy'] = {'label': "",
                                    'value': Card.objects.filter(quantity=1).count()}

        # Stock of deposits
        in_deposits = 0
        deposits_cost = 0.0
        for dep in Deposit.objects.all():
            balance = dep.checkout_balance()
            for card_tuple in balance['cards']:
                deposits_cost += card_tuple[0].price
                nb_current = card_tuple[1].nb_current
                if nb_current > 0:
                    in_deposits += nb_current

        res['in_deposits'] = {'label': "",
                              'value': in_deposits}
        # xxx: percentage cards we bought / in deposit / in both

        # Cost
        res['deposits_cost'] = {'label': "",
                                'value': deposits_cost}
        # XXX: long query ! See comments for Card.quantity
        try:
            total_cost = sum([it.price * it.quantity for it in Card.objects.all()])
            res['total_cost'] = {'label': "",
                             # Round the float... or just {:.2f}.format.
                                 'value': roundfloat(total_cost)}
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

    def best_sells_month(self, limit=10):
        """Best sells of the current month, total revenue, total nb of cards
        sold, average sell.

        """
        nb_sold_cards = 0

        # Get the sells since the beginning of this month
        now = timezone.now()
        month_beg = now - timezone.timedelta(days=now.day - 1)
        sells_obj = Sell.search(date_min=month_beg)

        # Add the quantity sold of each card.
        best_sells = {} # title -> qty
        # and count the total revenue
        revenue = 0
        for sell in sells_obj:
            soldcards = sell.soldcards_set.all()
            for soldcard in soldcards:
                title = soldcard.card.title
                qty = soldcard.quantity
                nb_sold_cards += qty
                revenue += qty * soldcard.price_sold
                if not best_sells.get("title"):
                    best_sells[title] = 0
                best_sells[title] += qty

        # Put into a list.
        res = []
        for (title, qty) in best_sells.iteritems():
            res.append({'title': title, 'quantity': qty})


        # Sort by decreasing qty
        res = sorted(res, key=lambda it: it['quantity'], reverse=True)

        # Average sell
        sell_mean = None
        if nb_sold_cards:
            sell_mean = revenue / nb_sold_cards

        to_ret = {
            "best_sells": res[:limit],
            "revenue": roundfloat(revenue),
            "nb_sold_cards": nb_sold_cards,
            "mean": roundfloat(sell_mean),
            }

        return to_ret

    def entries_month(self):
        """
        """
        now = timezone.now()
        month_beg = now - timezone.timedelta(days=now.day - 1)
        res = history.Entry.objects.filter(created__gt=month_beg)
        res = [it.to_dict() for it in res]
        nb = sum([it.entrycopies_set.count() for it in res])
        return {"cards": res,
                "total": nb}

    def _shelf_age(self, shelf_id):
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
            if not stats.has_key(key):
                stats[key] = []

        # to dict
        stats = valmap(lambda its: [it.to_dict() for it in its], stats)

        return stats

    def stock_age(self, shelf):
        return self._shelf_age(shelf)
