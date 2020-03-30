# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0063_auto_20191112_1835'),
    ]

    operations = [
        migrations.CreateModel(
            name='Restocking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='RestockingCopies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=0)),
                ('card', models.ForeignKey(to='search.Card', on_delete=models.CASCADE)),
                ('restocking', models.ForeignKey(to='search.Restocking', on_delete=models.CASCADE)),
            ],
        ),
    ]
