# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0035_auto_20170315_2332'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryCommnand',
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
            name='InventoryCommnandCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('inventory', models.ForeignKey(to='search.InventoryCommnand')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='inventorycommnand',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCommnandCopies', blank=True),
        ),
    ]
