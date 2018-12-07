# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0049_auto_20181028_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typ', models.IntegerField(choices=[(1, b'sell'), (2, b'return'), (3, b'loss'), (4, b'gift')])),
                ('reason', models.CharField(max_length=200, null=True, blank=True)),
                ('nb', models.IntegerField()),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True)),
                ('card', models.ForeignKey(to='search.Card')),
            ],
        ),
        migrations.CreateModel(
            name='OutMovementCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=1, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('movement', models.ForeignKey(to='search.OutMovement')),
            ],
        ),
        migrations.AddField(
            model_name='outmovement',
            name='copies',
            field=models.ManyToManyField(related_name='copies', through='search.OutMovementCopies', to='search.Card', blank=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='distributor',
            field=models.ForeignKey(to='search.Distributor'),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='origin',
            field=models.ForeignKey(to='search.Place'),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='publisher',
            field=models.ForeignKey(to='search.Publisher'),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='recipient',
            field=models.ForeignKey(to='search.Address'),
        ),
    ]
