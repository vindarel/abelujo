# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_card_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]
