# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0041_card_imgfile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='card',
            old_name='img',
            new_name='cover',
        ),
    ]
