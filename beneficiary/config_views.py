from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import *
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
import json
from facilities.models import CodeConfig
from .serializers import CodeConfigSerializer
from service.views import model_field_exists
from masterdata.views import pg_size, CustomPagination
from math import ceil
from django.db.models import ForeignKey, Q
from beneficiary.models import *


class CodeConfigCreate(CreateAPIView):
    serializer_class = CodeConfigSerializer

    def post(self, request):
        response = {'status':0}
        model = CodeConfig
        mtm_fields = [i.name for i in model._meta.many_to_many]
        object_list = model.objects.filter(content_type_id=request.data['content_type_id'])
        if object_list:
            response.update({'status':0, 'message':"content type already exists"})
        else:
            dt = request.data
            var1 = request.data.keys()
            data1 = {}
            for v1 in var1:
                if not v1 in mtm_fields and model_field_exists(model, v1):
                    data1.update({v1:dt.get(v1)})
            model.objects.create(**data1)
            response.update({'message':'Successfully added', 'status':2})
        return Response(response)

class CodeConfigUpdate(CreateAPIView):
    serializer_class = CodeConfigSerializer

    def post(self, request):
        """
            update code config
            ---
            parameters:
            - name: id
              description: pass code config id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        model = CodeConfig
        mtm_fields = [i.name for i in model._meta.many_to_many]
        ctid = request.data.get('content_type_id')
        object_list = None
        if ctid and not ctid == '':
            try:
                object_list = model.objects.filter(content_type_id=request.data['content_type_id']).exclude(id=request.data['id'])
            except:
                pass
        if object_list:
            response.update({'status':0, 'message':"content type already exists"})
        else:
            dt = request.data
            var1 = request.data.keys()
            data1 = {'is_updated':True}
            obj = model.objects.get(id=request.data['id'])
            for v1 in var1:
                if not v1 in mtm_fields:
                    get_model_details(model, v1, dt, data1)
            obj.__dict__.update(data1)
            obj.save()
            response.update({'message':'Successfully updated', 'status':2})
        return Response(response)

def get_model_details(model, v1, dt, data1):
    if model_field_exists(model, v1):
        if v1 == 'sequence':
            if dt.get(v1) == 'false':
                boole = False
            elif dt.get(v1) == 'true':
                boole = True
            data1.update({v1:boole})
        else:
            data1.update({v1:dt.get(v1)})
    return data1

class CodeConfigListing(APIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        response = {}
        all_fields = [i for i in CodeConfig._meta.get_all_field_names()]
        object_list = CodeConfig.objects.filter(active=2).order_by('-id')
        data = []
        for obj in object_list:
            objdict = {'content_object':obj.content_object.name if obj.content_object else ''}
            for field in all_fields:
                try:
                    if self.get_fk_model(CodeConfig, field):
                        g = getattr(obj, field)
                        objdict.update({field:g.model.capitalize()})
                except:
                    pass
                get_updated_objdict(obj, field, objdict)
            data.append(objdict)
        response.update({'data':data, 'status':2, 'message':'Successfully Retrieved'})
        data.append(dict(pages=ceil(float(object_list.count()) / float(pg_size))))
        get_page = int(data[-1].get('pages'))
        paginator = CustomPagination()
        del data[-1]
        result_page = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'),21,  get_page)

def get_updated_objdict(obj, field, objdict):
    try:
        if obj.__dict__[field] == None:
            obj.__dict__[field] = ''
        objdict.update({field:obj.__dict__[field]})
    except:
        pass
    return objdict

class CodeConfigDetail(APIView):

    def get_fk_model(self, model, fieldname):
        '''returns None if not foreignkey, otherswise the relevant model'''
        field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
        if not m2m and direct and isinstance(field_object, ForeignKey):
            return field_object.rel.to
        return None

    def post(self, request):
        """
            Retreive code config detail
            ---
            parameters:
            - name: id
              description: pass code config id
              required: true
              type: integer
              paramType: form
        """
        response = {'status':0}
        obj = None
        try:
            obj = CodeConfig.objects.get(id=request.data['id'])
        except:
            pass
        if obj:
            all_fields = [i for i in CodeConfig._meta.get_all_field_names()]
            objdict = {}
            for field in all_fields:
                try:
                    if self.get_fk_model(CodeConfig, field):
                        g = getattr(obj, field)
                        objdict.update({field:g.model.capitalize()})
                except:
                    pass
                get_updated_objdict(obj, field, objdict)
            response.update(objdict)
            response.update({'status':2})
        return Response(response)

class RetrieveContentType(APIView):

    def post(self, request):
        response = {'status':0}
        objdict = []
        models = ['partner']
        content_types = ContentType.objects.filter(model__in=models)
        [objdict.append({'id':i.id, 'model':i.model}) for i in content_types]
        response.update({'status':2, 'data':objdict})
        return Response(response)

class HouseholdTypeDetail(APIView):

    def post(self, request):
        """
            ---
            parameters:
            - name: householdid
              description: pass household id
              required: true
              type: integer
              paramType: form
        """
        response = {}
        beneficiary = Beneficiary.objects.get(id=request.data.get('householdid'))
        get_child_bene = Beneficiary.objects.filter(parent=beneficiary, active=2)
        
        final_data = []
        bentypes = BeneficiaryType.objects.filter(is_main=False, active=2).exclude(parent=None)
        for i in bentypes:
            type_dict = {}
            type_dict.update({'name':i.name, 'id':int(i.id)})
            data_list = []
            for ben in get_child_bene.filter(beneficiary_type=i):
                ben_dict = {}
                ben_dict.update({'id':ben.id, 'name':ben.name,
                    'code':ben.code, 'age':ben.jsondata['age'][0] if type(ben.jsondata['age']) == list else ben.jsondata['age']})
                data_list.append(ben_dict)
            type_dict.update({'data':data_list})
            final_data.append(type_dict)
        response.update({'data':final_data, 'status':2})
        return Response(response)
