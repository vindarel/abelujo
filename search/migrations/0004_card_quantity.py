# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_auto_20151127_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
