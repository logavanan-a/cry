# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-12 09:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beneficiary', '0003_beneficiary_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='beneficiary',
            name='code',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Name'),
        ),
    ]
