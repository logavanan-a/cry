from collections import (deque)
from math import (ceil,)
import threading
from django.core.management import call_command
from rest_framework.generics import (CreateAPIView, )
from rest_framework.response import Response
from ccd.settings import(REST_FRAMEWORK, )
from masterdata.views import (CustomPagination,)
from .models import (Boundary, MasterLookUp)
from .serializers import(MasterDataImport, LocationDataReportSerializer)
import csv

pg_size = REST_FRAMEWORK.get('MASTERDATA_LOCATION', 0)


REPORT_TYPES = {
    2: 'State',
    3: 'District',
    'location-rural': {
        4: 'Block',
        5: 'GramaPanchayath',
        6: 'Village',
        7: 'Hamlet'
    },
    'location-urban': {
        4: 'City',
        5: 'Area',
        6: 'Ward',
        7: 'Mohalla/Slum',
    },
    'rural-urban': {
        4: 'Block / City',
        5: 'GramaPanchayath / Area',
        6: 'Village / Ward',
        7: 'Hamlet / Mohalla / Slum'
    }
}

LEVELS_TYPES = {
    2: {'display_headers': ['Country ID', 'Country Name', 'State ID', 'State Name'],
        'headers': ['country_id', 'country_name', 'state_id', 'state_name', ]},
    3: {'display_headers': ['Country ID', 'Country Name',
                            'State ID', 'State Name', 'District ID', 'District Name'],
        'headers': ['country_id', 'country_name', 'state_id', 'state_name',
                    'district_id', 'district_name']},
    'location-rural': {
        4: ['Country', 'State', 'District', 'Block'],
        5: ['Country', 'State', 'District', 'Block', 'GramaPanchayath'],
        6: ['Country', 'State', 'District', 'Block', 'GramaPanchayath', 'Village'],
        7: ['Country', 'State', 'District', 'Block', 'GramaPanchayath',
            'Village', 'Hamlet']
    },
    'location-urban': {
        4: ['Country', 'State', 'District', 'City'],
        5: ['Country', 'State', 'District', 'City', 'Area'],
        6: ['Country', 'State', 'District', 'City', 'Area', 'Ward'],
        7: ['Country', 'State', 'District', 'City', 'Area', 'Ward', 'Mohalla/Slum'],
    },
    'rural-urban': {
        4: ['Country', 'State', 'District', 'Block / City'],
        5: ['Country', 'State', 'District', 'Block / City', 'GramaPanchayath / Area'],
        6: ['Country', 'State', 'District', 'Block / City', 'GramaPanchayath / Area',
            'Village / Ward'],
        7: ['Country', 'State', 'District', 'Block / City', 'GramaPanchayath / Area',
            'Village / Ward', 'Hamlet / Mohalla / Slum']
    }
}


