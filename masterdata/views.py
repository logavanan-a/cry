"""File to Write Business Logics."""
import requests
import json
from ast import literal_eval
from collections import (namedtuple,)
from itertools import (chain,)
from operator import (itemgetter,)
from math import ceil
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from rest_framework import (pagination, status)
from rest_framework.utils.urls import replace_query_param
from rest_framework.views import APIView
from rest_framework.generics import (CreateAPIView, ListCreateAPIView,
                                     RetrieveUpdateAPIView, ListAPIView)
from rest_framework.response import Response
from box import Box
from ccd.settings import HOST_URL, REST_FRAMEWORK
from partner.serializers import (PartnerListingSlugSerializer,)
from .models import (Boundary, MasterLookUp)
from .serializers import (BoundarySerializer, MasterLookUpSerializer, BoundaryListingSerializer,
                          SearchSerializer, MasterLookupPartnerListing, BoundaryUpdateSerializer)
from partner.models import Partner
from userroles.models import UserPartnerMapping,UserRoles

pg_size = REST_FRAMEWORK.get('MASTERDATA_LOCATION', 0)


class MasterLookUpGetLocation(CreateAPIView):
    queryset = MasterLookUp.objects.filter(active=2)
    serializer_class = PartnerListingSlugSerializer

    def get_master_look_data(self, master, levels_name, slug):
        point = namedtuple('point', ['name', 'level', 'key', 'common_key'])
        response = []
        for m in master:
            for l in levels_name:
                leve = point(*l)
                if leve.name == m.slug:
                    response.append({'id': m.id, 'name': m.name, 'slug': m.slug, 'common_key': leve.common_key,
                                     'level': leve.level, 'key': leve.key, 'data': m.get_child()})
        response = sorted(response, key=itemgetter('level'))
        return response

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerListingSlugSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            levels_name_dict = {'location-urban': [['urban-state', 2, 1, 0], ['urban-district', 3, 3, 0],
                                                   ['urban-city', 4, 3,
                                                       1], ['urban-area', 5, 3, 1],
                                                   ['urban-ward', 6, 6, 1], ['urban-mohallaslum', 7, 3, 1]],
                                'location-rural': [['rural-state', 2, 1, 0], ['rural-district', 3, 3, 0],

                                                   ['rural-block', 4, 3, 1], 

                                    ['rural-gramapanchayath', 5, 3, 1],
                ['rural-village', 6, 3, 1], ['rural-hamlet', 7, 3, 1]]}
            master = MasterLookUp.objects.filter(
                active=2, parent__slug__iexact=data.slug)
            if request.data.get('key', '1') == '0':
                response = {}
                response.update({data.slug: list()})
                master1 = master
                for m in master1:
                    master = MasterLookUp.objects.filter(
                        active=2, parent__slug__iexact=m.slug)
                    levels_name = levels_name_dict.get(m.slug)
                    local_dict = {}
                    local_lsist = response[data.slug]
                    local_dict.update({"slug": m.slug,
                                       "id": m.id,
                                       "name": m.name,
                                       "boundaries": self.get_master_look_data(master, levels_name, data.slug)})
                    local_lsist.append(local_dict)

            else:
                levels_name = levels_name_dict.get(data.slug)
                response = self.get_master_look_data(
                    master, levels_name, data.slug)
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class BoundaryList(CreateAPIView):
    """Get Location based on Parent ID."""

    queryset = Boundary.objects.filter(active=2)
    serializer_class = BoundaryListingSerializer

    def retrieve_parent(self, queryset):
        if queryset:
            bound = queryset[0]
            new_levels = range(1, bound.boundary_level)
            get_parent_id = bound.id
            response = {'ward_type': 0, bound.boundary_level: bound.id}
            for nl in new_levels[::-1]:
                b = Boundary.objects.get(
                    id=get_parent_id, parent__boundary_level=nl)
                get_parent_id = b.parent.id
                response[nl] = get_parent_id
                if nl == 6:
                    ward_type = b.parent.ward_type.id if b.parent.ward_type else 0
                    response['ward_type'] = ward_type
            del response[1]
            return response

    def post(self, request):
        """Custom method to get all the Location."""
        response = {'message': 'something went wrong'}
        serializer = BoundaryListingSerializer(data=request.data)
        if serializer.is_valid():
            data = request.data
            if int(data.get('common_key')) == 1:
                get_location_type = self.get_queryset().filter(
                    object_id=int(request.data.get('location_type', 0)))
            else:
                get_location_type = self.get_queryset().filter(object_id=0)
            # 4:
            # get_location_type.filter(id=data.get('boundary_id')).values('parent'),
            try:
                partner_id = data.get('partner_id')
                partner_obj = Partner.objects.get(id=partner_id)
            except:
                partner_obj = None
            get_loc = {1: get_location_type.filter(boundary_level=data.get('level')),
                       2: get_location_type.filter(parent__id=data.get('boundary_id')),
                       3: get_location_type.filter(boundary_level=data.get('level'), parent__id=data.get('boundary_id')),
                       4: self.retrieve_parent(get_location_type.filter(id=data.get('boundary_id'))),
                       5: get_location_type.filter(region__id=data.get('region_id')),
                       6: get_location_type.filter(boundary_level=data.get('level'), ward_type__id=data.get('ward_type'), parent__id=data.get('boundary_id')),
                       7: get_location_type.filter(boundary_level=data.get('level'), ward_type__id=data.get('ward_type')).values('id', 'name')}
            bound = get_loc.get(int(data.get('key')))
            level = data.get('level')
            if partner_obj and not data.get('boundary_id') and not data.get('region_id'):
                bound = get_level_partnerwise_data(level, bound, partner_obj)
            get_loc_con = {1: 1,
                           2: 1,
                           3: 1,
                           4: 0,
                           5: 1,
                           6: 1,
                           7: 0}
            if get_loc_con.get(int(data.get('key')), 0):
                response = [{'id': i.id, 'name': i.name} for i in bound]
                response.append(
                    dict(pages=ceil(float(bound.count()) / float(pg_size))))
            else:
                response = bound
        else:
            response.update(errors=serializer.errors)
        return Response(response)


