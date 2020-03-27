# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0012_distributor_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='price',
            field=models.FloatField(default=0.0, null=True, blank=True),
        ),
    ]
