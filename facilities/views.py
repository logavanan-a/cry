from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import *
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from .serializers import FacilityModelSerializer, FacilityCentreSerializer
from masterdata.models import MasterLookUp, Boundary
from userroles.models import Address
from .models import Facility, FacilityCentre, Centres , FacilityBeneficiaryDeactivate
from service.views import model_field_exists
from service.serializers import ServiceSerializer
from service.models import Service
from django.db.models.fields.related import ManyToManyField
from beneficiary.models import Beneficiary, BeneficiaryType
from beneficiary.serializers import BeneficiaryAddSerializer
from beneficiary.views import fadd
from masterdata.views import CustomPagination
from math import ceil
from masterdata.views import pg_size
from django.db.models import ForeignKey
import uuid
from survey.capture_sur_levels import convert_string_to_date
from django.contrib.auth.models import User


class FacilityAdd(CreateAPIView):


    def get_serializer_class(self):
        dic = {'facility': FacilityModelSerializer, 'service': ServiceSerializer,
               'beneficiary': BeneficiaryAddSerializer}
        serializer_class = dic[self.kwargs['key']]
        return serializer_class

    def get_model_class(self):
        dic = {'facility': Facility, 'service': Service,
               'beneficiary': Beneficiary}
        model_class = dic[self.kwargs['key']]
        return model_class

    def post(self, request, key):
        serializer_class = self.get_serializer_class()
        model = self.get_model_class()
        serializer = serializer_class(data=request.data)
        get_fields = [i for i in model._meta.get_fields()]
        mtm_fields = [i.name for i in model._meta.many_to_many]
        response = {}
        if serializer.is_valid():
            dt = request.data
            version = float(dt.get('av',0.0))
            if version < 25.0:
                response.update({'msg':'Please Update Your App', 'status':0})
                return Response(response)
            var1 = request.data.keys()
            data1, data2 = {}, {}
            for v1 in var1:
                if not v1 in mtm_fields:
                    if model_field_exists(model, v1):
                        data1.update({v1: dt.get(v1)})
                    if model_field_exists(Address, v1):
                        data2.update({v1: dt.get(v1)})
                    if model_field_exists(model, 'jsondata'):
                        data1.update({'jsondata': dict(dt)})
            obj = model.objects.create(**data1)
            if request.data.get('source') == 'android':
                obj.uuid = request.data.get('uuid')
            else:
                obj.uuid = uuid.uuid4()
            obj.save()
            if hasattr(obj, 'code'):
                fadd(obj)

            for field in get_fields:

                if isinstance(field, ManyToManyField):
                    mtm = getattr(obj, field.name)
                    mtm.clear()
                    try:
                        fact = [str(i) for i in
                                request.data.get(field.name).split(',')]
                        mtm.add(*fact)
                    except:
                        pass
            if model.__name__ not in ['Service']:
                address_obj = Address.objects.create(**data2)
                address_obj.content_type = ContentType.objects.get_for_model(
                    obj)
                address_obj.object_id = int(obj.id)
                address_obj.save()
            response.update({'msg': 'Success', 'status': 2, 'objid':obj.id})
        else:
            response.update({'msg': 'Invalid Data', 'status': 0,
                             'errors': serializer.errors})
        return Response(response)


class FacilityUpdate(CreateAPIView):

    def get_serializer_class(self):
        dic = {'facility': FacilityModelSerializer, 'service': ServiceSerializer,
               'beneficiary': BeneficiaryAddSerializer}
        serializer_class = dic[self.kwargs['key']]
        return serializer_class

    def get_model_class(self):
        dic = {'facility': Facility, 'service': Service,
               'beneficiary': Beneficiary}
        model_class = dic[self.kwargs['key']]
        return model_class

    def post(self, request, key):
        """
        Generic Edit Option
        ---
            parameters:
            - name: id
              description: Enter Id
              type: Integer
              required: true
        """
        objid = request.data['id']
        serializer_class = self.get_serializer_class()
        model = self.get_model_class()
        get_fields = [i for i in model._meta.get_fields()]
        serializer = serializer_class(data=request.data)
        response = {}
        obj = None
        smdict = {}
        addr = {}
        aobj = None
        version = float(request.data.get('av',0.0))
        if version < 25.0:
            response.update({'msg':'Please Update Your App', 'status':0})

        if serializer.is_valid() and version >= 25.0:
            var1 = [i for i in request.data.keys() if not i == 'id']
            try:
                obj = model.objects.get(id=objid)
            except:
                pass
            if obj:
                try:
                    aobj = Address.objects.get(
                        content_type=ContentType.objects.get_for_model(obj), object_id=obj.id)
                except:
                    pass
                for k in var1:
                    if hasattr(obj, k):
                        smdict.update({k: request.data.get(k)})
                    if hasattr(aobj, k):
                        addr.update({k: request.data.get(k)})
                if model_field_exists(model, 'jsondata'):
                    smdict.update({'jsondata': dict(request.data)})
                obj.__dict__.update(smdict)
                obj.save()
                if aobj:
                    aobj.__dict__.update(addr)
                    aobj.save()
                for field in get_fields:
                    if isinstance(field, ManyToManyField):
                        mtm = getattr(obj, field.name)
                        mtm.clear()
                        try:
                            fact = [str(i) for i in
                                    request.data.get(field.name).split(',')]
                            mtm.add(*fact)
                        except:
                            pass
                response.update({'status': 2, 'msg': 'Updated successfully'})
            else:
                response.update({'status': 0, 'msg': 'Invalid Id'})
        elif version >= 25.0:
            response.update({'status': 0, 'errors': serializer.errors})
        return Response(response)


