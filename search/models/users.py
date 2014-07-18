#!/usr/bin/env python

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
