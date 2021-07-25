# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0038_auto_20210725_1641'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='send_by_post',
            field=models.BooleanField(default=False),
        ),
    ]
