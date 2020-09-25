# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0015_auto_20200724_1735'),
    ]

    operations = [
        migrations.AddField(
            model_name='basketcopies',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 9, 25, 15, 32, 29, 701687, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='basketcopies',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2020, 9, 25, 15, 32, 45, 795628, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
