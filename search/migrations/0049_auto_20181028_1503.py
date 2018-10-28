# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0048_basket_distributor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='depositcopies',
            name='card',
        ),
        migrations.RemoveField(
            model_name='depositcopies',
            name='deposit',
        ),
        migrations.RemoveField(
            model_name='deposit',
            name='copies',
        ),
        migrations.AddField(   # confirmed.
            model_name='depositstatecopies',
            name='nb_initial',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='DepositCopies',
        ),
    ]
