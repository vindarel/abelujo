# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0034_auto_20210709_1604'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='is_excluded_for_website',
            field=models.BooleanField(default=False, verbose_name='Ne pas montrer sur le site vitrine'),
        ),
    ]
