# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-06-14 06:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic_listing', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='dynamic_listing',
            new_name='DynamicListing',
        ),
    ]
