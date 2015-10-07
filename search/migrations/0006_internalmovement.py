# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0005_auto_20151001_1018'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.IntegerField()),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('dest', models.ForeignKey(related_name=b'mvt_dest', to='search.Place')),
                ('origin', models.ForeignKey(related_name=b'mvt_origin', to='search.Place')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
