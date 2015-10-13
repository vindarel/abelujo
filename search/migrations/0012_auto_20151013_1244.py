# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0011_auto_20151013_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billcopies',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
