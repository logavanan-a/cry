"""Storing Data in JsonField."""
import csv
import json
from math import (ceil,)
import os
import re
from string import punctuation
from collections import namedtuple
from django.contrib.contenttypes.models import ContentType
from rest_framework.generics import (
    CreateAPIView, ListAPIView, RetrieveDestroyAPIView)
from rest_framework.response import Response
from ccd.settings import (BASE_DIR, REST_FRAMEWORK, HOST_URL)
from masterdata.models import (MasterLookUp, Boundary)
from masterdata.views import (CustomPagination, SecondaryCustomPagination)
from survey.models import (SurveyRestore, SurveyDump)
from userroles.models import (UserRoles, OrganizationLocation)
from survey.serializers import (SurveyRestoreSerializer,)

pg_size = REST_FRAMEWORK.get('MASTERDATA_LOCATION', 0)


class DataRestore(CreateAPIView):
    queryset = SurveyRestore.objects.filter(active=2)
    serializer_class = SurveyRestoreSerializer

    def get_clean_value(self, headers):
        for ul in headers:
            yield re.sub(r'[%s + ' ']' % punctuation, '_', ul).lower()

    def get_boundary_location(self, location_id):
        get_loc = None
        if location_id != '' or location_id != '0':
            get_loc = Boundary.objects.get_or_none(id=int(location_id))
        return get_loc

    def dump_data(self, create_file):
        status = {'status': 0, 'message': 'Something went wrong.'}
        if create_file:
            """1000000 is 1MB when loading data."""
            with open(BASE_DIR + '/' + create_file.restore_file.url, 'rb+', 1000000) as f:
                status = {'status': 2,
                          'message': 'Successfully uploaded the data.'}
                reader = csv.reader(f)
                headers = self.get_clean_value(reader.next())
                head_ = namedtuple(
                    'head_', headers)
                try:
                    for sr in reader:
                        h = head_(*sr)
                        get_loc = self.get_boundary_location(h.location_id)
                        if get_loc:
                            sur_dump = SurveyDump.objects.create(
                                response=dict(h.__dict__), survey_restore=create_file)
                            sur_dump.boundary_id = h.location_id
                            sur_dump.save()
                except:
                    pass
        return status

    def create(self, request, *args, **kwargs):
        status = {'status': 0, 'message': 'Something went wrong.'}
        data = request.data
        get_file_obj = data.get('get_docu')
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            get_file = get_file_obj.name
            if os.path.splitext(get_file)[1] in ['.csv', '.xlxs']:
                status = {'status': 2,
                          'message': 'Successfully uploaded the data.'}
                create_file = SurveyRestore.objects.create(survey_user_id=data.get('survey_user'), level=data.get('level'),
                                                           name=data.get('name', 'pradam'), restore_file=get_file_obj)
                create_file.content_type, create_file.object_id = ContentType.objects.get_for_model(
                    MasterLookUp), data.get('object_id')
                create_file.save()
                get_dump_status = self.dump_data(create_file)
                if get_dump_status.get('status'):
                    create_file.exported = 1
                create_file.save()
            else:
                status.update(
                    errors='Unsupported file format please upload csv or excel file.')
        else:
            status.update(errors=serializer.errors)
        return Response(status)

    def post(self, request, *args, **kwargs):
        """
        API to add Express Interest.
        ---
        parameters:
        - name: get_docu
          description: Pass Documentation
          required: true
          type: file
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class DataRestoreListing(ListAPIView):
    queryset = SurveyDump.objects.filter(active=2)
    serializer_class = SurveyRestoreSerializer

    def get_location_access(self, user_id):
        get_user, get_location = UserRoles.objects.filter(
            active=2, user__id=user_id), []
        if get_user:
            get_location = get_user[0].get_location_type()
        return get_location

    def list(self, request, *args, **kwargs):
        get_level_loc = []
        response = {'status': 0,
                    'message': 'Something went wrong', 'data': []}
        data = request.query_params
        queryset = self.get_queryset()
        get_user_based = list(SurveyRestore.objects.filter(active=2,
                                                           survey_user__id=data.get('user_id')))
        get_level_loc = list(set(queryset.filter(boundary__id__in=self.get_location_access(
            data.get('user_id'))).values_list('survey_restore', flat=True)))
        if get_level_loc or get_user_based:
            rest = SurveyRestore.objects.filter(active=2)
            fina_ = map(lambda x: rest.filter(id=x)[0] if rest.filter(
                id=x) else None, get_level_loc)
            combined_data = get_user_based + list(fina_)
            data_ = [{'id': cd.id, 'name': cd.name, 'download': HOST_URL + '/' + cd.restore_file.url
                      if cd.restore_file else '', 'level': cd.level, 'level_type': cd.location_name()}
                     for cd in list(set(combined_data)) if cd != None]
            data_.sort(key=lambda x: x.get('id'), reverse=True)
            response = {'status': 2,
                        'message': 'Successfully retrieved the data'}
            response['data'] = data_
            if data.get('key') == '1':
                get_page = ceil(
                    float(len(combined_data)) / float(pg_size))
                paginator = CustomPagination()
                result_page = paginator.paginate_queryset(data_, request)
                return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), 31,  get_page)
        return Response(response)


class DataRestoreDetails(RetrieveDestroyAPIView):

    queryset = SurveyRestore.objects.filter(active=2)
    serializer_class = SurveyRestoreSerializer

    def retrieve(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong'}
        user_id = request.query_params.get('user_id')
        obj = DataRestoreListing()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = serializer.data
        loc_id = obj.get_location_access(user_id)
        response[
            'survey_user_name'] = instance.survey_user.username if instance.survey_user else ''
        response['download'] = HOST_URL + '/' + \
            instance.restore_file.url if instance.restore_file else ''
        response.update(instance.get_dump_data(loc_id))
        big_data = response.get('response')
        get_page = ceil(
            float(len(big_data)) / float(pg_size))
        response['get_page'] = get_page
        response['levels'] = 32
        response['obj'] = instance.id
        paginator = SecondaryCustomPagination()
        result_page = paginator.paginate_queryset(big_data, request)
        return paginator.get_paginated_response(result_page, **response)

    def perform_destroy(self, instance):
        return instance.get_parent_child_destory()
