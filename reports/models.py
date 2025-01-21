from __future__ import unicode_literals

from django.db import models
import datetime
from beneficiary.models import *
from partner.models import *
from masterdata.models import *
from survey.models import *

year_range = range(1950, 2018)[::-1]
YEAR_CHOICE = [(i, i) for i in year_range]
quarter_range = range(1, 5)[::-1]
quarter_name = {1:'Apr-Jun', 2:'Jul-Sep', 3:'Oct-Dec', 4:'Jan-Mar'}
QUARTER_CHOICE = [(i, quarter_name[i]) for i in quarter_range]


class PartnerReportYear(BaseContent):
    '''This model stores year for the reports
    partner is a foreign key'''

    year = models.IntegerField(choices=YEAR_CHOICE, blank=True, null=True)
    partner = models.ForeignKey(Partner, blank=True, null=True)

    def __unicode__(self):
        return str(self.year)

    def get_quarters(self):
        return PartnerReportQuarter.objects.filter(partner_year=self).order_by('quarter')


class PartnerReportQuarter(BaseContent):
    '''This model stores quarter for the reports
    partner_year is a foreign key which stores partner year
    quarter stores which quarter report belongs to'''

    quarter = models.IntegerField(choices=QUARTER_CHOICE, blank=True, null=True)
    partner_year = models.ForeignKey(PartnerReportYear, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return str(self.partner_year)


class ReportSurvey(BaseContent):
    '''Model to store the set of block
    for a quarter of a partner'''

    name = models.CharField(max_length=500, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def get_report_survey_blocks(self):
        return ReportBlock.objects.filter(report_survey=self, active=2).order_by('report_order')


class ReportBlock(BaseContent):
    '''Model to store the set of questions
    for a quarter of a partner'''

    name = models.CharField(max_length=500, blank=True, null=True)
    report_survey = models.ForeignKey(ReportSurvey, blank=True, null=True)
    no_of_questions_in_a_row = models.IntegerField(default=1)
    no_of_rows_with_one_row = models.IntegerField(default=0)
    report_order = models.IntegerField(blank=True, null=True)
    dynamic_block = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_report_block_question(self):
        return ReportQuestion.objects.filter(report_block=self, active=2, parent=None).order_by('report_order')


class ReportQuestion(BaseContent):
    '''Model to store the questions
    for a quarter of a partner'''

    name = models.CharField(max_length=500, blank=True, null=True)
    question = models.ForeignKey(Question, blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    report_block = models.ForeignKey(ReportBlock, blank=True, null=True)
    report_order = models.IntegerField(blank=True, null=True)
    answer_code = models.CharField(max_length=5000, blank=True, null=True)
    answer_code_two = models.CharField(max_length=5000, blank=True, null=True)
    is_quarter_question = models.BooleanField(default=False)
    initial_code = models.CharField(max_length=500, blank=True, null=True)
    location_level = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.question.text if self.question else self.name

    def get_sub_questions(self):
        return ReportQuestion.objects.filter(active=2, parent=self).order_by('report_order')


class ReportData(BaseContent):
    '''Model to store the data to be displayed
    in the frontend based on partner, quarter etc..'''
    response = JSONField(blank=True, null=True)
    quarter = models.ForeignKey(PartnerReportQuarter)
    partner = models.ForeignKey(Partner)
    excel_file = models.FileField(upload_to='static/%Y/%m/%d', blank=True, null=True)
    pdf_file = models.FileField(upload_to='static/%Y/%m/%d', blank=True, null=True)

    def __unicode__(self):
        return str(self.partner.name) + '-' + str(self.quarter.partner_year.year) + '-' +\
            str(self.quarter.quarter)

class AggregateReportConfig(BaseContent):
    """Model to config the beneficiary reports of version 2"""
    report_name = models.CharField(max_length=250)
    model_config = JSONField()
    survey_config = JSONField()
    mutant_app_table = models.ForeignKey(ContentType,blank=True,null=True)
    custom_sqlquery_config = JSONField(blank=True,null=True)
    udf1 = models.PositiveIntegerField(default=0)
    udf2 = models.PositiveIntegerField(default=0)
    udf3 = models.PositiveIntegerField(default=0)
    
    
    def __unicode__(self):
        return str(self.report_name)


class ProfileView(BaseContent):
    """A model which will store all profile question related information"""
    jsonid = models.PositiveIntegerField(default = 0)
    uuid_lid = models.CharField(max_length=500, blank=True, null=True)
    type_name = models.CharField(max_length=500, blank=True, null=True)
    type_id = models.PositiveIntegerField(default=0)
    ben_fac_loc_id = models.PositiveIntegerField(default=0)
    profile_info = JSONField()
    partner_id = models.PositiveIntegerField(default=0)
    submission_date = models.DateTimeField()

    
    def __unicode__(self):
        return str(self.type_name)
