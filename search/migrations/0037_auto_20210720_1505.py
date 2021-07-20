# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0036_auto_20210718_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='nb_pages',
            field=models.IntegerField(null=True, verbose_name='Number of pages', blank=True),
        ),
    ]
