# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0007_auto_20200701_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='ignore_for_revenue',
            field=models.BooleanField(default=False, verbose_name='ignore when counting the revenue?'),
        ),
    ]
