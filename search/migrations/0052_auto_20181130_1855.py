# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0051_outmovement_created'),
    ]

    operations = [
        migrations.RenameField(
            model_name='outmovement',
            old_name='reason',
            new_name='comment',
        ),
    ]
