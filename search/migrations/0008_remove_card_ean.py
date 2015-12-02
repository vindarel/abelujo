# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0007_ean_to_cleaned_isbn_20151203_1106'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='ean',
        ),
    ]
