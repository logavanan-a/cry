import csv
from masterdata.models import *
from facilities.models import *
from beneficiary.views import fadd
import uuid
from userroles.models import *
import re

def replace_special_characters(text):
    return re.sub(r'[\\u\n]+','', text)

def import_facility():
    '''Function to import facility
    the input file should be a csv file
    using csvreader will get all the contents in the csv file'''
    csv_path = raw_input('Enter the csv file path: ')

    with open(csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            partner_id = row['Partner']
            fac_name = row['Name']
            fac_type_id = row['Facility Type']
            fac_subtype_id = row['Facility SubType']
            fac_thematic_area_id = row['Thematic area']
            fac_address1 = replace_special_characters(row['Address1'].decode('ascii','ignore'))
            fac_address2 = replace_special_characters(row['Address2'].decode('ascii','ignore'))
            fac_pincode = row['Pincode']
            
            fac_services = row['Service']
            fac_boundary_id = row['Location ID']
            fac_tempid = row['Tempid']
            jdata = {}
            jdata.update({'name':fac_name, 'facility_type_id':fac_type_id,
                'facility_subtype_id':fac_subtype_id,
                'thematic_area_id':fac_thematic_area_id,
                'address':{'address_0':{'address1':str(fac_address1), 'address2':str(fac_address2), 'pincode':fac_pincode,
                'boundary_id':int(fac_boundary_id)}},
                'partner_id':int(partner_id),
                'tempid':int(fac_tempid)
                })
            fac_dict = {'name':fac_name,
                         'partner_id':int(partner_id), 'uuid':uuid.uuid4(),
                         'jsondata':jdata, 'facility_type_id':fac_type_id,
                         'facility_subtype_id':fac_subtype_id,
                         'thematic_area_id':fac_thematic_area_id,
                         'tempid':int(fac_tempid)
                    }
            address_dict = {'address1':str(fac_address1), 'address2':str(fac_address2), 'pincode':fac_pincode,
                'boundary_id':int(fac_boundary_id), 'office':1}
            obj = Facility.objects.create(**fac_dict)
            services = fac_services.split(',')
            obj.services.add(*services)
            addr_obj = Address.objects.create(**address_dict)
            addr_obj.content_type = ContentType.objects.get_for_model(obj)
            addr_obj.object_id = obj.id
            addr_obj.save()
