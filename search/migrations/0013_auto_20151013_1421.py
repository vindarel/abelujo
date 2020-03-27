# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0012_auto_20151013_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='summary',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entrycopies',
            name='price_bought',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
