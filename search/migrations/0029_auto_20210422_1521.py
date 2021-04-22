# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0028_auto_20210421_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reservation',
            name='notified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reservation',
            name='success',
            field=models.BooleanField(default=True),
        ),
    ]
