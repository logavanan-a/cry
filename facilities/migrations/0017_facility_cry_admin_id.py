# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2018-08-30 07:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0016_auto_20180625_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='cry_admin_id',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
