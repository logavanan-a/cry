from __future__ import unicode_literals
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from masterdata.models import BaseContent
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.
class DynamicListing(BaseContent):
    model_name = models.ForeignKey(ContentType)
    listing_name = models.CharField(max_length=50,blank=False,null=True)
    listing_fields = JSONField(blank=True,null=True)
    content_type = models.ForeignKey(ContentType,blank=True,null=True,related_name='sub_model_type_dynamic_listing')
    object_id = models.PositiveIntegerField(default=0,blank=True,null=True)
    genericForeignKey = GenericForeignKey('content_type','object_id')

    def __unicode__(self):
        return str(self.model_name)

class DynamicFilter(BaseContent):
    model_name = models.ForeignKey(ContentType)
    filter_name = models.CharField(max_length=50,null=True)
    filtering_query = JSONField(blank=True,null=True)
    content_type = models.ForeignKey(ContentType,blank=True,null=True,related_name='sub_model_type_dynamic_filter')
    object_id = models.PositiveIntegerField(default=0,blank=True,null=True)
    genericForeignKey = GenericForeignKey('content_type','object_id')

    def __unicode__(self):
        return str(self.model_name)

class DynamicField(BaseContent):
    model_name = models.ForeignKey(ContentType)
    model_fields = JSONField()
    content_type = models.ForeignKey(ContentType,blank=True,null=True,related_name='sub_model_type')
    object_id = models.PositiveIntegerField(default=0,blank=True,null=True)
    genericForeignKey = GenericForeignKey('content_type','object_id')

    def __unicode__(self):
        return str(self.model_name)
