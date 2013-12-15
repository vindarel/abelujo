# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.

# copied from django-library
from datetime import date

from django.db import models

#TODO: don't put the model in the search app
class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Location(TimeStampedModel):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Author(TimeStampedModel):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Card(TimeStampedModel):
    """a Card represents a book, a CD, a t-shirt, etc. This isn't the
    physical object
    """
    origkey = models.CharField(max_length=36, blank=True, null=True)
    title = models.TextField()
    sortkey = models.TextField('Authors', blank=True)
    year_published = models.DateField(blank=True, null=True)
    # authors = models.ManyToManyField(Author)
    authors = models.TextField(null=True)
    # location = models.ForeignKey(Location, blank=True, null=True)
        #    default=u'?', on_delete=models.SET_DEFAULT)
    ean = models.TextField(null=True)
    isbn = models.TextField(null=True)
    comment = models.TextField(blank=True)


    class Meta:
        ordering = ('sortkey', 'year_published', 'title')

    def __unicode__(self):
        # return u'%s (%s): "%s"' % (self.sortkey, self.year_published, self.title)
        return u'%s (%s): "%s"' % (self.title, self.authors, self.ean)

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
        ret = Card.objects.all()[:nb]
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
    def from_dict(book):
        """Add a book from a dict.

        Format of dict:
            title:      string
            year:       int or None
            authors:    list of strings
            location:   string
            sortkey:    string of authors in the order they appear on
                        the cover
            origkey:    (optional) original key, like an ISBN, or if
                        converting from another system
        """
        # Some books always go missing...
        print "---- adding a book"
        # location_string = book.get('location', u'?')
        # location, _ = Location.objects.get_or_create(name=location_string)

        # Unknown years is okay
        year = book.get('year', None)
        try:
            int(year)
            year = date(year, 1, 1)
        except TypeError:
            year = None

        # Books can have more than one author, some have none
        author_ids = []
        print "---- hello"

        # for a in book.get('authors', []):
        #     author, created = Author.objects.get_or_create(name=a)
        #     author_ids.append(author.id)
        # authors = Author.objects.filter(id__in=author_ids)

        # Make the book
        book, created = Card.objects.get_or_create(
                title=book['title'],
                year_published=year,
                authors = book.get('authors', None),
                # location=location,
                # origkey=book.get('origkey', None),
                # sortkey=book.get('sortkey', u''),
        )

        # Add the authors
        print " ++++++ foo"
        # for author in authors:
            # book.authors.add(author)

        # Make a sortkey in case it is missing
        # book.set_sortkey()

        print "--------- let's return"
        return book
