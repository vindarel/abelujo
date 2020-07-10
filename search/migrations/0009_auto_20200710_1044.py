# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0008_auto_20200710_1038'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sell',
            name='ignore_for_revenue',
        ),
        migrations.AddField(
            model_name='soldcards',
            name='ignore_for_revenue',
            field=models.BooleanField(default=False, verbose_name='ignore when counting the revenue?'),
        ),
    ]
