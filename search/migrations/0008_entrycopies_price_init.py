# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0007_entry_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrycopies',
            name='price_init',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
