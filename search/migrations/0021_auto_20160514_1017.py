# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0020_auto_20160508_1847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='deposits',
            field=models.ManyToManyField(to='search.Deposit', blank=True),
        ),
        migrations.AlterField(
            model_name='basket',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BasketCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BillCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to='search.Place', through='search.PlaceCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to='search.Publisher', blank=True),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.DepositCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='deposit_type',
            field=models.CharField(default=b'fix', max_length=200, choices=[(b'D\xc3\xa9p\xc3\xb4t de libraire', ((b'lib', b'd\xc3\xa9p\xc3\xb4t de libraire'), (b'fix', b'd\xc3\xa9p\xc3\xb4t fixe'))), (b'D\xc3\xa9p\xc3\xb4t de distributeur', ((b'dist', b'd\xc3\xa9p\xc3\xb4t de distributeur'),))]),
        ),
        migrations.AlterField(
            model_name='depositstate',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.DepositStateCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCards', blank=True),
        ),
        migrations.AlterField(
            model_name='sell',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.SoldCards', blank=True),
        ),
    ]
