# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0011_auto_20200720_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='vat',
            field=models.FloatField(null=True, verbose_name='VAT tax', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='price_bought',
            field=models.FloatField(null=True, verbose_name='price bought (leave blank if you use a supplier and its discount)', blank=True),
        ),
    ]
