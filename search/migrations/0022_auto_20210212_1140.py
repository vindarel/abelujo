# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0021_sell_total_for_revenue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sell',
            name='total_for_revenue',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
    ]
