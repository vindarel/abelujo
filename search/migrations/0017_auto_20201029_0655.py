# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0016_auto_20200925_1532'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='discount',
            field=models.IntegerField(null=True, verbose_name='Discount', blank=True),
        ),
    ]
