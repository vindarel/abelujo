# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0039_auto_20170317_2308'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('closed', models.DateTimeField(null=True, blank=True)),
                ('applied', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InventoryCommandCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('inventory', models.ForeignKey(to='search.InventoryCommand')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='inventorycommnand',
            name='copies',
        ),
        migrations.RemoveField(
            model_name='inventorycommnandcopies',
            name='card',
        ),
        migrations.RemoveField(
            model_name='inventorycommnandcopies',
            name='inventory',
        ),
        migrations.AlterField(
            model_name='command',
            name='inventory',
            field=models.OneToOneField(null=True, blank=True, to='search.InventoryCommand'),
        ),
        migrations.DeleteModel(
            name='InventoryCommnand',
        ),
        migrations.DeleteModel(
            name='InventoryCommnandCopies',
        ),
        migrations.AddField(
            model_name='inventorycommand',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCommandCopies', blank=True),
        ),
    ]
