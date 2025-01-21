import csv
from masterdata.models import *
from beneficiary.models import Beneficiary, BeneficiaryType
from beneficiary.views import fadd
import uuid
from userroles.models import *
import re
import random

def replace_special_characters(text):
    return re.sub(r'[\\u\n]+','', text)

def import_beneficiary():
    '''Function to import beneficiary
    the input file should be a csv file
    using csvreader will get all the contents in the csv file'''

    csv_path = raw_input('Enter the csv file path: ')
    with open(csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            partner_id = row['Partner']
            ben_name = row['Name']
            ben_type_id = row['Beneficiary Type']
            parent_id = row['Household']
            ben_gender = row['Gender']
            ben_age = row['Age']
            ben_tempid = row['Tempid']
            ben_contact_number = row['Contact Number']
            ben_address1 = replace_special_characters(row['Address1'].decode('ascii','ignore'))
            ben_address2 = replace_special_characters(row['Address2'].decode('ascii','ignore'))
            ben_pincode = row['Pincode']
            row['Level']
            ben_boundary_id = row['Hamlet ID']
            jdata = {}
            contact_no = str(map(int, ben_contact_number.split(','))) if ben_contact_number else '[]'
            jdata.update({'name':ben_name, 'btype':'Child',
                'contact_no':contact_no, 'beneficiary_type_id':int(ben_type_id),
                'parent_id':parent_id, 'gender':ben_gender.lower(), 'age':ben_age,
                'address':{'address_0':{'address1':str(ben_address1), 'address2':str(ben_address2), 'pincode':ben_pincode,
                'boundary_id':int(ben_boundary_id)}},
                'partner_id':int(partner_id),
                'tempid':int(ben_tempid),
                })
            try:
                parent_obj = Beneficiary.objects.get(tempid=ben_tempid)
            except:
                parent_obj = None
            ben_dict = {'name':ben_name, 'btype':'Child', 'beneficiary_type_id':int(ben_type_id),
                        'parent_id':'',
                         'partner_id':int(partner_id), 'uuid':uuid.uuid4(),
                         'jsondata':jdata, 'tempid':int(ben_tempid)
                    }
            address_dict = {'address1':str(ben_address1), 'address2':str(ben_address2), 'pincode':ben_pincode,
                'boundary_id':int(ben_boundary_id), 'office':1}
            obj = Beneficiary.objects.create(**ben_dict)
            addr_obj = Address.objects.create(**address_dict)
            addr_obj.content_type = ContentType.objects.get_for_model(obj)
            addr_obj.object_id = obj.id
            addr_obj.save()

from django.contrib.auth.models import User
from uuid import uuid4
from userroles.models import *
from partner.models import *

def user_import():
    files = raw_input("Enter your file path : ")
    with open(files,'rb') as fil:
        reader = csv.reader(fil)
        keys = reader.next()
        for row in reader:
            data = dict(zip(keys, row))
            part = data.get('partner')
            username = data.get('username')
            fname = data.get('firstname')
            mail = data.get('mail')
            if Partner.objects.filter(partner_id=part).exists():
                partid = Partner.objects.filter(partner_id=part).latest('id')
                userobj = User.objects.create_user(username=username,first_name=fname, email=mail)
                userobj.set_password('cry@2018')
                userobj.is_active=True
                userobj.save()
                activation = ResetActivation.objects.create(key=uuid4().hex, user=userobj)
                orguni = OrganizationUnit.objects.get(id=1)
                rotype = RoleTypes.objects.get(id=1)
                userrolesobj = UserRoles.objects.create(user=userobj, user_type=2, title=0, organization_unit=orguni)
                userrolesobj.partner = partid
                userrolesobj.role_type.add(rotype)
                userrolesobj.save()
                print "Succuessfully created %d" %(userrolesobj.id)
            else:
                print "Not existed" (part,username)
