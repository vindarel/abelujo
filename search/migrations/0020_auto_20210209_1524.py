# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0019_auto_20201223_1745'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='payment_2',
            field=models.CharField(default=(7, b'ESP\xc3\x88CES'), choices=[(7, b'ESP\xc3\x88CES'), (9, b'CB'), (8, b'CH\xc3\x88QUE'), (10, b'transfert'), (100, b"bon d'achat"), (11, b'autre')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
        migrations.AddField(
            model_name='sell',
            name='total_payment_1',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='sell',
            name='total_payment_2',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(7, b'ESP\xc3\x88CES'), (9, b'CB'), (8, b'CH\xc3\x88QUE'), (10, b'transfert'), (100, b"bon d'achat"), (11, b'autre')]),
        ),
        migrations.AlterField(
            model_name='sell',
            name='payment',
            field=models.CharField(default=(7, b'ESP\xc3\x88CES'), choices=[(7, b'ESP\xc3\x88CES'), (9, b'CB'), (8, b'CH\xc3\x88QUE'), (10, b'transfert'), (100, b"bon d'achat"), (11, b'autre')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
    ]
