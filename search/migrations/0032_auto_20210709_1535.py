# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0031_auto_20210709_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='title_ascii',
            field=models.CharField(verbose_name='title_ascii', max_length=200, null=True, editable=False, blank=True),
        ),
    ]
