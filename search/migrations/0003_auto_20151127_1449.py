# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_auto_20151123_1422'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deposit',
            name='initial_nb_copies',
        ),
        migrations.AlterField(
            model_name='depositcopies',
            name='nb',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='depositstatecopies',
            name='nb_current',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='depositstatecopies',
            name='nb_to_return',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='soldcards',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
