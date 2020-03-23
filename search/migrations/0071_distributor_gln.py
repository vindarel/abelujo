# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0070_preferences_others'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='gln',
            field=models.CharField(max_length=200, null=True, verbose_name='GLN', blank=True),
        ),
    ]
