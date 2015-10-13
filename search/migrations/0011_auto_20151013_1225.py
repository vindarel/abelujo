# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0010_bill_distributor'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='nb',
            new_name='ref',
        ),
        migrations.AlterField(
            model_name='bill',
            name='due_date',
            field=models.DateField(),
        ),
    ]
