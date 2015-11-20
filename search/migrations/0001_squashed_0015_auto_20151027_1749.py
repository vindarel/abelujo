# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    replaces = [(b'search', '0001_initial'), (b'search', '0002_auto_20150915_0738'), (b'search', '0003_auto_20150925_0747'), (b'search', '0004_auto_20151001_0659'), (b'search', '0005_auto_20151001_1018'), (b'search', '0006_internalmovement'), (b'search', '0007_entry_payment'), (b'search', '0008_entrycopies_price_init'), (b'search', '0009_auto_20151013_1205'), (b'search', '0010_bill_distributor'), (b'search', '0011_auto_20151013_1225'), (b'search', '0012_auto_20151013_1244'), (b'search', '0013_auto_20151013_1421'), (b'search', '0014_auto_20151013_1651'), (b'search', '0015_auto_20151027_1749')]

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
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BasketCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('basket', models.ForeignKey(to='search.Basket')),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
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
                ('authors', models.ManyToManyField(to=b'search.Author')),
            ],
            options={
                'ordering': ('sortkey', 'year_published', 'title'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('ordered', models.IntegerField(null=True, blank=True)),
                ('parent', models.ForeignKey(blank=True, to='search.Collection', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DepositCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('nb', models.IntegerField(default=1)),
                ('threshold', models.IntegerField(default=1, null=True, blank=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('deposit', models.ForeignKey(to='search.Deposit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DepositState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('closed', models.DateField(default=None, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DepositStateCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb_current', models.IntegerField(default=1)),
                ('nb_to_return', models.IntegerField(default=1)),
                ('card', models.ForeignKey(to='search.Card')),
                ('deposit_state', models.ForeignKey(to='search.DepositState')),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InventoryCards',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('inventory', models.ForeignKey(to='search.Inventory')),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nb', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('place', models.ForeignKey(to='search.Place')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default_place', models.OneToOneField(to='search.Place')),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField()),
                ('payment', models.CharField(default=(0, b'cash'), max_length=200, null=True, blank=True, choices=[(0, b'cash'), (1, b'check'), (2, b'credit card'), (3, b'gift'), (4, b'other')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SoldCards',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=1)),
                ('price_sold', models.FloatField(default=0)),
                ('card', models.ForeignKey(to='search.Card')),
                ('sell', models.ForeignKey(to='search.Sell')),
                ('price_init', models.FloatField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sell',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.SoldCards', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='inventory',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.InventoryCards', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='inventory',
            name='place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='depositstatecopies',
            name='sells',
            field=models.ManyToManyField(to=b'search.Sell'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='depositstate',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.DepositStateCopies', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='depositstate',
            name='deposit',
            field=models.ForeignKey(to='search.Deposit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deposit',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.DepositCopies', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deposit',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='card_type',
            field=models.ForeignKey(blank=True, to='search.CardType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='collection',
            field=models.ForeignKey(blank=True, to='search.Collection', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='places',
            field=models.ManyToManyField(to=b'search.Place', null=True, through='search.PlaceCopies', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='publishers',
            field=models.ManyToManyField(to=b'search.Publisher', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='basketcopies',
            name='card',
            field=models.ForeignKey(to='search.Card'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='basket',
            name='basket_type',
            field=models.ForeignKey(blank=True, to='search.BasketType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='basket',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.BasketCopies', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alert',
            name='card',
            field=models.ForeignKey(to='search.Card'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alert',
            name='deposits',
            field=models.ManyToManyField(to=b'search.Deposit', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deposit',
            name='dest_place',
            field=models.ForeignKey(blank=True, to='search.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deposit',
            name='due_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('typ', models.IntegerField(default=1)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EntryCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('entry', models.ForeignKey(to='search.Entry')),
                ('created', models.DateTimeField(default=datetime.date(2015, 10, 1), auto_now_add=True)),
                ('modified', models.DateTimeField(default=datetime.date(2015, 10, 1), auto_now=True)),
                ('price_init', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
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
                ('basket', models.ForeignKey(blank=True, to='search.Basket', null=True)),
                ('card', models.ForeignKey(to='search.Card')),
                ('dest', models.ForeignKey(related_name=b'mvt_dest', to='search.Place')),
                ('origin', models.ForeignKey(related_name=b'mvt_origin', to='search.Place')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='entry',
            name='payment',
            field=models.CharField(blank=True, max_length=200, null=True, choices=[(0, b'cash'), (1, b'check'), (2, b'credit card'), (3, b'gift'), (4, b'other')]),
            preserve_default=True,
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BillCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('bill', models.ForeignKey(to='search.Bill')),
                ('card', models.ForeignKey(to='search.Card')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bill',
            name='copies',
            field=models.ManyToManyField(to=b'search.Card', null=True, through='search.BillCopies', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='distributor',
            field=models.ForeignKey(to='search.Distributor', null=True),
            preserve_default=True,
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
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='card',
            name='category',
            field=models.ForeignKey(blank=True, to='search.Category', null=True),
            preserve_default=True,
        ),
    ]
