# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0010_sell_canceled'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=1, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='email_pro',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
