# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0005_card_presedit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='parent',
        ),
        migrations.AlterField(
            model_name='card',
            name='collection',
            field=models.CharField(max_length=200, null=True, verbose_name='collection', blank=True),
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
    ]
