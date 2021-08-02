# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0041_auto_20210729_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='is_unavailable',
            field=models.BooleanField(default=False, verbose_name="This book is not available. Don't check on Dilicom. Don't show it on a website."),
        ),
    ]
