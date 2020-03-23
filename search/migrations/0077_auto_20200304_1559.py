# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.db import models, migrations


def create_coupons(apps, schema_editor):
    # We can't import the model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    CouponGeneric = apps.get_model('search', 'CouponGeneric')

    default_coupons = [5, 10, 15, 20, 30, 50, 90]
    for amount in default_coupons:
        coupon, created = CouponGeneric.objects.get_or_create(amount=amount)

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('search', '0076_auto_20200304_1557'),
    ]

    operations = [
        migrations.RunPython(create_coupons, backwards),
    ]
