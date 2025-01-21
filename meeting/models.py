from __future__ import unicode_literals
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from constants import OPTIONAL
from masterdata.models import (BaseContent, )
# Create your models here.

class UserProfile(BaseContent):
    created_by = models.ForeignKey('auth.User', **OPTIONAL)
    name = models.CharField(max_length=400, **OPTIONAL)
    designation = models.ForeignKey('masterdata.MasterLookUp',related_name="designation_user_type",blank=True,null=True)
    contact_no = models.CharField('Contact Number',max_length = 600, blank=True,null=True)
    email = models.EmailField(blank=True,null=True)
    landline = models.CharField(max_length=20, blank=True,null=True)
    fax = models.CharField(max_length=20, blank=True,null=True)

    def __unicode__(self):
        return self.name

class Meeting(BaseContent):
    agenda = models.TextField(**OPTIONAL)
    created_by = models.ForeignKey('auth.User', **OPTIONAL)
    held_by = models.ForeignKey(UserProfile, **OPTIONAL)
    held_on = models.DateTimeField(**OPTIONAL)
    venue = models.ForeignKey('masterdata.Boundary', **OPTIONAL)

    def __unicode__(self):
        return self.created_by.username

STATUS = ((1, 'OPEN'), (2, 'CLOSED'))
class Issue(BaseContent):
    category = models.ForeignKey('masterdata.MasterLookup', related_name='masterlookup_category', **OPTIONAL)
    sub_category = models.ForeignKey('masterdata.MasterLookup', related_name='masterlookup_sub_category', **OPTIONAL)
    person = models.ForeignKey(UserProfile, **OPTIONAL)
    requirements = models.TextField(**OPTIONAL)
    date_of_completion = models.DateTimeField(**OPTIONAL)
    location = models.ForeignKey('masterdata.Boundary', **OPTIONAL)
    cost = models.FloatField(**OPTIONAL)
    status = models.IntegerField(choices=STATUS, **OPTIONAL)
    financial_issue = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.category.name

class MeetingGroup(BaseContent):
    group = models.ForeignKey('masterdata.MasterLookup', related_name='masterlookup_group', **OPTIONAL)
    sub_group = models.ForeignKey('masterdata.MasterLookup', related_name='masterlookup_sub_group', **OPTIONAL)
    female = models.CharField(max_length=200,**OPTIONAL)
    male = models.CharField(max_length=200,**OPTIONAL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.group.name

class FinanceDetail(BaseContent):
    created_by = models.ForeignKey('auth.User', **OPTIONAL)
    group = models.ForeignKey('masterdata.MasterLookup', related_name='masterlookup_finance', **OPTIONAL)
    cost = models.FloatField(**OPTIONAL)
    remarks = models.TextField(**OPTIONAL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode_(self):
        return self.group.name