class FacilityTypeListing(CreateAPIView):

    def post(self, request):
        response = {}
        response = [{'id': i.id, 'name': i.name, 'sub_category':get_facility_subcategory(i.id)}
                    for i in MasterLookUp.objects.filter(parent__slug='facility-type')]
        return Response(response)


class ThematicAreaListing(CreateAPIView):

    def post(self, request):
        """
        Listing for sub types
        ---
            parameters:
            - name: key
              description: Enter key if not thematic area will be sent
              type: string
              required: false
        """
        key = request.data.get('key', 'theme')
        response = {}
        response = [{'id': i.id, 'name': i.name}
                    for i in MasterLookUp.objects.filter(parent__slug=key)]
        return Response(response)


def get_facility_subcategory(parent_id):
    response = {}
    response = [{'id': i.id, 'name': i.name}
                    for i in MasterLookUp.objects.filter(parent__id=parent_id)]
    return response

class FacilitySubTypeListing(CreateAPIView):

    def post(self, request):
        """
        Listing for Facility subtype
        ---
            parameters:
            - name: id
              description: Enter facility type Id
              type: Integer
              required: true
        """
        response = {}
        response = [{'id': i.id, 'name': i.name}
                    for i in MasterLookUp.objects.filter(parent__id=request.data['id'])]
        return Response(response)


class FacilityDetail(APIView):

    def get_model_class(self):
        dic = {'facility': Facility, 'service': Service,
               'beneficiary': Beneficiary, 'beneficiarytype': BeneficiaryType}
        model_class = dic[self.kwargs['key']]
        return model_class

    def post(self, request, key):
        """
        Generic Detail Option
        ---
            parameters:
            - name: id
              description: Enter Id
              type: Integer
              required: true
        """
        objid = request.data['id']
        response = {}
        model = self.get_model_class()
        exclude_fields = ['id', 'jsondata']

        all_fields = [i for i in model._meta.get_all_field_names()
                      if not i in exclude_fields]
        get_fields = [i for i in model._meta.get_fields()]
        address_fields = [
            i for i in Address._meta.get_all_field_names() if not i == 'id']
        data = {}
        addressdict = {}
        obj = None
        aobj = None
        jsondt = {}
        try:
            obj = model.objects.get(id=objid)
        except:
            pass
        try:
            aobj = Address.objects.get(
                content_type=ContentType.objects.get_for_model(obj), object_id=obj.id)
        except:
            pass

        if obj:
            for field in all_fields:
                try:
                    if obj.__dict__[field] == None:
                        obj.__dict__[field] = ''
                    data.update({field: obj.__dict__[field]})
                except:
                    pass
            for field in get_fields:
                if isinstance(field, ManyToManyField):
                    data.update(
                        {field.name: list(field.value_from_object(obj).values_list('pk', flat=True))})
            if hasattr(obj, 'jsondata'):
                jsondata = ''

                try:
                    jsondata = obj.jsondata.items()
                except:
                    pass
                if not jsondata:
                    try:
                        jsondata = eval(obj.jsondata).items()
                    except:
                        jsondata = eval(eval(obj.jsondata)).items()
                for jdata in jsondata:
                    try:
                        if jdata[1][0] == 'null':
                            jdata[1][0] = ''
                        jsondt.update({jdata[0]: jdata[1][0]})
                    except:

                        pass
                data.update({'jsondata': jsondt})
            response.update({'data': data, 'success': 2, 'msg': 'Success'})
        else:
            response.update({'msg': 'Invalid Id', 'success': 0})
        if aobj:
            for field1 in address_fields:
                try:
                    addressdict.update({field1: aobj.__dict__[field1]})
                except:
                    pass
            response.update({'address': addressdict})
            try:
                boundary_obj = Boundary.objects.get(id=int(aobj.boundary_id))
                if boundary_obj.parent:
                    location_type = boundary_obj.get_facility_data()
                    ward_type = boundary_obj.ward_type.id if boundary_obj.ward_type else 0
                    addressdict.update({'level': boundary_obj.boundary_level,
                                        'boundary_name': boundary_obj.name.encode('ascii', 'replace'),
                                        'boundary_parent_id': boundary_obj.parent.pk,
                                        'boundary_parent_name': boundary_obj.parent.name.encode('ascii', 'replace'),
                                        'location_type': location_type, 'ward_type': ward_type})
            except:
                pass
        return Response(response)


