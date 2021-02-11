# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0020_auto_20210209_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='total_for_revenue',
            field=models.FloatField(default=0),
        ),
    ]
