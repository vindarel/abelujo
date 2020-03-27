# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0008_entrycopies_price_init'),
    ]

    operations = [
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
                ('quantity', models.IntegerField()),
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
            field=models.ManyToManyField(to='search.Card', null=True, through='search.BillCopies', blank=True),
            preserve_default=True,
        ),
    ]
