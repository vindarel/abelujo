# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0047_deposit_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='distributor',
            field=models.ForeignKey(blank=True, to='search.Distributor', null=True),
        ),
    ]
