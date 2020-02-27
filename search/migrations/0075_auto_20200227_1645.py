# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0074_auto_20200226_1828'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ('city',)},
        ),
        migrations.RemoveField(
            model_name='client',
            name='contact',
        ),
        migrations.AddField(
            model_name='client',
            name='address1',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='address2',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='city',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='country',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='mobilephone',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='state',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='telephone',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='website',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='zip_code',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='firstname',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='recipient',
            field=models.ForeignKey(blank=True, to='search.Client', null=True),
        ),
        migrations.DeleteModel(
            name='Contact',
        ),
    ]
