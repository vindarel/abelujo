# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0057_auto_20190410_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('firstname', models.CharField(max_length=200)),
                ('contact', models.ForeignKey(blank=True, to='search.Contact', null=True)),
            ],
        ),
    ]
