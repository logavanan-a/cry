"""Data to Import Locations and Partners."""
from collections import (namedtuple,)
import csv
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.utils.text import (slugify,)
from rest_framework.generics import (CreateAPIView,)
from rest_framework.response import Response
from ccd.settings import (HOST_URL,)
from partner.models import (Partner, Program, Project)
from .models import (MasterLookUp, Boundary)
from .serializers import (MasterDataImport,)
from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned


class ImportMaster(CreateAPIView):
    serializer_class = MasterDataImport

    def get_parent(self, parent_level, level, parent, content_type):
        if level == 3 or level == 2:
            parent_level = 0
        get_parent_ = Boundary.objects.filter(
            name__iexact=parent.strip().title(), boundary_level=level,
            object_id=parent_level, content_type=content_type)
        return get_parent_[0] if get_parent_ else 0

    def import_rural_data(self, key, level, read_file):
        response = {'status': 0, 'message': 'Something went wrong'}
        region = dict(MasterLookUp.objects.filter(
            parent__slug='region').values_list('name', 'id'))
        content_type = ContentType.objects.get_for_model(
            MasterLookUp)
        data = MasterLookUp.objects.filter(
            active=2, slug__iexact='location-rural')
        if data:
            levels = data[0].id
        if level == 2 or level == 3:
            levels = 0
        reader = csv.reader(read_file)
        headers = reader.next()
        head_ = namedtuple(
            'head_', headers)

        count = 0
        not_save = []
        if key == '3':
            for rur in reader:

                h = head_(*rur)
                get_parent = self.get_parent(
                    levels, level - 1, h.Parent, content_type)
                obj_ = Boundary.objects.filter(
                    name__iexact=h.Name.strip().title(), boundary_level=level,
                    object_id=levels, content_type=content_type, parent=get_parent).order_by('id')
                obj = obj_[0] if obj_ else 0
                if not obj:
                    obj, created = Boundary.objects.get_or_create(
                        name=h.Name.strip().title(), boundary_level=level,
                        object_id=levels, content_type=content_type, parent=get_parent)
                if h.code != '' or h.code != '0':
                    setattr(obj, 'code', h.code)
                if h.region != '' or h.region != '0':
                    obj.region_id = region.get(h.region.strip().title())
                obj.save()
                count += 1
                response = {'status': 2, 'count': count, 'not_save': not_save,
                            'message': 'Successfully Uploaded the data'}
        return response

    def import_urban_data(self, key, level, read_file):
        response = {'status': 0, 'message': 'Something went wrong'}
        ward = dict(MasterLookUp.objects.filter(
            parent__slug='urban-ward').values_list('name', 'id'))
        region = dict(MasterLookUp.objects.filter(
            parent__slug='region').values_list('name', 'id'))
        content_type = ContentType.objects.get_for_model(
            MasterLookUp)
        data = MasterLookUp.objects.filter(
            active=2, slug__iexact='location-urban')
        if data:
            levels = data[0].id
        if level == 2 or level == 3:
            levels = 0
        reader = csv.reader(read_file)
        headers = reader.next()
        response = {'status': 0, 'message': 'Something went wrong'}
        head_ = namedtuple(
            'head_', headers)
        uploaded_ = 1
        count = 0
        not_save = []
        if key == '4':
            for rur in reader:
                try:
                    uploaded_ += 1
                    h = head_(*rur)
                    get_parent = self.get_parent(
                        levels, level - 1, h.Parent, content_type)
                    obj_ = Boundary.objects.filter(
                        name__iexact=h.Name.strip().title(), boundary_level=level,
                        object_id=levels, content_type=content_type, parent=get_parent).order_by('id')
                    obj = obj_[0] if obj_ else 0
                    if not obj:
                        obj, created = Boundary.objects.get_or_create(
                            name=h.Name.strip().title(), boundary_level=level,
                            object_id=levels, content_type=content_type, parent=get_parent)
                    if h.code != '' or h.code != '0':
                        setattr(obj, 'code', h.code)
                    if h.region != '' or h.region != '0':
                        obj.region_id = region.get(h.region.strip().title())
                    if h.ward != '' or h.ward != '0':
                        obj.ward_type_id = ward.get(h.ward.strip().title())
                    obj.save()
                    count += 1
                    response = {'status': 2, 'count': count, 'not_save': not_save,
                                'message': 'Successfully Uploaded the data'}
                except ValueError as e:
                    not_save.append(uploaded_)
                    response.update(errors=e.message)
        return response

    def create(self, request, *args, **kwargs):
        import_dict = {'status': 0, 'message': 'Something went wrong'}
        data = request.data
        key = data.get('key')
        import_file = request.FILES['import_file']
        level = int(data.get('level', 0))
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            import_dict = {
                '3': self.import_rural_data(key, level, import_file),
                '4': self.import_urban_data(key, level, import_file)}.get(key)
        else:
            import_dict.update(errors=serializer.errors)
        return Response(import_dict)

    def post(self, request, *args, **kwargs):
        """
        API to Import the data.
        ---
        parameters:
        - name: import_file
          description: Pass CSV to import the data
          required: true
          type: file
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class ImportMasterDetails(CreateAPIView):
    serializer_class = MasterDataImport

    def inactive_other_objects(self, queryset):
        map(lambda x: (setattr(x, 'active', 0), x.save()), queryset)

    def import_masterdata(self, key, read_file):
        reader = csv.reader(read_file)
        headers = reader.next()
        response = {'status': 0, 'message': 'Something went wrong'}
        head_ = namedtuple(
            'head_', headers)
        if key == '1':
            for sr in reader:
                h = head_(*sr)
                if h.slug != '':
                    self.inactive_other_objects(
                        MasterLookUp.objects.filter(active=2, parent__slug__iexact=h.slug))
                    obj, created = MasterLookUp.objects.get_or_create(
                        slug=h.slug)
                    if h.Parent != '':
                        obj.name = h.Parent
                        obj.save()
                    child_items = map(lambda y: y.strip(), h.Name.split(','))
                    map(lambda x: MasterLookUp.objects.create(
                        name=x, slug=slugify(x), parent=obj), child_items)
                    response = {'status': 2,
                                'message': 'Successfully Imported the Data'}
        return response

    def create(self, request, *args, **kwargs):
        import_dict = {'status': 0, 'message': 'Something went wrong'}
        data = request.data
        key = data.get('key')
        import_file = request.FILES['import_file']

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            import_dict = {'1': self.import_masterdata(
                key, import_file)}.get(key)
        else:
            import_dict.update(errors=serializer.errors)
        return Response(import_dict)

    def post(self, request, *args, **kwargs):
        """
        API to Import the data.
        ---
        parameters:
        - name: import_file
          description: Pass CSV to import the data
          required: true
          type: file
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class ImportPartnerDetails(CreateAPIView):
    serializer_class = MasterDataImport

    def import_partner_details(self, key, read_file):
        reader = csv.reader(read_file)
        headers = reader.next()
        response = {'status': 0, 'message': 'Something went wrong'}
        if key == '2':
            for part in reader:
                data = dict(zip(headers, part))
                # Region  State   Name    Status  Nature  From  To
                get_region, created = MasterLookUp.objects.get_or_create(active=2,
                                                                         name=data.get(
                                                                             'region', '').strip(),
                                                                         parent__slug__iexact='region')
                get_state, created = Boundary.objects.get_or_create(active=2,
                                                                    name=data.get(
                                                                        'State', '').strip(),
                                                                    boundary_level=2)
                get_status, created = MasterLookUp.objects.get_or_create(active=2,
                                                                         name=data.get(
                                                                             'Status', '').strip(),
                                                                         parent__slug='partnership-status')
                get_nature, created = MasterLookUp.objects.get_or_create(active=2,
                                                                         name=data.get(
                                                                             'Nature', '').strip(),
                                                                         parent__slug='nature-type-of-partner')
                to_ = datetime.strptime(
                    data.get('From', '21/07/1991'), '%d/%m/%Y')
                from_ = datetime.strptime(
                    data.get('To', '07/21/1991'), '%m/%d/%Y')
                create_part = Partner.objects.create(
                    name=data.get('Name', '').strip(), region=get_region, state=get_state,
                    nature_of_partner=get_nature, status=get_status,
                    support_from=to_, support_to=from_)
                create_part.partner_id = 'CRY - ' + str(create_part.id)
                create_part.save()
                prog = Program.objects.create(partner=create_part)
                Project.objects.create(program=prog)
                response = {'status': 2,
                            'message': 'Successfully Imported the Data'}
        return response

    def create(self, request, *args, **kwargs):
        import_dict = {'status': 0, 'message': 'Something went wrong'}
        data = request.data
        key = data.get('key')
        import_file = request.FILES['import_file']
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            import_dict = {
                '2': self.import_partner_details(key, import_file), }.get(key)
        else:
            import_dict.update(errors=serializer.errors)
        return Response(import_dict)

    def post(self, request, *args, **kwargs):
        """
        API to Import the data.
        ---
        parameters:
        - name: import_file
          description: Pass CSV to import the data
          required: true
          type: file
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class ImportAllLocations():

    @staticmethod
    def import_rural_locations(file_path,level):
        ml = MasterLookUp.objects.get(id=17)
        ct = ContentType.objects.get(model='masterlookup')
        file_reader = csv.DictReader(open(file_path,'r'))

        for i in file_reader:
            level_conv = {2:'State',3:'District',4:'Block',5:'GP',6:'Village',7:'Hamlet'}
            print i
            level_helper = {
                            # 2: {'region_id': i.get("RegionCode").replace(" ",""),
                            #     'cry_admin_id':i.get('StateCode').replace(" ",""),
                            #     'name':i.get('State'),
                            #     'parent_id':1,
                            #     'boundary_level':level,
                            #     },
                            # 3: {
                            #     'cry_admin_id':i.get('DistrictCode'),
                            #     'name':i.get('District'),
                            #     'boundary_level':level
                            #     },

                            # 4: {
                            #     'cry_admin_id': i.get('BlockCode').replace(" ",""),
                            #     'boundary_level':level,
                            #     'object_id':17,
                            #     'content_type_id':ct.id,
                            #     },

                            # 5: {
                            #     'cry_admin_id':i.get('GPCode').replace(" ",""),
                            #     'name':i.get('GP'),
                            #     'boundary_level':level,
                            #     'object_id':17,
                            #     'content_type_id':ct.id
                            #     },

                            # 6:{
                            #    'cry_admin_id':i.get("VillageCode").replace(" ",""),
                            #    'name':i.get("Village"),
                            #    'boundary_level':level,
                            #    'object_id':17,
                            #    },

                            # 7:{
                            #    'cry_admin_id':i.get("HamletCode"),
                            #    'name':i.get("Hamlet"),
                            #    'boundary_level':level,
                            #    'object_id':17,
                            #    'content_type_id':ct.id,
                            #    },

                            }

            try:
                create = Boundary.objects.create(**level_helper.get(level))
                create.parent = Boundary.objects.get(boundary_level=level-1,cry_admin_id=i.get('VillageCode'),parent__cry_admin_id=i.get('GPCode'),parent__parent__cry_admin_id=i.get('BlockCode'),parent__parent__parent__cry_admin_id=i.get('DistrictCode'))
                create.save()
            except Exception as e:
                print e.message


    def call_rural(self,path,level):
        return ImportAllLocations.import_rural_locations(path,level)


    def call_urban(self,path,level):
        return ImportAllLocations.import_urban_locations(path,level)

    @staticmethod
    def import_urban_locations(file_path, level):
        ml = MasterLookUp.objects.get(id=18)
        ct = ContentType.objects.get(model='masterlookup')
        file_reader = csv.DictReader(open(file_path, 'r'))

        for i in file_reader:
            print i
            level_conv = {2: 'State', 3: 'District', 4: 'Block', 5: 'GP', 6: 'Village', 7: 'Hamlet'}
            level_helper = {
                              # 2: {'region_id': i.get("RegionCode"),
                              #   'name':i.get("State"),
                              #   'cry_admin_id':i.get("StateCode").replace(" ",""),
                              #   'boundary_level':level,
                              #   'parent_id':1,
                              #   },

                            # 3: {
                            #     'name': i.get("District"),
                            #     'cry_admin_id':i.get('DistrictCode').replace(" ",""),
                            #     'boundary_level':level,
                            #     },

                            # 4: {
                            #     'name': i.get("City"),
                            #     'cry_admin_id':i.get('CityCode'),
                            #     'boundary_level':level,
                            #     'object_id':18,
                            #     'content_type_id':ct.id
                            #     },

                            # 5: {
                            #     'name': i.get("Area"),
                            #     'cry_admin_id':i.get('AreaCode').replace(" ",""),
                            #     'boundary_level':level,
                            #     'object_id':18,
                            #     'content_type_id':ct.id
                            #     },

                            # 6: {
                            #     'name': i.get("Ward"),
                            #     'cry_admin_id': i.get('WardCode').replace(" ", ""),
                            #     'boundary_level':level,
                            #     'object_id':18,
                            #     'content_type_id':ct.id,
                            #     'ward_type_id':i.get('WardCategory'),
                            #     },

                            7: {
                                'name': i.get("Slum"),
                                'cry_admin_id': i.get('SlumCode').replace(" ", ""),
                                'boundary_level':level,
                                'object_id':18,
                                'content_type_id':ct.id,
                                },
                            }
            try:
                #b = Boundary.objects.create(**level_helper.get(level))
                b = Boundary.objects.get(boundary_level=level,object_id=18,cry_admin_id=i.get('SlumCode'))
                p = Boundary.objects.get(boundary_level=level-1,object_id=18,cry_admin_id=i.get('WardCode'))
                b.parent = p
                b.save()

            except Exception as e:
                pass

def import_partner(file_path):
    file_reader = csv.DictReader(open(file_path, 'r'))
    for i in file_reader:
        print i
        boundary= Boundary.objects.get(boundary_level=2,cry_admin_id=i.get('state_id'))
        region = MasterLookUp.objects.get(parent__slug='region',name=i.get('region'))
        ptnr = Partner.objects.create(state=boundary,name=i.get('name'),region=region,partner_id=i.get('cry_admin_id').replace(" ",""))
        prg = Program.objects.create(partner=ptnr,name=ptnr.name)
        Project.objects.create(program=prg,name=prg.name)
