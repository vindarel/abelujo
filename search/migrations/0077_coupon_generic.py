# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0076_coupon_coupongeneric'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='generic',
            field=models.ForeignKey(to='search.CouponGeneric', null=True),
        ),
    ]
