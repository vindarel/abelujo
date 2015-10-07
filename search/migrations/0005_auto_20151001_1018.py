# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_auto_20151001_0659'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrycopies',
            name='created',
            field=models.DateTimeField(default=datetime.date(2015, 10, 1), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entrycopies',
            name='modified',
            field=models.DateTimeField(default=datetime.date(2015, 10, 1), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='entry',
            name='typ',
            field=models.IntegerField(default=1, choices=[(1, b'purchase'), (2, b'deposit'), (3, b'gift')]),
        ),
    ]
