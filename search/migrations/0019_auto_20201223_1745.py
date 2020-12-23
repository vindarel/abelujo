# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0018_auto_20201102_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='vat_other_product',
            field=models.FloatField(default=20.0, null=True, verbose_name='other products VAT', blank=True),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='vat_book',
            field=models.FloatField(default=5.5, null=True, verbose_name='book vat', blank=True),
        ),
    ]
