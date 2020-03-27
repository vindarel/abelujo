# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0031_barcode64'),
    ]

    operations = [
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
                ('card', models.ForeignKey(to='search.Card')),
                ('command', models.ForeignKey(to='search.Command')),
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
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
        ),
        migrations.AddField(
            model_name='command',
            name='publisher',
            field=models.ForeignKey(blank=True, to='search.Publisher', null=True),
        ),
    ]
