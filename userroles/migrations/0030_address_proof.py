# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-02-28 10:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('masterdata', '0019_auto_20171130_1114'),
        ('userroles', '0029_userpartnermapping'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='proof',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='address_proof', to='masterdata.MasterLookUp'),
        ),
    ]
