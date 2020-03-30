# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0064_restocking_restockingcopies'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='restockingcopies',
            name='card',
            field=models.ForeignKey(blank=True, to='search.Card', null=True, on_delete=models.CASCADE),
        ),
    ]
