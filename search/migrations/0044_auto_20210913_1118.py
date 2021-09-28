# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0043_auto_20210906_0852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basketcopies',
            name='basket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Basket', null=True),
        ),
        migrations.AlterField(
            model_name='basketcopies',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='inventorycommandcopies',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='inventorycopies',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='placecopies',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='placecopies',
            name='place',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Place', null=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='search.Card', null=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Client', null=True),
        ),
        migrations.AlterField(
            model_name='soldcards',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='search.Card', null=True),
        ),
    ]
