# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0024_auto_20160715_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='applied',
            field=models.BooleanField(default=False),
        ),
    ]
