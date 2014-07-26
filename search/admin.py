from django.contrib import admin

from search.models import Author
from search.models import Basket
from search.models import BasketCopies
from search.models import Card
from search.models import Distributor
from search.models import Deposit
from search.models import Place
from search.models import PlaceCopies
from search.models import Publisher

admin.site.register(Author)
admin.site.register(Basket)
admin.site.register(BasketCopies)
admin.site.register(Card)
admin.site.register(Deposit)
admin.site.register(Distributor)
admin.site.register(Place)
admin.site.register(PlaceCopies)
admin.site.register(Publisher)