class FacilityListing(APIView):

    def get_model_class(self):
        dic = {'facility': Facility, 'service': Service,
               'beneficiary': Beneficiary, 'beneficiarytype': BeneficiaryType}
        model_class = dic[self.kwargs['key']]
        return model_class

    def get_pagination_id(self):
        dic = {'facility': 11, 'service': 12,
               'beneficiary': 13, 'beneficiarytype': 20}
        pagination_id = dic[self.kwargs['key']]
        return pagination_id

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(
            fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request, key):
        """
        Generic Listing Option
        ---
            parameters:
            - name: partner_id
              description: Enter Id
              type: Integer
              required: false
        """
        response = {}
        model = self.get_model_class()
        page_no = self.get_pagination_id()
        
        try:
            partner_id = request.data['partner_id']
        except:
            partner_id = None
        all_fields = [i for i in model._meta.get_all_field_names()]
        if key == 'beneficiarytype':
            nm = request.POST.get('name')
            object_list = model.objects.filter(
                active=2).exclude(id__in=[1]).order_by('-id')
            
        elif key == 'facility' and partner_id:
                object_list = model.objects.filter(partner_id=partner_id).order_by('-id')
        else:
            object_list = model.objects.filter(active=2).order_by('-id')
        if request.POST.get('name'):
            object_list = object_list.filter(name__icontains=request.POST.get('name'))
        if request.POST.get('btype'):
            object_list = object_list.filter(facility_type_id=request.POST.get('btype'))
        data = []
        for obj in object_list:
            objdict = {}
            for field in all_fields:

                if field == 'jsondata' and key == 'facility':
                    boundary_id = ''
                    try:
                        boundary_id = int(obj.jsondata.get('boundary_id')[0])
                    except:
                        pass
                    if not boundary_id:
                        try:
                            boundary_id = int(
                                eval(obj.jsondata).get('boundary_id')[0])
                        except:
                            boundary_id = int(
                                eval(eval(obj.jsondata)).get('boundary_id')[0])
                    boundary_name = str(
                        Boundary.objects.get(id=boundary_id).name.encode('ascii', 'replace'))
                    objdict.update({'boundary_id': boundary_id,
                                    'boundary_name': boundary_name})
                else:
                    try:
                        if self.get_fk_model(model, field):
                            g = getattr(obj, field)
                            objdict.update({field: g.name})
                    except:
                        pass
                    try:
                        objdict.update({field: obj.__dict__[field]})
                    except:
                        pass

            data.append(objdict)
        response.update({'data': data, 'status': 2,
                         'message': 'Successfully Retrieved'})
        data.append(
            dict(pages=ceil(float(object_list.count()) / float(pg_size))))
        get_page = int(data[-1].get('pages'))
        paginator = CustomPagination()
        del data[-1]
        result_page = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), page_no,  get_page)


