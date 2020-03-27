# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0009_auto_20151013_1205'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='distributor',
            field=models.ForeignKey(to='search.Distributor', null=True),
            preserve_default=True,
        ),
    ]
