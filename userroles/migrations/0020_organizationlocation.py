# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-05-09 10:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('masterdata', '0012_auto_20170509_0903'),
        ('userroles', '0019_auto_20170504_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('organization_level', models.IntegerField(blank=True, choices=[(1, b'Country'), (2, b'State'), (3, b'District'), (4, b'Taluk'), (5, b'Mandal'), (6, b'GramaPanchayath'), (7, b'Village')], null=True)),
                ('location', models.ManyToManyField(blank=True, to='masterdata.Boundary')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userroles.UserRoles')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
