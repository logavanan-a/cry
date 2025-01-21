from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from masterdata.models import BaseContent, MasterLookUp
from django.template.defaultfilters import slugify
from beneficiary.models import Beneficiary
from partner.models import Partner

class ServiceType(BaseContent):
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self', blank=True, null=True)
    slug = models.SlugField("SEO friendly url, use only aplhabets and hyphen",
                                max_length=120, blank=True, null=True)
    cry_admin_id = models.CharField(max_length=15,blank=True,null=True)
    def __unicode__(self):
        return self.name

class ServiceMonitor(BaseContent):
    name = models.CharField('Name', max_length=100)
    servicetype = models.ForeignKey(ServiceType)
    child = models.ForeignKey(Beneficiary, blank=True, null=True)
    jsondata = JSONField()

    def __unicode__(self):
        return self.name

class Service(BaseContent):
    service_type = models.ForeignKey(MasterLookUp, related_name = 'service_servicetype')
    service_subtype = models.ForeignKey(MasterLookUp, blank=True, null=True, related_name = 'service_servicesubtype')
    thematic_area = models.ForeignKey(MasterLookUp, related_name = 'service_thematicarea')
    beneficiary = models.ForeignKey(Beneficiary, blank=True, null=True, related_name='service_beneficiary')
    partner = models.ForeignKey(Partner, blank=True, null=True, related_name='service_partner')
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self', blank=True, null=True)
    tempid = models.IntegerField(default=0)
    jsondata = JSONField()
    cry_admin_id = models.CharField(max_length=15,blank=True,null=True)

    def __unicode__(self):
        return self.name