class LocationMasterData(CreateAPIView):
    serializer_class = MasterDataImport
    queryset = MasterLookUp.objects.filter(active=2)

    def create(self, request, *args, **kwargs):
        response = {'status': 0,
                    'message': 'Something went wrong', 'data': []}
        query = self.get_queryset()
        location_exclude = range(1, 4)
        loca_type = list(query.filter(
            parent__slug='location-type').values('id', 'name'))
        combined_data = query.filter(
            slug='rural-urban').values('id', 'name')
        loca_type_combined = list(combined_data)
        loca_type.extend(loca_type_combined)
        ward_type = query.filter(
            parent__slug='urban-ward').values('id', 'name')
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = request.data
            key = int(data.get('key', 0))
            level = int(data.get('level', 0))
            get_dict = {1: loca_type, 2: query.filter(
                parent__id=level).exclude(code__in=location_exclude).values('code', 'name').order_by('code'),
                3: ward_type, 4: query.filter(parent__slug__iexact='rural-urban').values('code', 'name').order_by('code')}
            loca_ = get_dict.get(key)
            response = {'status': 2,
                        'message': 'Successfully data retrieved', 'data': loca_}
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class LocationDataReport(CreateAPIView):
    queryset = Boundary.objects.filter(active=2)
    serializer_class = LocationDataReportSerializer

    def run_thread(self, data, location_ids):
        call_command('reports', data, location_ids)

    def get_tree_struct(self, level):
        d = deque(['id', 'name'])
        parent = 'parent.'
        parent_value = 1
        while level - 1:
            name, id_ = [
                (parent * parent_value) + 'name',
                (parent * parent_value) + 'id']
            d.appendleft(name)
            d.appendleft(id_)
            parent_value += 1
            level -= 1
        return list(d)

    def get_levels_down_data(self, loc_type, parent_id, next_level, slug, loc_ids, key):
        if key == 1 and loc_ids == '0' and (next_level != 2 and next_level != 3):
            all_every_location = Boundary.objects.filter(
                active=2, boundary_level=next_level, object_id=loc_type).values_list('id', flat=True)
        elif key == 1 and loc_ids == '0' and (next_level == 2 or next_level == 3):
            all_every_location = Boundary.objects.filter(
                active=2, boundary_level=next_level, object_id=0).values_list('id', flat=True)
        elif key == 1 and loc_ids != '0' and (next_level == 2 or next_level == 3):
            all_every_location = Boundary.objects.filter(parent__id=parent_id,
                                                         active=2, boundary_level=next_level, object_id=0).values_list('id', flat=True)
        else:
            wanted_level = next_level
            if slug != 'rural-urban':
                all_location = Boundary.objects.filter(
                    active=2, object_id=loc_type)
            else:
                all_location = Boundary.objects.filter(active=2)
            all_levels = {}
            get_parent = Boundary.objects.get(id=parent_id)
            par_level = get_parent.boundary_level
            level = par_level + 1
            list_parent = [parent_id]
            if par_level == level:
                get_location = all_location.filter(
                    parent__id__in=list_parent, boundary_level=level).values_list('id', flat=True)
                all_levels[par_level] = get_location
            else:
                all_levels[par_level] = list_parent
                while par_level < wanted_level:
                    loc = all_levels.get(par_level)
                    get_location = all_location.filter(
                        parent__id__in=loc, boundary_level=level).values_list('id', flat=True)
                    par_level += 1
                    all_levels[par_level] = get_location
                    level += 1
            all_every_location = list(all_levels.get(wanted_level))
        return all_every_location

    def get_listing_location(self, location):
        for loc in location:
            get_location = Boundary.objects.get_or_none(id=loc)
            if get_location:
                yield get_location

    def get_name(self, name):
        return ''.join(map(lambda x: x.strip().replace(' ', '_').lower(), name.split('/')))

    def get_dict_data(self, data):
        kill_dict = {'display_headers': [], 'headers': []}
        for nam in kill_dict.keys():
            data_list = kill_dict[nam]
            for internin in data:
                if nam == 'display_headers':
                    id_inter = internin + ' ' + 'ID'
                    name_inter = internin + ' ' + 'Name'
                else:
                    id_inter = self.get_name(internin) + '_' + 'id'
                    name_inter = self.get_name(internin) + '_' + 'name'
                data_list.extend([id_inter, name_inter])
        return kill_dict

    def create(self, request, *args, **kwargs):
        get_mast_slug, slug = 'rural-urban', ''
        display_headers = headers = []
        response = {'status': 0, 'message': 'Something went wrong.',
                    'display_headers': display_headers, 'headers': headers, 'data': []}
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            location = []
            loc_type = int(data.get('loc_type', 0))
            loc_level = int(data.get('loc_level', 0))
            user_id = int(data.get('user_id', 0))
            loc_ids = map(int, data.get('loc_ids', '0').split(','))
            key = int(data.get('key', 0))
            get_slug = MasterLookUp.objects.get_or_none(id=loc_type)
            if loc_level == 2 or loc_level == 3:
                get_data = LEVELS_TYPES.get(loc_level)
                location_name = REPORT_TYPES.get(loc_level)
                display_headers = get_data.get('display_headers')
                headers = get_data.get('headers')
                levels_data = self.get_tree_struct(loc_level)
            else:
                get_mast_slug = MasterLookUp.objects.get_or_none(id=loc_type)
                if get_mast_slug:
                    slug = get_mast_slug.slug
                    get_data_slug = LEVELS_TYPES.get(slug)
                    get_data = self.get_dict_data(get_data_slug.get(loc_level))
                    location_na = REPORT_TYPES.get(slug)
                    location_name = location_na.get(loc_level)
                    display_headers = get_data.get('display_headers')
                    headers = get_data.get('headers')
                    levels_data = self.get_tree_struct(loc_level)
            for kill in loc_ids:
                location.extend(self.get_levels_down_data(
                    loc_type, kill, loc_level, slug, data.get('loc_ids', '0'), key))
            if key == 1:
                location_yield = list(self.get_listing_location(location))
                get_loc_list = [{'id': locs_.id, 'name': locs_.name}
                                for locs_ in location_yield]
                get_page = ceil(
                    float(len(location_yield)) / float(pg_size))
                paginator = CustomPagination()
                result_page = paginator.paginate_queryset(
                    get_loc_list, request)
                return paginator.get_paginated_response(result_page, 200, 'Successfully retrieved the location',
                                                        loc_level, get_page)
            else:
                level_name = levels_data
                level_headers = headers
                data = {'display_headers': display_headers, 'location_name': location_name,
                        'user_id': user_id,
                        'location_type': get_slug.name if get_slug else 'N/A',
                        'level_name': level_name, 'level_headers': level_headers}
                location_ids = map(int, location)
                th = threading.Thread(target=self.run_thread,
                                      args=(str(data), str(location_ids)))
                th.start()
                response = {
                    'status': 2, 'message': 'Successfully CSV File has been sent to your mail.'}
        else:
            response.update(errors=serializer.errors)
        return Response(response)

