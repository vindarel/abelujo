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
from django.contrib import admin

from search.models import Author
from search.models import Basket
from search.models import BasketCopies
from search.models import Bill
from search.models import Card
from search.models import Category
from search.models import Distributor
from search.models import Deposit
from search.models import Place
from search.models import PlaceCopies
from search.models import Publisher
from search.models import Sell

class CardAdmin(admin.ModelAdmin):
    class Meta:
        model = Card

    search_fields = ["title", "authors__name"]
    list_display = ("title", "distributor", "price",)
    list_editable = ("distributor", "price",)
    filter_horizontal = ("authors", "publishers",)

class DistributorAdmin(admin.ModelAdmin):
    class Meta:
        model = Distributor

    list_display = ("name", "discount", "stars")
    list_editable = ("discount", "stars")

class BillAdmin(admin.ModelAdmin):
    class Meta:
        model = Bill

    list_display = ("name", "ref", "distributor", "total")

admin.site.register(Author)
admin.site.register(Basket)
admin.site.register(BasketCopies)
admin.site.register(Bill, BillAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Category)
admin.site.register(Deposit)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Place)
admin.site.register(PlaceCopies)
admin.site.register(Publisher)
admin.site.register(Sell)
