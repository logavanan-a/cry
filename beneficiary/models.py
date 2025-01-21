from __future__ import unicode_literals

from django.db import models
from masterdata.models import BaseContent, MasterLookUp
from django.contrib.postgres.fields import JSONField
from partner.models import Partner
from userroles.models import Address
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

Beneficiary_choices = (('Household', 'Household'),
                       ('Mother', 'Mother'), ('Child', 'Child'))


class BeneficiaryType(BaseContent):
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self', blank=True, null=True)
    is_main = models.BooleanField(default=False)
    order = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_childs(self):
        return BeneficiaryType.objects.filter(parent=self, active=2).order_by('order')


class Beneficiary(BaseContent):
    beneficiary_type = models.ForeignKey(
        BeneficiaryType, blank=True, null=True)
    btype = models.CharField(
        max_length=100, choices=Beneficiary_choices, default='Household')
    name = models.CharField('Name', max_length=100)
    code = models.CharField('Code', max_length=100, blank=True, null=True)
    partner = models.ForeignKey(
        Partner, blank=True, null=True, related_name='beneficiary_partner')
    parent = models.ForeignKey('self', blank=True, null=True)
    uuid = models.CharField('UUID', max_length=100, blank=True, null=True)
    tempid = models.IntegerField(default=0)
    jsondata = JSONField()
    cry_admin_id=models.CharField(max_length=20,blank=True,null=True)

    def __unicode__(self):
        return self.name

    def get_boundary_name(self):
        name = self.name
        try:
            address_obj = Address.objects.get(
                office=1, content_type=ContentType.objects.get_for_model(self), object_id=self.id)
            name = name + "-" + address_obj.boundary.name
            if address_obj.boundary.parent:
                name = name + "-" + address_obj.boundary.parent.name
        except:
            pass
        return name

    def get_address(self):
        address_obj = None
        try:
            address_obj = Address.objects.filter(
                office=1, content_type=ContentType.objects.get_for_model(self), object_id=self.id, active=2).latest('id')
        except:
            pass
        return address_obj


    def get_all_address(self):
        address_obj = Address.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, active=2)
        return address_obj

class BeneficiaryRelation(BaseContent):
    partner = models.ForeignKey(
        Partner, blank=True, null=True, related_name='beneficiaryrelation_partner')
    primary_beneficiary = models.ForeignKey(
        Beneficiary, related_name='primary_beneficiary')
    secondary_beneficiary = models.ForeignKey(
        Beneficiary, related_name='secondary_beneficiary')
    relation = models.ForeignKey(MasterLookUp)

    def __unicode__(self):
        return self.relation.name

    class Meta:
        unique_together = ("primary_beneficiary",
                           "secondary_beneficiary", "relation")


@receiver(post_save, sender=BeneficiaryType)
def add_codeconfig(sender, instance, created, **kwargs):
    from facilities.models import CodeConfig
    if created:
        cobj = CodeConfig.objects.create(ctype=ContentType.objects.get_for_model(instance), object_id=instance.id,
                                         for_object=True
                                         )
        cobj.save()
