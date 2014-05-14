from django.contrib import admin

from search.models import Author
from search.models import Card
from search.models import Publisher

admin.site.register(Card)
admin.site.register(Author)
admin.site.register(Publisher)
