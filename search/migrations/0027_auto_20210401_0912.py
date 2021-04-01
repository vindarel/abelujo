# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0026_auto_20210312_1627'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='is_catalogue_selection',
            field=models.BooleanField(default=False, verbose_name='S\xe9lection du libraire pour le catalogue en ligne'),
        ),
    ]
