# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0030_card_date_publication'),
    ]

    operations = [
        migrations.CreateModel(
            name='Barcode64',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('ean', models.CharField(max_length=200, null=True, blank=True)),
                ('barcodebase64', models.CharField(max_length=10000, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
