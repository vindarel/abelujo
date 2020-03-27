# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0061_auto_20191019_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
