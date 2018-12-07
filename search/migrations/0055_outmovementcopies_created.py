# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0054_auto_20181207_2143'),
    ]

    operations = [
        migrations.AddField(
            model_name='outmovementcopies',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2018, 12, 7, 21, 46, 7, 113295, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
