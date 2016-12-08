# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0029_preferences_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='date_publication',
            field=models.DateField(null=True, blank=True),
        ),
    ]
