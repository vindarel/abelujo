# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0037_auto_20210720_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reservation',
            name='payment_meta',
            field=models.TextField(max_length=10000, null=True, verbose_name='More data (JSON as text)', blank=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='payment_origin',
            field=models.CharField(max_length=200, null=True, verbose_name='Origin of the payment (Stripe?)', blank=True),
        ),
    ]
