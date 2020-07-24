# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_auto_20200723_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='initial_sells_quantity',
            field=models.IntegerField(default=0, verbose_name='The number of registered sells the client has on the previous system.'),
        ),
    ]
