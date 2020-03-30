# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import uuid

# Squashed 2020-03-30.
# during upgrade to Django 20.

# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# search.migrations.0006_auto_20151201_1715 (compute card.quantity: uneeded now)
# search.migrations.0007_ean_to_cleaned_isbn_20151203_1106 (cleanup isbn: uneeded now)
# search.migrations.0077_auto_20200304_1559 : create Coupons (not a good idea inside migration)

class Migration(migrations.Migration):

    replaces = [('search', '0001_squashed_0015_auto_20151027_1749'), ('search', '0002_auto_20151123_1422'), ('search', '0003_auto_20151127_1449'), ('search', '0004_card_quantity'), ('search', '0005_auto_20151201_1700'), ('search', '0006_auto_20151201_1715'), ('search', '0007_ean_to_cleaned_isbn_20151203_1106'), ('search', '0008_remove_card_ean'), ('search', '0009_auto_20160113_1539'), ('search', '0010_sell_canceled'), ('search', '0011_auto_20160204_1540'), ('search', '0012_distributor_email'), ('search', '0013_auto_20160314_0755'), ('search', '0014_inventory_basket'), ('search', '0015_card_in_stock'), ('search', '0016_auto_20160404_1357'), ('search', '0017_inventory_shelf'), ('search', '0018_auto_20160412_1451'), ('search', '0019_auto_20160419_1448'), ('search', '0020_auto_20160508_1847'), ('search', '0021_auto_20160514_1017'), ('search', '0022_inventory_publisher'), ('search', '0023_inventory_closed'), ('search', '0024_auto_20160715_1640'), ('search', '0025_inventory_applied'), ('search', '0026_auto_20160718_2205'), ('search', '0027_preferences_vat_book'), ('search', '0028_auto_20160926_0809'), ('search', '0029_preferences_language'), ('search', '0030_card_date_publication'), ('search', '0031_barcode64'), ('search', '0032_auto_20170120_1706'), ('search', '0033_preferences_asso_name'), ('search', '0034_card_fmt'), ('search', '0035_auto_20170315_2332'), ('search', '0036_auto_20170317_2229'), ('search', '0037_command_inventory'), ('search', '0038_auto_20170317_2258'), ('search', '0039_auto_20170317_2308'), ('search', '0040_auto_20170319_1130'), ('search', '0041_card_imgfile'), ('search', '0042_auto_20171212_2232'), ('search', '0043_remove_basket_descrition'), ('search', '0044_remove_card_quantity'), ('search', '0045_auto_20180517_1604'), ('search', '0046_auto_20180628_1559'), ('search', '0047_deposit_comment'), ('search', '0048_basket_distributor'), ('search', '0049_auto_20181028_1503'), ('search', '0050_auto_20181130_1555'), ('search', '0051_outmovement_created'), ('search', '0052_auto_20181130_1855'), ('search', '0053_auto_20181201_1731'), ('search', '0054_auto_20181207_2143'), ('search', '0055_outmovementcopies_created'), ('search', '0056_auto_20190410_1642'), ('search', '0057_auto_20190410_1702'), ('search', '0058_client'), ('search', '0059_auto_20190921_0931'), ('search', '0060_auto_20191019_1614'), ('search', '0061_auto_20191019_1614'), ('search', '0062_card_quantity'), ('search', '0063_auto_20191112_1835'), ('search', '0064_restocking_restockingcopies'), ('search', '0065_auto_20200104_1347'), ('search', '0066_basket_archived_date'), ('search', '0067_auto_20200128_2236'), ('search', '0068_auto_20200131_1620'), ('search', '0069_auto_20200205_1414'), ('search', '0070_preferences_others'), ('search', '0071_distributor_gln'), ('search', '0072_remove_card_price_sold'), ('search', '0073_card_currency'), ('search', '0074_auto_20200226_1828'), ('search', '0075_auto_20200227_1645'), ('search', '0076_auto_20200304_1557'), ('search', '0077_auto_20200304_1559'), ('search', '0078_auto_20200318_1526')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('surname', models.CharField(max_length=200, null=True, blank=True)),
                ('enterprise', models.CharField(max_length=200, null=True, blank=True)),
                ('responsability', models.CharField(max_length=200, null=True, blank=True)),
                ('cellphone', models.CharField(max_length=200, null=True, blank=True)),
                ('tel_private', models.CharField(max_length=200, null=True, blank=True)),
                ('tel_office', models.CharField(max_length=200, null=True, blank=True)),
                ('website', models.CharField(max_length=200, null=True, blank=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('email_pro', models.EmailField(max_length=75, null=True, blank=True)),
                ('address1', models.CharField(max_length=200, null=True, blank=True)),
                ('address2', models.CharField(max_length=200, null=True, blank=True)),
                ('zip_code', models.CharField(max_length=200, null=True, blank=True)),
                ('city', models.CharField(max_length=200, null=True, blank=True)),
                ('state', models.CharField(max_length=200, null=True, blank=True)),
                ('country', models.CharField(max_length=200, null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('date_resolution', models.DateField(null=True, blank=True)),
                ('resolution_auto', models.BooleanField(default=False)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('descrition', models.CharField(max_length=200, null=True, blank=True)),
                ('comment', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='BasketCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('basket', models.ForeignKey(to='search.Basket', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='BasketType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('ean', models.CharField(max_length=99, null=True, blank=True)),
                ('isbn', models.CharField(max_length=99, null=True, blank=True)),
                ('has_isbn', models.NullBooleanField(default=True)),
                ('sortkey', models.TextField(verbose_name=b'Authors', blank=True)),
                ('price', models.FloatField(null=True, blank=True)),
                ('price_sold', models.FloatField(null=True, blank=True)),
                ('year_published', models.DateField(null=True, blank=True)),
                ('img', models.URLField(null=True, blank=True)),
                ('data_source', models.CharField(max_length=200, null=True, blank=True)),
                ('details_url', models.URLField(null=True, blank=True)),
                ('comment', models.TextField(blank=True)),
                ('authors', models.ManyToManyField(to='search.Author')),
            ],
            options={
                'ordering': ('sortkey', 'year_published', 'title'),
            },
        ),
        migrations.CreateModel(
            name='CardType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('ordered', models.IntegerField(null=True, blank=True)),
                ('parent', models.ForeignKey(blank=True, to='search.Collection', null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Deposit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('deposit_type', models.CharField(default=(b'D\xc3\xa9p\xc3\xb4t de libraire', ((b'lib', b'd\xc3\xa9p\xc3\xb4t de libraire'), (b'fix', b'd\xc3\xa9p\xc3\xb4t fixe'))), max_length=200, choices=[(b'D\xc3\xa9p\xc3\xb4t de libraire', ((b'lib', b'd\xc3\xa9p\xc3\xb4t de libraire'), (b'fix', b'd\xc3\xa9p\xc3\xb4t fixe'))), (b'D\xc3\xa9p\xc3\xb4t de distributeur', ((b'dist', b'd\xc3\xa9p\xc3\xb4t de distributeur'),))])),
                ('initial_nb_copies', models.IntegerField(default=0, null=True, verbose_name=b"Nombre initial d'exemplaires pour ce d\xc3\xa9p\xc3\xb4t:", blank=True)),
                ('minimal_nb_copies', models.IntegerField(default=0, null=True, verbose_name=b"Nombre minimun d'exemplaires", blank=True)),
                ('auto_command', models.BooleanField(default=True, verbose_name=b'Automatiquement marquer les fiches \xc3\xa0 commander')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='DepositCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.IntegerField(default=0)),
                ('threshold', models.IntegerField(default=1, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('deposit', models.ForeignKey(to='search.Deposit', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='DepositState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('closed', models.DateField(default=None, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DepositStateCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb_current', models.IntegerField(default=1)),
                ('nb_to_return', models.IntegerField(default=1)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('deposit_state', models.ForeignKey(to='search.DepositState', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Distributor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('discount', models.IntegerField(default=0, null=True, blank=True)),
                ('stars', models.IntegerField(default=0, null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('inventory', models.ForeignKey(to='search.Inventory', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('date_deletion', models.DateField(null=True, blank=True)),
                ('is_stand', models.BooleanField(default=False)),
                ('can_sell', models.BooleanField(default=True)),
                ('inventory_ongoing', models.BooleanField(default=False)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='PlaceCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('place', models.ForeignKey(to='search.Place', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default_place', models.OneToOneField(to='search.Place', on_delete=models.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('isbn', models.CharField(max_length=200, null=True, blank=True)),
                ('address', models.TextField(null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Sell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField()),
                ('payment', models.CharField(default=(0, b'cash'), max_length=200, null=True, blank=True, choices=[(0, b'cash'), (1, b'check'), (2, b'credit card'), (3, b'gift'), (4, b'other')])),
            ],
        ),
        migrations.CreateModel(
            name='SoldCards',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('price_sold', models.FloatField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.SET_NULL)),
                ('sell', models.ForeignKey(to='search.Sell', on_delete=models.CASCADE)),
                ('price_init', models.FloatField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='sell',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.SoldCards', blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.InventoryCopies', blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='depositstatecopies',
            name='sells',
            field=models.ManyToManyField(to='search.Sell'),
        ),
        migrations.AddField(
            model_name='depositstate',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.DepositStateCopies', blank=True),
        ),
        migrations.AddField(
            model_name='depositstate',
            name='deposit',
            field=models.ForeignKey(to='search.Deposit', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='deposit',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.DepositCopies', blank=True),
        ),
        migrations.AddField(
            model_name='deposit',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='card',
            name='card_type',
            field=models.ForeignKey(blank=True, to='search.CardType', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='card',
            name='collection',
            field=models.ForeignKey(blank=True, to='search.Collection', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='card',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to='search.Place', null=True, through='search.PlaceCopies', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to='search.Publisher', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='basketcopies',
            name='card',
            field=models.ForeignKey(to='search.Card', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='basket',
            name='basket_type',
            field=models.ForeignKey(blank=True, to='search.BasketType', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='basket',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.BasketCopies', blank=True),
        ),
        migrations.AddField(
            model_name='alert',
            name='card',
            field=models.ForeignKey(to='search.Card', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='alert',
            name='deposits',
            field=models.ManyToManyField(to='search.Deposit', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='deposit',
            name='dest_place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='deposit',
            name='due_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('typ', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='EntryCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.SET_NULL)),
                ('entry', models.ForeignKey(to='search.Entry', on_delete=models.CASCADE)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('price_init', models.FloatField(null=True, blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='entry',
            name='typ',
            field=models.IntegerField(default=1, choices=[(1, b'purchase'), (2, b'deposit'), (3, b'gift')]),
        ),
        migrations.CreateModel(
            name='InternalMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.IntegerField()),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True, on_delete=models.SET_NULL)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('dest', models.ForeignKey(related_name=b'mvt_dest', to='search.Place', on_delete=models.CASCADE)),
                ('origin', models.ForeignKey(related_name=b'mvt_origin', to='search.Place', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(0, b'cash'), (1, b'check'), (2, b'credit card'), (3, b'gift'), (4, b'other')]),
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('due_date', models.DateTimeField()),
                ('total_no_taxes', models.FloatField(null=True, blank=True)),
                ('shipping', models.FloatField(null=True, blank=True)),
                ('total', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='BillCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('bill', models.ForeignKey(to='search.Bill', on_delete=models.CASCADE)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='bill',
            name='copies',
            field=models.ManyToManyField(to='search.Card', null=True, through='search.BillCopies', blank=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='distributor',
            field=models.ForeignKey(to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.RenameField(
            model_name='bill',
            old_name='nb',
            new_name='ref',
        ),
        migrations.AlterField(
            model_name='bill',
            name='due_date',
            field=models.DateField(),
        ),
        migrations.AddField(
            model_name='card',
            name='summary',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='card',
            name='category',
            field=models.ForeignKey(blank=True, to='search.Category', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='depositstate',
            name='closed',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.RemoveField(
            model_name='deposit',
            name='initial_nb_copies',
        ),
        migrations.AlterField(
            model_name='depositstatecopies',
            name='nb_current',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='depositstatecopies',
            name='nb_to_return',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
        # migrations.RunPython(
            # code=search.migrations.0006_auto_20151201_1715.set_card_quantity,
        # ),
        # migrations.RunPython(
            # code=search.migrations.0007_ean_to_cleaned_isbn_20151203_1106.set_isbn,
        # ),
        migrations.RemoveField(
            model_name='card',
            name='ean',
        ),
        migrations.AddField(
            model_name='entry',
            name='reason',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='typ',
            field=models.IntegerField(default=1, choices=[(1, b'purchase'), (2, b'deposit'), (3, b'gift'), (4, b'sell canceled')]),
        ),
        migrations.AddField(
            model_name='sell',
            name='canceled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=1, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='email_pro',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='price',
            field=models.FloatField(default=0.0, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='basket',
            field=models.ForeignKey(blank=True, to='search.Basket', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='card',
            name='in_stock',
            field=models.BooleanField(default=False),
        ),
        migrations.RenameModel(
            old_name='Category',
            new_name='Shelf',
        ),
        migrations.RenameField(
            model_name='card',
            old_name='category',
            new_name='shelf',
        ),
        migrations.AddField(
            model_name='inventory',
            name='shelf',
            field=models.ForeignKey(blank=True, to='search.Shelf', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='soldcards',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 12, 14, 51, 5, 901571, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='soldcards',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 12, 14, 51, 19, 634229, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='basket',
            name='comment',
            field=models.CharField(max_length=10000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='deposits',
            field=models.ManyToManyField(to='search.Deposit', blank=True),
        ),
        migrations.AlterField(
            model_name='basket',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BasketCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BillCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to='search.Place', through='search.PlaceCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to='search.Publisher', blank=True),
        ),
        migrations.RemoveField(
            model_name='deposit',
            name='copies',
        ),
        migrations.AlterField(
            model_name='deposit',
            name='deposit_type',
            field=models.CharField(default=b'fix', max_length=200, choices=[(b'D\xc3\xa9p\xc3\xb4t de libraire', ((b'lib', b'd\xc3\xa9p\xc3\xb4t de libraire'), (b'fix', b'd\xc3\xa9p\xc3\xb4t fixe'))), (b'D\xc3\xa9p\xc3\xb4t de distributeur', ((b'dist', b'd\xc3\xa9p\xc3\xb4t de distributeur'),))]),
        ),
        migrations.AlterField(
            model_name='depositstate',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.DepositStateCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='sell',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.SoldCards', blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='inventory',
            name='closed',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='applied',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='preferences',
            name='vat_book',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='preferences',
            name='language',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='date_publication',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.CreateModel(
            name='Barcode64',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('ean', models.CharField(max_length=200, null=True, blank=True)),
                ('barcodebase64', models.CharField(max_length=10000, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('date_received', models.DateField(null=True, blank=True)),
                ('date_bill_received', models.DateField(null=True, blank=True)),
                ('date_payment_sent', models.DateField(null=True, blank=True)),
                ('date_paid', models.DateField(null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommandCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('command', models.ForeignKey(to='search.Command', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='command',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.CommandCopies', blank=True),
        ),
        migrations.AddField(
            model_name='command',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='command',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='preferences',
            name='asso_name',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='fmt',
            field=models.TextField(null=True, blank=True),
        ),
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
        migrations.AddField(
            model_name='command',
            name='inventory',
            field=models.OneToOneField(null=True, blank=True, to='search.InventoryCommand', on_delete=models.CASCADE),
        ),
        migrations.CreateModel(
            name='InventoryCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('closed', models.DateTimeField(null=True, blank=True)),
                ('applied', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InventoryCommandCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('inventory', models.ForeignKey(to='search.InventoryCommand', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='inventorycommand',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCommandCopies', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='imgfile',
            field=models.ImageField(null=True, upload_to='covers', blank=True),
        ),
        migrations.RenameField(
            model_name='card',
            old_name='img',
            new_name='cover',
        ),
        migrations.RemoveField(
            model_name='basket',
            name='descrition',
        ),
        migrations.RemoveField(
            model_name='card',
            name='quantity',
        ),
        migrations.AddField(
            model_name='sell',
            name='deposit',
            field=models.ForeignKey(blank=True, to='search.Deposit', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='sell',
            name='place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True, on_delete=models.SET_NULL),
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
        migrations.AlterField(
            model_name='shelf',
            name='name',
            field=models.CharField(unique=True, max_length=200),
        ),
        migrations.AddField(
            model_name='deposit',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='basket',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.RemoveField(
            model_name='depositcopies',
            name='card',
        ),
        migrations.RemoveField(
            model_name='depositcopies',
            name='deposit',
        ),
        migrations.AddField(
            model_name='depositstatecopies',
            name='nb_initial',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='DepositCopies',
        ),
        migrations.CreateModel(
            name='OutMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typ', models.IntegerField(choices=[(1, b'sell'), (2, b'return'), (3, b'loss'), (4, b'gift')])),
                ('reason', models.CharField(max_length=200, null=True, blank=True)),
                ('nb', models.IntegerField()),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True, on_delete=models.SET_NULL)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='OutMovementCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=1, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.SET_NULL)),
                ('movement', models.ForeignKey(to='search.OutMovement', on_delete=models.CASCADE)),
                ('created', models.DateTimeField(default=datetime.datetime(2018, 12, 7, 21, 46, 7, 113295, tzinfo=utc), auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='outmovement',
            name='copies',
            field=models.ManyToManyField(related_name='copies', through='search.OutMovementCopies', to='search.Card', blank=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='origin',
            field=models.ForeignKey(blank=True, to='search.Place', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='recipient',
            field=models.ForeignKey(blank=True, to='search.Client', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2018, 12, 7, 21, 43, 23, 50788, tzinfo=utc), auto_now_add=True),
        ),
        migrations.RenameField(
            model_name='outmovement',
            old_name='reason',
            new_name='comment',
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='card',
            field=models.ForeignKey(blank=True, to='search.Card', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='outmovement',
            name='nb',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ('city',)},
        ),
        migrations.RenameField(
            model_name='address',
            old_name='tel_private',
            new_name='telephone',
        ),
        migrations.RemoveField(
            model_name='address',
            name='email_pro',
        ),
        migrations.RemoveField(
            model_name='address',
            name='enterprise',
        ),
        migrations.RemoveField(
            model_name='address',
            name='name',
        ),
        migrations.RemoveField(
            model_name='address',
            name='surname',
        ),
        migrations.RemoveField(
            model_name='address',
            name='tel_office',
        ),
        migrations.RenameModel(
            old_name='Address',
            new_name='Contact',
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('firstname', models.CharField(max_length=200)),
                ('contact', models.ForeignKey(blank=True, to='search.Contact', null=True, on_delete=models.SET_NULL)),
            ],
        ),
        migrations.AddField(
            model_name='inventory',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='inventorycommand',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='card',
            name='authors',
            field=models.ManyToManyField(to='search.Author', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='authors',
            field=models.ManyToManyField(to='search.Author', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, blank=True),
        ),
        migrations.CreateModel(
            name='Restocking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='RestockingCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(blank=True, to='search.Card', null=True, on_delete=models.SET_NULL)),
                ('restocking', models.ForeignKey(to='search.Restocking', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='basket',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='basket',
            name='archived_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ('name',), 'verbose_name': 'author'},
        ),
        migrations.AlterModelOptions(
            name='basket',
            options={'ordering': ('name',), 'verbose_name': 'Basket'},
        ),
        migrations.AlterModelOptions(
            name='card',
            options={'ordering': ('sortkey', 'year_published', 'title'), 'verbose_name': 'card'},
        ),
        migrations.AlterModelOptions(
            name='cardtype',
            options={'verbose_name': 'Card type'},
        ),
        migrations.AlterModelOptions(
            name='collection',
            options={'ordering': ('name',), 'verbose_name': 'collection'},
        ),
        migrations.AlterModelOptions(
            name='command',
            options={'verbose_name': 'Command'},
        ),
        migrations.AlterModelOptions(
            name='deposit',
            options={'ordering': ('name',), 'verbose_name': 'deposit'},
        ),
        migrations.AlterModelOptions(
            name='distributor',
            options={'ordering': ('name',), 'verbose_name': 'distributor'},
        ),
        migrations.AlterModelOptions(
            name='inventory',
            options={'verbose_name': 'Inventory', 'verbose_name_plural': 'Inventories'},
        ),
        migrations.AlterModelOptions(
            name='place',
            options={'ordering': ('name',), 'verbose_name': 'place', 'verbose_name_plural': 'places'},
        ),
        migrations.AlterModelOptions(
            name='preferences',
            options={'verbose_name': 'Preferences'},
        ),
        migrations.AlterModelOptions(
            name='publisher',
            options={'ordering': ('name',), 'verbose_name': 'publisher'},
        ),
        migrations.AlterModelOptions(
            name='sell',
            options={'verbose_name': 'sell'},
        ),
        migrations.AlterModelOptions(
            name='shelf',
            options={'verbose_name': 'shelf', 'verbose_name_plural': 'shelves'},
        ),
        migrations.AlterField(
            model_name='author',
            name='name',
            field=models.CharField(unique=True, max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='basket',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='archived'),
        ),
        migrations.AlterField(
            model_name='basket',
            name='archived_date',
            field=models.DateField(null=True, verbose_name='date archived', blank=True),
        ),
        migrations.AlterField(
            model_name='basket',
            name='basket_type',
            field=models.ForeignKey(verbose_name='basket type', blank=True, to='search.BasketType', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='basket',
            name='comment',
            field=models.CharField(max_length=10000, null=True, verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='basket',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='basket',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='card',
            name='authors',
            field=models.ManyToManyField(to='search.Author', verbose_name='authors', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='card_type',
            field=models.ForeignKey(verbose_name='card type', blank=True, to='search.CardType', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='card',
            name='collection',
            field=models.ForeignKey(verbose_name='collection', blank=True, to='search.Collection', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='card',
            name='comment',
            field=models.TextField(verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='cover',
            field=models.URLField(null=True, verbose_name='cover', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='data_source',
            field=models.CharField(max_length=200, null=True, verbose_name='data source', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='date_publication',
            field=models.DateField(null=True, verbose_name='date publication', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='details_url',
            field=models.URLField(null=True, verbose_name='details url', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='card',
            name='has_isbn',
            field=models.NullBooleanField(default=True, verbose_name='has isbn'),
        ),
        migrations.AlterField(
            model_name='card',
            name='in_stock',
            field=models.BooleanField(default=False, verbose_name='in stock'),
        ),
        migrations.AlterField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to='search.Place', verbose_name='places', through='search.PlaceCopies', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='price',
            field=models.FloatField(default=0.0, null=True, verbose_name='price', blank=True),
        ),
        migrations.RemoveField(
            model_name='card',
            name='price_sold',
        ),
        migrations.AlterField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to='search.Publisher', verbose_name='publishers', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(verbose_name='quantity', null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='shelf',
            field=models.ForeignKey(verbose_name='shelf', blank=True, to='search.Shelf', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='card',
            name='summary',
            field=models.TextField(null=True, verbose_name='summary', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=1, null=True, verbose_name='threshold', blank=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='title',
            field=models.CharField(max_length=200, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='card',
            name='year_published',
            field=models.DateField(null=True, verbose_name='year published', blank=True),
        ),
        migrations.AlterField(
            model_name='cardtype',
            name='name',
            field=models.CharField(max_length=100, null=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='ordered',
            field=models.IntegerField(null=True, verbose_name='ordered', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='comment',
            field=models.TextField(null=True, verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_bill_received',
            field=models.DateTimeField(null=True, verbose_name='date bill received', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_paid',
            field=models.DateTimeField(null=True, verbose_name='date paid', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_payment_sent',
            field=models.DateTimeField(null=True, verbose_name='date payment sent', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='date_received',
            field=models.DateTimeField(null=True, verbose_name='date received', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='command',
            name='inventory',
            field=models.OneToOneField(null=True, blank=True, to='search.InventoryCommand', verbose_name='inventory', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='command',
            name='name',
            field=models.CharField(max_length=200, null=True, verbose_name='name', blank=True),
        ),
        migrations.AlterField(
            model_name='command',
            name='publisher',
            field=models.ForeignKey(verbose_name='publisher', blank=True, to='search.Publisher', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='auto_command',
            field=models.BooleanField(default=True, verbose_name='Automatically mark the cards to command'),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='comment',
            field=models.TextField(null=True, verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='deposit_type',
            field=models.CharField(default=b'fix', max_length=200, verbose_name='deposit type', choices=[(b'D\xc3\xa9p\xc3\xb4t de libraire', ((b'lib', b'd\xc3\xa9p\xc3\xb4t de libraire'), (b'fix', b'd\xc3\xa9p\xc3\xb4t fixe'))), (b'D\xc3\xa9p\xc3\xb4t de distributeur', ((b'dist', b'd\xc3\xa9p\xc3\xb4t de distributeur'),))]),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='dest_place',
            field=models.ForeignKey(verbose_name='destination place', blank=True, to='search.Place', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='due_date',
            field=models.DateField(null=True, verbose_name='due date', blank=True),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='minimal_nb_copies',
            field=models.IntegerField(default=0, null=True, verbose_name='Minimun number of copies to have in stock', blank=True),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='name',
            field=models.CharField(unique=True, max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='discount',
            field=models.FloatField(default=0, verbose_name='discount', blank=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='basket',
            field=models.ForeignKey(verbose_name='basket', blank=True, to='search.Basket', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='place',
            field=models.ForeignKey(verbose_name='place', blank=True, to='search.Place', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='publisher',
            field=models.ForeignKey(verbose_name='publisher', blank=True, to='search.Publisher', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='shelf',
            field=models.ForeignKey(verbose_name='shelf', blank=True, to='search.Shelf', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='place',
            name='can_sell',
            field=models.BooleanField(default=True, verbose_name='can sell?'),
        ),
        migrations.AlterField(
            model_name='place',
            name='comment',
            field=models.TextField(null=True, verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='place',
            name='date_creation',
            field=models.DateField(auto_now_add=True, verbose_name='creation date'),
        ),
        migrations.AlterField(
            model_name='place',
            name='date_deletion',
            field=models.DateField(null=True, verbose_name='deletion date', blank=True),
        ),
        migrations.AlterField(
            model_name='place',
            name='inventory_ongoing',
            field=models.BooleanField(default=False, verbose_name='inventory ongoing'),
        ),
        migrations.AlterField(
            model_name='place',
            name='is_stand',
            field=models.BooleanField(default=False, verbose_name='is stand?'),
        ),
        migrations.AlterField(
            model_name='place',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='asso_name',
            field=models.CharField(max_length=200, null=True, verbose_name='bookshop name', blank=True),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='default_place',
            field=models.OneToOneField(verbose_name='default place', to='search.Place', on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='language',
            field=models.CharField(max_length=200, null=True, verbose_name='language', blank=True),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='vat_book',
            field=models.FloatField(null=True, verbose_name='book vat', blank=True),
        ),
        migrations.AlterField(
            model_name='publisher',
            name='address',
            field=models.TextField(null=True, verbose_name='address', blank=True),
        ),
        migrations.AlterField(
            model_name='publisher',
            name='comment',
            field=models.TextField(null=True, verbose_name='comment', blank=True),
        ),
        migrations.AlterField(
            model_name='publisher',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='sell',
            name='canceled',
            field=models.BooleanField(default=False, verbose_name='canceled'),
        ),
        migrations.AlterField(
            model_name='sell',
            name='deposit',
            field=models.ForeignKey(verbose_name='deposit', blank=True, to='search.Deposit', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='sell',
            name='payment',
            field=models.CharField(default=(0, 'cash'), choices=[(0, 'cash'), (1, 'check'), (2, 'credit card'), (3, 'gift'), (5, 'transfer'), (4, 'other')], max_length=200, blank=True, null=True, verbose_name='payment'),
        ),
        migrations.AlterField(
            model_name='sell',
            name='place',
            field=models.ForeignKey(verbose_name='place', blank=True, to='search.Place', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='shelf',
            name='name',
            field=models.CharField(unique=True, max_length=200, verbose_name='name'),
        ),
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
        migrations.AlterField(
            model_name='card',
            name='threshold',
            field=models.IntegerField(default=0, null=True, verbose_name='threshold', blank=True),
        ),
        migrations.AddField(
            model_name='preferences',
            name='others',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='distributor',
            name='gln',
            field=models.CharField(max_length=200, null=True, verbose_name='GLN', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='currency',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='currency', choices=[(b'euro', b'\xe2\x82\xac'), (b'chf', b'CHF')]),
        ),
        migrations.AlterField(
            model_name='card',
            name='cover',
            field=models.URLField(null=True, verbose_name='cover url', blank=True),
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
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ('city',)},
        ),
        migrations.RemoveField(
            model_name='client',
            name='contact',
        ),
        migrations.AddField(
            model_name='client',
            name='address1',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='address2',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='city',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='country',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='mobilephone',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='state',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='telephone',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='website',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='client',
            name='zip_code',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='firstname',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.DeleteModel(
            name='Contact',
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('exhausted', models.BooleanField(default=False, editable=False)),
                ('comment', models.CharField(max_length=200, null=True, blank=True)),
                ('client', models.ForeignKey(to='search.Client', on_delete=models.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CouponGeneric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('amount', models.FloatField(verbose_name='Amount')),
                ('active', models.BooleanField(default=True, help_text='Can we currently generate coupons of this amount to clients?', max_length=200, verbose_name='Active')),
                ('code', models.CharField(max_length=200, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='coupon',
            name='generic',
            field=models.ForeignKey(to='search.CouponGeneric', null=True, on_delete=models.SET_NULL),
        ),
        # migrations.RunPython(
            # code=search.migrations.0077_auto_20200304_1559.create_coupons,
            # reverse_code=search.migrations.0077_auto_20200304_1559.backwards,
        # ),
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