def get_level_partnerwise_data(level, bound, partner_obj):
    state_id = int(partner_obj.state_id)
    if str(level) == '2':
        bound = bound.filter(id=state_id)
    elif str(level) == '3':
        bound = bound.filter(parent__id=state_id)
    elif str(level) == '4':
        bound = bound.filter(parent__parent__id=state_id)
    elif str(level) == '5':
        bound = bound.filter(parent__parent__parent__id=state_id)
    elif str(level) == '6':
        bound = bound.filter(parent__parent__parent__parent__id=state_id)
    elif str(level) == '7':
        bound = bound.filter(parent__parent__parent__parent__parent__id=state_id)
    return bound


class BoundaryLiveSearch(ListAPIView):

    def get_location_type(self):
        queryset = MasterLookUp.objects.filter(active=2)
        loca_type = queryset.filter(
            parent__slug='location-type')
        dict_type = {}
        for lotyp in loca_type:
            if lotyp.slug == 'rural-urban':
                dict_type[lotyp.id] = 0
            else:
                dict_type[lotyp.id] = lotyp.id
        return dict_type


    def get_user_states(self,user_id):
        if user_id == 0:
            return []
        usr = UserRoles.objects.get(user_id=user_id)
        state_list = []
        if usr.user_type == 1:
            try:
                state_list = set(UserPartnerMapping.objects.get(user_id=user_id).partner.all().values_list('state',flat=True))
            except:
                pass
        else:
            state_list = [usr.partner.state.id]
        return state_list

    def get_results(self, data):
        query_set_ = Boundary.objects.filter(active=2)
        location_type = data.get('location_type')
        level = int(data.get('level', 0))
        user_name = data.get('user_name', 0)
        common_key = int(data.get('common_key', 0))
        ward_type = int(data.get('ward_type', 0))
        location_ = data.get('location_id', '0')
        object_id = int(data.get('object_id', 0))
        partner_id = int(data.get('partner_id', 0))
        #user_id = int(data.get('user_id'),0)
        location_id = map(int, location_.split(','))
        try:
            partner_id = data.get('partner_id')
            partner_obj = Partner.objects.get(id=partner_id)
        except:
            partner_obj = None
        if common_key == 0:
            query_set = query_set_.filter(object_id=0)
        if common_key == 0 and data.get('location_id') == '0':#control the level wise data here for partners
            query_set = query_set_.filter(boundary_level=level)
        if common_key == 0 and data.get('location_id') != '0':
            query_set = query_set_.filter(parent__id__in=location_id)
        if common_key == 1:
            query_set = query_set_.filter(object_id=location_type)
        if common_key == 1 and ward_type != 0:
            query_set = query_set_.filter(ward_type__id=ward_type)
        if common_key == 0 and level and user_name and data.get('location_id', '0') == '0':#control the districtsv level
            query_set = query_set_.filter(boundary_level=level)
        if common_key == 2 and location_id != [0]:
            query_set = query_set_.filter(
                parent__id__in=location_id)
            get_type = self.get_location_type()
            if get_type.get(object_id, 0):
                query_set = query_set.filter(object_id=int(object_id))
        if not partner_id == 0 and partner_obj:
            query_set = get_level_partnerwise_data(level, query_set, partner_obj)
        users_data = []
        if user_name:
            get_name = user_name.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.name + ' - ' + u.parent.name} for u in query_set.filter(
                boundary_level=int(level), name__istartswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def list(self, request, *args, **kwargs):
        data = request.query_params
        get_data = self.get_results(data)
        return Response(get_data)


class MasterLookUpLiveSearch(ListAPIView):

    def get_results(self, data):
        query_set = MasterLookUp.objects.filter(active=2)
        user_name = data.get('user_name', 0)
        if user_name:
            get_name = user_name.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.name} for u in query_set.filter(
                active=2, name__istartswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def list(self, request, *args, **kwargs):
        data = request.query_params
        get_data = self.get_results(data)
        return Response(get_data)


class BoundaryCounts(APIView):
    """Get all the level counts."""

    def get_ward_type(self, l, get_location_type, get_level_slug):
        get_all_wards = {}
        get_wards = MasterLookUp.objects.filter(
            active=2, parent__slug='urban-ward')
        if l == 6 and get_level_slug == 'location-urban' and get_wards:
            get_all_wards = {gw.name: Boundary.objects.filter(active=2, object_id=int(get_location_type), boundary_level=l, ward_type__id=gw.id).count()
                             for gw in get_wards}
        return get_all_wards

    def get(self, request, *args, **kwargs):
        """Get Data Response."""
        get_location_type = request.query_params.get('location_type')
        response = {'status': 0, 'message': 'Something went wrong'}
        levels_listing = {2: '/level-2/listing/',
                          3: '/level-3/listing/',
                          4: '/level-4/listing/',
                          5: '/level-5/listing/',
                          6: '/level-6/listing/',
                          7: '/level-7/listing/'}
        levels = range(2, 8)
        levels_name_dict = {'location-urban': ['State', 'District', 'City', 'Area', 'Ward', 'Mohalla / Slum'],
                            'location-rural': ['State', 'District', 'Block', 'GramaPanchayath', 'Village', 'Hamlet']}
        get_level_slug = MasterLookUp.objects.get(id=get_location_type).slug
        get_level_id = {ml.name: ml.id for ml in MasterLookUp.objects.filter(
            parent__slug__iexact=get_level_slug)}
        levels_name = levels_name_dict.get(get_level_slug)
        try:
            response = []
            for l, n in zip(levels, levels_name):
                if n == 'State' or n == 'District':
                    counting = str(Boundary.objects.filter(
                        active=2, boundary_level=l, object_id=0).count())
                else:
                    counting = str(Boundary.objects.filter(active=2, object_id=int(
                        get_location_type), boundary_level=l).count())
                data_ = {'name': n,
                         'id': get_level_id.get(n, 0),
                         'count': counting,
                         'level': l,
                         'level_id': n,
                         'listing_url': HOST_URL + '/masterdata' + levels_listing.get(l),
                         'childs': [self.get_ward_type(l, get_location_type, get_level_slug)]}
                response.append(data_)
        except:
            response
        return Response(response)


class BoundaryLevelCount(APIView):
    """Get all the level counts."""

    def get(self, request):
        """Get Data Response."""
        ru = requests.get(HOST_URL + '/masterdata/boundary/count/',
                          params={'location_type': request.query_params.get('location_type')})
        response = {'status': ru.status_code, 'data': literal_eval(ru.content)}
        return Response(response)


class BoundarySearch(CreateAPIView):
    """Search Location based on Text."""

    queryset = Boundary.objects.filter(active=2)
    serializer_class = SearchSerializer

    def post(self, request):
        """Get all the Boundary Based on Level and Text."""
        response = {'message': 'something went wrong'}
        serializer = SearchSerializer(data=request.data)
        data = request.data
        if serializer.is_valid():
            get_level = Boundary.objects.filter(active=2, object_id=int(request.data.get(
                'location_type', 0)), boundary_level=data.get('level'), name__icontains=data.get('text'))
            if int(request.data.get('ward_type')):
                get_level = get_level.filter(
                    ward_type__id=int(request.data.get('ward_type')))
            response = [{'id': i.id, 'name': i.name} for i in get_level]
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class BoundaryCreate(CreateAPIView):
    """Location Create."""

    queryset = Boundary.objects.filter(active=2)
    serializer_class = BoundarySerializer

    def perform_create(self, serializer):
        serializers = serializer.save()
        return serializers

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializers = self.perform_create(serializer)
        if request.data.get('ward_type', '0') != '0':
            serializers.ward_type_id = request.data.get('ward_type')
        if request.data.get('common_key') == '1':
            serializers.content_type = ContentType.objects.get_for_model(
                MasterLookUp)
        serializers.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        """Pass Location Type Id.
        ---
        parameters:
        - name: ward_type
          description: pass wards_type
          required: false
          type: integer
          paramType: form
        - name: common_key
          description: pass common_key 0 or 1.
          required: true
          type: integer
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class BoundaryDetail(APIView):
    """State Basic Operations."""

    def post(self, request):
        response = {'message': 'something went wrong'}
        data = request.data
        try:
            if data.get('pk'):
                bound = Boundary.objects.get(active=2, id=int(data.get('pk')))
                response = {'id': bound.id, 'name': bound.name, 'code': bound.code or '', 'level': bound.boundary_level,
                            'desc': bound.desc or '', 'slug': bound.slug or '', 'parent': [bound.parent.id] if bound.parent else '',
                            'parent_name': [bound.parent.name] if bound.parent else '',
                            'latitude': bound.latitude or '', 'longitude': bound.longitude or '',
                            'ward_type': bound.ward_type.name if bound.ward_type else '',
                            'ward_type_id': bound.ward_type.id if bound.ward_type else 0,
                            'location_type': bound.object_id}
        except:
            pass
        return Response(response)


class BoundaryUpdate(CreateAPIView):
    """State Basic Operations."""
    queryset = Boundary.objects.filter(active=2)
    serializer_class = BoundaryUpdateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        response = {'status': 201, 'message': 'something went wrong'}
        if serializer.is_valid():
            data = {'boundary_level': request.data.get('boundary_level'),
                    'location_type': request.data.get('location_type'),
                    'ward_type': request.data.get('ward_type'),
                    'desc': request.data.get('desc'),
                    'latitude': request.data.get('latitude'),
                    'longitude': request.data.get('longitude'),
                    'name': request.data.get('name'),
                    'parent': request.data.get('parent'),
                    'pk': request.data.get('pk'),
                    'code': request.data.get('code', '')}
            response.update(data=data)
            try:
                get_bound = Boundary.objects.get(id=data.get('pk'))
                get_bound.name = data.get('name')
                get_bound.desc = data.get('desc')
                get_bound.boundary_level = data.get('boundary_level')
                get_bound.latitude = data.get('latitude')
                get_bound.longitude = data.get('longitude')
                if data.get('ward_type'):
                    get_bound.ward_type_id = data.get('ward_type')
                get_bound.parent_id = data.get('parent')
                get_bound.code = data.get('code')
                if request.data.get('common_key') == '1':
                    get_bound.content_type, get_bound.object_id = ContentType.objects.get_for_model(
                        MasterLookUp), int(data.get('location_type', 0))
                get_bound.save()
                response = {'status': 201, 'message': 'updated successfully'}
            except:
                pass
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class BoundaryActions(APIView):
    """Boundary Activate and Deactive."""

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
        """
        data = request.data
        response = {'status': 0, 'message': 'Something went  wrong.'}
        try:
            # Activate and Deactivate the Objects.
            get_object = Boundary.objects.get(id=data.get('object_id'))
            get_object.switch()
            response = {'data': {'active_id': get_object.active, 'name': get_object.get_active_display()},
                        'message': 'Successfully switched the object.'}
        except:
            pass
        return Response(response)


class MasterLookUpActions(APIView):
    """Master Lookup Activate and Deactive."""

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
        """
        data = request.data
        response = {'status': 0, 'message': 'Something went  wrong.'}
        try:
            # Activate and Deactivate the Objects.
            get_object = MasterLookUp.objects.get(id=data.get('object_id'))
            get_object.switch()
            response = {'data': {'active_id': get_object.active, 'name': get_object.get_active_display()},
                        'message': 'Successfully switched the object.'}
        except:
            pass
        return Response(response)


class CustomPagination(pagination.PageNumberPagination):

    def get_page_dict(self, level, page_number):
        get_next = {2: replace_query_param(HOST_URL + '/masterdata/level-2/listing/', self.page_query_param, page_number),
                    3: replace_query_param(HOST_URL + '/masterdata/level-3/listing/', self.page_query_param, page_number),
                    4: replace_query_param(HOST_URL + '/masterdata/level-4/listing/', self.page_query_param, page_number),
                    5: replace_query_param(HOST_URL + '/masterdata/level-5/listing/', self.page_query_param, page_number),
                    6: replace_query_param(HOST_URL + '/masterdata/level-6/listing/', self.page_query_param, page_number),
                    7: replace_query_param(HOST_URL + '/masterdata/level-7/listing/', self.page_query_param, page_number),
                    # 8: replace_query_param(HOST_URL + '/masterdata/habitation/village/listing/', self.page_query_param, page_number),
                    # 9: replace_query_param(HOST_URL +
                    # '/masterdata/hamlets/listing/', self.page_query_param,
                    # page_number),
                    10: replace_query_param(HOST_URL + '/masterdata/master/lookup/', self.page_query_param, page_number),
                    11: replace_query_param(HOST_URL + '/facilities/facilitylisting/', self.page_query_param, page_number),
                    12: replace_query_param(HOST_URL + '/service/servicelistingwithpagination/', self.page_query_param, page_number),
                    13: replace_query_param(HOST_URL + '/beneficiary/listing/', self.page_query_param, page_number),
                    14: replace_query_param(HOST_URL + '/partner/list/', self.page_query_param, page_number),
                    15: replace_query_param(HOST_URL + '/beneficiary/typewiselisting/', self.page_query_param, page_number),
                    16: replace_query_param(HOST_URL + '/beneficiary/relation/list/', self.page_query_param, page_number),
                    17: replace_query_param(HOST_URL + '/partner/registration/list/', self.page_query_param, page_number),
                    18: replace_query_param(HOST_URL + '/partner/bank/list/', self.page_query_param, page_number),
                    19: replace_query_param(HOST_URL + '/partner/address/list/', self.page_query_param, page_number),
                    20: replace_query_param(HOST_URL + '/beneficiary/btype/listing/', self.page_query_param, page_number),
                    21: replace_query_param(HOST_URL + '/beneficiary/codeconfig/listing/', self.page_query_param, page_number),
                    22: replace_query_param(HOST_URL + '/partner/employee/list/', self.page_query_param, page_number),
                    23: replace_query_param(HOST_URL + '/partner/project/', self.page_query_param, page_number),
                    24: replace_query_param(HOST_URL + '/partner/dfp/budget-config/listing/', self.page_query_param, page_number),
                    25: replace_query_param(HOST_URL + '/partner/dfp/funding/listing/', self.page_query_param, page_number),
                    26: replace_query_param(HOST_URL + '/partner/dfp/donar/listing/', self.page_query_param, page_number),
                    27: replace_query_param(HOST_URL + '/workflow/state/', self.page_query_param, page_number),
                    28: replace_query_param(HOST_URL + '/workflow/configure/', self.page_query_param, page_number),
                    29: replace_query_param(HOST_URL + '/workflow/configure/survey/', self.page_query_param, page_number),
                    30: replace_query_param(HOST_URL + '/workflow/batches/', self.page_query_param, page_number),
                    31: replace_query_param(HOST_URL + '/survey-file/survey-data-listing/', self.page_query_param, page_number),
                    32: replace_query_param(HOST_URL + '/survey-file/survey-data-retrieve/', self.page_query_param, page_number),
                    33: replace_query_param(HOST_URL + '/partner/report/view/', self.page_query_param, page_number),
                    34: replace_query_param(HOST_URL + '/dynamic_listing/filter-listing/', self.page_query_param, page_number),
                    35: replace_query_param(HOST_URL + '/masterdata/report/list/', self.page_query_param, page_number),
                    36: replace_query_param(HOST_URL + '/survey/survey_responses/', self.page_query_param, page_number),
                    37: replace_query_param(HOST_URL + '/reports/customreports-listing/', self.page_query_param, page_number),
                    }
        return get_next.get(level)

    def get_paginated_response(self, data, status, message, level, page, headers=None, download=None, mass_download=None, table=None):
        result = {'next': self.get_next_link(data, level, table=table),
                  'previous': self.get_previous_link(data, level, table=table),
                  'count': self.page.paginator.count,
                  'data': data,
                  'status': status,
                  'pages': page,
                  'message': message}
        if headers:
            result.update(display_headers=headers,
                          headers=download, download=mass_download)
        return Response(result)

    def get_next_link(self, data, level, table=None):
        if not self.page.has_next():
            return ''
        page_number = self.page.next_page_number()
        get_page_next = self.get_page_dict(level, page_number)
        if table:
            get_page_next = get_page_next+'&table='+str(table)
        return get_page_next

    def get_previous_link(self, data, level, table=None):
        if not self.page.has_previous():
            return ''
        page_number = self.page.previous_page_number()
        get_page_next = self.get_page_dict(level, page_number)
        if table:
            get_page_next = get_page_next+'&table='+str(table)
        return get_page_next


class SecondaryCustomPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data, **kwargs):
        result = {'next': self.get_next_link(data, kwargs.get('levels'), kwargs.get('obj')),
                  'previous': self.get_previous_link(data, kwargs.get('levels'), kwargs.get('obj')),
                  'count': self.page.paginator.count,
                  'data': data,
                  'status': 2,
                  'pages': kwargs.get('get_page'),
                  'message': 'successfully retreived the data',
                  'name': kwargs.get('name'),
                  'survey_user': kwargs.get('survey_user'),
                  'level': kwargs.get('level'),
                  'survey_user_name': kwargs.get('survey_user_name'),
                  'download': kwargs.get('download'),
                  'headers': kwargs.get('headers'),
                  'levels': kwargs.get('levels'),
                  }
        return Response(result)

    def get_next_link(self, data, levels, obj):

        if not self.page.has_next():
            return ''
        page_number = self.page.next_page_number()
        get_next = {
            32: replace_query_param(HOST_URL + '/survey-file/survey-data-retrieve/%d/' % obj, self.page_query_param, page_number),
        }

        return get_next.get(levels)

    def get_previous_link(self, data, levels, obj):
        if not self.page.has_previous():
            return ''
        page_number = self.page.previous_page_number()
        get_previous = {
            32: replace_query_param(HOST_URL + '/survey-file/survey-data-retrieve/%d/' % obj, self.page_query_param, page_number),
        }
        return get_previous.get(levels)


class MasterLookUpCreate(ListCreateAPIView):
    """Master Lookup Create and listing."""
    p_ids = MasterLookUp.objects.filter(
        active=2, parent__id=None).values_list('id', flat=True)
    queryset = MasterLookUp.objects.filter(active=2, id__in=p_ids)
    serializer_class = MasterLookUpSerializer

    def get(self, request):
        response = {'status': 0, 'message': 'Something went wrong.'}
        try:
            get_loc_list = [{'id': i.id, 'name': i.name, 'parent': {'id': i.id if i.parent else '',
                                                                    'name': i.name if i.parent else ''}, 'child': i.get_child()} for i in self.get_queryset()]
            get_loc_list.append(
                dict(pages=ceil(float(self.get_queryset().count()) / float(pg_size))))
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {
                'status': 2, 'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(get_loc_list, request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), 10,  get_page)
        except Exception as e:
            response = {'message': e.message}
        return Response(response)


class MasterLookUpDetail(RetrieveUpdateAPIView):
    """Master Lookup Basic Operations."""

    queryset = MasterLookUp.objects.filter(active=2)
    serializer_class = MasterLookUpSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data.update({'parent': [instance.parent.id] if instance.parent else 0,
                     'parent_name': instance.parent.name if instance.parent else ''})
        return Response(data)

    def put(self, request, *args, **kwargs):
        data = request.data
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            obj = self.get_object()
            obj.name = data.get('name')
            if data.get('parent'):
                get_parent = MasterLookUp.objects.get(
                    id=int(data.get('parent')))
                obj.parent = get_parent
            obj.save()
            response = {'status': 2,
                        'message': 'Successfully object has been updated'}
        except:
            pass
        return Response(response)


class MasterLookUpPartnerCreate(CreateAPIView):

    queryset = MasterLookUp.objects.filter(active=2)
    serializer_class = MasterLookupPartnerListing

    def post(self, request):
        data = request.data
        serializer = MasterLookupPartnerListing(data=data)
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            if serializer.is_valid():
                get_ = literal_eval(data.get('get_list'))
                for ml in get_:
                    MasterLookUp.objects.create(
                        name=ml, parent_id=int(data.get('parent')), slug=slugify(ml))
                response = {'status': 2, 'message': 'Successfully created'}
        except:
            pass
        return Response(response)


class StateCreate(APIView):
    """State Create."""

    def post(self, request):
        """To Create State."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        if serializer.is_valid():
            r = requests.post(HOST_URL + '/masterdata/boundary/', data=data)
            response = {'status': r.status_code,
                        'message': 'Successfully created', 'data': data}
        else:
            response.update(erros=serializer.errors)
        # except:
        #     pass
        return Response(response)


class StateListing(APIView):
    """State Listing."""

    def post(self, request):
        """To Get State List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '2':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class StateDetial(APIView):
    """State Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '2':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class StateUpdate(APIView):
    """
    API to update the State.
    """

    def post(self, request):
        """To Create State.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class StateAction(APIView):
    """
    API to update the State.
    """

    def post(self, request):
        """To Create State.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}
        return Response(response)


