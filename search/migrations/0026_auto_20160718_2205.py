# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0025_inventory_applied'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='in_stock',
            field=models.BooleanField(default=False),
        ),
    ]
