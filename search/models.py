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
    title = models.TextField()
    card_type = models.ForeignKey(CardType, blank=True, null=True)
    #: type of the card, if specified (book, CD, tshirt, …)
    sortkey = models.TextField('Authors', blank=True)
    year_published = models.DateField(blank=True, null=True)
    authors = models.ManyToManyField(Author)
    # authors = models.TextField(null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    ean = models.CharField(max_length=99, null=True)
    isbn = models.CharField(max_length=99, null=True, blank=True)
    img = models.CharField(max_length=CHAR_LENGTH, null=True, blank=True)
    comment = models.TextField(blank=True)
    price = models.CharField(null=True, max_length=20)
    sold = models.DateField(blank=True, null=True)
    price_sold = models.CharField(null=True, max_length=20, blank=True)
    quantity = models.IntegerField(null=False, default=1)
    #: Publisher of the card:
    publisher = models.ForeignKey(Publisher, blank=True, null=True)

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
        """search some card: quick to test
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
        )

        if card_authors:  # TODO: more tests !
            card_obj.authors.add(*card_authors)

        # add the type of the card
        if not card.get('card_type'):
            card['card_type'] = "unknown"
        if card.get('card_type'):
            try:
                type_obj = CardType.objects.get(name=card.get('card_type'))
            except ObjectDoesNotExist, e:
                type_obj = CardType.objects.get(name="unknown")

            card_obj.card_type = type_obj
            card_obj.save()

        # add the publisher
        if card.get('card_type'):
            try:
                pub = card.get("publisher").lower()
                publisher_obj, created = Publisher.objects.get_or_create(name=pub)
                card_obj.publisher = publisher_obj
                card_obj.save()
                if created:
                    print "--- new publisher created: %s" % (pub.capitalize(),)
            except Exception, e:
                print "--- error while adding the publisher: %s" % (e,)

        # Make a sortkey in case it is missing
        # card.set_sortkey()

        return card_obj
