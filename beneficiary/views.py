from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import *
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
import json

from .serializers import BeneficiarySerializer, BeneficiaryAddSerializer,\
            BeneficiaryModelSerializer, BeneficiaryAddressSerializer,\
            BeneficiaryRelationSerializer, BeneficiaryAddressSerializerCustom,\
            BeneficiaryTypeSerializer
from .models import Beneficiary, BeneficiaryType, BeneficiaryRelation
from userroles.models import Address, OrganizationLocation
from masterdata.models import Boundary, MasterLookUp
from masterdata.views import pg_size, CustomPagination
from math import ceil
from facilities.models import CodeConfig, Facility, CodeContentCount
from service.models import Service
from service.views import model_field_exists
from datetime import datetime
from django.db.models.fields.related import ManyToManyField
from django.db.models import ForeignKey
from partner.models import Partner
import pytz
import uuid

class BeneficiaryAdd(CreateAPIView):
    serializer_class = BeneficiaryAddSerializer

    def post(self, request):
        serializer = BeneficiaryAddSerializer(data=request.data)

        response = {}
        if serializer.is_valid():
            dt = request.data
            version = float(dt.get('av',0.0))
            if version < 25.0:
                response.update({'msg':'Please Update Your App', 'status':0})
                return Response(response)
            var1 = ['btype', 'name', 'parent_id', 'partner_id', 'beneficiary_type_id']
            
            data1 , data2 = {}, {}
            for v1 in var1:
                if v1 in dt.keys():
                    data1.update({v1:dt.get(v1)})
            data1.update({'jsondata':dict(dt)})
            obj = Beneficiary.objects.create(**data1)
            obj.uuid = request.data.get('uuid') or uuid.uuid4()
            try:
                obj.created = pytz.utc.localize(datetime.strptime(request.data.get('created_date')+".10000","%Y-%m-%d %H:%M:%S.%f"))
            except:
                pass
            obj.save()
            fadd(obj)
            address = request.data['address']
            addrdict = eval(address)
            addrkeys = eval(address).keys()
            for addr in addrkeys:
                hs = addr.split('_')
                adict = addrdict[addr]
                add_list = ['address_id', 'least_location_name', 'primary', 'location_level']
                remove_element_from_dict(adict, add_list)
                addr_obj = Address.objects.create(**adict)
                if hs[1] == '0':
                    addr_obj.office = 1
                else:
                    addr_obj.office = 0
                addr_obj.content_type = ContentType.objects.get_for_model(obj)
                addr_obj.object_id = obj.id
                addr_obj.save()
            response.update({'msg':'Success', 'status':2, 'ben_id':obj.id})
            return Response(response)
        response.update({'msg':'Invalid Data', 'status':0})
        response.update(serializer.errors)
        return Response(response)


def remove_element_from_dict(dict1, list_of_elements):
    for kl in list_of_elements:
        try:
            del dict1[kl]
        except:
            pass
    return None


class HouseholdLisitng(APIView):

    def post(self, request):
        response = {}
        response = [{'id':i.id, 'name':i.name} for i in Beneficiary.objects.filter(btype='Household', parent=None, active=2)]
        return Response(response)

