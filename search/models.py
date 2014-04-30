# -*- coding: utf-8 -*-

from datetime import date

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

CHAR_LENGTH = 200

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Author(TimeStampedModel):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

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
        ordering = ("name",)

    def __unicode__(self):
        return self.name

class CardType(models.Model):
    """The type of a card: a book, a CD, a t-shirt, a DVD,…
    """
    name = models.CharField(max_length=100, null=True)

    def __unicode__(self):
        return self.name


class Card(TimeStampedModel):
    """A Card represents a book, a CD, a t-shirt, etc. This isn't the
    physical object.
    """
    origkey = models.CharField(max_length=36, blank=True, null=True)
    title = models.CharField(max_length=CHAR_LENGTH)
    #: type of the card, if specified (book, CD, tshirt, …)
    card_type = models.ForeignKey(CardType, blank=True, null=True)
    #: ean/isbn (mandatory)
    ean = models.CharField(max_length=99, null=True)
    isbn = models.CharField(max_length=99, null=True, blank=True)
    sortkey = models.TextField('Authors', blank=True)
    authors = models.ManyToManyField(Author)
    price = models.CharField(null=True, max_length=20)
    quantity = models.IntegerField(null=False, default=1)
    #: Publisher of the card:
    publisher = models.ForeignKey(Publisher, blank=True, null=True)
    year_published = models.DateField(blank=True, null=True)
    #: Collection
    collection = models.ForeignKey(Collection, blank=True, null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    sold = models.DateField(blank=True, null=True)
    price_sold = models.CharField(null=True, max_length=20, blank=True)
    img = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: the internet source from which we got the card's informations
    data_source = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    #: link to the card's data source
    details_url = models.URLField(max_length=CHAR_LENGTH, null=True, blank=True)
    comment = models.TextField(blank=True)


    class Meta:
        ordering = ('sortkey', 'year_published', 'title')

    def __unicode__(self):
        return u'%s (%s): "%s"' % (self.title, self.authors.all(), self.ean)

    @models.permalink
    def get_absolute_url(self):
        return ('book_detail', (), {'pk': self.pk})

    def display_authors(self):
        if self.sortkey:
            return self.sortkey
        return u', '.join([a.name for a in self.authors.all()])

    def display_year_published(self):
        "We only care about the year"

        return self.year_published.strftime(u'%Y')

    def set_sortkey(self):
        "Generate a sortkey"

        if not self.sortkey and self.authors:
            self.sortkey = ', '.join([a.name for a in self.authors.all()])
            self.save()

    @staticmethod
    def first_cards(nb):
        """get the first n cards from our collection (very basic, to test)
        """
        ret = Card.objects.order_by("-created")[:nb]
        return ret

    @staticmethod
    def get_from_kw(words):
        """search some card: quick to test
        TODO:
        """
        #TODO: all key words !
        print "TODO: search on all keywords"
        return Card.objects.filter(title__contains=words[0])

    @staticmethod
    def sell(ean=None, quantity=1):
        """Sell a card. Decreases its quantity.

        return: a tuple (return_code, "message")
        """
        try:
            card = Card.objects.get(ean=ean)
            card.sold = date.today()
            card.price_sold = card.price
            card.quantity = card.quantity - quantity
            card.save()
            return (True, "")
        except ObjectDoesNotExist, e:
            print "Requested card %s does not exist: %s" % (ean, e)
            return (None, "La notice n'existe pas.")

    @staticmethod
    def from_dict(card):
        """Add a book from a dict.

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
        print "--- authors ? ", card.get('authors')
        # Get authors or create
        card_authors = []
        if "authors" in card:
            for aut in card["authors"]:
                author, created = Author.objects.get_or_create(name=aut)
                card_authors.append(author)
        else:
            print "this card has no authors (ok for a CD): %s" % (card['title'],)

        card_obj, created = Card.objects.get_or_create(
            title=card.get('title'),
            year_published=year,
            price = card.get('price',  0),
            ean = card.get('ean'),
            img = card.get('img', ""),
            quantity = card.get('quantity', 1),
            details_url = card.get('details_url'),
            data_source = card.get('data_source'),
        )

        if card_authors:  # TODO: more tests !
            card_obj.authors.add(*card_authors)

        # add the type of the card
        if not card.get("card_type"):
            card['card_type'] = "unknown"
        typ = card.get("card_type")
        if typ:
            try:
                type_obj = CardType.objects.get(name=typ)
            except ObjectDoesNotExist, e:
                type_obj = CardType.objects.get(name="unknown")

            card_obj.card_type = type_obj
            card_obj.save()

        # add the publisher
        pub = card.get("publisher")
        if pub:
            pub = pub.lower()
            try:
                publisher_obj, created = Publisher.objects.get_or_create(name=pub)  # manage case
                card_obj.publisher = publisher_obj
                card_obj.save()
                if created:
                    print "--- new publisher created: %s" % (pub,)
            except Exception, e:
                print "--- error while adding the publisher: %s" % (e,)

        # add the collection
        collection = card.get("collection")
        if collection:
            collection = collection.lower()
            try:
                collection_obj, created = Collection.objects.get_or_create(name=collection)
                card_obj.collection = collection_obj
                card_obj.save()
                if created:
                    print "--- new collection created: %s" % (collection,)
            except Exception, e:
                print "--- error while adding the collection: %s" % (e,)

        # Make a sortkey in case it is missing
        # card.set_sortkey()

        return card_obj
