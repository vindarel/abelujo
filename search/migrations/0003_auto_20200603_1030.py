# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_auto_20200602_1013'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='city',
            field=models.CharField(max_length=200, null=True, verbose_name='City', blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='comm_via_dilicom',
            field=models.CharField(max_length=4, null=True, verbose_name='Comm. via Dilicom: yes or no?', blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='country',
            field=models.CharField(max_length=200, null=True, verbose_name='Country', blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='nb_titles_in_FEL',
            field=models.IntegerField(null=True, verbose_name='Number of titles in FEL (june, 2020)', blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='postal_code',
            field=models.CharField(max_length=200, null=True, verbose_name='Postal code', blank=True),
        ),
    ]
