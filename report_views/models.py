from __future__ import unicode_literals

from django.db import models
from masterdata.models import BaseContent
# Create your models here.

class ChildNeverEnrolled(models.Model):
    id = models.BigIntegerField(primary_key=True)
    created = models.DateField()
    partner_name = models.CharField(max_length=1000)
    bid = models.PositiveIntegerField()
    child_name = models.CharField(max_length=1000)
    age = models.CharField(max_length=100)
    gender = models.CharField(max_length=100)
    hh_chores_involvement = models.CharField(max_length=1000)
    economic_activities = models.CharField(max_length=1000)
    class Meta:
        managed = False
        db_table = 'child_never_enrolled'

