# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0062_card_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, blank=True),
        ),
    ]
