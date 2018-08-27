# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0046_auto_20180628_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
    ]
