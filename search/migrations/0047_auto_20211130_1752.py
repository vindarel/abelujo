# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0046_auto_20210913_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='bon_de_commande',
            field=models.CharField(max_length=200, null=True, verbose_name='Bon de commande', blank=True),
        ),
    ]
