# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0067_auto_20200128_2236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(1, 'cash'), (2, 'check'), (3, 'credit card'), (4, 'gift'), (5, 'transfer'), (6, 'other')]),
        ),
        migrations.AlterField(
            model_name='entrycopies',
            name='price_init',
            field=models.FloatField(default=0.0, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='sell',
            name='payment',
            field=models.CharField(default=(1, 'cash'), choices=[(1, 'cash'), (2, 'check'), (3, 'credit card'), (4, 'gift'), (5, 'transfer'), (6, 'other')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
    ]
