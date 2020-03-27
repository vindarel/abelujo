# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0026_auto_20160718_2205'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='vat_book',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
