# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0024_auto_20210217_1450'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reception',
            fields=[
                ('basket_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='search.Basket')),
            ],
            bases=('search.basket',),
        ),
    ]
