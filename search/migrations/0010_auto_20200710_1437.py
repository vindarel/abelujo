# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0009_auto_20200710_1044'),
    ]

    operations = [
        migrations.AddField(
            model_name='soldcards',
            name='deposit',
            field=models.ForeignKey(verbose_name='deposit', blank=True, to='search.Deposit', null=True),
        ),
    ]
