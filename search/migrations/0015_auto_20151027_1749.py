# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_auto_20151013_1651'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entrycopies',
            name='price_bought',
        ),
        migrations.AlterField(
            model_name='inventory',
            name='place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
        ),
        migrations.AlterField(
            model_name='inventorycards',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
