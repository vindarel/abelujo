# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0022_inventory_publisher'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='closed',
            field=models.BooleanField(default=False),
        ),
    ]
