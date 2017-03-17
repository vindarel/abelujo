# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0037_command_inventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='command',
            name='inventory',
            field=models.ForeignKey(blank=True, to='search.InventoryCommnand', null=True),
        ),
    ]
