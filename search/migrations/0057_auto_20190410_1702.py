# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0056_auto_20190410_1642'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Address',
            new_name='Contact',
        ),
        migrations.DeleteModel(
            name='Client',
        ),
    ]
