#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
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
import factory
from factory.django import DjangoModelFactory

from search.models import Author
# from search.models import Basket
# from search.models import Card
from search.models import Client
# from search.models import CardType
# from search.models import Collection
# from search.models import Command
from search.models import Deposit
from search.models import Distributor
from search.models import Inventory
# from search.models import InventoryCommand
from search.models import Place
# from search.models import PlaceCopies
from search.models import Preferences
from search.models import Publisher
from search.models import Sell
# from search.models import Shelf
# from search.models import SoldCards


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Sequence(lambda n: "author test %d" % n)

class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    name = factory.Sequence(lambda n: "client test %d" % n)

class SellsFactory(DjangoModelFactory):
    class Meta:
        model = Sell

    created = datetime.date.today()

class DepositFactory(DjangoModelFactory):
    class Meta:
        model = Deposit
    name = factory.Sequence(lambda n: "deposit test %d" % n)
    distributor = None
    dest_place = None
    due_date = datetime.date.today() + datetime.timedelta(days=30)

class DistributorFactory(DjangoModelFactory):
    class Meta:
        model = Distributor
    name = factory.Sequence(lambda n: "distributor test %s" % n)
    discount = 35

class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = Place
    name = factory.Sequence(lambda n: "place test %s" % n)
    is_stand = False
    can_sell = True

class PreferencesFactory(DjangoModelFactory):
    class Meta:
        model = Preferences
    default_place = PlaceFactory()
    vat_book = "5.5"

class PublisherFactory(DjangoModelFactory):
    class Meta:
        model = Publisher
    name = factory.Sequence(lambda n: "publisher test %s" % n)

class InventoryFactory(DjangoModelFactory):
    class Meta:
        model = Inventory
