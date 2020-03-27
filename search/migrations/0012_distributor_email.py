# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0011_auto_20160204_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
