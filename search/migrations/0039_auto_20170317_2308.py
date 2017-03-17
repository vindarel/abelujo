# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0038_auto_20170317_2258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='command',
            name='inventory',
            field=models.OneToOneField(null=True, blank=True, to='search.InventoryCommnand'),
        ),
    ]
