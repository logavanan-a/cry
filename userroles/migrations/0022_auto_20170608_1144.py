# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-06-08 11:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userroles', '0021_auto_20170519_0610'),
    ]

    operations = [
        migrations.AddField(
            model_name='adtable',
            name='first_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='adtable',
            name='username',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
