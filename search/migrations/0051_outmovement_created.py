# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0050_auto_20181130_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='outmovement',
            name='created',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
