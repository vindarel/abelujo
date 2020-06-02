# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
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
                ('name', models.CharField(unique=True, max_length=200, verbose_name='name')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'author',
            },
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
            name='Basket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('comment', models.CharField(max_length=10000, null=True, verbose_name='comment', blank=True)),
                ('archived', models.BooleanField(default=False, verbose_name='archived')),
                ('archived_date', models.DateField(null=True, verbose_name='date archived', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Basket',
            },
        ),
        migrations.CreateModel(
            name='BasketCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('basket', models.ForeignKey(to='search.Basket')),
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
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('ref', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('due_date', models.DateField()),
                ('total_no_taxes', models.FloatField(null=True, blank=True)),
                ('shipping', models.FloatField(null=True, blank=True)),
                ('total', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('bill', models.ForeignKey(to='search.Bill')),
            ],
        ),
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
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('has_isbn', models.NullBooleanField(default=True, verbose_name='has isbn')),
                ('isbn', models.CharField(max_length=99, null=True, blank=True)),
                ('sortkey', models.TextField(verbose_name='Authors', blank=True)),
                ('price', models.FloatField(default=0.0, null=True, verbose_name='price', blank=True)),
                ('currency', models.CharField(blank=True, max_length=10, null=True, verbose_name='currency', choices=[(b'euro', b'\xe2\x82\xac'), (b'chf', b'CHF')])),
                ('in_stock', models.BooleanField(default=False, verbose_name='in stock')),
                ('quantity', models.IntegerField(verbose_name='quantity', null=True, editable=False, blank=True)),
                ('threshold', models.IntegerField(default=0, null=True, verbose_name='Minimal quantity before command', blank=True)),
                ('year_published', models.DateField(null=True, verbose_name='year published', blank=True)),
                ('cover', models.URLField(null=True, verbose_name='cover url', blank=True)),
                ('imgfile', models.ImageField(null=True, upload_to='covers', blank=True)),
                ('data_source', models.CharField(verbose_name='data source', max_length=200, null=True, editable=False, blank=True)),
                ('details_url', models.URLField(verbose_name='details url', null=True, editable=False, blank=True)),
                ('date_publication', models.DateField(null=True, verbose_name='date publication', blank=True)),
                ('summary', models.TextField(null=True, verbose_name='summary', blank=True)),
                ('fmt', models.TextField(verbose_name='Book format (pocket, etc)', null=True, editable=False, blank=True)),
                ('comment', models.TextField(verbose_name='comment', blank=True)),
                ('authors', models.ManyToManyField(to='search.Author', verbose_name='authors', blank=True)),
            ],
            options={
                'ordering': ('sortkey', 'year_published', 'title'),
                'verbose_name': 'card',
            },
        ),
        migrations.CreateModel(
            name='CardType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Card type',
            },
        ),
        migrations.CreateModel(
            name='Client',
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
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('ordered', models.IntegerField(null=True, verbose_name='ordered', blank=True)),
                ('parent', models.ForeignKey(blank=True, to='search.Collection', null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'collection',
            },
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, null=True, verbose_name='name', blank=True)),
                ('date_received', models.DateTimeField(null=True, verbose_name='date received', blank=True)),
                ('date_bill_received', models.DateTimeField(null=True, verbose_name='date bill received', blank=True)),
                ('date_payment_sent', models.DateTimeField(null=True, verbose_name='date payment sent', blank=True)),
                ('date_paid', models.DateTimeField(null=True, verbose_name='date paid', blank=True)),
                ('comment', models.TextField(null=True, verbose_name='comment', blank=True)),
            ],
            options={
                'verbose_name': 'Command',
            },
        ),
        migrations.CreateModel(
            name='CommandCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('command', models.ForeignKey(to='search.Command')),
            ],
            options={
                'abstract': False,
            },
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
                ('client', models.ForeignKey(to='search.Client')),
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
        migrations.CreateModel(
            name='Deposit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200, verbose_name='name')),
                ('deposit_type', models.CharField(default='fix', max_length=200, verbose_name='deposit type', choices=[('D\xe9p\xf4t de libraire', (('lib', 'd\xe9p\xf4t de libraire'), ('fix', 'd\xe9p\xf4t fixe'))), ('D\xe9p\xf4t de distributeur', (('dist', 'd\xe9p\xf4t de distributeur'),))])),
                ('due_date', models.DateField(null=True, verbose_name='due date', blank=True)),
                ('minimal_nb_copies', models.IntegerField(default=0, null=True, verbose_name='Minimun number of copies to have in stock', blank=True)),
                ('auto_command', models.BooleanField(default=True, verbose_name='Automatically mark the cards to command')),
                ('comment', models.TextField(null=True, verbose_name='comment', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'deposit',
            },
        ),
        migrations.CreateModel(
            name='DepositState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('closed', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DepositStateCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb_initial', models.IntegerField(default=0)),
                ('nb_current', models.IntegerField(default=0)),
                ('nb_to_return', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('deposit_state', models.ForeignKey(to='search.DepositState')),
            ],
        ),
        migrations.CreateModel(
            name='Distributor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('gln', models.CharField(max_length=200, null=True, verbose_name='GLN', blank=True)),
                ('discount', models.FloatField(default=0, verbose_name='discount', blank=True)),
                ('stars', models.IntegerField(default=0, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'distributor',
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('typ', models.IntegerField(default=1, choices=[(1, 'purchase'), (2, 'deposit'), (3, 'gift'), (4, 'sell canceled')])),
                ('payment', models.CharField(blank=True, max_length=200, null=True, choices=[(1, 'cash'), (2, 'check'), (3, 'credit card'), (4, 'gift'), (5, 'transfer'), (6, 'other')])),
                ('reason', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntryCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('price_init', models.FloatField(default=0.0, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('entry', models.ForeignKey(to='search.Entry')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InternalMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.IntegerField()),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True)),
                ('card', models.ForeignKey(to='search.Card')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('closed', models.DateTimeField(null=True, blank=True)),
                ('archived', models.BooleanField(default=False)),
                ('applied', models.BooleanField(default=False)),
                ('basket', models.ForeignKey(verbose_name='basket', blank=True, to='search.Basket', null=True)),
            ],
            options={
                'verbose_name': 'Inventory',
                'verbose_name_plural': 'Inventories',
            },
        ),
        migrations.CreateModel(
            name='InventoryCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('closed', models.DateTimeField(null=True, blank=True)),
                ('archived', models.BooleanField(default=False)),
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
                ('card', models.ForeignKey(to='search.Card')),
                ('inventory', models.ForeignKey(to='search.InventoryCommand')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InventoryCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('inventory', models.ForeignKey(to='search.Inventory')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OutMovement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('typ', models.IntegerField(choices=[(1, 'sell'), (2, 'return'), (3, 'loss'), (4, 'gift')])),
                ('comment', models.CharField(max_length=200, null=True, blank=True)),
                ('nb', models.IntegerField(null=True, blank=True)),
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True)),
                ('card', models.ForeignKey(blank=True, to='search.Card', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='OutMovementCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('quantity', models.IntegerField(default=1, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('movement', models.ForeignKey(to='search.OutMovement')),
            ],
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('date_creation', models.DateField(auto_now_add=True, verbose_name='creation date')),
                ('date_deletion', models.DateField(null=True, verbose_name='deletion date', blank=True)),
                ('is_stand', models.BooleanField(default=False, verbose_name='is stand?')),
                ('can_sell', models.BooleanField(default=True, verbose_name='can sell?')),
                ('inventory_ongoing', models.BooleanField(default=False, verbose_name='inventory ongoing')),
                ('comment', models.TextField(null=True, verbose_name='comment', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'place',
                'verbose_name_plural': 'places',
            },
        ),
        migrations.CreateModel(
            name='PlaceCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('place', models.ForeignKey(to='search.Place')),
            ],
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asso_name', models.CharField(max_length=200, null=True, verbose_name='bookshop name', blank=True)),
                ('vat_book', models.FloatField(null=True, verbose_name='book vat', blank=True)),
                ('language', models.CharField(max_length=200, null=True, verbose_name='language', blank=True)),
                ('others', models.TextField(null=True, blank=True)),
                ('default_place', models.OneToOneField(verbose_name='default place', to='search.Place')),
            ],
            options={
                'verbose_name': 'Preferences',
            },
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('isbn', models.CharField(max_length=200, null=True, blank=True)),
                ('address', models.TextField(null=True, verbose_name='address', blank=True)),
                ('comment', models.TextField(null=True, verbose_name='comment', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'publisher',
            },
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
                ('card', models.ForeignKey(blank=True, to='search.Card', null=True)),
                ('restocking', models.ForeignKey(to='search.Restocking')),
            ],
        ),
        migrations.CreateModel(
            name='Sell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField()),
                ('payment', models.CharField(default=(1, 'cash'), choices=[(1, 'cash'), (2, 'check'), (3, 'credit card'), (4, 'gift'), (5, 'transfer'), (6, 'other')], max_length=200, blank=True, null=True, verbose_name='payment')),
                ('canceled', models.BooleanField(default=False, verbose_name='canceled')),
            ],
            options={
                'verbose_name': 'sell',
            },
        ),
        migrations.CreateModel(
            name='Shelf',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, verbose_name='name')),
            ],
            options={
                'verbose_name': 'shelf',
                'verbose_name_plural': 'shelves',
            },
        ),
        migrations.CreateModel(
            name='SoldCards',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(default=0)),
                ('price_init', models.FloatField(default=0)),
                ('price_sold', models.FloatField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('sell', models.ForeignKey(to='search.Sell')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='sell',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.SoldCards', blank=True),
        ),
        migrations.AddField(
            model_name='sell',
            name='deposit',
            field=models.ForeignKey(verbose_name='deposit', blank=True, to='search.Deposit', null=True),
        ),
        migrations.AddField(
            model_name='sell',
            name='place',
            field=models.ForeignKey(verbose_name='place', blank=True, to='search.Place', null=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='copies',
            field=models.ManyToManyField(related_name='copies', through='search.OutMovementCopies', to='search.Card', blank=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='origin',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True),
        ),
        migrations.AddField(
            model_name='outmovement',
            name='recipient',
            field=models.ForeignKey(blank=True, to='search.Client', null=True),
        ),
        migrations.AddField(
            model_name='inventorycommand',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCommandCopies', blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.InventoryCopies', blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='place',
            field=models.ForeignKey(verbose_name='place', blank=True, to='search.Place', null=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='publisher',
            field=models.ForeignKey(verbose_name='publisher', blank=True, to='search.Publisher', null=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='shelf',
            field=models.ForeignKey(verbose_name='shelf', blank=True, to='search.Shelf', null=True),
        ),
        migrations.AddField(
            model_name='internalmovement',
            name='dest',
            field=models.ForeignKey(related_name='mvt_dest', to='search.Place'),
        ),
        migrations.AddField(
            model_name='internalmovement',
            name='origin',
            field=models.ForeignKey(related_name='mvt_origin', to='search.Place'),
        ),
        migrations.AddField(
            model_name='depositstatecopies',
            name='sells',
            field=models.ManyToManyField(to='search.Sell'),
        ),
        migrations.AddField(
            model_name='depositstate',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.DepositStateCopies', blank=True),
        ),
        migrations.AddField(
            model_name='depositstate',
            name='deposit',
            field=models.ForeignKey(to='search.Deposit'),
        ),
        migrations.AddField(
            model_name='deposit',
            name='dest_place',
            field=models.ForeignKey(verbose_name='destination place', blank=True, to='search.Place', null=True),
        ),
        migrations.AddField(
            model_name='deposit',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='coupon',
            name='generic',
            field=models.ForeignKey(to='search.CouponGeneric', null=True),
        ),
        migrations.AddField(
            model_name='command',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.CommandCopies', blank=True),
        ),
        migrations.AddField(
            model_name='command',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='command',
            name='inventory',
            field=models.OneToOneField(null=True, blank=True, to='search.InventoryCommand', verbose_name='inventory'),
        ),
        migrations.AddField(
            model_name='command',
            name='publisher',
            field=models.ForeignKey(verbose_name='publisher', blank=True, to='search.Publisher', null=True),
        ),
        migrations.AddField(
            model_name='card',
            name='card_type',
            field=models.ForeignKey(verbose_name='card type', blank=True, to='search.CardType', null=True),
        ),
        migrations.AddField(
            model_name='card',
            name='collection',
            field=models.ForeignKey(verbose_name='collection', blank=True, to='search.Collection', null=True),
        ),
        migrations.AddField(
            model_name='card',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to='search.Place', verbose_name='places', through='search.PlaceCopies', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to='search.Publisher', verbose_name='publishers', blank=True),
        ),
        migrations.AddField(
            model_name='card',
            name='shelf',
            field=models.ForeignKey(verbose_name='shelf', blank=True, to='search.Shelf', null=True),
        ),
        migrations.AddField(
            model_name='billcopies',
            name='card',
            field=models.ForeignKey(to='search.Card'),
        ),
        migrations.AddField(
            model_name='bill',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BillCopies', blank=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='distributor',
            field=models.ForeignKey(to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='basketcopies',
            name='card',
            field=models.ForeignKey(to='search.Card'),
        ),
        migrations.AddField(
            model_name='basket',
            name='basket_type',
            field=models.ForeignKey(verbose_name='basket type', blank=True, to='search.BasketType', null=True),
        ),
        migrations.AddField(
            model_name='basket',
            name='copies',
            field=models.ManyToManyField(to='search.Card', through='search.BasketCopies', blank=True),
        ),
        migrations.AddField(
            model_name='basket',
            name='distributor',
            field=models.ForeignKey(verbose_name='distributor', blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='alert',
            name='card',
            field=models.ForeignKey(to='search.Card'),
        ),
        migrations.AddField(
            model_name='alert',
            name='deposits',
            field=models.ManyToManyField(to='search.Deposit', blank=True),
        ),
    ]
