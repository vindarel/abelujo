# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
from django.contrib import admin

from search.models import Author
from search.models import Basket
from search.models import Bill
from search.models.users import Bookshop
from search.models import Card
from search.models import CardType
from search.models import CouponGeneric
from search.models import Coupon
from search.models import Client
from search.models import Command
from search.models import Shelf
from search.models import Distributor
from search.models import Deposit
from search.models import Inventory
from search.models import Place
from search.models import Publisher
from search.models import RestockingCopies
from search.models import Reservation
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shelf":
            # It seems we can't sort with the locale, because we'd return a list
            # and we must return a queryset. So lowercase names are not sorted properly.
            kwargs["queryset"] = Shelf.objects.order_by('name')

        return super(CardAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    search_fields = ["title", "authors__name", "isbn"]
    list_display = ("title", "distributor", "price",)
    list_editable = ("distributor", "price",)
    filter_horizontal = ("authors", "publishers",)
    exclude = ("in_stock",)


class CardTypeAdmin(admin.ModelAdmin):
    class Meta:
        model = CardType


class AuthorAdmin(admin.ModelAdmin):
    class Meta:
        model = Author

    search_fields = ["name"]
    # list_editable = ("name",)

class BasketAdmin(admin.ModelAdmin):
    class Meta:
        model = Basket

    search_fields = ["name"]
    list_display = ["pk", "name", "comment", "archived", "is_box"]
    list_editable = ("name",)

class ClientAdmin(admin.ModelAdmin):
    class Meta:
        model = Client

    search_fields = ["name", "firstname", "mobilephone", "address1", "city", "country", "zip_code"]
    list_display = ["name", "firstname", "mobilephone", "email", "discount"]
    ordering = ["name", "firstname"]


class CommandAdmin(admin.ModelAdmin):
    class Meta:
        model = Command

    search_fields = ["supplier_name"]
    list_display = ("__unicode__", "supplier_name", "date_received", "date_paid")


class DistributorAdmin(admin.ModelAdmin):
    class Meta:
        model = Distributor

    search_fields = ["name", "gln", "city", "country", "postal_code"]
    list_display = ("name", "discount", "stars", "email")
    list_editable = ("discount", "stars", "email")
    ordering = ("name",)

class BillAdmin(admin.ModelAdmin):
    class Meta:
        model = Bill

    list_display = ("name", "ref", "total")

class DepositAdmin(admin.ModelAdmin):
    class Meta:
        model = Deposit

    list_display = ("name", "distributor", "dest_place", "due_date", "auto_command")
    ordering = ("name",)

class InventoryAdmin(admin.ModelAdmin):
    class Meta:
        model = Inventory

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shelf":
            kwargs["queryset"] = Shelf.objects.order_by('name')
            return super(InventoryAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ("name", "created", "closed")

class PublisherAdmin(admin.ModelAdmin):
    class Meta:
        model = Publisher

    list_display = ("name",)
    list_editable = ("name",)
    search_fields = ["name"]
    ordering = ("name",)


class ReservationAdmin(admin.ModelAdmin):
    class Meta:
        model = Reservation

    search_fields = ["card__title"]
    list_display = ("pk", "client", "card", "created", "archived")


class ShelfAdmin(admin.ModelAdmin):
    class Meta:
        model = Shelf

    def in_shelf(shelf):
        return shelf.cards_qty

    list_display = ("name", in_shelf)
    list_editable = ("name",)
    search_fields = ["name"]
    ordering = ("name",)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Bookshop)
admin.site.register(Bill, BillAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(CardType, CardTypeAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(CouponGeneric)
admin.site.register(Coupon)
admin.site.register(Command, CommandAdmin)
admin.site.register(Shelf, ShelfAdmin)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Place)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(RestockingCopies)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Sell)

admin_site = MyAdmin(name='myadmin')
admin_site.register(Author, AuthorAdmin)
admin_site.register(Basket, BasketAdmin)
admin_site.register(Card, CardAdmin)
admin_site.register(CardType, CardTypeAdmin)
admin_site.register(Client, ClientAdmin)
admin_site.register(Command, CommandAdmin)
admin_site.register(Distributor)
admin_site.register(Deposit, DepositAdmin)
admin_site.register(Place)
admin_site.register(Publisher, PublisherAdmin)
admin_site.register(Sell)
admin_site.register(Reservation, ReservationAdmin)
admin_site.register(Shelf, ShelfAdmin)
