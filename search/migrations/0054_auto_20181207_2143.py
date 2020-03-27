# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0053_auto_20181201_1731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outmovement',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2018, 12, 7, 21, 43, 23, 50788, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
