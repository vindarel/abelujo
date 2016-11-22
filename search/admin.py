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
from django.contrib import admin

from search.models import Author
from search.models import Basket
from search.models import BasketCopies
from search.models import Bill
from search.models import Card
from search.models import Shelf
from search.models import Distributor
from search.models import Deposit
from search.models import Inventory
from search.models import Place
from search.models import PlaceCopies
from search.models import Publisher
from search.models import Sell

# Custom admin for the client admin:
# show less things than the default admin,
# in particular no need to show the intermediate classes.
class MyAdmin(admin.AdminSite):
    site_header = 'Abelujo administration'
    site_title = 'Abelujo admin'

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

    list_display = ("name", "discount", "stars", "email")
    list_editable = ("discount", "stars", "email")

class BillAdmin(admin.ModelAdmin):
    class Meta:
        model = Bill

    list_display = ("name", "ref", "distributor", "total")

class DepositAdmin(admin.ModelAdmin):
    class Meta:
        model = Deposit

    list_display = ("name", "distributor", "dest_place", "due_date", "auto_command")

class InventoryAdmin(admin.ModelAdmin):
    class Meta:
        model = Inventory

    list_display = ("name", "created", "closed")

class PublisherAdmin(admin.ModelAdmin):
    class Meta:
        model = Publisher

    list_display = ("name",)
    list_editable = ("name",)
    search_fields = ["name"]

admin.site.register(Author)
admin.site.register(Basket)
admin.site.register(BasketCopies)
admin.site.register(Bill, BillAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Shelf)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Place)
admin.site.register(PlaceCopies)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Sell)

admin_site = MyAdmin(name='myadmin')
admin_site.register(Author)
admin_site.register(Basket)
admin_site.register(Card, CardAdmin)
admin_site.register(Distributor)
admin_site.register(Deposit, DepositAdmin)
admin_site.register(Place)
admin_site.register(PlaceCopies)
admin_site.register(Publisher, PublisherAdmin)
admin_site.register(Sell)
admin_site.register(Shelf)
