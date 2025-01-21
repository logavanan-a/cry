from __future__ import unicode_literals
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib import admin
import six
from constants import OPTIONAL
from masterdata.manager import ActiveQuerySet
from simple_history.admin import SimpleHistoryAdmin
# Create your models here.


class BaseContentBase(models.base.ModelBase):

    def __iter__(self):
        return self.objects.all().__iter__()

    @staticmethod
    def register(mdl):
        if (not hasattr(mdl, 'Meta')) or getattr(getattr(mdl, '_meta', None),'abstract', True):
            return mdl

        class MdlAdmin(admin.ModelAdmin):
            list_display = ['__str__'] + getattr(mdl, 'admin_method', []) + [i.name for i in mdl._meta.fields]
            filter_horizontal = [i.name for i in mdl._meta.many_to_many]

        if hasattr(mdl, 'Admin'):
            class NewMdlAdmin(mdl.Admin, MdlAdmin):
                pass
            admin.site.register(mdl, NewMdlAdmin)
        else:
            admin.site.register(mdl, MdlAdmin)

    def __new__(cls, name, bases, attrs):
        mdl = super(BaseContentBase, cls).__new__(cls, name, bases, attrs)
        BaseContentBase.register(mdl)
        return mdl


class BaseContent(six.with_metaclass(BaseContentBase, models.Model)):
    # ---------comments-----------------------------------------------------#
    # BaseContent is the abstract base model for all
    # the models in the project
    # This contains created and modified to track the
    # history of a row in any table
    # This also contains switch method to deactivate one row if it is active
    # and vice versa
    # ------------------------ends here---------------------------------------------#

    ACTIVE_CHOICES = ((0, 'Inactive'), (2, 'Active'), (1, 'Migrated'),)
    active = models.PositiveIntegerField(choices=ACTIVE_CHOICES,
                                         default=2)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = ActiveQuerySet.as_manager()

    #                                        BaseContent
    class Meta:
        #-----------------------------------------#
        # Don't create a table in database
        # This table is abstract
        #--------------------ends here--------------------#
        abstract = True

    #                                        BaseContent
    def switch(self):
        # Deactivate a model if it is active
        # Activate a model if it is inactive
        self.active = {2: 0, 0: 2}[self.active]
        self.save()

    #                                        BaseContent
    def copy(self, commit=True):
        # Create a copy of given item and save in database
        obj = self
        obj.pk = None
        if commit:
            obj.save()
        return obj

    #                                        BaseContent
    def __unicode__(self):
        for i in ['name', 'text']:
            if hasattr(self, i):
                return getattr(self, i, 'Un%sed' % i)
        if hasattr(self, '__str__'):
            return self.__str__()
        return super(BaseContent, self).__unicode__()


class Boundary(BaseContent):
    """Table to Save DIfferent Locations based on Level."""
    region = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_boundary_region', **OPTIONAL)
    ward_type = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_ward', **OPTIONAL)
    name = models.CharField('Name', max_length=100)
    code = models.CharField('Hamlet Code', max_length=100, **OPTIONAL)
    boundary_level = models.IntegerField()
    desc = models.TextField('Description', **OPTIONAL)
    slug = models.SlugField('Slug', max_length=255, **OPTIONAL)
    parent = models.ForeignKey('self', **OPTIONAL)
    latitude = models.CharField(max_length=100, **OPTIONAL)
    longitude = models.CharField(max_length=100, **OPTIONAL)
    _polypoints = models.CharField(default='[]', max_length=500, **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')
    cry_admin_id = models.CharField(max_length=15,**OPTIONAL)

    def __unicode__(self):
        """Return Name."""
        return self.name

    def get_county(self):
        """Return the Country for the level 2."""
        return Boundary.objects.filter(parent=self)

    def get_parent_locations(self, prev_loc=[]):
        """ Returns the parent level object """

        parent = Boundary.objects.get(id=self.id).parent
        if parent:
            if parent.get_parent_locations():
                prev_loc.append(
                    {'level' + str(parent.boundary_level) + '_id': int(parent.id)})
                parent.get_parent_locations(prev_loc)
            else:
                prev_loc.append(
                    {'level' + str(parent.boundary_level) + '_id': int(parent.id)})
            return prev_loc
        elif not parent and not prev_loc:
            return []

    def get_facility_data(self):
        object_id = 0
        
        rural = 'location-rural'
        if self.boundary_level >= 4:
            if self.object_id:
                mast = MasterLookUp.objects.get(id=self.object_id)
                object_id = mast.id
        else:
            mast = MasterLookUp.objects.get(slug__iexact=rural)
            object_id = mast.id
        return object_id


class MasterLookUp(BaseContent):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', **OPTIONAL)
    slug = models.SlugField(_("Slug"), blank=True)
    code = models.IntegerField(default=0)
    cry_admin_id = models.CharField(max_length=15,**OPTIONAL)

    def __unicode__(self):
        return self.name

    def get_child(self):
        child_obj = MasterLookUp.objects.filter(active=2, parent__id=self.id)
        child_list = []
        if child_obj:
            for i in child_obj:
                child_list.append(
                    {'id': i.id, 'name': i.name, 'child': i.get_child(), 'parent_id': self.id})
            return child_list
        else:
            return child_list


class ResetActivation(BaseContent):
    key = models.CharField(max_length=100, **OPTIONAL)
    user = models.ForeignKey("auth.User", **OPTIONAL)

    def __unicode__(self):
        return str(self.id)


class DocumentCategory(BaseContent):
    name = models.CharField("Document Name", max_length=300, **OPTIONAL)
    order = models.IntegerField(default=0)
    slug = models.SlugField('Slug', max_length=255, **OPTIONAL)

    def __unicode__(self):
        return self.name or ''


class Attachments(BaseContent):
    document_category = models.ForeignKey(DocumentCategory, **OPTIONAL)
    name = models.CharField(max_length=100)
    description = models.TextField(**OPTIONAL)
    attachment = models.FileField(upload_to='static/%Y/%m/%d', **OPTIONAL)
    link = models.URLField(**OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name or ''


PRIORITY = ((1, 'Primary'), (2, 'Secondary'), (3, 'Others'))


class ContactDetail(BaseContent):
    priority = models.IntegerField(choices=PRIORITY, **OPTIONAL)
    contact_no = models.CharField(
        'Contact Number', max_length=600, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    landline = models.CharField(max_length=20, blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.email or ''


@receiver(post_save, sender=MasterLookUp)
def add_codeconfig_facility(sender, instance, created, **kwargs):
    from facilities.models import CodeConfig, Facility
    if created and instance.parent and instance.parent.slug in ['service-type', 'facility-type']:
        cobj = CodeConfig.objects.create(ctype=ContentType.objects.get_for_model(instance), object_id=instance.id,
                                         for_object=True
                                         )
        cobj.save()

CHOICES_TYPE = ((1, 'Master Locations'),)


class DynamicContent(BaseContent):

    subject = models.CharField(max_length=500, **OPTIONAL)
    content_type = models.IntegerField(choices=CHOICES_TYPE, **OPTIONAL)
    content = models.TextField()

    def __unicode__(self):
        return '{}'.format(self.get_content_type_display())
