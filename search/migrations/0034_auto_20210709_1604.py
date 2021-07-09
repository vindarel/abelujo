# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0033_auto_20210709_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='bio',
            field=models.TextField(null=True, verbose_name='biography', blank=True),
        ),
    ]
