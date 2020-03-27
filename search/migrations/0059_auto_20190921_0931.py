# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0058_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='inventorycommand',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
