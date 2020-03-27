# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_inventory_basket'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='in_stock',
            field=models.BooleanField(default=True),
        ),
    ]
