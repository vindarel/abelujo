# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0015_card_in_stock'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Category',
            new_name='Shelf',
        ),
        migrations.RenameField(
            model_name='card',
            old_name='category',
            new_name='shelf',
        ),
    ]
