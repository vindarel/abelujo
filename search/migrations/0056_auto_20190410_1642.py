# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0055_outmovementcopies_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ('city',)},
        ),
        migrations.RenameField(
            model_name='address',
            old_name='tel_private',
            new_name='telephone',
        ),
        migrations.RemoveField(
            model_name='address',
            name='email_pro',
        ),
        migrations.RemoveField(
            model_name='address',
            name='enterprise',
        ),
        migrations.RemoveField(
            model_name='address',
            name='name',
        ),
        migrations.RemoveField(
            model_name='address',
            name='surname',
        ),
        migrations.RemoveField(
            model_name='address',
            name='tel_office',
        ),
    ]
