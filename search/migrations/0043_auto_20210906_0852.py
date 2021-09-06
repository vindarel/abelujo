# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0042_auto_20210802_1152'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='imgfile2',
            field=models.ImageField(null=True, upload_to='covers', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='imgfile3',
            field=models.ImageField(null=True, upload_to='covers', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='imgfile4',
            field=models.ImageField(null=True, upload_to='covers', blank=True),
        ),
    ]
