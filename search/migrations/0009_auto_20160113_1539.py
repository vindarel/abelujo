# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0008_remove_card_ean'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='reason',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='entry',
            name='typ',
            field=models.IntegerField(default=1, choices=[(1, b'purchase'), (2, b'deposit'), (3, b'gift'), (4, b'sell canceled')]),
        ),
    ]
