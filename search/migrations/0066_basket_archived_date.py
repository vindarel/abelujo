# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0065_auto_20200104_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='archived_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
