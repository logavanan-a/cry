# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-05-04 09:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userroles', '0018_address_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='data',
        ),
        migrations.RemoveField(
            model_name='address',
            name='fax',
        ),
        migrations.RemoveField(
            model_name='address',
            name='landline',
        ),
        migrations.AlterField(
            model_name='address',
            name='office',
            field=models.IntegerField(blank=True, choices=[(1, b'Registered Office'), (2, b'Head Office'), (3, b'Registered & Head Office'), (4, b'Correspondence Office'), (5, b'Project Manager')], null=True),
        ),
    ]
