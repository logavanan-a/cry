# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-14 07:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userroles', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roleconfig',
            name='role',
        ),
        migrations.AddField(
            model_name='roleconfig',
            name='role',
            field=models.ManyToManyField(to='userroles.RoleTypes'),
        ),
    ]
