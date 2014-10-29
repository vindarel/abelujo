#!/usr/bin/env python
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

from django.db import models

from models import CHAR_LENGTH

class Address(models.Model):
    """Contact information.

    Distinguish the informations between a physical or a moral person ?
    """
    class Meta:
        app_label = "search"
        ordering = ("name",)

    name           = models.CharField(max_length=CHAR_LENGTH)
    surname        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    enterprise     = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    responsability = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    cellphone      = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    tel_private    = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    tel_office     = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    website        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    email          = models.EmailField(blank=True, null=True)
    email_pro      = models.EmailField(blank=True, null=True)

    address1       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    address2       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    zip_code       = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    city           = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    state          = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)
    country        = models.CharField(blank=True, null=True, max_length=CHAR_LENGTH)

    comment        = models.TextField(blank=True, null=True)
