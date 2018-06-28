# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0045_auto_20180517_1604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='name',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
