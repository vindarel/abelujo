# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0045_auto_20210913_1134'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='archived',
            field=models.BooleanField(default=False, verbose_name="This card is archived: it was 'deleted' one day, but it's kept for historical purposes."),
        ),
        migrations.AddField(
            model_name='card',
            name='archived_date',
            field=models.DateField(null=True, verbose_name='date archived', blank=True),
        ),
    ]