class DistrictCreate(APIView):
    """District Create."""

    def post(self, request):
        """To Create District."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class DistrictListing(APIView):
    """District Listing."""

    def post(self, request):
        """To Get District List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '3':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class DistrictDetial(APIView):
    """District Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '3':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class DistrictUpdate(APIView):
    """
    API to update the District.
    """

    def post(self, request):
        """To Create District.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class DistrictAction(APIView):
    """
    API to update the District.
    """

    def post(self, request):
        """To Create District.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}

        return Response(response)


class TalukCreate(APIView):
    """Taluk Create."""

    def post(self, request):
        """To Create Taluk."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class TalukListing(APIView):
    """Taluk Listing."""

    def post(self, request):
        """To Get Taluk List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '4':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class TalukDetial(APIView):
    """Taluk Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '4':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class TalukUpdate(APIView):
    """
    API to update the Taluk.
    """

    def post(self, request):
        """To Create Taluk.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class TalukAction(APIView):
    """
    API to update the Taluk.
    """

    def post(self, request):
        """To Create District.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}

        return Response(response)


class GPCreate(APIView):
    """GP Create."""

    def post(self, request):
        """To Create GP."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class GPListing(APIView):
    """GP Listing."""

    def post(self, request):
        """To Get GP List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '5':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class GPDetial(APIView):
    """GP Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '5':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class GPUpdate(APIView):
    """
    API to update the GP.
    """

    def post(self, request):
        """To Create GP.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class GPAction(APIView):
    """
    API to update the GP.
    """

    def post(self, request):
        """To Create GP.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}

        return Response(response)

"""Level 6"""


class RevenueVillageCreate(APIView):
    """Revenue Village."""

    def post(self, request):
        """To Create Revenue Village."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class RevenueVillageListing(APIView):
    """Revenue Village Listing."""

    def post(self, request):
        """To Get Revenue Village List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '6':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class RevenueVillageDetial(APIView):
    """RevenueVillage Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '6':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class RevenueVillageUpdate(APIView):
    """
    API to update the RevenueVillage.
    """

    def post(self, request):
        """To Create Revenue Village.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class RevenueVillageAction(APIView):
    """
    API to update the Revenue Village.
    """

    def post(self, request):
        """To Create Revenue Village.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}

        return Response(response)

