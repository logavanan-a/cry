# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2019-02-07 20:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0027_auto_20181106_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectlocation',
            name='boundary',
            field=models.ManyToManyField(blank=True, to='masterdata.Boundary'),
        ),
    ]
