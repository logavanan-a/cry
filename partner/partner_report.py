"""File to Generate Partner Report."""
from collections import namedtuple
from itertools import (chain,)
import csv
from math import ceil
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from rest_framework.generics import (ListAPIView, CreateAPIView)
from rest_framework.response import Response
from ccd.settings import(BASE_DIR, REST_FRAMEWORK, HOST_URL)
from masterdata.models import (Boundary, MasterLookUp,)
from masterdata.views import (CustomPagination,)
from .serializers import (FilterDataSerializer, PartnerReportTableSerializer)
from .models import (Partner, PartnerReportFile)

pg_size = REST_FRAMEWORK.get('PAGE_SIZE')
mist_ = MasterLookUp.objects.filter(active=2,
                                    parent__slug__iexact='theme').order_by('id')
theme_ = mist_.values_list('name', flat=True)
mast = ['CRY Theme: ' + the_ + ' (Y/N)' for the_ in theme_]
data_mast = [the_.lower() for the_ in theme_]

display_headers = ['ID',
                   'Updated on (date)',
                   'Region',
                   'State',
                   'Name of Initiative',
                   'Nature',
                   'Ongoing Grant Cycle',
                   'Budget as per Sanctioned AER',
                   'Registration Status - FCRA / Non-FC',
                   'CRY Location',
                   'CRY Support Since',
                   'Available for booking']
display_headers.extend(mast)
display_headers.append('DS Remarks')

DATA = [
    'id',
    'update',
    'region',
    'state',
    'name',
    'nature',
    'ongoing_cycle',
    'budget',
    'reg_stat',
    'cry_location',
    'support',
    'booking']
DATA.extend(data_mast)
DATA.append('ds_remarks')


class PartnerDownloadReport(ListAPIView):
    queryset = Partner.objects.filter(active=2).order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = args[0]
        response = {'status': 0, 'count': 0,
                    'message': 'Something went wrong.', 'download': ''}
        with open(BASE_DIR + '/static/' + 'partners.csv', 'wb+') as f:
            write = csv.writer(f)
            write.writerow(display_headers)
            for pc in queryset:
                write.writerow(pc.get_partner_master_data())
            part_report, created = PartnerReportFile.objects.get_or_create(
                name='partner_report')
            part_report.report.save(f.name, File(f))
            download = HOST_URL + '/' + part_report.report.url
            response = {
                'status': 2, 'message': 'Successfully data retrieved', 'download': download}
        return Response(response)


class PartnerReportTable(CreateAPIView):
    queryset = Partner.objects.filter(active=2).order_by('-id')
    serializer_class = PartnerReportTableSerializer

    def split_up_id(self, text):
        data_ids = []
        if text:
            data_ids = map(int, text.split(','))
        return data_ids

    def get_data(self, b_, data):
        return data[1] if b_ == data[0] else 0

    def get_partner_data(self, data, query):
        booking = 0
        data_ = data
        queryset = query
        region_id = self.split_up_id(data_.get('region_id', 0))
        state = self.split_up_id(data_.get('state', 0))
        nature = self.split_up_id(data_.get('nature', 0))
        book = data_.get('booking', 0)
        if book:
            booking = book.split(',')
        part_dict = []
        data = namedtuple('data', DATA)
        if data_.get('key') == '2':
            if region_id:
                queryset = queryset.filter(region__id__in=region_id)
            if state:
                queryset = queryset.filter(state__id__in=state)
            if nature:
                queryset = queryset.filter(nature_of_partner__id__in=nature)
            if booking:
                book_query = [pj.get_dpf_data() for pj in queryset]
                partner_ids = []
                for b_ in booking:
                    for book in book_query:
                        b_data = self.get_data(b_, book)
                        if b_data:
                            partner_ids.append(b_data)
                queryset = queryset.filter(id__in=partner_ids)
        for part in queryset:
            get_part = data(*part.get_partner_master_data())
            part_dict.append(get_part._asdict())
        return part_dict, queryset

    def post(self, request, *args, **kwargs):
        data = request.data
        queryset = self.get_queryset()
        response = {'status': 0, 'count': 0,
                    'message': 'No Data to display.', 'data': [],
                    'display_headers': display_headers}
        get_data, query_data = self.get_partner_data(data,
                                                     queryset)
        if get_data:
            pdr = PartnerDownloadReport()
            data_response = pdr.list(request, query_data)
            response = {'status': 2, 'message': 'Successfully data retrieved',
                        'display_headers': display_headers}
            response['data'] = get_data
            get_page = ceil(float(len(get_data)) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(get_data, request)
            return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 33,
                                                    get_page, display_headers, DATA, data_response.data.get('download'))
        return Response(response)


class DPFilterData(ListAPIView):
    queryset = MasterLookUp.objects.filter(active=2)
    serializer_class = FilterDataSerializer

    def get_response(self, query_name, queryset, region=None):
        users_data = []
        if query_name and queryset:
            get_name = query_name.split(',')
            query = lambda x: queryset.filter(
                active=2, name__istartswith=x)
            if region:
                query = lambda x: queryset.filter(
                    active=2, region__id__in=map(int, region.split(',')), name__istartswith=x)
            all_names = lambda x: [
                {'id': u.id, 'name': u.name} for u in query(x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def get_raw_data(self, query):
        return [{'id': q.id, 'name': q.name} for q in query]

    def get_results(self, data, query):
        key = int(data.get('key', 0))
        query_name = data.get('user_name', '')
        region_id = data.get('region_id', '')
        bound_states = Boundary.objects.filter(
            active=2, boundary_level=2, object_id=0, content_type=ContentType.objects.get_for_model(
                MasterLookUp))
        nature = query.filter(
            parent__slug__iexact='nature-type-of-partner')
        region = query.filter(parent__slug__iexact='region')
        partner = Partner.objects.filter(active=2)
        booking = [{'name': 'Not-Available'}, {'name': 'Available'}]
        data = {1: region, 2: bound_states, 3: nature, 4: booking, 5: partner}
        if key == 2 or key == 3 or key == 5:
            query_set = self.get_response(
                query_name, data.get(key, 0), region_id)
        elif key == 4:
            query_set = data.get(key)
        else:
            query_set = self.get_raw_data(data.get(key))
        return query_set

    def list(self, request, *args, **kwargs):
        res_data = {'status': 0,
                    'message': 'No Data to display.'}
        data = request.query_params
        query = self.get_queryset()
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            res_data = self.get_results(data, query)
        else:
            res_data.update(errors=serializer.errors)
        return Response(res_data)
