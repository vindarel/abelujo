# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_auto_20200603_1030'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='height',
            field=models.IntegerField(null=True, verbose_name='Height', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='theme',
            field=models.CharField(max_length=4, null=True, verbose_name='Theme (Dilicom)', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='thickness',
            field=models.IntegerField(null=True, verbose_name='Thickness', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='weight',
            field=models.IntegerField(null=True, verbose_name='Weight', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='width',
            field=models.IntegerField(null=True, verbose_name='Width', blank=True),
        ),
    ]
