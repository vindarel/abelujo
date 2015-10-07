# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_internalmovement'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(0, b'cash'), (1, b'check'), (2, b'credit card'), (3, b'gift'), (4, b'other')]),
            preserve_default=True,
        ),
    ]