class HouseholdDetail(APIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        """
        Detail for Beneficiary
        ---
            parameters:
            - name: id
              description: Enter Id
              type: Integer
              required: true
        """
        response = {}
        objid = request.data['id']
        obj = Beneficiary.objects.get(id=objid)
        exclude_fields = ['id', 'jsondata']
        all_fields = [i for i in Beneficiary._meta.get_all_field_names() if not i in exclude_fields]
        get_fields = [i for i in Beneficiary._meta.get_fields()]
        data = {}
        obj = None

        try:
            obj = Beneficiary.objects.get(id=objid)
        except:
            pass
        address_objs = Address.objects.filter(content_type=
            ContentType.objects.get_for_model(obj), object_id=obj.id)
        if obj:
            for field in all_fields:
                try:
                    if self.get_fk_model(Beneficiary, field):
                        g = getattr(obj, field)
                        data.update({field:g.name})
                except:
                    pass
                try:
                    if obj.__dict__[field] == None:
                        obj.__dict__[field] = ''
                    data.update({field:obj.__dict__[field]})
                except:
                    pass
            if hasattr(obj, 'jsondata'):
                jsondata = obj.jsondata.items()
                for jdata in jsondata:
                    get_jsondata_details(jdata, data)
            for field in get_fields:
                if isinstance(field, ManyToManyField):
                    data.update({field.name:list(field.value_from_object(obj).values_list('pk', flat=True))})
            try:
                if isinstance(obj.jsondata['mother_uuid'],list):
                    data['mother_uuid']= obj.jsondata['mother_uuid'][0]
                else:
                    data['mother_uuid']= obj.jsondata['mother_uuid']
            except:
                data['mother_uuid'] = 0
            response.update({'data':data, 'success':2, 'msg':'Success'})
        else:
            response.update({'msg':'Invalid Id', 'success':0})
        if address_objs:
            addrdict = get_household_address_detail(address_objs)
            response.update({'address': addrdict})
        return Response(response)

def get_household_address_detail(address_objs):
    addrdict = []
    address_fields = [i for i in Address._meta.get_all_field_names()]
    for count, aobj in enumerate(address_objs):
        addressdict = {}
        for field1 in address_fields:
            try:
                if aobj.__dict__[field1] == None:
                    aobj.__dict__[field1] = ''
                addressdict.update({field1:aobj.__dict__[field1]})
            except:
                pass
            get_beneficiary_address_dict(aobj, addressdict)
        addrdict.append(addressdict)
    return addrdict

def get_beneficiary_address_dict(aobj, addressdict):
    try:
        boundary_obj = Boundary.objects.get(id=int(aobj.boundary_id))
        blist = []
        for rang in range(1,int(boundary_obj.boundary_level)):
            if boundary_obj.parent:
                addressdict.update({'level_'+str(boundary_obj.boundary_level):boundary_obj.parent.pk})
                blist.append(boundary_obj.parent.pk)
                boundary_obj = boundary_obj.parent
        addressdict.update({'level_list':blist})
    except:
        pass
    return None

def get_jsondata_details(jdata, data):
    if jdata[0] in ['age', 'contact_no', 'gender', 'date_of_birth', 'dob_option', 'alias_name']:
        if type(jdata[0]) == list:
            lk = jdata[1][0]
        elif jdata[0] == 'contact_no':
            try:
                if type(eval(jdata[1])) == list:
                    lk = eval(jdata[1])
            except:
                if type(eval(jdata[1][0])) == list:
                    lk = eval(jdata[1][0])

        else:
            lk = jdata[1]
        if jdata[1] and jdata[1][0] == 'null':
            lk = ''
        elif jdata[1] and jdata[1][0] != 'null' and jdata[0] in ['date_of_birth', 'dob_option', 'alias_name'] and type(jdata[1]) == list:
            lk = jdata[1][0]
        data.update({jdata[0]:lk})
    if not data.has_key('date_of_birth'):
        data.update({'date_of_birth':''})
    if not data.has_key('dob_option'):
        data.update({'dob_option':''})
    if not data.has_key('alias_name'):
        data.update({'alias_name':''})
    return data


class HouseholdUpdate(CreateAPIView):
    serializer_class = BeneficiaryAddSerializer

    def post(self, request):
        """
        Edit Option for Beneficiary
        ---
            parameters:
            - name: id
              description: Enter Id
              type: Integer
              required: true
        """
        hid = request.data['id']
        obj = None
        response = {'status':0, 'message':'Something went wrong'}
        housedict = {}
        version = float(request.data.get('av',0.0))
        if version < 25.0:
            response.update({'msg':'Please Update Your App', 'status':0})
            return Response(response)
        var1 = ['name', 'parent_id', 'partner_id', 'age', 'contact_no', 'gender', 'date_of_birth', 'dob_option', 'alias_name','mother_uuid']
        try:
            obj = Beneficiary.objects.get(id=hid)
        except:
            pass
        if obj:
            for key in var1:
                if key in request.data.keys():
                    try:
                        eval(obj.jsondata)[key] = request.data.get(key)
                    except:
                        obj.jsondata[key] = request.data.get(key)
                if hasattr(obj, key):
                    housedict.update({key:request.data.get(key)})
            obj.__dict__.update(housedict)
            obj.save()
            try:
                address = request.data['address']
                try:
                    addrkeys = address.keys()
                    addrdict = address
                except:
                    addrkeys = eval(address).keys()
                    addrdict = eval(address)
                for i in obj.get_all_address():
                    i.active = 0
                    i.save()
                for addr in addrkeys:
                    hs = addr.split('_')
                    adict = addrdict[addr]
                    try:
                        addr_obj = Address.objects.get(id=int(adict['address_id']))
                        addr_obj.__dict__.update(adict)
                    except:
                        add_list = ['address_id', 'least_location_name', 'primary', 'location_level']
                        remove_element_from_dict(adict, add_list)
                        addr_obj = Address.objects.create(**adict)
                        addr_obj.content_type = ContentType.objects.get_for_model(obj)
                        addr_obj.object_id = obj.id
                    if hs[1] == '0':
                        addr_obj.office = 1
                    else:
                        addr_obj.office = 0
                    addr_obj.active = 2
                    addr_obj.save()
            except:
                pass
            response.update({'status':2, 'message':'Successfully updated'})
        return Response(response)

class ActiveDeactiveActions(APIView):
    """Object Activate and Deactive."""

    def post(self, request):
        """
        API to Switch Active and Deactive.
        ---
        parameters:
        - name: object_id
          description: pass object id
          required: true
          type: integer
          paramType: form
        - name: model_name
          description: pass model name
          required: true
          type: character
          paramType: form
        """
        data = request.data
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if 'model_name' in data.keys() and 'object_id' in data.keys():
            try:
                model_name = data.get('model_name')
                get_object = eval(model_name).objects.get(id=data.get('object_id'))
                get_object.switch()
                response = {'data': {'active': get_object.active },
                                    'message': 'Successfully switched the object.'}
            except:
                pass
        return Response(response)

class RetreiveMother(APIView):
    """ Retreive mother based on Household"""

    def post(self, request):
        """
        Retreive mother based on Household.
        ---
        parameters:
        - name: id
          description: pass household id
          required: true
          type: integer
          paramType: form
        """

        response = {'status': 0, 'message': 'Something went  wrong.'}
        hid = request.data.get('id')
        obj = None
        try:
            obj = Beneficiary.objects.get(id=hid, parent=None)
        except:
            pass
        if not obj:
            response.update({'message': 'Invalid Id', 'data':[]})
        else:
            res = [{'id':i.id, 'name':i.name} for i in Beneficiary.objects.filter(parent=obj, btype='Mother', active=2)]
            response.update({'data':res})
            response.update({'message': 'Success', 'status':2})
        return Response(response)

class GenericListing(CreateAPIView):

    def get_model_class(self):
        model_class = self.kwargs['slug']
        return model_class

    def post(self, request, slug):
        response = {}
        slug = self.get_model_class()
        response = [{'id':i.id, 'name':i.name}
            for i in MasterLookUp.objects.filter(parent__slug=slug)]
        return Response(response)

def fadd(obj):
    key = ''
    curr_month = datetime.today().month
    curr_year = datetime.today().year
    if curr_month > 3:
        year = str(curr_year)[-2:] + str(curr_year+1)[-2:]
        start_date = datetime.strptime("01-04-"+str(curr_year), '%d-%m-%Y')
        end_date = datetime.strptime("31-03-"+str(curr_year+1), '%d-%m-%Y')
    else:
        year = str(curr_year-1)[-2:] + str(curr_year)[-2:]
        start_date = datetime.strptime("01-04-"+str(curr_year-1), '%d-%m-%Y')
        end_date = datetime.strptime("31-03-"+str(curr_year), '%d-%m-%Y')
    class_name = obj.__class__.__name__
    if class_name == 'Beneficiary':
        obj_ct = ContentType.objects.get_for_model(obj.beneficiary_type)
        cc = CodeConfig.objects.get(ctype=obj_ct, object_id=obj.beneficiary_type.id)
    else:
        obj_ct = ContentType.objects.get_for_model(obj)
        cc = CodeConfig.objects.get(content_type=obj_ct)
    if cc.prefix_type == 'Non-Financial':
        ccc_obj, created = CodeContentCount.objects.get_or_create(content_type=ContentType.objects.get_for_model(cc), financial_year='')
        if created:
            if class_name == 'Beneficiary':
                obj_count = type(obj).objects.filter(beneficiary_type=obj.beneficiary_type).count()
            else:
                obj_count = type(obj).objects.all().count()
            ccc_obj.content_count = obj_count
        else:
            ccc_obj.content_count = ccc_obj.content_count + 1
    else:
        ccc_obj, created = CodeContentCount.objects.get_or_create(content_type=ContentType.objects.get_for_model(cc), financial_year=year)
        if created:
            if not cc.sequence:
                year2 = str(curr_year-1)[-2:] + str(curr_year)[-2:]
                try:
                    ccc_obj_old = CodeContentCount.objects.get(content_type=ContentType.objects.get_for_model(cc), financial_year=year2)
                    ccc_obj.content_count = ccc_obj_old.content_count + 1
                except:
                    if class_name == 'Beneficiary':
                        obj_count = type(obj).objects.filter(created__gte=start_date, created__lte=end_date, beneficiary_type=obj.beneficiary_type).count()
                    else:
                        obj_count = type(obj).objects.filter(created__gte=start_date, created__lte=end_date).count()
                    ccc_obj.content_count = obj_count
            else:
                if class_name == 'Beneficiary':
                    obj_count = type(obj).objects.filter(created__gte=start_date, created__lte=end_date, beneficiary_type=obj.beneficiary_type).count()
                else:
                    obj_count = type(obj).objects.filter(created__gte=start_date, created__lte=end_date).count()
                ccc_obj.content_count = obj_count
        else:
            ccc_obj.content_count = ccc_obj.content_count + 1
    ccc_obj.save()
    if cc.prefix_type == 'Non-Financial':
        year = curr_year
    start_number, padlength, separator, prefix = 0, 6, '-', 'BEN'
    if cc.start_number:
        start_number = cc.start_number
    if cc.padlength:
        padlength = cc.padlength
    if cc.separator:
        separator = cc.separator
    if cc.prefix:
        prefix = cc.prefix
    key = prefix + str(separator) + str(year) +\
        str(separator) + format((start_number + ccc_obj.content_count), '0'+str(padlength)+'d')
    if hasattr(obj, 'code'):
        obj.code = key
        obj.save()
    return key

class BeneficiaryMenuListing(CreateAPIView):

    def post(self, request):
        response = []
        for i in BeneficiaryType.objects.filter(parent=None).order_by('order'):
            if i.get_childs():
                main_menu_dict = {}
                main_menu_dict.update({'id':i.id, 'name':i.name, 'order':i.order if i.order else ''})
                sub_menu_list = []
                for j in i.get_childs():
                    sub_menu_dict = {}
                    sub_menu_dict.update({'id':j.id, 'name':j.name, 'order':j.order if j.order else ''})
                    sub_menu_list.append(sub_menu_dict)
                main_menu_dict.update({'submenus':sub_menu_list})
                response.append(main_menu_dict)
        return Response(response)

class BeneficiaryTypeWiseListing(APIView):

    def post(self, request):

        """
            Retreive Beneficiary type wise listing
            ---
            parameters:
            - name: id
              description: pass beneficiary id
              required: true
              type: integer
              paramType: form
        """
        response = {}
        bid = request.data['id']
        try:
            partner_id = int(request.data['partner_id'])
        except:
            partner_id = ''
        if partner_id:
            beneficiary_objs = Beneficiary.objects.filter(beneficiary_type_id=bid,partner__id = partner_id)
        else:
            beneficiary_objs = Beneficiary.objects.filter(beneficiary_type_id=bid)
        if request.POST.get('name'):
            beneficiary_objs = beneficiary_objs.filter(name__icontains=request.POST.get('name'))
        if request.POST.get('age'):
            beneficiary_objs = beneficiary_objs.filter(jsondata__icontains=request.POST.get('age'))
        if request.POST.get('gender'):
            beneficiary_objs = beneficiary_objs.filter(jsondata__icontains=request.POST.get('gender'))
        data = []
        for i in beneficiary_objs:
            age = ''
            try:
                if type(i.jsondata.get('age')) == list:
                    age = i.jsondata.get('age')[0]
                else:
                    age = i.jsondata.get('age')
            except:
                pass
            beneficiary_dict = {}
            beneficiary_dict.update({'id':i.id, 'name':i.name,
                'code':i.code if i.code else '',
                'age':age if age else '',
                'related_survey':[],
                'active':i.active})
            data.append(beneficiary_dict)
        data.append(dict(pages=ceil(float(beneficiary_objs.count()) / float(pg_size))))
        get_page = int(data[-1].get('pages'))
        paginator = CustomPagination()
        del data[-1]
        result_page = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'),15,  get_page)

class RetreiveBtypeParentsListing(APIView):

    def post(self, request):
        """
            Retreive Beneficiary type parent listing
            ---
            parameters:
            - name: beneficiary_type_id
              description: pass beneficiary type id
              required: true
              type: integer
              paramType: form
            - name: partner_id
              description: pass partner id
              required: false
              type: integer
              paramType: form
        """
        response = {'status':0}
        btid = request.data['beneficiary_type_id']
        try:
            partner_id = request.data['partner_id']
        except:
            partner_id = None
        parent_obj = None
        try:
            parent_obj = BeneficiaryType.objects.get(id=btid, is_main=0).parent
        except:
            pass
        if parent_obj:
            beneficiary_type_objs = BeneficiaryType.objects.filter(parent=parent_obj, is_main=2)
            for i in beneficiary_type_objs:
                beneficiary_type_list = []
                if partner_id:
                    beneficiary_obj = Beneficiary.objects.filter(beneficiary_type=i, active=2, partner_id=partner_id)
                else:
                    beneficiary_obj = Beneficiary.objects.filter(beneficiary_type=i, active=2)
                for j in beneficiary_obj:
                    beneficiary_dict = {}
                    beneficiary_dict.update({'id':j.id, 'name':j.name})
                    beneficiary_type_list.append(beneficiary_dict)
                response.update({i.name:beneficiary_type_list, 'status':2})
        return Response(response)

class BeneficiaryAddress(RetrieveUpdateAPIView):
    serializer_class = BeneficiaryAddressSerializer
    lookup_field = 'pk'
    queryset = Address.objects.all()

    def get(self, request, pk):
        response = {'status':0}
        addressdict = {}
        address_fields = [i for i in Address._meta.get_all_field_names()  if not i in ['content_type', 'boundary']]
        try:
            address_obj = Address.objects.get(id=int(pk))
            for field1 in address_fields:
                try:
                    if address_obj.__dict__[field1] == None:
                        address_obj.__dict__[field1] = ''
                    response.update({field1:address_obj.__dict__[field1]})
                except:
                    pass
            boundary_obj = Boundary.objects.get(id=int(address_obj.boundary_id))
            orig_value = boundary_obj.object_id
            blist = []
            for rang in range(1,int(boundary_obj.boundary_level)):
                if boundary_obj.parent:
                    addressdict.update({'level_'+str(boundary_obj.boundary_level):boundary_obj.parent.pk})
                    blist.append(boundary_obj.parent.pk)
                    boundary_obj = boundary_obj.parent
            response.update({'level_list':blist,'location_type_slug':MasterLookUp.objects.get(id=orig_value).slug if orig_value else ''})
        except:
            response.update({'level_list':[],'location_type_slug':''})
        return Response(response)

class BeneficiaryAddressCreate(CreateAPIView):
    serializer_class = BeneficiaryAddressSerializerCustom

    def get_model_class(self):
        dic = {'beneficiary':Beneficiary}
        model_class = dic[self.kwargs['key']]
        return model_class

    def post(self, request, key):
        """
            Retreive Beneficiary address create
            ---
            parameters:
            - name: id
              description: pass beneficiary id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        var1 = ['boundary_id', 'pincode', 'address1', 'address2', 'contact_no']
        data = {}
        model = self.get_model_class()
        content_type_id = ContentType.objects.get_for_model(model).id
        object_id = request.data['id']
        for key in var1:
            data.update({key:request.data.get(key)})
        data.update({'content_type_id':content_type_id, 'object_id':object_id})
        address_obj = Address.objects.create(**data)
        address_obj.save()
        response.update({'status':2, 'message':'Added Successfully'})
        return Response(response)

class BeneficiaryAddressUpdate(CreateAPIView):
    serializer_class = BeneficiaryAddressSerializerCustom

    def post(self, request):
        """
            Retreive Beneficiary address detail
            ---
            parameters:
            - name: id
              description: pass address id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        obj = None
        var1 = ['boundary_id', 'pincode', 'address1', 'address2', 'contact_no', 'proof_id']
        try:
            obj = Address.objects.get(id=request.data['id'])
        except:
            pass
        data = {}
        if obj:
            for key in var1:
                if hasattr(obj, key):
                    data.update({key:request.data.get(key)})
            obj.__dict__.update(data)
            obj.save()
            try:
                obj.relatedTo.save()
            except:
                pass
            response.update({'status':2, 'message':'Updated Successfully'})
        return Response(response)

class BeneficiaryRelationCreate(CreateAPIView):
    serializer_class = BeneficiaryRelationSerializer

    def post(self, request):
        response = {'status':0}
        dt = request.data
        data, data1 = {}, {}
        var1 = ['primary_beneficiary_id', 'secondary_beneficiary_id', 'relation_id', 'partner_id']
        for v1 in var1:
            if v1 in dt.keys():
                data.update({v1:dt.get(v1)})
        for v1 in var1:
            if v1 == 'primary_beneficiary_id':
                data1.update({'secondary_beneficiary_id':dt.get('primary_beneficiary_id')})
            elif v1 == 'secondary_beneficiary_id':
                data1.update({'primary_beneficiary_id':dt.get('secondary_beneficiary_id')})
            else:
                data1.update({v1:dt.get(v1)})
        br_obj1 = BeneficiaryRelation.objects.filter(**data1)
        br_obj = BeneficiaryRelation.objects.filter(**data)
        if dt['primary_beneficiary_id'] == dt['secondary_beneficiary_id']:
            response.update({'message':"Both primary and secondary beneficiary should not be same"})
        elif not br_obj and not br_obj1:
            br_obj_create= BeneficiaryRelation.objects.create(**data)
            br_obj_create.save()
            response = {'status':2, 'message':'Added Successfully'}
        else:
            response.update({'message':"Relation already exists"})
        return Response(response)

class BeneficiaryRealtionListing(APIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        """
            Retreive Beneficiary relation listing
            ---
            parameters:
            - name: partner_id
              description: pass partner id
              required: false
              type: integer
              paramType: form
        """
        response = {'status':0}
        try:
            partner_id = request.data['partner_id']
        except:
            partner_id = None
        response = {}
        exclude_fields = ['jsondata']
        all_fields = [i for i in BeneficiaryRelation._meta.get_all_field_names() if not i in exclude_fields]
        if partner_id:
            object_list = BeneficiaryRelation.objects.filter(active=2, partner_id=partner_id).order_by('-id')
        else:
            object_list = BeneficiaryRelation.objects.filter(active=2).order_by('-id')
        data = []
        for obj in object_list:
            objdict = {}
            for field in all_fields:
                try:
                    if self.get_fk_model(BeneficiaryRelation, field):
                        g = getattr(obj, field)
                        objdict.update({field:g.name})
                        if field == 'partner':
                            objdict.update({'name':g.name})
                except:
                    pass
                try:
                    if obj.__dict__[field] == None:
                        obj.__dict__[field] = ''
                    objdict.update({field:obj.__dict__[field]})
                except:
                    pass
            data.append(objdict)
        response.update({'data':data, 'status':2, 'message':'Successfully Retrieved'})
        data.append(dict(pages=ceil(float(object_list.count()) / float(pg_size))))
        get_page = int(data[-1].get('pages'))
        paginator = CustomPagination()
        del data[-1]
        result_page = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'),16,  get_page)

class RetreiveBeneficiaryTypes(APIView):

    def post(self, request):
        response = []
        object_list = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('id')
        for i in object_list:
            main_menu_dict = {}
            main_menu_dict.update({'id':i.id, 'name':i.name, 'order':i.order if i.order else ''})
            response.append(main_menu_dict)
        return Response(response)

class RetreivePartnerBasedBeneficiary(APIView):

    def post(self, request):
        """
            Retreive Beneficiary partner wise listing
            ---
            parameters:
            - name: beneficiary_type_id
              description: pass beneficiary type id
              required: true
              type: integer
              paramType: form
            - name: partner_id
              description: pass partner id
              required: true
              type: integer
              paramType: form
        """
        response = []
        object_list = Beneficiary.objects.filter(active=2, partner_id=request.data['partner_id'], beneficiary_type_id=request.data['beneficiary_type_id']).order_by('id')
        for i in object_list:
            main_menu_dict = {}
            main_menu_dict.update({'id':i.id, 'name':i.get_boundary_name(), 'code':i.code})
            response.append(main_menu_dict)
        return Response(response)

class BeneficiaryRealtionDetail(APIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        """
            Retreive Beneficiary relation detail
            ---
            parameters:
            - name: id
              description: pass beneficiary relation id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        obj = None
        try:
            obj = BeneficiaryRelation.objects.get(id=request.data['id'])
        except:
            pass
        if obj:
            all_fields = [i for i in BeneficiaryRelation._meta.get_all_field_names()]
            objdict = {}
            for field in all_fields:
                try:
                    if field == 'primary_beneficiary_id':
                        btype_id = Beneficiary.objects.get(id=int(obj.__dict__[field])).beneficiary_type_id
                        objdict.update({'primary_beneficiarytype_id':btype_id})
                    if field == 'secondary_beneficiary_id':
                        btype_id = Beneficiary.objects.get(id=int(obj.__dict__[field])).beneficiary_type_id
                        objdict.update({'secondary_beneficiarytype_id':btype_id})
                except:
                    pass
                try:
                    if self.get_fk_model(BeneficiaryRelation, field):
                        g = getattr(obj, field)
                        objdict.update({field:g.name})
                except:
                    pass
                try:
                    if obj.__dict__[field] == None:
                        obj.__dict__[field] = ''
                    objdict.update({field:obj.__dict__[field]})
                except:
                    pass
            response.update(objdict)
            response.update({'status':2})
        return Response(response)

class BeneficiaryRelationUpdate(CreateAPIView):
    serializer_class = BeneficiaryRelationSerializer

    def post(self, request):
        """
            Retreive Beneficiary relation detail
            ---
            parameters:
            - name: id
              description: pass beneficiary relation id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        dt = request.data
        data, data1 = {}, {}
        var1 = ['primary_beneficiary_id', 'secondary_beneficiary_id', 'relation_id', 'partner_id']
        for v1 in var1:
            if v1 in dt.keys():
                data.update({v1:dt.get(v1)})
        for v1 in var1:
            if v1 == 'primary_beneficiary_id':
                data1.update({'secondary_beneficiary_id':dt.get('primary_beneficiary_id')})
            elif v1 == 'secondary_beneficiary_id':
                data1.update({'primary_beneficiary_id':dt.get('secondary_beneficiary_id')})
            else:
                data1.update({v1:dt.get(v1)})
        br_obj1 = BeneficiaryRelation.objects.filter(**data1).exclude(id=request.data['id'])
        br_obj= BeneficiaryRelation.objects.filter(**data).exclude(id=request.data['id'])
        if dt['primary_beneficiary_id'] == dt['secondary_beneficiary_id']:
            response.update({'message':"Both primary and secondary beneficiary should not be same"})
        elif not br_obj and not br_obj1:
            br_obj_update= BeneficiaryRelation.objects.get(id=request.data['id'])
            br_obj_update.__dict__.update(data)
            br_obj_update.save()
            response = {'status':2, 'message':'Added Updated'}
        else:
            response.update({'message':"Relation already exists"})
        return Response(response)

class BeneficiaryTypeCreate(CreateAPIView):
    serializer_class = BeneficiaryTypeSerializer

    def get_model_class(self):
        dic = {'beneficiarytype': BeneficiaryType}
        model_class = dic[self.kwargs['model']]
        return model_class

    def post(self, request, model):
        response = {'status':0}
        model = self.get_model_class()

        mtm_fields = [i.name for i in model._meta.many_to_many]
        try:
            object_list = model.objects.filter(name=request.data['name'], parent_id=request.data['parent_id'])
        except:
            object_list = model.objects.filter(name=request.data['name'], parent=None)
        try:
            object_list1 = model.objects.filter(order=request.data['order'], parent_id=request.data['parent_id'])
        except:
            object_list1 = model.objects.filter(order=request.data['order'], parent=None)
        if object_list:
            response.update({'status':0, 'message':"Name already exists"})
        elif object_list1:
            response.update({'status':0, 'message':"Beneficiary with this order already exists"})
        else:
            dt = request.data
            var1 = request.data.keys()
            data1 = {}
            for v1 in var1:
                if (not v1 in mtm_fields) and model_field_exists(model, v1):

                    data1.update({v1:dt.get(v1)})
            model.objects.create(**data1)
            response.update({'message':'Successfully added', 'status':2})
        return Response(response)

class BeneficiaryTypeUpdate(CreateAPIView):
    serializer_class = BeneficiaryTypeSerializer

    def get_model_class(self):
        dic = {'beneficiarytype': BeneficiaryType}
        model_class = dic[self.kwargs['model']]
        return model_class

    def post(self, request, model):
        """
            update beneficiary type
            ---
            parameters:
            - name: id
              description: pass beneficiary type id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        model = self.get_model_class()

        mtm_fields = [i.name for i in model._meta.many_to_many]
        try:
            object_list = model.objects.filter(name=request.data['name'], parent_id=request.data['parent_id']).exclude(id=request.data['id'])
        except:
            object_list = model.objects.filter(name=request.data['name'], parent=None).exclude(id=request.data['id'])
        try:
            object_list1 = model.objects.filter(order=request.data['order'], parent_id=request.data['parent_id']).exclude(id=request.data['id'])
        except:
            object_list1 = model.objects.filter(order=request.data['order'], parent=None).exclude(id=request.data['id'])
        if object_list:
            response.update({'status':0, 'message':"Name already exists"})
        elif object_list1:
            response.update({'status':0, 'message':"Beneficiary with this order already exists"})
        else:
            dt = request.data
            var1 = request.data.keys()
            data1 = {}
            obj = model.objects.get(id=request.data['id'])
            for v1 in var1:
                if (not v1 in mtm_fields) and model_field_exists(model, v1):

                    data1.update({v1:dt.get(v1)})
            obj.__dict__.update(data1)
            obj.save()
            response.update({'message':'Successfully updated', 'status':2})
        return Response(response)

class BeneficiarySubTypeListing(CreateAPIView):

    def post(self, request):
        response = {}
        response = [{'id':i.id, 'name':i.name}
            for i in BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('id')]
        return Response(response)

class UpdateAddressType(CreateAPIView):

    def get_model_class(self):
        dic = {'beneficiary': Beneficiary, 'partner':Partner}
        model_class = dic[self.kwargs['model']]
        return model_class

    def post(self, request, model):
        """
            update beneficiary address type
            ---
            parameters:
            - name: id
              description: pass content type id
              required: true
              type: integer
              paramType: form
            - name: address_id
              description: pass address id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        model = self.get_model_class()
        address_objs = Address.objects.filter(content_type=ContentType.objects.get_for_model(model), object_id=request.data['id'])
        for i in address_objs:
            i.office = None
            i.save()
        address_obj = Address.objects.get(id=request.data['address_id'])
        address_obj.office = 1
        address_obj.save()
        response.update({'status':2, 'message':"Successfully updated"})
        return Response(response)

def convert_string_to_date(string):
    date_object = ''
    try:
        date_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    except:
        date_object = None
    if not date_object:
        try:
            date_obj = datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f')
            date_object = datetime(int(date_obj.year),int(date_obj.month),int(date_obj.day),int(date_obj.hour),int(date_obj.minute),int(date_obj.second),int(date_obj.microsecond),pytz.UTC)
        except:
            date_object = None
    return date_object

def get_user_location_ids(user_id):
    location_ids = []
    user_roles = OrganizationLocation.objects.filter(user__user_id=user_id)
    for i in user_roles:
        for loc in i.location.all():
            if loc.boundary_level == 7:
                location_ids.append(int(loc.id))
            elif loc.boundary_level == 6:
                location_ids.extend(Boundary.objects.filter(parent_id=int(loc.id), boundary_level=7).values_list("id",flat=True))
            elif loc.boundary_level == 5:
                location_ids.extend(Boundary.objects.filter(parent__parent_id=int(loc.id), boundary_level=7).values_list("id",flat=True))
            elif loc.boundary_level == 4:
                location_ids.extend(Boundary.objects.filter(parent__parent__parent_id=int(loc.id), boundary_level=7).values_list("id",flat=True))
            elif loc.boundary_level == 3:
                location_ids.extend(Boundary.objects.filter(parent__parent__parent__parent_id=int(loc.id), boundary_level=7).values_list("id",flat=True))
            elif loc.boundary_level == 2:
                location_ids.extend(Boundary.objects.filter(parent__parent__parent__parent__parent_id=int(loc.id), boundary_level=7).values_list("id",flat=True))
#            elif loc.boundary_level == 3:
#                location_ids.extend(Boundary.objects.filter(parent__parent__parent__parent__parent__parent_id=int(loc.id), boundary_level=9).values_list("id",flat=True))
#            elif loc.boundary_level == 2:
#                location_ids.extend(Boundary.objects.filter(parent__parent__parent__parent__parent__parent__parent_id=int(loc.id), boundary_level=9).values_list("id",flat=True))
    return list(set(location_ids))

class BeneficiaryListingDateWise(CreateAPIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        """
            Retreive Beneficiary type parent listing
            ---
            parameters:
            - name: modified_date
              description: pass modified date
              required: false
              type: string
              paramType: form
            - name: user_id
              description: pass user id
              required: true
              type: integer
              paramType: form
            - name: partner_id
              description: pass partner id
              required: true
              type: integer
              paramType: form
        """
        response = {}
        modified_on = ''
        try:
            modified_on = request.data['modified_date']
        except:
            pass

        partner_id = request.data.get('partner_id')
        import ipdb; ipdb.set_trace()
        date_object = convert_string_to_date(modified_on)
        if not partner_id:
            object_list_ids =[]
        elif date_object:
            object_list_ids = Beneficiary.objects.filter(modified__gt=date_object,partner__id=int(partner_id)).values_list('id',flat=True)
        else:
            object_list_ids = Beneficiary.objects.filter(partner__id=int(partner_id)).values_list('id',flat=True)
        if request.data.get('dumpdb') == 'True':
            beneficiaries = Beneficiary.objects.filter(id__in=object_list_ids).order_by('modified')
        else:
            beneficiaries = Beneficiary.objects.filter(id__in=object_list_ids).order_by('modified')[:800]
        if request.POST.get('name'):
            beneficiaries = beneficiaries.filter(name__icontains=request.POST.get('name'))
        if request.POST.get('age'):
            beneficiaries = beneficiaries.filter(name__icontains=request.POST.get('age'))
        if request.POST.get('gender'):
            beneficiaries = beneficiaries.filter(name__icontains=request.POST.get('gender'))
        beneficiary_list = []
        exclude_fields = ['jsondata']
        all_fields = [i for i in Beneficiary._meta.get_all_field_names() if not i in exclude_fields]
        for obj in beneficiaries:
            objdict = {}
            try:
                if isinstance(obj.jsondata.get('mother_uuid'),list):
                    objdict['muuid']=str(obj.jsondata.get('mother_uuid')[0])
                else:
                    objdict['muuid'] = str(obj.jsondata.get('mother_uuid'))
            except:
                objdict['muuid']=""
            
            address_objs = obj.get_all_address()

            if obj.parent:
                objdict.update({'puuid':str(obj.parent.uuid)})
            else:
                objdict.update({'puuid':''})
            for field in all_fields:
                get_updated_bendict(self, field, objdict, obj)
                get_updated_jsondict(obj, objdict)
            ben_data = get_updated_benlist(beneficiary_list, objdict, address_objs)
            beneficiary_list = ben_data['beneficiary_list']
            objdict = ben_data['objdict']
        response.update({'data':beneficiary_list, 'status':2})
        return Response(response)


def get_updated_benlist(beneficiary_list, objdict, address_objs):
    address_list = []
    for address_obj in address_objs:
        if address_obj.boundary:
            address_dict = address_builder(address_obj)
            if address_obj.office == 1:
                address_list.insert(0, address_dict)
            else:
                address_list.append(address_dict)
    objdict.update({"address":address_list})
    beneficiary_list.append(objdict)
    return {'beneficiary_list':beneficiary_list, 'objdict':objdict}

def address_builder(address_obj):
    address_dict = {}
    address_dict.update({'ll': int(address_obj.boundary.boundary_level),
                         'bid': int(address_obj.boundary.id),
                         'llnm': str(address_obj.boundary.name) if address_obj.boundary.name else "",
                         'ad1': str(address_obj.address1.encode('ascii', 'ignore').encode('utf-8')),
                         'ad2': str(address_obj.address2.encode('ascii', 'ignore').encode('utf-8')) if address_obj.address2 else '',
                         'pcd': str(address_obj.pincode),
                         'adid': str(address_obj.id),
                         'proid': str(address_obj.proof_id) if address_obj.proof else "",
                         'pri': 1 if address_obj.office == 1 else 0})
    return address_dict


def get_updated_jsondict(obj, objdict):
    if hasattr(obj, 'jsondata'):
        try:
            jsondata = obj.jsondata.items()
        except:
            jsondata = eval(obj.jsondata).items()
        for jdata in jsondata:
            if jdata[0] in ['age', 'gender', 'contact_no', 'date_of_birth', 'dob_option', 'alias_name']:
                get_dict_updated_agegender(jdata, objdict)
    return None

def get_dict_updated_agegender(jdata, objdict):
    if jdata[0] == 'contact_no':
        lk = get_inner_updated_bendata(jdata)
    elif type(jdata[0]) == list or type(jdata[1]) == list:
        lk = jdata[1][0]
    else:
        lk = jdata[1]
    if jdata[1] and jdata[1][0] == 'null':
        lk = ''
    elif jdata[1] and jdata[1][0] != 'null' and jdata[0] in ['date_of_birth', 'dob_option', 'alias_name']:
        if type(jdata[1]) == list:
            lk = jdata[1][0]
        else:
            lk = jdata[1]
    objdict.update({jdata[0]:lk})
    if not objdict.has_key('date_of_birth'):
        objdict.update({'date_of_birth':''})
    if not objdict.has_key('dob_option'):
        objdict.update({'dob_option':''})
    if not objdict.has_key('alias_name'):
        objdict.update({'alias_name':''})
    return None


def get_inner_updated_bendata(jdata):
    lk = ''

    try:
        if type(eval(jdata[1].replace('null,', ''))) == list:
            lk = map(str, eval(jdata[1].replace('null,', '')))
        elif type(eval(jdata[1].replace('null,', ''))) == tuple:
            lk = map(str, list(eval(jdata[1].replace('null,', ''))))
        elif type(eval(jdata[1].replace('null,', ''))) == int:
            lk = map(str, [jdata[1].replace('null,', '')])
    except:
        if type(filter(None, eval(jdata[1][0].replace('null,', '')))) == list:
            lk = map(str, filter(None, eval(jdata[1][0].replace('null,', ''))))
        elif type(eval(jdata[1][0].replace('null,', ''))) == tuple:
            lk = map(str, list(eval(jdata[1][0].replace('null,', ''))))
        elif type(eval(jdata[1][0].replace('null,', ''))) == int:
            lk = map(str, [jdata[1][0].replace('null,', '')])
    return lk


def get_updated_bendict(self, field, objdict, obj):
    if self.get_fk_model(Beneficiary, field):
        try:
            g = getattr(obj, field)
            objdict.update({field:g.name})
        except:
            objdict.update({field:""})
    try:
        if obj.__dict__[field] == None:
            obj.__dict__[field] = 0
        objdict.update({field:obj.__dict__[field]})
    except:
        pass
    try:
        g = getattr(obj, field)
        objdict.update({field:g.strftime('%Y-%m-%d %H:%M:%S.%f')})
    except:
        pass
    return None
