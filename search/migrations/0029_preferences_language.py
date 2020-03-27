# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0028_auto_20160926_0809'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='language',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
