# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0023_preferences_auto_command_after_sell'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sell',
            name='payment_2',
            field=models.CharField(default='0', choices=[(7, b'ESP\xc3\x88CES'), (9, b'CB'), (8, b'CH\xc3\x88QUE'), (10, b'transfert'), (100, b"bon d'achat"), (11, b'autre')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
    ]
