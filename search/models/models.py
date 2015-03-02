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

import logging
from datetime import date
from textwrap import dedent

from django.utils.http import quote
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q

CHAR_LENGTH = 200

log = logging.getLogger(__name__)

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = "search"


class Author(TimeStampedModel):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ('name',)
        app_label = "search"

    def __unicode__(self):
        return self.name


class Distributor(TimeStampedModel):
    """The entity that distributes the copies (a publisher can be a
    distributor).
    """

    name = models.CharField(max_length=CHAR_LENGTH)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return self.name

    @staticmethod
    def get_from_kw(**kwargs):
        """Return a list of deposits.

        No arguments: return all.
        """
        return Deposit.objects.order_by("name")

    @staticmethod
    def search(query=None):
        if not query:
            return Distributor.objects.all()


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

class CardType(models.Model):
    """The type of a card: a book, a CD, a t-shirt, a DVD,…
    """
    name = models.CharField(max_length=100, null=True)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return self.name


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
    sortkey = models.TextField('Authors', blank=True)
    authors = models.ManyToManyField(Author)
    price = models.CharField(null=True, max_length=20, blank=True)
    quantity = models.IntegerField(null=False, default=1)
    #: Publisher of the card:
    publishers = models.ManyToManyField(Publisher, blank=True, null=True)
    year_published = models.DateField(blank=True, null=True)
    #: Distributor:
    distributor = models.ForeignKey("Distributor", blank=True, null=True)
    #: Collection
    collection = models.ForeignKey(Collection, blank=True, null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    #: the places were we can find this card (and how many).
    places = models.ManyToManyField("Place", through="PlaceCopies", blank=True, null=True)  #TODO: allow null
    sold = models.DateField(blank=True, null=True)
    price_sold = models.CharField(null=True, max_length=20, blank=True)
    img = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: the internet source from which we got the card's informations
    data_source = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: link to the card's data source
    details_url = models.URLField(max_length=CHAR_LENGTH, null=True, blank=True)
    comment = models.TextField(blank=True)


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
        distributor = self.distributor.name if self.distributor else "aucun"
        return u'%s, %s, éditeur: %s, distributeur: %s' % (self.title, authors, publishers, distributor)

    def display_authors(self):
        if self.sortkey:
            return self.sortkey
        return u', '.join([a.name for a in self.authors.all()])

    def getAuthorsString(self):
        """returns a string with the list of authors.
        It is called from the templates so can't take any arg.
        """
        return "; ".join([aut.name for aut in self.authors.all()])

    @staticmethod
    def obj_to_list(cards):
        """Transform a list of Card objects to a python list.

        Used to save a search result in the session, which needs a
        serializable object.
        TODO: https://docs.djangoproject.com/en/1.6/topics/serialization/
        """

        retlist = []
        for card in cards:
            retlist.append({
                "title": card.title,
                "authors": ", ".join([ca.name for ca in card.authors.all()]),
                "price": card.price,
                "ean": card.ean,
                "id": card.id,
                "img": card.img,
                "get_absolute_url": card.get_absolute_url(),
                "quantity": card.quantity,
                "publishers": ", ".join([p.name.capitalize() for p in card.publishers.all()]),
                "collection": card.collection.name.capitalize() if card.collection else None,
                "details_url": card.details_url,
                "data_source": card.data_source,
                "places": ", ".join([p.name for p in card.places.all()]),
                "distributor": card.distributor.name if card.distributor else None
            })
        return retlist

    @staticmethod
    def first_cards(nb, to_list=False):
        """get the first n cards from our collection (very basic, to test)
        """
        ret = Card.objects.order_by("-created")[:nb]
        if to_list:
            ret = Card.obj_to_list(ret)
        return ret

    @staticmethod
    def search(words, card_type_id=None, distributor=None, to_list=False):
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

        if distributor and cards:
            cards = cards.filter(distributor__name__exact=distributor)

        if cards and card_type_id:
            cards = cards.filter(card_type=card_type_id)

        if to_list:
            cards = Card.obj_to_list(cards)

        return cards[:SIZE_LIMIT]

    @staticmethod
    def get_from_kw(words, to_list=False):
        """search some card: quick to test
        """
        log.debug("TODO: search the collection on all keywords")
        res = Card.objects.filter(title__icontains=words[0])
        if to_list:
            res = Card.obj_to_list(res)
        return res

    @staticmethod
    def get_from_id_list(cards_id):
        """
        cards_id: list of card ids

        returns: a list of Card objects
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
    def sell(id=None, quantity=1):
        """Sell a card. Decreases its quantity.

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
            card.sold = date.today()
            card.price_sold = card.price
            card.quantity = card.quantity - quantity
            card.save()
        except ObjectDoesNotExist, e:
            log.warning("Requested card %s does not exist: %s" % (id, e))
            return (None, "La notice n'existe pas.")

        if card.quantity <= 0:
            Basket.add_to_auto_command(card)

        return (True, "")

    @staticmethod
    def from_dict(card):
        """Add a card from a dict.

        Format of dict:
            title:      string
            year:       int or None
            authors:    list of authors names (list of str)
            location:   string
            sortkey:    string of authors in the order they appear on
                        the cover
            origkey:    (optional) original key, like an ISBN, or if
                        converting from another system
        """
        # Some books always go missing...
        # location_string = card.get('location', u'?')
        # location, _ = Location.objects.get_or_create(name=location_string)

        # Unknown years is okay
        year = card.get('year', None)
        try:
            int(year)
            year = date(year, 1, 1)
        except TypeError:
            year = None

        # Make the card
        # Get authors or create
        card_authors = []
        if "authors" in card:
            for aut in card["authors"]:
                author, created = Author.objects.get_or_create(name=aut)
                card_authors.append(author)
        else:
            log.warning("this card has no authors (ok for a CD): %s" % card['title'])

        card_obj, created = Card.objects.get_or_create(
            title=card.get('title'),
            year_published=year,
            price = card.get('price',  0),
            ean = card.get('ean'),
            img = card.get('img', ""),
            details_url = card.get('details_url'),
            data_source = card.get('data_source'),
        )

        # add the authors
        if card_authors:  # TODO: more tests !
            card_obj.authors.add(*card_authors)

        # add the quantity of exemplaries
        if not created:
            card_obj.quantity = card_obj.quantity + card.get('quantity', 1)
            card_obj.save()
        else:
            card_obj.quantity = card.get('quantity', 1)
            card_obj.save()

        # add the type of the card
        if not card.get("card_type"):
            typ = "unknown"
        else:
            typ = card.get("card_type")

        try:
            type_obj = CardType.objects.get(name=typ)
        except ObjectDoesNotExist, e:
            type_obj = CardType.objects.get(name="unknown")

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
                log.error("--- error while adding the publisher: %s" % (e,))

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
            except Exception, e:
                log.error("--- error while adding the collection: %s" % (e,))

        # Add the default place (to the intermediate table).
        # try:
        #     default_place = Preferences.objects.all()[0].default_place
        #     place_copy, created = PlaceCopies.objects.get_or_create(card=card_obj, place=default_place)
        #     place_copy.nb = 1
        #     place_copy.save()
        # except Exception, e:
        #     log.error("--- error while setting the default place: %s" % (e,))

        return card_obj

    def get_absolute_url(self):
        return "/admin/search/card/{}".format(self.id)

    def display_year_published(self):
        "We only care about the year"
        return self.year_published.strftime(u'%Y')

    def set_sortkey(self):
        "Generate a sortkey"

        if not self.sortkey and self.authors:
            self.sortkey = ', '.join([a.name for a in self.authors.all()])
            self.save()


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
            log.error("--- error while setting the default place: %s" % (e,))

    def add_copies(self, card, nb=1):
        """Adds the given number of copies (1 by default) of the given card to
        this place.

        - card: a card objects
        - nb: the number of copies to add (optional)

        returns:
        - nothing

        """
        try:
            place_copy = self.placecopies_set.get(card=card)
            place_copy.nb += nb
            place_copy.save()
        except Exception,e:
            log.error("--- error while adding %s to the place %s" % (card.name, self.name))
            log.error(e)

class Preferences(models.Model):
    """
    Default preferences.
    """
    #: What place to add the cards by default ? (we register them, then move them)
    default_place = models.OneToOneField(Place)

    class Meta:
        app_label = "search"

    def __unicode__(self):
        return "Place: %s" % (self.default_place.name,)

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
            log.error("Error while adding a card to basket %s: %s" % (self.name,e))

    @staticmethod
    def add_to_auto_command(card):
        """Add the given Card object to the basket for auto commands.
        """
        try:
            Basket.objects.get(name="auto_command").add_copy(card)
        except:
            log.error("Error while adding the card {} to the auto_command basket.".format(card.__unicode__))

class BasketType (models.Model):
    """
    """

    name = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)

    class Meta:
        app_label = "search"
        ordering = ("name",)

    def __unicode__(self):
        return self.name


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
    threshold = models.IntegerField(blank=True, null=True, default=0)
    #: Do we have a limit of time to pay ?
    due_date = models.DateField(blank=True, null=True)

