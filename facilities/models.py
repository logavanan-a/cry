from __future__ import unicode_literals
from django.db import models
from django.contrib.postgres.fields import JSONField
from masterdata.models import BaseContent, MasterLookUp
from django.template.defaultfilters import slugify
from service.models import Service
from beneficiary.models import Beneficiary, Beneficiary_choices
from partner.models import Partner
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User


class Facility(BaseContent):
    facility_type = models.ForeignKey(
        MasterLookUp, related_name='facility_facilitytype')
    facility_subtype = models.ForeignKey(
        MasterLookUp, related_name='facility_facilitysubtype', blank=True, null=True)
    thematic_area = models.ManyToManyField(
        MasterLookUp, related_name='facility_thematicarea')
    beneficiary = models.ForeignKey(
        Beneficiary, blank=True, null=True, related_name='facility_beneficiary')
    partner = models.ForeignKey(
        Partner, blank=True, null=True, related_name='facility_facilit')
    btype = models.CharField(
        max_length=100, choices=Beneficiary_choices, blank=True, null=True)
    name = models.CharField('Name', max_length=100)
    services = models.ManyToManyField(Service, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    uuid = models.CharField('UUID', max_length=100, blank=True, null=True)
    tempid = models.IntegerField(default=0)
    jsondata = JSONField()
    cry_admin_id = models.CharField(max_length=15,blank=True,null=True)

    def __unicode__(self):
        return self.name

PREFIX_TYPES = (('Non-Financial', 'Non-Financial'), ('Financial', 'Financial'))


class CodeConfig(BaseContent):
    content_type = models.ForeignKey(
        ContentType, related_name='codeconfig_mainctype', blank=True, null=True)
    prefix_type = models.CharField(
        max_length=100, choices=PREFIX_TYPES, default='Non-Financial')
    prefix = models.CharField(max_length=100, blank=True, null=True)
    separator = models.CharField(max_length=100, blank=True, null=True)
    padlength = models.PositiveIntegerField(blank=True, null=True)
    start_number = models.PositiveIntegerField(blank=True, null=True)
    ctype = models.ForeignKey(ContentType, blank=True,
                              null=True, related_name='codeconfig_ctype')
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('ctype', 'object_id')
    is_updated = models.BooleanField(default=False)
    for_object = models.BooleanField(default=False)
    sequence = models.BooleanField(default=False)

    def __unicode__(self):
        try:
            return self.content_type.model
        except:
            try:
                return self.content_object.name
            except:
                return str(self.id)


class CodeContentCount(BaseContent):
    content_type = models.ForeignKey(
        ContentType, related_name='codecontent_ctype', blank=True, null=True)
    financial_year = models.CharField(max_length=100, blank=True, null=True)
    content_count = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        try:
            return self.content_type.model
        except:
            try:
                return self.content_object.name
            except:
                return str(self.id)


class FacilityCentre(BaseContent):
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self', blank=True, null=True)
    facilities = models.ManyToManyField(Facility)
    centre = models.ForeignKey('facilities.Centres', blank=True, null=True)
    jsondata = JSONField()

    def __unicode__(self):
        return self.name


class Centres(BaseContent):
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self', blank=True, null=True)
    slug = models.SlugField("SEO friendly url, use only aplhabets and hyphen",
                            max_length=120, blank=True, null=True)

    def __unicode__(self):
        return self.name

class FacilityBeneficiaryDeactivate(BaseContent):
    ACTIONS = ((0, 'Created'), (1, 'Deleted'), (2, 'Updated'), (3, 'Activated') , (4, 'Deactivated') , (5 , 'Others'))
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reason = models.CharField('Reason' , max_length = 200 , blank = True , null = True )
    user = models.ForeignKey(User, blank=True, null=True)
    action = models.PositiveIntegerField(choices=ACTIONS,default=5)
    
    def __str__(self):
        return self.reason
