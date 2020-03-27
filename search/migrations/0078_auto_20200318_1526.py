# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0077_auto_20200304_1559'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookshop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('firstname', models.CharField(max_length=200, null=True, blank=True)),
                ('mobilephone', models.CharField(max_length=200, null=True, blank=True)),
                ('telephone', models.CharField(max_length=200, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('website', models.CharField(max_length=200, null=True, blank=True)),
                ('company_number', models.CharField(max_length=200, null=True, verbose_name="The company's registered number (State's industry chamber)", blank=True)),
                ('bookshop_number', models.CharField(max_length=200, null=True, verbose_name="The bookshop's official number.", blank=True)),
                ('address1', models.CharField(max_length=200, null=True, blank=True)),
                ('address2', models.CharField(max_length=200, null=True, blank=True)),
                ('zip_code', models.CharField(max_length=200, null=True, blank=True)),
                ('city', models.CharField(max_length=200, null=True, blank=True)),
                ('state', models.CharField(max_length=200, null=True, blank=True)),
                ('country', models.CharField(max_length=200, null=True, blank=True)),
                ('presentation_comment', models.TextField(max_length=10000, null=True, verbose_name='A comment to add after the default presentation, which contains name, address, contact and official number. Can be useful when the bookshop is officially administrated by another entity. This appears on bills.', blank=True)),
                ('checks_order', models.CharField(max_length=200, null=True, verbose_name='Checks order (if different from name)', blank=True)),
                ('checks_address', models.CharField(max_length=200, null=True, verbose_name='Checks address (if different than address)', blank=True)),
                ('bank_IBAN', models.CharField(max_length=200, null=True, verbose_name='IBAN', blank=True)),
                ('bank_BIC', models.CharField(max_length=200, null=True, verbose_name='BIC', blank=True)),
                ('is_vat_exonerated', models.BooleanField(default=False, verbose_name='Exonerated of VAT?')),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('firstname',),
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ('firstname',)},
        ),
        migrations.AddField(
            model_name='client',
            name='bank_BIC',
            field=models.CharField(max_length=200, null=True, verbose_name='BIC', blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='bank_IBAN',
            field=models.CharField(max_length=200, null=True, verbose_name='IBAN', blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='bookshop_number',
            field=models.CharField(max_length=200, null=True, verbose_name="The bookshop's official number.", blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='checks_address',
            field=models.CharField(max_length=200, null=True, verbose_name='Checks address (if different than address)', blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='checks_order',
            field=models.CharField(max_length=200, null=True, verbose_name='Checks order (if different from name)', blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='company_number',
            field=models.CharField(max_length=200, null=True, verbose_name="The company's registered number (State's industry chamber)", blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='is_vat_exonerated',
            field=models.BooleanField(default=False, verbose_name='Exonerated of VAT?'),
        ),
        migrations.AddField(
            model_name='client',
            name='presentation_comment',
            field=models.TextField(max_length=10000, null=True, verbose_name='A comment to add after the default presentation, which contains name, address, contact and official number. Can be useful when the bookshop is officially administrated by another entity. This appears on bills.', blank=True),
        ),
    ]
