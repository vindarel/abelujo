# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0021_auto_20160514_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True),
        ),
    ]
