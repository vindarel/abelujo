# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_squashed_0015_auto_20151027_1749'),
    ]

    operations = [
        migrations.AlterField(
            model_name='depositstate',
            name='closed',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='entrycopies',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='entrycopies',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
