# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0034_card_fmt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='command',
            name='date_bill_received',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_paid',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_payment_sent',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_received',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