DEPOSIT_TYPES_CHOICES = [
    ("Dépôt de libraire", (
        ("lib", "dépôt de libraire"),
        ("fix", "dépôt fixe"),
      )),
    ("Dépôt de distributeur", (
        ("dist", "dépôt de distributeur"),
    )),
    ]

class Deposit(TimeStampedModel):
    """Deposits. The bookshop received copies (from different cards) from
    a distributor but didn't pay them yet.
    """
    name = models.CharField(primary_key=True, max_length=CHAR_LENGTH)
    #: the distributor (or person) we have the copies from.
    distributor = models.ForeignKey(Distributor, blank=True, null=True)
    #: the cards to include in this deposit, with their nb of copies.
    copies = models.ManyToManyField(Card, through="DepositCopies", blank=True, null=True)

    #: type of the deposit. Some people also sent their books to a
    #: library and act like a distributor.
    deposit_type = models.CharField(choices=DEPOSIT_TYPES_CHOICES,
                                    default=DEPOSIT_TYPES_CHOICES[0],
                                    max_length=CHAR_LENGTH)

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
        return u"Deposit '%s' with distributor: %s" % (self.name, self.distributor)

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

    def get_absolute_url(self):
        return quote(self.name)

    def add_copies(self, copies):
        "Add the given list of copies objects to this deposit."
        msgs = []
        try:
            for copy in copies:
                if copy.distributor and (copy.distributor.name == self.distributor.name):
                    deposit_copy = self.depositcopies_set.create(card=copy)
                    deposit_copy.save()
                else:
                    log.error("Error: we should have filtered the copies before.")
            return []

        except Exception as e:
            log.error("Error while adding a card to the deposit.", e)
            return msgs.append({'level': messages.ERROR,
                                'message': e})  # don't add this error in prod.

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
        copies = depo_dict.pop('copies')  # add the copies after deposit creation.
        copies_to_add, msgs = Deposit.filter_copies(copies, depo_dict["distributor"].name)
        # Don't create it if it has no valid copies.
        if not copies_to_add:
            msgs.append({'level': "warning",
                         'message': u"Le dépôt n'a pas été créé. Il doit contenir au moins une notice valide."})
        else:
            if depo_dict.get("auto_command") == "true":
                depo_dict["auto_command"] = True  # TODO: form validation beforehand.
            try:
                dep = Deposit.objects.create(**depo_dict)
                msgs += dep.add_copies(copies_to_add)
                msgs.append({'level': "success",
                             'message':"Le dépôt a été créé avec succès."})
            except Exception as e:
                log.error("Adding a Deposit from_dict error ! {}".format(e))
                return msgs.append({'level': "danger",
                                    'message': e})

        return  msgs
