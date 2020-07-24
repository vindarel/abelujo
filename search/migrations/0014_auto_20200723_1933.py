# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_auto_20200721_1134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bill',
            name='distributor',
        ),
        migrations.AddField(
            model_name='sell',
            name='client',
            field=models.ForeignKey(verbose_name='client', blank=True, to='search.Client', null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='selling_price',
            field=models.FloatField(null=True, verbose_name="Selling price (leave blank if it's the same than the public price)", blank=True),
        ),
    ]
