# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2019-03-24 03:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0083_auto_20190314_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowbatch',
            name='current_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.WorkFlowSurveyRelation'),
        ),
    ]
