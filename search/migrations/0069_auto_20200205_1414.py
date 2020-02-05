# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0068_auto_20200131_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=0, null=True, verbose_name='threshold', blank=True),
        ),
    ]
