# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0012_auto_20200720_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='auto_update',
            field=models.BooleanField(default=True, verbose_name='Automatic update?'),
        ),
    ]
