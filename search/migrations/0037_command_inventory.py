# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0036_auto_20170317_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='command',
            name='inventory',
            field=models.ForeignKey(blank=True, to='search.InventoryCommnandCopies', null=True),
        ),
    ]
