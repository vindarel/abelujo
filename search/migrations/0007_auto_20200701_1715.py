# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_auto_20200617_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnBasket',
            fields=[
                ('basket_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='search.Basket')),
            ],
            bases=('search.basket',),
        ),
        migrations.AlterField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(1, b'ESP\xc3\x88CES'), (7, b'MAESTRO'), (8, b'POSTCARD'), (9, b'VPAY'), (10, b'MASTERCARD'), (11, b'VISA'), (12, b'interne'), (13, b'en attente'), (6, b'autre')]),
        ),
        migrations.AlterField(
            model_name='sell',
            name='payment',
            field=models.CharField(default=(1, b'ESP\xc3\x88CES'), choices=[(1, b'ESP\xc3\x88CES'), (7, b'MAESTRO'), (8, b'POSTCARD'), (9, b'VPAY'), (10, b'MASTERCARD'), (11, b'VISA'), (12, b'interne'), (13, b'en attente'), (6, b'autre')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
    ]
