# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0027_preferences_vat_book'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
    ]
