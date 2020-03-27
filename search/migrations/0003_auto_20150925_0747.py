# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_auto_20150915_0738'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='dest_place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deposit',
            name='due_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
