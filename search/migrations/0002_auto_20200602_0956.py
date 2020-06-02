# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_squashed_0078_auto_20200318_1526'),
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
        migrations.AlterField(
            model_name='deposit',
            name='deposit_type',
            field=models.CharField(default='fix', max_length=200, verbose_name='deposit type', choices=[('D\xe9p\xf4t de libraire', (('lib', 'd\xe9p\xf4t de libraire'), ('fix', 'd\xe9p\xf4t fixe'))), ('D\xe9p\xf4t de distributeur', (('dist', 'd\xe9p\xf4t de distributeur'),))]),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='outmovementcopies',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
