# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0069_auto_20200205_1414'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='others',
            field=models.TextField(null=True, blank=True),
        ),
    ]
