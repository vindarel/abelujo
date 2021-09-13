# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0044_auto_20210913_1118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basket',
            name='distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='card_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='card type', blank=True, to='search.CardType', null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='shelf',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='shelf', blank=True, to='search.Shelf', null=True),
        ),
    ]
