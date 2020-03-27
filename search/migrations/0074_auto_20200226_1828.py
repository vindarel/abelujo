# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0073_card_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='cover',
            field=models.URLField(null=True, verbose_name='cover url', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='currency',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='currency', choices=[(b'euro', b'\xe2\x82\xac'), (b'chf', b'CHF')]),
        ),
        migrations.AlterField(
            model_name='card',
            name='data_source',
            field=models.CharField(verbose_name='data source', max_length=200, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='details_url',
            field=models.URLField(verbose_name='details url', null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='fmt',
            field=models.TextField(verbose_name='Book format (pocket, etc)', null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=0, null=True, verbose_name='Minimal quantity before command', blank=True),
        ),
    ]
