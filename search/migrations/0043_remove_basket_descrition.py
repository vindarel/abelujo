# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0042_auto_20171212_2232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basket',
            name='descrition',
        ),
    ]