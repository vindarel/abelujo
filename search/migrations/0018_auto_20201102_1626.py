# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0017_auto_20201029_0655'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='is_box',
            field=models.BooleanField(default=False, verbose_name='Behave like a box? Adding a book removes it from the stock.'),
        ),
    ]
