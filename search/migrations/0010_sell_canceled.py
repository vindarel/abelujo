# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0009_auto_20160113_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='canceled',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
