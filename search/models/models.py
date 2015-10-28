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
import operator
from datetime import date
from textwrap import dedent

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.http import quote
from django.utils.translation import ugettext as _
from search.models import history
from search.models.common import DATE_FORMAT
from search.models.common import PAYMENT_CHOICES
from search.models.common import TimeStampedModel

CHAR_LENGTH = 200
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

# Statuses for the client (understood by bootstrap).
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = "search"


class Author(TimeStampedModel):
    name = models.CharField(unique=True, max_length=200)

    class Meta:
        ordering = ('name',)
        app_label = "search"

    def __unicode__(self):
        return self.name

    @staticmethod
    def search(query):
        """Search for names containing "query", return a python list.
        """
        try:
            data = Author.objects.filter(name__icontains=query)
        except Exception as e:
            log.error("Author.search error: {}".format(e))
            data = [
                {"alerts": {"level": STATUS_ERROR,
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

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return self.name

    def to_list(self):
        return {
            "id": self.id,
            "name": self.name,
            "discount": self.discount,
            "stars": self.stars,
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
        return self.name

    @staticmethod
    def search(query):
        try:
            data = Publisher.objects.filter(name__icontains=query)
        except Exception as e:
            log.error("Publisher.search error: {}".format(e))
            data = [
                {"alerts": {"level": STATUS_ERROR,
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
        return self.name

class Category(models.Model):
    """Categories:

    - ...

    For now, a Card has only one category.
    """
    class Meta:
        app_label = "search"

    #: Name of the category
    name = models.CharField(max_length=CHAR_LENGTH)

    def __unicode__(self):
        #idea: show the nb of cards with that category.
        return "{}".format(self.name)


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
        if query == "":
            log.info("CardType: we return everything")
            return CardType.objects.all()

        try:
            data = CardType.objects.filter(name__icontains=query)
        except Exception as e:
            log.error("CardType.search error: {}".format(e))
            data = [
                {"alerts": {"level": STATUS_ERROR,
                            "message": "error while searching for authors"}}
            ]

        return data


class Card(TimeStampedModel):
    """A Card represents a book, a CD, a t-shirt, etc. This isn't the
    physical object.
    """

    title = models.CharField(max_length=CHAR_LENGTH)
    #: type of the card, if specified (book, CD, tshirt, …)
    card_type = models.ForeignKey(CardType, blank=True, null=True)
    #: ean/isbn (mandatory)
    ean = models.CharField(max_length=99, null=True, blank=True)
    isbn = models.CharField(max_length=99, null=True, blank=True)
    #: Maybe this card doesn't have an isbn. It's good to know it isn't missing.
    has_isbn = models.NullBooleanField(default=True, blank=True, null=True)
    sortkey = models.TextField('Authors', blank=True)
    authors = models.ManyToManyField(Author)
    price = models.FloatField(null=True, blank=True)
    #: price_sold is only used to generate an angular form, it is not
    #: stored here in the db.
    price_sold = models.FloatField(null=True, blank=True)
    # quantity: a property, accessible like a field. The sum of quantities in each place.
    #: Publisher of the card:
    publishers = models.ManyToManyField(Publisher, blank=True, null=True)
    year_published = models.DateField(blank=True, null=True)
    #: Distributor:
    distributor = models.ForeignKey("Distributor", blank=True, null=True)
    #: Collection
    collection = models.ForeignKey(Collection, blank=True, null=True)
    #: Category (for now, only one category).
    category = models.ForeignKey(Category, blank=True, null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    #: the places were we can find this card (and how many).
    places = models.ManyToManyField("Place", through="PlaceCopies", blank=True, null=True)  #TODO: allow null
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
        distributor = self.distributor.name if self.distributor else _("aucun")
        return u"{}:{}, {}, editor: {}, distributor: {}".format(self.id, self.title, authors, publishers, distributor)

    def display_authors(self):
        return u', '.join([a.name for a in self.authors.all()])

    def getAuthorsString(self):
        """returns a string with the list of authors.
        It is called from the templates so can't take any arg.
        """
        return "; ".join([aut.name for aut in self.authors.all()])

    @property
    def quantity(self):
        quantity = 0
        if self.placecopies_set.count():
            quantity = sum([pl.nb for pl in self.placecopies_set.all()])
        return quantity

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

    def to_list(self):
        authors = self.authors.all()
        # comply to JS format (needs harmonization!)
        auth = [{"fields": {'name': it.name}} for it in authors]
        authors_repr = ", ".join(it.name for it in authors)
        publishers = self.publishers.all()
        pubs = [{'fields': {'name': it.name}} for it in publishers]
        pubs_repr = ", ".join(it.name for it in publishers)

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
            "ean": self.ean,
            "get_absolute_url": get_absolute_url,
            "img": self.img,
            "isbn": self.isbn if self.isbn else self.ean,
            "model": self.__class__.__name__, # useful to sort history.
            "places": ", ".join([p.name for p in self.places.all()]),
            "price": self.price,
            "price_sold": self.price_sold,
            # "publishers": ", ".join([p.name.capitalize() for p in self.publishers.all()]),
            "publishers": pubs,
            "pubs_repr": pubs_repr,
            "quantity": self.quantity,
            "title": self.title,
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
    def search(words, card_type_id=None, distributor=None, to_list=False,
               publisher_id=None, place_id=None, category_id=None):
        """Search a card on its title and its authors' names.

        SIZE_LIMIT = 100

        words: (list of strings) a list of key words

        card_type_id: id referencing to CardType

        to_list: if True, we return a list of dicts, not Card
        objects. Used to store the search result into the session,
        which doesn't know how to store Card objects.

        returns: a list of objects or a list of dicts if to_list is
        specified.
        """
        SIZE_LIMIT = 100 #TODO: pagination
        if words:
            # Doesn't pass data validation of the view.
            head = words[0]
            cards = Card.objects.filter(Q(title__icontains=head) |
                                         Q(authors__name__icontains=head))
            if len(words) > 1:
                for elt in words[1:]:
                    cards = cards.filter(Q(title__icontains=elt)|
                                         Q(authors__name__icontains=elt))
        else:
            cards = Card.objects.all()  # returns a QuerySets, which are lazy.

        if cards and category_id:
            try:
                cards = cards.filter(category=category_id)
            except Exception as e:
                log.error(e)

        if cards and place_id:
            try:
                cards = cards.filter(placecopies__place__id=place_id)
            except Exception as e:
                log.error(e)

        if distributor and cards:
            cards = cards.filter(distributor__name__exact=distributor)

        if cards and card_type_id:
            cards = cards.filter(card_type=card_type_id)

        if cards and publisher_id:
            try:
                pub = Publisher.objects.get(id=publisher_id)
                cards = cards.filter(publishers=pub)
            except Exception as e:
                log.error("we won't search for a publisher that doesn't exist: {}".format(e))

        if to_list:
            cards = Card.obj_to_list(cards)

        return cards[:SIZE_LIMIT]

    @staticmethod
    def get_from_id_list(cards_id):
        """cards_id: list of card ids

        returns: a dictionnary "messages", "results" with a list of
        error messages and the list of Card object.
        """
        res = {"result": [],
               "messages": []}
        for id in cards_id:
            try:
                card = Card.objects.get(id=id)
                res["result"].append(card)
            except ObjectDoesNotExist:
                msg = "the card of id {} doesn't exist.".format(id)
                log.debug(msg)
                res["messages"].append({"level": messages.WARNING, "message": msg})
        return res

    @staticmethod
    def sell(id=None, quantity=1, place_id=None):
        """Sell a card. Decreases its quantity in the given place.

        Warning: this is a static method, use it like this:
        >>> import models.Card; Card.sell(the_card_id)

        :param int id: the id of the card to sell.
        return: a tuple (return_code, "message")
        """
        # Why use a static method ? Because from the view, we get
        # back an id and not a Card object. Why ? Because we want to
        # store list of cards into the session, and we can't serialize
        # Card objects as is, so we use lits of dicts (but we may use
        # django serialization instead).
        try:
            card = Card.objects.get(id=id)

            # Get the place from where we sell it.
            if place_id:
                place_obj = card.placecopies_set.get(id=place_id)
            else:
                if card.placecopies_set.count():
                    # XXX: get the default place
                    log.warning("selling: select the place: to finish")
                    place_obj = card.placecopies_set.first()
                else:
                    return False, "We can not sell card {}: it is not associated with any place.".format(card.title)

            place_obj.nb = place_obj.nb - quantity
            place_obj.save()
            # card.quantity = card.quantity - quantity
            # card.save()
        except ObjectDoesNotExist as e:
            log.warning(u"Requested card %s does not exist: %s" % (id, e))
            return (None, "La notice n'existe pas.")
        except Exception as e:
            log.error(u"Error selling a card: {}.".format(e))

        if card.quantity <= 0:
            Basket.add_to_auto_command(card)

        return (True, "")

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
            if card_dict.get('isbn'):
                clist = Card.objects.filter(isbn=card_dict.get('isbn'))
            elif card_dict.get('ean'):
                clist = Card.objects.filter(ean=card_dict.get('ean'))
            if clist:
                return clist, msgs

        # Get the title.
        if not card_dict.get('title'):
            return None, ["Error: this card has no title."]
        clist = Card.objects.filter(title=card_dict.get('title'))
        if clist:
            for obj in clist:
                if card_dict.get('publishers'):
                    set_obj = set([it.name for it in obj.publishers.all()])
                    set_dict = set(card_dict.get('publishers'))
                    if not set_obj == set_dict:
                        msgs.append("A card with isbn exists, but it has a different publisher")
                        return None, msgs

                if card_dict.get('authors'):
                    set_obj = set([it.name for it in obj.authors.all()])
                    set_dict = set(card_dict.get('authors'))
                    if not set_obj == set_dict:
                        msgs.append("A card with same isbn exists, but it has different authors.")
                        return None, msgs

            # What to do about not uniq result ?
            return clist, msgs

        return None, msgs

    @staticmethod
    def from_dict(card):
        """Add a card from a dict.

        Format of dict:
            title:      string
            year:       int or None
            authors:    list of authors names (list of str) or list of Author objects.
            category:   id (int)
            distributor: id of a Distributor
            publishers: list of names of publishers (create one on the fly, like with webscraping)
            publishers_ids: list of ids of publishers
            has_isbn:   boolean
            isbn:       int
            details_url: url (string)
            card_type:  name of the type (string)
            location:   string
            sortkey:    string of authors in the order they appear on
                        the cover
            origkey:    (optional) original key, like an ISBN, or if
                        converting from another system


        return: a tuple Card objec created or existing, message (str).
        """
        # Some books always go missing...
        # location_string = card.get('location', u'?')
        # location, _ = Location.objects.get_or_create(name=location_string)

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
            if type(card["authors"][0]) in [type("string"), type(u"unicode-str")]:
                for aut in card["authors"]:
                    author, created = Author.objects.get_or_create(name=aut)
                    card_authors.append(author)
            else:
                # We already have objects.
                card_authors = card["authors"]
        else:
            log.warning(u"this card has no authors (ok for a CD): %s" % card.get('title'))

        # Get the distributor:
        card_distributor=None
        if card.get("distributor"):
            try:
                card_distributor = Distributor.objects.get(id=card.get("distributor"))
            except Exception as e:
                log.warning("couldn't get distributor {}. This is not necessarily a bug.".format(card.get('distributor')))

        # Get the publishers:
        card_publishers = []
        if card.get("publishers_ids"):
            card_publishers = [Publisher.objects.get(id=it) for it in card.get("publishers_ids")]

        exists_list, _msgs = Card.exists(card)
        created = False
        if exists_list:
            if len(exists_list) > 1:
                log.warning("checking existence: found {} many similar cards of title {}.".format(len(exists_list), card.get('title')))

            card_obj = exists_list[0]

            # Update fields, except isbn (as with "else" below)
            card_obj.distributor = card_distributor
            card_obj.save()

        else:
            # Create the card with its simple fields.
            # Add the relationships afterwards.
            card_obj, created = Card.objects.get_or_create(
                title=card.get('title'),
                year_published=year,
                price = card.get('price',  0),
                price_sold = card.get('price_sold',  0),
                ean = card.get('ean') or card.get('isbn'),
                isbn = card.get('isbn'),
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

            # add the category
            category = card.get('category')
            if category and category != "0":
                try:
                    cat_obj = Category.objects.get(id=category)
                    card_obj.category = cat_obj
                    card_obj.save()
                except Exception as e:
                    log.error(e)

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

        return card_obj, [msg_success]

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
        #TODO: sum()
        return reduce(operator.add, [it.nb for it in self.depositcopies_set.all()], 0)

    def ambiguous_sell(self):
        in_deposits = self.quantity_deposits()
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
        return "%s: %i exemplaries of \"%s\"" % (self.place.name, self.nb, self.card.title)


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
        return self.name

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

    def add_copy(self, card, nb=1):
        """Adds the given number of copies (1 by default) of the given card to
        this place.

        - card: a card object
        - nb: the number of copies to add (optional)

        returns:
        - nothing

        """
        try:
            place_copy, created = self.placecopies_set.get_or_create(card=card)
            place_copy.nb += nb
            place_copy.save()

            # Add a log to the Entry history
            history.Entry.new([card])

            return place_copy.nb
        except Exception,e:
            log.error(u"Error while adding %s to the place %s" % (card.title, self.name))
            log.error(e)

    def quantity_of(self, card):
        """How many copies of this card do we have ?
        """
        try:
            place_copies = self.placecopies_set.filter(card__id=card.id).first()
            return place_copies.nb
        except Exception as e:
            log.error(e)
            return None


class Preferences(models.Model):
    """
    Default preferences.
    """
    #: What place to add the cards by default ? (we register them, then move them)
    default_place = models.OneToOneField(Place)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return "default place: %s" % (self.default_place.name,)

class BasketCopies(models.Model):
    """Copies present in a basket (intermediate table).
    """
    card = models.ForeignKey("Card")
    basket = models.ForeignKey("Basket")
    nb = models.IntegerField(default=0)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return "Basket %s: %s copies of %s" % (self.basket.name, self.nb, self.card.title)

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
    copies = models.ManyToManyField(Card, through="BasketCopies", blank=True, null=True)
    # Access the intermediate table with basketcopies_set.all(), basketcopies_set.get(card=card)
    #: Comment:
    comment = models.CharField(max_length=CHAR_LENGTH, blank=True, null=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return self.name

    def to_dict(self):
        return {"name": self.name,
                "id": self.id,
                "length": self.copies.count(),
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

    @staticmethod
    def add_to_auto_command(card):
        """Add the given Card object to the basket for auto commands.
        """
        try:
            Basket.objects.get(name="auto_command").add_copy(card)
        except Exception as e:
            log.error(u"Error while adding the card {} to the auto_command basket: {}.".format(card.id, e))

class BasketType (models.Model):
    """
    """

    name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return self.name

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
    nb_current = models.IntegerField(default=1)
    #: number of wanted copies.
    # nb_wanted = models.IntegerField(default=1)
    #: quantity to command to the distributor.
    # nb_to_command = models.IntegerField(default=1)
    #: quantity to return. (beware, some distributors ask a card not
    # to stay longer than a certain time in a deposit)
    nb_to_return = models.IntegerField(default=1)

    def __unicode__(self):
        return "card {}, initial: {}, current: {}, sells: {}, etc".format(
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
    # it to be more precise (datetime.datetime.now())
    created = models.DateTimeField(blank=True, null=True)
    copies = models.ManyToManyField(Card, through="DepositStateCopies", blank=True, null=True)
    closed = models.DateField(default=None, blank=True, null=True)

    def __unicode__(self):
        ret = "deposit '{}' with {} copies. Closed ? {}".format(self.deposit, self.copies.count(), self.closed)
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

    def add_copies(self, cards_sells):
        """Add cards to this deposit state.
        Updates the sells if the card is already registered.

        - cards_sells: list of dict: "card": card object, "sells": list of Sell objects of this card.
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
                depostate_copy.add_sells(sells)
                depostate_copy.nb_current = card.quantity
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
        """
        sold_cards = []
        for card in self.deposit.copies.all():
            sells = Sell.search(card_id=card.id, date_min=self.created).all()
            sold_cards.append({"card": card, "sells": sells})

        self.add_copies(sold_cards)

    def close(self):
        """
        return: a tuple status / list of messages (str).
        """
        if not self.ambiguous:
            self.closed = datetime.datetime.now()
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
    nb = models.IntegerField(default=1)
    #: Minimum of copies we want to have.
    threshold = models.IntegerField(blank=True, null=True, default=1)

class Deposit(TimeStampedModel):
    """Deposits. The bookshop received copies (from different cards) from
    a distributor but didn't pay them yet.
    """
    name = models.CharField(unique=True, max_length=CHAR_LENGTH)
    #: the distributor (or person) we have the copies from.
    distributor = models.ForeignKey(Distributor, blank=True, null=True)
    #: the cards to include in this deposit, with their nb of copies.
    copies = models.ManyToManyField(Card, through="DepositCopies", blank=True, null=True)

    #: type of the deposit. Some people also sent their books to a
    #: library and act like a distributor.
    deposit_type = models.CharField(choices=DEPOSIT_TYPES_CHOICES,
                                    default=DEPOSIT_TYPES_CHOICES[0],
                                    max_length=CHAR_LENGTH)

    #: in case of a deposit for a publisher, the place (client?) who
    #: we send our cards to.
    dest_place = models.ForeignKey(Place, blank=True, null=True)
    #: due date for payment (optional)
    due_date = models.DateField(blank=True, null=True)
    #: initial number of all cards for that deposit (create another deposit if you need it).
    initial_nb_copies = models.IntegerField(blank=True, null=True, default=0,
                                            verbose_name="Nombre initial d'exemplaires pour ce dépôt:")

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
        ret = {
            "name": self.name,
            "distributor": self.distributor.name if self.distributor else "",
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
                cur_dist = copy.distributor.name if copy.distributor else "aucun"
                msgs.append({'level': messages.WARNING,
                             'message': MSG_CARD_DIFFERENT_DIST %
                             (copy.title, cur_dist, distributor)})

        return filtered, msgs

    def add_copies(self, copies, nb=1):
        """Add the given list of copies objects to this deposit (if their
        distributor matches).

        copies: list of Card objects.

        return: []

        """
        msgs = []
        try:
            for copy in copies:
                if copy.distributor and (copy.distributor.name == self.distributor.name):
                    deposit_copy = self.depositcopies_set.create(card=copy, nb=nb)
                    deposit_copy.save()
                else:
                    log.error(dedent(u"""Error: the distributor names do not match.
                    We should have filtered the copies before."""))
            return []

        except Exception as e:
            log.error(u"Error while adding a card to the deposit: {}".format(e))
            return msgs.append({'level': messages.ERROR,
                                'message': _("Wooops, an error occured while adding a card to the deposit. That shouldn't happen !")})

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

        returns: a list of messages which are dictionnaries:
        level: success/danger/warning (angular-bootstrap labels),
        message: string

        """
        msgs = []
        dep = None
        copies = depo_dict.pop('copies')  # add the copies after deposit creation.
        copies_to_add, msgs = Deposit.filter_copies(copies, depo_dict["distributor"].name)
        # Don't create it if it has no valid copies.
        if not copies_to_add:
            msgs.append({'level': messages.WARNING,
                         'message': _(u"The deposit wasn't created. It must contain at least one valid card")})
        else:
            dest_place_id = None
            if depo_dict.get("dest_place"):
                dest_place_id = depo_dict.pop('dest_place')
            if depo_dict.get("auto_command") == "true":
                depo_dict["auto_command"] = True  # TODO: form validation beforehand.
            try:
                dep = Deposit.objects.create(**depo_dict)
                msgs += dep.add_copies(copies_to_add)
                msgs.append({'level': "success",
                             'message':_("The deposit was successfully created.")})
            except Exception as e:
                log.error(u"Adding a Deposit from_dict error ! {}".format(e))
                return msgs.append({'level': "danger",
                                    'message': e})

            # Link to the destination place, if any.
            if dep and dest_place_id:
                try:
                    dep.dest_place = Place.objects.get(id=dest_place_id)
                    dep.save()
                except Exception as e:
                    log.error(u"{}".format(e))

        return  msgs

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

    def last_checkout(self):
        """Return the date at which we did the last checkout of this
        deposit."""
        # TODO to test
        try:
            last_checkout_obj = DepositState.objects.filter(deposit__name=self.name).order_by("created").last()
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
        if not self.copies.count():
            log.debug("this deposit has no cards.")
            return None, [_("this deposit has no cards. Impossible to do a checkout.")]

        msgs = []
        existing = DepositState.existing(self)
        if existing and not existing.closed:
            log.debug("a depositState already exists and is not closed.")
            return None, [_("Hey oh, a deposit state for this deposit already exists. \
            Please close it before opening a new one.")]

        last_checkout = self.last_checkout()
        if last_checkout:
            last_checkout_date = last_checkout.created
        else:
            last_checkout_date = self.created

        sold_cards = [] # list of dict card, list of sell objects
        # Register the cards associated with the deposit at that time
        # and their corresponding sells.
        for card in self.copies.all():
            sells = Sell.search(card_id=card.id, date_min=last_checkout_date).all()
            sold_cards.append({"card": card, "sells": sells})

        checkout = DepositState(deposit=self, created=datetime.datetime.now())
        checkout.save()
        if sold_cards:
            checkout.add_copies(sold_cards)
        else:
            msgs.append(_("No cards were sold since the last deposit state."))

        return checkout, msgs

class SoldCards(models.Model):

    class Meta:
        app_label = "search"

    card = models.ForeignKey(Card)
    sell = models.ForeignKey("Sell")
    #: Number of this card sold:
    quantity = models.IntegerField(default=1)
    #: Initial price
    price_init = models.FloatField(default=DEFAULT_PRICE)
    #: Price sold:
    price_sold = models.FloatField(default=DEFAULT_PRICE)

    def __unicode__(self):
        ret = "card id {}, {} sold at price {}".format(self.card.id, self.quantity, self.price_sold)
        return ret

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
    copies = models.ManyToManyField(Card, through="SoldCards", blank=True, null=True)
    payment = models.CharField(choices=PAYMENT_CHOICES, #XXX: table
                               default=PAYMENT_CHOICES[0],
                               max_length=CHAR_LENGTH,
                               blank=True, null=True)
    # alerts
    # client

    def __unicode__(self):
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
    def total_price_init(self):
        total = 0
        for card in self.soldcards_set.all():
            total += card.price_init * card.quantity
        return total

    def get_absolute_url(self):
        return reverse("sell_details", args=(self.id,))

    @staticmethod
    def search(card_id=None, date_min=None):
        """Search for the given card id in sells more recent than "date_min".

        - card_id: int
        - date_min: date obj

        return: a list of Sell objects.
        """
        sells = []
        try:
            sells = Sell.objects.filter(copies__id=card_id)
            if date_min:
                # dates must be datetime.datetime.now() for precision.
                sells = sells.filter(created__gt=date_min)
        except Exception as e:
            log.error("search for sells of card id {}: ".format(card_id), e)

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
        cards = map(lambda it: Card.obj_to_list([it.card])[0],
                  self.soldcards_set.all())
        ret = {
            "id": self.id,
            "created": self.created.strftime(DATE_FORMAT), #YYYY-mm-dd
            "cards": cards,
            # "payment": self.payment,
            "total_price_init": self.total_price_init,
            "total_price_sold": self.total_price_sold,
            "details_url": "/admin/search/{}/{}".format(self.__class__.__name__.lower(), self.id),
            "model": self.__class__.__name__,
            }

        return ret

    @staticmethod
    def sell_cards(ids_prices_nb, date=None, payment=None, cards=[]):
        """ids_prices_nb: list of dict {"id", "price sold", "quantity" to sell}.

        The default of "price_sold" is the card's price, the default
        quantity is 1. No error is returned, only a log (it's supposed
        not to happen, to be checked before calling this method).

        - cards: can be used as a shortcut to write tests. Price and quantity will be default.

        return: a 3-tuple (the Sell object, the global status, a list of messages).

        """
        alerts = [] # error messages
        status = STATUS_SUCCESS
        cards_obj = []
        sell = None

        TEST_DEFAULT_QUANTITY = 1
        if cards:
            ids_prices_nb = []
            for it in cards:
                ids_prices_nb.append({'id': it.id, 'price': it.price, "quantity": TEST_DEFAULT_QUANTITY})

        if not ids_prices_nb:
            log.warning(u"Sell: no cards are passed on. That shouldn't happen.")
            status = STATUS_WARNING
            return sell, status, alerts

        if not date:
            date = datetime.datetime.now()

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
                log.info("Alert created for card {}".format(card.title))

            try:
                Card.sell(id, quantity=quantity)
            except ObjectDoesNotExist:
                msg = "Error: the card of id {} doesn't exist.".format(id)
                log.error(msg)
                alerts.append({"level": STATUS_ERROR, "message": msg})
                status = STATUS_WARNING

        # Create the Sell.
        try:
            sell = Sell(created=date, payment=payment)
            sell.save()
        except Exception as e:
            status = STATUS_ERROR
            alerts.append({"message": "Ooops, we couldn't sell anything :S",
                           "level": STATUS_ERROR})
            log.error(u"Error on creating Sell object: {}".format(e))

        # Add the cards and their attributes.
        for i, card in enumerate(cards_obj):
            price_sold = ids_prices_nb[i].get("price_sold", card.price)
            if not price_sold:
                log.error(u"Error: the price_sold of card {} wasn't set and the card's price is None.".format(card.__unicode__()))
                status = STATUS_WARNING
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
                alerts.append({"message": _("Warning: we couldn't sell {}.".format(card.id)),
                              "level": STATUS_WARNING})
                log.error(u"Error on adding the card {} to the sell {}: {}".format(card.__unicode__(),
                                                                                   sell.id,
                                                                                   e))
                status = STATUS_ERROR

        # XXX: misleading names: alerts (messages) and Alert.
        if not alerts:
            alerts.append({"message": _(u"Sell successfull."),
                           "level": STATUS_SUCCESS})

        return (sell, status, alerts)

    def get_soldcard(self, card_id):
        """Get informations about this card that was sold: how many, how much etc.
        """
        if not card_id:
            return None

        return self.soldcards_set.filter(card__id=card_id)


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
    return toret, STATUS_SUCCESS, alerts


class Alert(models.Model):
    """An alert stores the information that a Sell is ambiguous. That
    happens when we want to sell a card and it has at least one
    exemplary in (at least) one deposit AND it also has exemplaries
    not in deposits. We need to ask the user which exemplary to sell.
    """

    class Meta:
        app_label = "search"

    card = models.ForeignKey("Card")
    deposits = models.ManyToManyField(Deposit, blank=True, null=True)
    date_creation = models.DateField(auto_now_add=True)
    date_resolution = models.DateField(null=True, blank=True)
    resolution_auto = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return "alert for card {}, created {}".format(self.card.id, self.date_creation)

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
        msgs = []
        status = STATUS_SUCCESS
        if to_list:
            alerts = [alert.obj_to_list() for alert in alerts]
        return (alerts, status, msgs)

    def add_deposits_of_card(self, card):
        for it in card.deposit_set.all():
            self.deposits.add(it)

class InventoryCards(models.Model):
    """The list of cards of an inventory, plus other information:
    - the quantity of them
    """
    card = models.ForeignKey(Card)
    inventory = models.ForeignKey("Inventory")
    #: How many copies of it did we find in our stock ?
    quantity = models.IntegerField(default=0)

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
    copies = models.ManyToManyField(Card, through="InventoryCards", blank=True, null=True)
    #: Place we are doing the inventory in.
    place = models.ForeignKey("Place", blank=True, null=True)

    def add_copy(self, copy, nb=1, add=True):
        """copy: a Card object.

        Add the quantities only if 'add' is True (the clientside may
        ask to *set* the quantity, not add them).

        """
        if type(nb) == type("str"):
            nb = int(nb)
        try:
            inv_copies, created = self.inventorycards_set.get_or_create(card=copy)
            if add:
                inv_copies.quantity += nb
            else:
                inv_copies.quantity = nb
            inv_copies.save()
        except Exception as e:
            log.error(e)
            return None

        return inv_copies.quantity

    def state(self):
        """Get the current state:
        - list of copies already inventored and their quantities,
        - list of copies not found te be searched for (and their quantities)

        """
        copies = [it.to_dict() for it in self.inventorycards_set.all()]
        total = len(copies)
        missing = self.place.placecopies_set.count() - total
        ret = {
            "copies": copies,
            "total_copies": total,
            "total_missing": missing,
            "place": self.place.to_dict(),
        }

        return ret

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

        return (status, msgs)
