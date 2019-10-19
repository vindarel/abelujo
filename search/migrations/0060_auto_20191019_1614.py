# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0059_auto_20190921_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='authors',
            field=models.ManyToManyField(to='search.Author', null=True, blank=True),
        ),
    ]
