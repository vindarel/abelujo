# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0032_auto_20210709_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='name_ascii',
            field=models.CharField(verbose_name='name_ascii', max_length=200, null=True, editable=False, blank=True),
        ),
    ]