def get_hierarchy_data():
    hamlet_info = open('level_info.csv','w')
    hamlet_writer = csv.writer(hamlet_info)
    masterlookup = MasterLookUp.objects.filter(id__in=[17,18])
    all_locations = Boundary.objects.filter(active=2)
    level7_objects = all_locations.filter(boundary_level=7).order_by('name')
    for one_obj in level7_objects:
        parent_level = convert_list_to_dict(one_obj.get_parent_locations([]))

        level = 6
        parent_info = []
        parent_info.append(str(masterlookup.get(id=one_obj.object_id)))
        parent_info.append(str(one_obj.id))
        parent_info.append(str(one_obj))
        parent_info.append("")

        while level > 1:
            parent_info.extend([str(parent_level.get('level'+str(level)+'_id')),str(all_locations.get(id=parent_level.get('level'+str(level)+'_id')))])
            level = level -1
        hamlet_writer.writerow(parent_info)
    hamlet_info.close()

def convert_list_to_dict(lis):
    dic = {}
    for i in lis:
        key = i.keys()[0]
        dic[key]=i[key]
    return dic

from survey.views.survey_views_two import get_required_level_info

def all_locations_step_export():
    location_writer = csv.writer(open('all_locations.csv','w'))
    state_list = Boundary.objects.filter(boundary_level=2)
    ml_resolver = {17:'Rural',18:'Urban'}
    for state in state_list:
        location_writer.writerow([str(state.id),str(state.name)])

        districts = eval(get_required_level_info(state.id,3).content).get('locations')
        for d in districts:
            print d
            location_writer.writerow(["", "District Id", "District Name", "Location Type"])
            location_writer.writerow(["",str(d.get('id')),str(d.get('name')),str(ml_resolver.get(d.get('object_id')))])
            block = eval(get_required_level_info(d.get('id'),4).content).get('locations')
            location_writer.writerow(["","","Block Id", "Block Name", "Location Type"])
            for b in block:
                print b
                location_writer.writerow(["","",str(b.get('id')),str(b.get('name')),str(ml_resolver.get(b.get('object_id')))])
                gp = eval(get_required_level_info(b.get('id'),5).content).get('locations')
                location_writer.writerow(["","","","GP Id", "GP Name", "Location Type"])
                for g in gp:
                    print g
                    location_writer.writerow(["","","",str(g.get('id')),str(g.get('name')),str(ml_resolver.get(g.get('object_id')))])
                    village = eval(get_required_level_info(g.get('id'),6).content).get('locations')
                    location_writer.writerow(["","","","","Village Id", "Village Name", "Location Type"])
                    for v in village:
                        print v
                        location_writer.writerow(["","","","",str(v.get('id')),str(v.get('name')),str(ml_resolver.get(v.get('object_id')))])
                        hamlet = eval(get_required_level_info(v.get('id'),7).content).get('locations')
                        location_writer.writerow(["","","","","","Hamlet Id", "Hamlet Name", "Location Type"])
                        for h in hamlet:
                            print h
                            location_writer.writerow(["","","","","",str(h.get('id')),str(h.get('name')),str(ml_resolver.get(h.get('object_id')))])
    location_writer.close()


