# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0029_auto_20210422_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2021, 4, 22, 15, 46, 2, 547137, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservation',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2021, 4, 22, 15, 46, 13, 900615, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
