from itertools import chain
from django.db import models
from django.contrib.auth.models import User
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.defaultfilters import slugify
from ccd.settings import (HOST_URL, EMAIL_HOST_USER,
                          BASE_DIR, FRONT_URL, REST_FRAMEWORK)
from constants import OPTIONAL
from masterdata.models import BaseContent, MasterLookUp
from django.contrib.postgres.fields import JSONField


TITLE_CHOICES = ((0, 'Mr.'), (1, 'Mrs'), (2, 'Miss'), (3, 'Other'))


class Menus(BaseContent):
    #-------------------#
    # Menus module
    # parent is a foriegn key
    # slug field is used
    #--------------------#
    name = models.CharField(max_length=100)
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60)
    parent = models.ForeignKey('self', blank=True, null=True)
    front_link = models.CharField(max_length=512, blank=True)
    backend_link = models.CharField(max_length=512, blank=True)
    icon = models.CharField(max_length=512, blank=True)
    menu_order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ('menu_order',)
        verbose_name_plural = 'Menus'

    def __str__(self):
        # string method to return name
        return self.name

    def get_sub_menus(self):
        # model method to filter menus based parent id
        return Menus.objects.filter(parent=self, active=2)

    def get_sub_child(self):
        menu = Menus.objects.filter(parent=self, active=2)
        for i in menu:
            return RoleConfig.objects.filter(menu=i, view=2)

    def get_childfather(self):
        m = Menus.objects.filter(parent=self, active=2)
        for i in m:
            return Menus.objects.filter(parent=i, active=2)

    def get_accessed_roles(self):
        # model method to filter role configuration based on menu id
        return RoleConfig.objects.filter(menu=self).distinct()

    def get_submenu_list(self, roleobj):
        try:
            menus = Menus.objects.filter(
                parent=self, active=2).order_by("menu_order")
            res = []
            for i in menus:
                roleconfig = RoleConfig.objects.get(role=roleobj.role, menu=i)
                if roleconfig.view == True:
                    res.append({"menu_name": i.name,
                                "menu_id": i.id,
                                "icon": "/" + i.icon if i.icon else '',
                                "front_end_url": i.front_link if i.front_link else '',
                                "back_end_api": i.backend_link if i.backend_link else '',
                                "child_menu": i.get_subchildmenu_list(roleconfig),
                                "slug": i.slug,
                                "add": roleconfig.add,
                                "edit": roleconfig.edit,
                                "view": roleconfig.view,
                                "delete": roleconfig.delete,
                                'search': roleconfig.search, }
                               )
        except:
            res = []
        return res

    def get_subchildmenu_list(self, roleobj):
        try:
            menus = Menus.objects.filter(
                parent=self, active=2).order_by("menu_order")
            res = []
            for i in menus:
                roleconfig = RoleConfig.objects.get(role=roleobj.role, menu=i)
                if roleconfig.view == True:
                    res.append({"menu_name": i.name,
                                "menu_id": i.id,
                                "icon": "/" + i.icon if i.icon else '',
                                "front_end_url": i.front_link if i.front_link else '',
                                "back_end_api": i.backend_link if i.backend_link else '',
                                "child_menu": [],
                                "slug": i.slug,
                                "add": roleconfig.add,
                                "edit": roleconfig.edit,
                                "view": roleconfig.view,
                                "delete": roleconfig.delete,
                                'search': roleconfig.search, }
                               )
        except:
            res = []
        return res

    def get_adminsubmenu_list(self):
        try:
            menus = Menus.objects.filter(
                parent=self, active=2).order_by("menu_order")
            res = []
            for i in menus:
                res.append({"menu_name": i.name,
                            "menu_id": i.id,
                            "icon": "/" + i.icon if i.icon else '',
                            "front_end_url": i.front_link if i.front_link else '',
                            "back_end_api": i.backend_link if i.backend_link else '',
                            "child_menu": i.get_adminsubmenu_list(),
                            "slug": i.slug,
                            "add": True,
                            "edit": True,
                            "view": True,
                            "delete": True,
                            'search': True, }
                           )
        except:
            res = []
        return res

