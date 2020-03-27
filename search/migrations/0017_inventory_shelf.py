# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0016_auto_20160404_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='shelf',
            field=models.ForeignKey(blank=True, to='search.Shelf', null=True),
        ),
    ]
