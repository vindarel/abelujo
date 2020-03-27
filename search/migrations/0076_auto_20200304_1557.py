# -*- coding: utf-8 -*-


from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0075_auto_20200227_1645'),
    ]

    operations = [
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
        migrations.AddField(
            model_name='coupon',
            name='generic',
            field=models.ForeignKey(to='search.CouponGeneric', null=True),
        ),
    ]
