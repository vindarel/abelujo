# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0072_remove_card_price_sold'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='currency',
            field=models.CharField(max_length=10, null=True, verbose_name='currency', blank=True),
        ),
    ]
