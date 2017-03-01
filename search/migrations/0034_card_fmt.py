# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0033_preferences_asso_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='fmt',
            field=models.TextField(null=True, blank=True),
        ),
    ]
