# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2019-01-17 05:46
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_auto_20181106_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='aggregatereportconfig',
            name='custom_sqlquery_config',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='aggregatereportconfig',
            name='udf1',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='aggregatereportconfig',
            name='udf2',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='aggregatereportconfig',
            name='udf3',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
