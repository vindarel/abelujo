# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0052_auto_20181130_1855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outmovement',
            name='card',
            field=models.ForeignKey(blank=True, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='nb',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='origin',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='recipient',
            field=models.ForeignKey(blank=True, to='search.Address', null=True),
        ),
    ]