"""Level 7"""


class HamletsCreate(APIView):
    """Hamlets Create."""

    def post(self, request):
        """To Create Hamlets."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class HamletsListing(APIView):
    """Hamlets Listing."""

    def post(self, request):
        """To Get Hamlets List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level'), 'location_type': data.get(
            'location_type'), 'common_key': data.get('common_key')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '7':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class HamletsDetial(APIView):
    """Hamlets Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '7':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class HamletsUpdate(APIView):
    """
    API to update the Hamlets.
    """

    def post(self, request):
        """To Create Village Hamlets.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class HamletsAction(APIView):
    """
    API to update the Hamlets.
    """

    def post(self, request):
        """To Create Hamlets.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}

        return Response(response)


class BoundaryListWithoutPagination(CreateAPIView):
    """Get Location based on Parent ID."""

    queryset = Boundary.objects.filter(active=2)
    serializer_class = BoundaryListingSerializer

    def post(self, request):
        """Custom method to get all the Location."""
        response = {'message': 'something went wrong'}
        serializer = BoundaryListingSerializer(data=request.data)
        if serializer.is_valid():
            response = {"count": 21, "status": 07, "next": "http://crymis.mahiti.org/masterdata/boundary/listing/", "pages": 1991}
            data = request.data
            get_loc = {1: Boundary.objects.filter(active=2, boundary_level=data.get('level')),
                       2: Boundary.objects.filter(active=2, parent__id=data.get('boundary_id')),
                       3: Boundary.objects.filter(active=2, boundary_level=data.get('level'), parent__id=data.get('boundary_id')),
                       4: Boundary.objects.filter(active=2, id=data.get('boundary_id')).values('parent')}
            bound = get_loc.get(1)
            data_bound = [{'id': i.id, 'name': i.name} for i in bound]
            response.update(data=data_bound)
        else:
            response.update(errors=serializer.errors)
        return Response(response)
