# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0040_auto_20170319_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='imgfile',
            field=models.ImageField(null=True, upload_to=b'covers', blank=True),
        ),
    ]
