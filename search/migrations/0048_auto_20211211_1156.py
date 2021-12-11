# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0047_auto_20211130_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='created',
            field=models.DateTimeField(default=datetime.date(1970, 1, 1), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='basket',
            name='modified',
            field=models.DateTimeField(default=datetime.date(1970, 1, 1), auto_now=True),
            preserve_default=False,
        ),
    ]