class FacilityWtPaginationListing(APIView):

    def get_model_class(self):
        dic = {'facility': Facility, 'service': Service,
               'beneficiary': Beneficiary}
        model_class = dic[self.kwargs['key']]
        return model_class

    def get_pagination_id(self):
        dic = {'facility': 11, 'service': Service, 'beneficiary': Beneficiary}
        pagination_id = dic[self.kwargs['key']]
        return pagination_id

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(
            fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request, key):
        """
            Retreive Datewise listing
            ---
            parameters:
            - name: modified_date
              description: pass modified date
              required: false
              type: string
              paramType: form
            - name: partner_id
              description: pass partner id
              required: false
              type: integer
              paramType: form
        """
        modified_on = ''
        try:
            modified_on = request.data['modified_date']
        except:
            pass
        try:
            partner_id = request.data['partner_id']
        except:
            partner_id = None
        date_object = convert_string_to_date(modified_on)
        response = {}
        model = self.get_model_class()
        flds = []
        all_fields = [i for i in model._meta.get_all_field_names()
                      if not i in flds]
        get_fields = [i for i in model._meta.get_fields()]
        if date_object:
            object_list = model.objects.filter(
                active=2, modified__gt=date_object).order_by('modified')
        else:
            object_list = model.objects.filter(active=2).order_by('modified')
        if partner_id and hasattr(model, 'partner'):

            object_list = object_list.filter(partner_id=partner_id)
        data = []
        for obj in object_list:

            objdict = {}
            for field in all_fields:
                if field == 'jsondata' and key == 'facility':
                    boundary_id = ''
                    try:
                        boundary_id = int(obj.jsondata.get('boundary_id')[0])
                    except:
                        pass
                    if not boundary_id:
                        try:
                            boundary_id = int(
                                eval(obj.jsondata).get('boundary_id')[0])
                        except:
                            boundary_id = int(
                                eval(eval(obj.jsondata)).get('boundary_id')[0])

                    try:
                        if isinstance(obj.jsondata.get('address1'),list):
                            address1 = obj.jsondata.get('address1')[0]
                        else:
                            address1 = obj.jsondata.get('address1') if obj.jsondata.get('address1') else ""
                    except:
                        address1 = eval(obj.jsondata).get('address1')[0]
                    try:
                        if isinstance(obj.jsondata.get('address2'),list):
                            address2 = obj.jsondata.get('address2')[0]
                        else:
                            address2 = obj.jsondata.get('address2') if obj.jsondata.get('address2') else ""
                    except:
                        address2 = eval(obj.jsondata).get('address2')[0]
                    try:
                        if isinstance(obj.jsondata.get('pincode'),list):
                            pincode = obj.jsondata.get('pincode')[0]
                        else:
                            pincode = obj.jsondata.get('pincode') if obj.jsondata.get('pincode') else ""
                    except:
                        pincode = eval(obj.jsondata).get('pincode')[0]
                    boundary_name = str(
                        Boundary.objects.get(id=boundary_id).name.encode('ascii', 'replace'))
                    boundary_level = str(
                        Boundary.objects.get(id=boundary_id).boundary_level)
                    objdict.update({'boundary_id': boundary_id,
                                    'boundary_name': boundary_name,
                                    'pincode':pincode,
                                    'address1':address1,
                                    'address2':address2,
                                    'boundary_level':boundary_level
                                    })
                else:
                    try:
                        objdict.update({field: obj.__dict__[field]})
                    except:
                        pass
                    try:
                        g = getattr(obj, field)
                        objdict.update(
                            {field: g.strftime('%Y-%m-%d %H:%M:%S.%f')})
                    except:
                        pass
                    try:
                        if self.get_fk_model(model, field):
                            g = getattr(obj, field)
                            objdict.update({field: g.name})
                    except:
                        pass
            for field in get_fields:
                if isinstance(field, ManyToManyField):
                    objdict.update(
                        {field.name: list(field.value_from_object(obj).values_list('pk', flat=True))})
            data.append(objdict)
        response.update({'data': data, 'status': 2,
                         'message': 'Successfully Retrieved'})
        return Response(response)



class FacilityTypeList(APIView):
    """
    Retrieve, facility_type list.
    """

    def get(self, request):
        natur = list(set(Facility.objects.all().values_list('facility_type_id',flat=True)))
        obj = MasterLookUp.objects.filter(id__in=natur).values('id','name')
        return Response({'status':2,'data':obj})


class FacilityBeneficiaryActivate_Deactivate(APIView):
    
    def post(self , request):
        status = 0
        post_params = request.POST
        content_obj = ContentType.objects.get(model =  post_params['type'])
        object_id = post_params['id']
        try:
            beneficiary_or_facility = content_obj.get_object_for_this_type(id = object_id)
            beneficiary_or_facility.active = post_params['active']
#            action_taken = post_params['Action']
            user = User.objects.get(id = post_params['userId'])
            FacilityBeneficiaryDeactivate.objects.create(content_type = content_obj , object_id = object_id , reason = post_params['reason'] , user = user)
            beneficiary_or_facility.save()
            return Response({'status':2 , })
        except:
            return Response({'status' : 0 ,})
            

def user_mapped_model(request , action , model_type , model_object_id):
    content_obj = ContentType.objects.get(model =  model_type)
    object_id = model_object_id
    action_taken = action
    user = request.user
    try:
        FacilityBeneficiaryDeactivate.objects.create(content_type = content_obj , object_id = object_id , user = user , action = action_taken)
        return True
    except:
        return False
