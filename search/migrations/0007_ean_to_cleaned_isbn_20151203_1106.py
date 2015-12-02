# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import string

from django.db import migrations
from django.db import models


def isbn_cleanup(isbn):
    res = isbn
    if isbn:
        punctuation = set(string.punctuation)
        res = "".join([it for it in isbn if it not in punctuation])

    return res

def set_isbn(apps, schema_director):
    Card = apps.get_model("search", "Card")
    for card in Card.objects.all():
        isbn = card.isbn or card.ean
        isbn = isbn_cleanup(isbn)
        card.isbn = isbn
        card.save()

class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_auto_20151201_1715'),
    ]

    operations = [
        migrations.RunPython(set_isbn)
    ]
