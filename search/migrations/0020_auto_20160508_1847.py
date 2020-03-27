# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0019_auto_20160419_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basket',
            name='comment',
            field=models.CharField(max_length=10000, null=True, blank=True),
        ),
    ]
