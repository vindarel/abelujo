# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0043_remove_basket_descrition'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='quantity',
        ),
    ]
