# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0066_basket_archived_date'),
    ]

    operations = [
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
        migrations.AlterField(
            model_name='card',
            name='price_sold',
            field=models.FloatField(null=True, verbose_name='price sold', blank=True),
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
            field=models.CharField(default='fix', max_length=200, verbose_name='deposit type', choices=[('D\xc3\xa9p\xc3\xb4t de libraire', (('li', 'd\xc3\xa9p\xc3\xb4t de libraire'), ('fix', 'd\xc3\xa9p\xc3\xb4t fixe'))), ('D\xc3\xa9p\xc3\xb4t de distributeur', (('dist', 'd\xc3\xa9p\xc3\xb4t de distributeur'),))]),
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
    ]
