# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0048_auto_20211211_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, verbose_name='discount (%)', blank=True),
        ),
    ]
