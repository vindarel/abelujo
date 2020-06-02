# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='name_ascii',
            field=models.CharField(max_length=200, null=True, verbose_name='name_ascii', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='title_ascii',
            field=models.CharField(max_length=200, null=True, verbose_name='title_ascii', blank=True),
        ),
    ]
