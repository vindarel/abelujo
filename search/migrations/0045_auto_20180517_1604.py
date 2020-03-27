# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0044_remove_card_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='sell',
            name='deposit',
            field=models.ForeignKey(blank=True, to='search.Deposit', null=True),
        ),
        migrations.AddField(
            model_name='sell',
            name='place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(0, 'cash'), (1, 'check'), (2, 'credit card'), (3, 'gift'), (5, 'transfer'), (4, 'other')]),
        ),
        migrations.AlterField(
            model_name='sell',
            name='payment',
            field=models.CharField(default=(0, 'cash'), max_length=200, null=True, blank=True, choices=[(0, 'cash'), (1, 'check'), (2, 'credit card'), (3, 'gift'), (5, 'transfer'), (4, 'other')]),
        ),
    ]
