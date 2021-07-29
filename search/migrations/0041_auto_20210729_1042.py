# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0040_auto_20210726_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_ready',
            field=models.BooleanField(default=True),
        ),
    ]
