# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0035_auto_20210714_2240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='due_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='ref',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='total',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='discount',
            field=models.IntegerField(null=True, verbose_name='Discount (%)', blank=True),
        ),
    ]
