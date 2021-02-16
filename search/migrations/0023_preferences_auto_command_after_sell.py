# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0022_auto_20210212_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='auto_command_after_sell',
            field=models.BooleanField(default=False, verbose_name='Automatically command? After a sell, if the quantity of the book gets below its minimal quantity, add the book to the list of commands.'),
        ),
    ]
