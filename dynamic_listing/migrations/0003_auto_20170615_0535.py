# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-06-15 05:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic_listing', '0002_auto_20170614_0626'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dynamiclisting',
            old_name='lisitng_fields',
            new_name='listing_fields',
        ),
    ]
