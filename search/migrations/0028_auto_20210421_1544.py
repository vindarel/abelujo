# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0027_auto_20210401_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='nb',
            field=models.IntegerField(default=1, null=True, blank=True),
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='card',
        ),
        migrations.AddField(
            model_name='reservation',
            name='card',
            field=models.ForeignKey(blank=True, to='search.Card', null=True),
        ),
    ]
