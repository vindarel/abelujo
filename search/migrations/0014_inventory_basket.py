# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_auto_20160314_0755'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='basket',
            field=models.ForeignKey(blank=True, to='search.Basket', null=True),
        ),
    ]
