# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2019-03-13 07:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0060_auto_20190129_1935'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionautofill',
            name='question',
        ),
        migrations.RemoveField(
            model_name='questionautofill',
            name='question_auto_fill',
        ),
        migrations.DeleteModel(
            name='Questionautofill',
        ),
    ]
