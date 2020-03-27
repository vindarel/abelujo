# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0017_inventory_shelf'),
    ]

    operations = [
        migrations.AddField(
            model_name='soldcards',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 12, 14, 51, 5, 901571, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='soldcards',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 12, 14, 51, 19, 634229, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
