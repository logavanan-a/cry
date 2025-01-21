# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2018-11-06 10:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0055_auto_20180925_1739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='appanswerdata',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='appissuetracker',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='applabel',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='applogindetails',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='block',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='blocklanguagetranslation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='choice',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='choicelanguagetranslation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='choicevalidation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='colorcode',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='dashboardresponse',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='databaselog',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='datacentre',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='dataentrylevel',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='detailedusersurveymap',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='errorlog',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='frequence',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='historicaljsonanswer',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='jsonanswer',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='labellanguagetranslation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='language',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='levels',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='locationtypes',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='media',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='metricsquestionlanguage',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='networkconnectionstatus',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='projectlevels',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='projectsurvey',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='question',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='questionlanguagetranslation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='questionlanguagevalidation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='questionvalidation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='samandmam',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='skipmandatory',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='survey',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveybeneficiarymap',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveydataentryconfig',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveydump',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveylanguagemap',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveylanguagetranslation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveylog',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveypartnerextension',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveyquestions',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveyrestore',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='surveyskip',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='trackanswerreportdump',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='usercluster',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='userimeiinfo',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='userlanguage',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='usertabdetails',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='usertimeintervals',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='usmcrontracker',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='validations',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='version',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
        migrations.AlterField(
            model_name='versionupdate',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active'), (1, 'Migrated')], default=2),
        ),
    ]
