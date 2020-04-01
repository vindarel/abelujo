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

"""
Django Rest Framework serializers of our models.
http://www.django-rest-framework.org/api-guide/serializers/
"""

from rest_framework import serializers

from .models import Command
from .models import Preferences


class PreferencesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Preferences
        depth = 1  # include the place name and co
        fields = '__all__'


class CommandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Command
        fields = ('id',
                  'name',
                  'publisher',
                  'distributor',
                  'copies',
                  'date_received',
                  'date_bill_received',
                  'date_payment_sent',
                  'date_paid',
                  'comment',

                  # and inherited fields:
                  'created',

                  # and properties:
                  'supplier_id',
                  'supplier_name',
                  'total_value',
                  'total_value_inctaxes',
                  'nb_copies')
