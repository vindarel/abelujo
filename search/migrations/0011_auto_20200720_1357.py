# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0010_auto_20200710_1437'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='price_bought',
            field=models.FloatField(null=True, verbose_name='price bought', blank=True),
        ),
    ]
