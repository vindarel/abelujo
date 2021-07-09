# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0030_auto_20210422_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='meta',
            field=models.TextField(blank=True),
        ),
    ]