class RoleTypes(BaseContent):
    # roletype model
    name = models.CharField(unique=True, max_length=100, error_messages={
                            'unique': "This role name already existed"})
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60, null=True, blank=True)
    code = models.CharField(max_length=8, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Role Types'

    def get_role_config(self):
        role_confs = []
        for i in Menus.objects.filter(active=2).order_by("menu_order"):
            rc, created = RoleConfig.objects.get_or_create(role=self, menu=i , active = 2)
            role_confs.append(rc)
        return role_confs

    def get_menu_config(self):
        return [RoleConfig.objects.get_or_create(role=self, menu=i)
                for i in Menus.objects.filter(parent=None)]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(RoleTypes, self).save(*args, **kwargs)


# to generate the folder name for saving the organization
def generate_image_folder(self, filename):
    image_folder = "Images/%s/%s" % (self.name, filename)
    return image_folder


class Organization(BaseContent):
    name = models.CharField(max_length=150, null=True, blank=True, unique=True)
    logo = models.ImageField(
        upload_to=generate_image_folder, null=True, blank=True)

    def __unicode__(self):
        return str(self.name)


class OrganizationUnit(BaseContent):
    ORGANIZATION_TYPE_CHOCES = ((1, 'Non-Location'), (2, 'Location'),)
    ORGANIZATION_LEVEL_CHOCES = (
        (1, 'Country'), (2, 'State'),
        (3, 'District'), (4, 'Taluk'),
        (5, 'Mandal'), (6, 'GramaPanchayath'),
        (7, 'Village'),
    )
    name = models.CharField(max_length=150, null=True, blank=True)
    organization_type = models.IntegerField(
        choices=ORGANIZATION_TYPE_CHOCES, default=1)
    organization_level = models.IntegerField(
        choices=ORGANIZATION_LEVEL_CHOCES,  null=True, blank=True)
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60, null=True, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    order = models.IntegerField(null=True, blank=True)
    roles = models.ManyToManyField(RoleTypes, blank=True)

    def __unicode__(self):
        if self.parent:
            return "%s - %s" % (self.name, self.parent.name)
        else:
            return str(self.name)


def get_location_type(loc_type):
    if not loc_type:
        get_default = MasterLookUp.objects.get(slug__iexact='location-rural')
        loc_type = get_default.id
    return loc_type


class UserRoles(BaseContent):
    #----------------------#
    # Userroles model
    # user is a one-to-one field
    # role_type is  a manytomany field
    #------------------------#
    USER_TYPE_CHOCES = ((1, 'CRY User'), (2, 'Partner'),)
    user = models.OneToOneField(User, blank=True, null=True)
    title = models.IntegerField(
        'TITLE_CHOICES', choices=TITLE_CHOICES, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    dob = models.DateField('Date of Birth ', blank=True, null=True)
    adhar_no = models.CharField(max_length=100, null=True, blank=True)
    pan_no = models.CharField(max_length=100, null=True, blank=True)
    organization_unit = models.ForeignKey(
        OrganizationUnit, blank=True, null=True)
    role_type = models.ManyToManyField(RoleTypes, blank=True)
    mobile_number = models.CharField(max_length=100, null=True, blank=True)
    user_type = models.IntegerField(choices=USER_TYPE_CHOCES, default=1)
    partner = models.ForeignKey('partner.Partner', null=True, blank=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = 'User Role'

    def user_roles_names(self):
        try:
            return ', '.join([i.name for i in self.role_type.all()])
        except:
            return ''

    def get_region_name(self):
        response = {'region_id': 0, 'region_name': ''}
        emp_region = EmploymentDetail.objects.filter(active=2, user=self.user)
        if emp_region:
            emp_ = emp_region[0]
            response['region_id'] = emp_.region.id
            response['region_name'] = emp_.region.name
        return response

    @staticmethod
    def get_location_type(loc_type):
        get_default = Boundary.objects.get(slug__iexact='location-rural')
        if not loc_type:
            get_default.id
        return loc_type

    def get_address(self):
        from django.contrib.contenttypes.models import ContentType
        main_address = {}
        address1 = address2 = boundary = pincode = contact_no = master_level = parent_id = parent_boundary_level = location_type = ''
        ward_type = 0
        boundary_name = parent_name = ""
        address_ = Address.objects.filter(content_type=ContentType.objects.get_for_model(
            self), object_id=self.id).order_by('-id')
        if address_:
            address = address_[0]
            address1 = address.address1
            address2 = address.address2
            try:
                location_type = get_location_type(
                    int(address.boundary.object_id))
                boundary = int(address.boundary.id)
                boundary_name = address.boundary.name
                parent_id = int(address.boundary.parent_id)
                parent_name = address.boundary.parent.name
                master_level = int(address.boundary.boundary_level)
                parent_boundary_level = int(
                    address.boundary.parent.boundary_level)
                ward_type = address.boundary.ward_type.id if address.boundary.ward_type else 0
                pincode = address.pincode
                contact_no = address.contact_no
            except:
                pass
        main_address = {'address1': address1, 'address2': address2, 'boundary_id': boundary,'boundary_name':boundary_name,
                        'pincode': pincode, 'contact_no': contact_no, 'location_type': get_location_type(location_type),
                        'master_level': master_level, 'parent_id': parent_id,'parent_name':parent_name,
                        'parent_boundary_level': parent_boundary_level, 'ward_type': ward_type}
        return main_address

    def managelocationstatus(self):
        location_status = 'False'
        try:
            orgunit = OrganizationUnit.objects.get(
                id=int(self.organization_unit.id))
            if orgunit.organization_type == 2:
                location_status = 'True'
        except:
            location_status = 'False'
        return location_status

    def locationstagged(self):
        orglocation = OrganizationLocation.objects.filter(
            user__id=int(self.id))
        if orglocation:
            location_status = 'True'
        else:
            location_status = 'False'
        return location_status

    def get_user_partner(u_id):
        return UserRoles.objects.get(user__id=uid).partner

    def get_location_type(self):
        loc_ = []
        get_organization = OrganizationLocation.objects.filter(
            active=2, user=self).values_list('location__id').order_by('-id')
        if get_organization:
            loc_ = list(chain.from_iterable(list(get_organization)))
        return loc_

class OrganizationLocation(BaseContent):
    ORGANIZATION_LEVEL_CHOCES = (
        (1, 'Country'), (2, 'State'),
        (3, 'District'), (4, 'Block'),
        (5, 'GramaPanchayath'), (6, 'Village'),
        (7, 'Hamlet'),
    )
    user = models.ForeignKey(UserRoles)
    organization_level = models.IntegerField(
        choices=ORGANIZATION_LEVEL_CHOCES,  null=True, blank=True)
    location = models.ManyToManyField('masterdata.Boundary', blank=True)

    def __unicode__(self):
        return str(self.user.user.first_name)


class EmploymentDetail(BaseContent):
    user = models.ForeignKey(
        'auth.User', related_name="user_reference", blank=True, null=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    designation = models.ForeignKey(
        'masterdata.MasterLookUp', related_name="designation_type", blank=True, null=True)
    region = models.ForeignKey(
        'masterdata.MasterLookUp', related_name="region_type", blank=True, null=True)
    reporting_to = models.ForeignKey(
        'auth.User', related_name="reporting_user", blank=True, null=True)

    def __str__(self):
        return str(self.id)


class RoleConfig(BaseContent):
    #-----------------------#
    # role config model
    # role,menu is a foriegn key
    #------------------------#
    role = models.ForeignKey(RoleTypes, blank=True, null=True)
    menu = models.ForeignKey(Menus)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    view = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    search = models.BooleanField(default=False)

    def __str__(self):
        return self.menu.name

    class Meta:
        verbose_name_plural = 'Role Config'

    def update(self, perms):
        #----------------------#
        # providing checkbox to give permission for particular menu
        # includes add,edit,view,delete,search
        #-----------------------#
        for perm in ['add', 'edit', 'view', 'delete',
                     'search', 'mlist', 'generate',
                     'task_status', ]:
            if perm in perms:
                self.__setattr__(perm, 2)
            else:
                self.__setattr__(perm, 0)
        self.save()

OFFICE_TYPE = ((1, 'registered_office'), (2, 'head_office'), (3,
                                                              'registered_&_head office'), (4, 'correspondence_office'), (5, 'project_manager'))


class Address(BaseContent):
    #---------------------------------#
    # model used for address
    # state,country is a foriegn key
    # address is using as a genricforiegnkey
    #---------------------------------#
    office = models.IntegerField(choices=OFFICE_TYPE, blank=True, null=True)
    address1 = models.CharField(
        'Address1', max_length=600, blank=True, null=True)
    address2 = models.CharField(
        'Address2', max_length=600, blank=True, null=True)
    boundary = models.ForeignKey('masterdata.Boundary', blank=True, null=True)
    contact_no = models.CharField(
        'Contact Number', max_length=600, blank=True, null=True)
    pincode = models.CharField(
        'Pincode', max_length=600, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, verbose_name=_(
        'content type'), related_name="content_type_set_for_%(class)s", blank=True, null=True)
    object_id = models.IntegerField(_('object ID'), blank=True, null=True)
    relatedTo = GenericForeignKey(
        ct_field="content_type", fk_field="object_id")
    proof = models.ForeignKey('masterdata.MasterLookUp', 
            related_name="address_proof", blank=True, null=True)
    address_type = models.ForeignKey('masterdata.MasterLookUp',blank=True,null=True)

    def __unicode__(self):
        return str(self.id)


class EmergencyContactDetail(BaseContent):
    name = models.CharField('Emergency Contact Name',
                            max_length=100, blank=True, null=True)
    relationship = models.CharField(
        'Emergency Contact Name', max_length=250, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, verbose_name=_(
        'content type'), related_name="content_type_set_for_%(class)s", blank=True, null=True)
    object_id = models.TextField(_('object ID'), blank=True, null=True)
    relatedTo = GenericForeignKey(
        ct_field="content_type", fk_field="object_id")

    def get_emergency_address(self):
        from django.contrib.contenttypes.models import ContentType
        emr_address1 = emr_address2 = emr_boundary = emr_pincode = emr_contact_no = emr_master_level = emr_parent_id = emr_parent_boundary_level = emr_location_type = ''
        emr_boundary_name = emr_parent_name = ""
        main_address = {}
        emergency_address = Address.objects.filter(content_type=ContentType.objects.get_for_model(
            self), object_id=self.id).order_by('-id')
        emr_ward_type = 0
        if emergency_address:
            address = emergency_address[0]
            emr_address1 = address.address1
            emr_address2 = address.address2
            try:
                emr_location_type = get_location_type(
                    int(address.boundary.object_id))
                emr_boundary = int(address.boundary.id)
                emr_boundary_name = address.boundary.name
                emr_parent_id = int(address.boundary.parent_id)
                emr_parent_name = address.boundary.parent.name
                emr_master_level = int(address.boundary.boundary_level)
                emr_parent_boundary_level = int(
                    address.boundary.parent.boundary_level)
                emr_ward_type = address.boundary.ward_type.id if address.boundary.ward_type else 0
                emr_pincode = address.pincode
                emr_contact_no = address.contact_no
            except:
                pass
        main_address = {'address1': emr_address1, 'address2': emr_address2, 'boundary_id': emr_boundary,'boundary_name':emr_boundary_name,
                        'pincode': emr_pincode, 'contact_no': emr_contact_no, 'location_type': get_location_type(emr_location_type),
                        'master_level': emr_master_level, 'parent_id': emr_parent_id,'parent_name':emr_parent_name,
                        'parent_boundary_level': emr_parent_boundary_level, 'ward_type': emr_ward_type}
        return main_address

    def get_contact_details(self):
        from masterdata.models import ContactDetail
        contact_list = ContactDetail.objects.filter(
            content_type=ContentType.objects.get_for_model(self), object_id=self.id)
        contacts = [{'contact_no': i.contact_no} for i in contact_list]
        return contacts


class ADTable(BaseContent):
    username = models.CharField(max_length=200, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.username, self.email)

class UserPartnerMapping(BaseContent):
    user = models.ForeignKey(User)
    partner = models.ManyToManyField('partner.Partner')

    def __unicode__(self):
        return "%s" % (self.user)
