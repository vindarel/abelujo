# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0071_distributor_gln'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='price_sold',
        ),
    ]
