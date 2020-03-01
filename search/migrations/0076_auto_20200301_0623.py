# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0075_auto_20200227_1645'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='card',
            options={'ordering': ('sortkey', 'title'), 'verbose_name': 'card'},
        ),
        migrations.RemoveField(
            model_name='card',
            name='year_published',
        ),
    ]
