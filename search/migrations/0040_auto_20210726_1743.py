# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0039_auto_20210725_1648'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='payment_intent',
            field=models.CharField(max_length=200, null=True, verbose_name='Stripe payment intent ID (internal field', blank=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='payment_session',
            field=models.TextField(max_length=10000, null=True, verbose_name='Stripe payment session (internal field)', blank=True),
        ),
    ]
