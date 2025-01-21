# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-07-14 06:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0011_auto_20170712_0609'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetyear',
            name='year',
        ),
        migrations.RemoveField(
            model_name='funding',
            name='end_year',
        ),
        migrations.RemoveField(
            model_name='funding',
            name='start_year',
        ),
        migrations.AddField(
            model_name='budgetyear',
            name='end_year',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='budgetyear',
            name='start_year',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='funding',
            name='year',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='partner.BudgetYear'),
        ),
    ]
