# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0023_inventory_closed'),
    ]

    operations = [
        migrations.RenameModel('InventoryCards', 'InventoryCopies'),
    ]
