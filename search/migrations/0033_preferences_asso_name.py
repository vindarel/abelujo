# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0032_auto_20170120_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='asso_name',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
