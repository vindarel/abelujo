# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_auto_20200603_1513'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='presedit',
            field=models.CharField(verbose_name='Pr\xe9sentation \xe9diteur', max_length=200, null=True, editable=False, blank=True),
        ),
    ]
