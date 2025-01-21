from beneficiary.models import *
from masterdata.models import *
from facilities.models import *
from service.models import *
from survey.models import *
from partner.models import *
from uuid import uuid4
import csv
from datetime import datetime
import sys,os

class ManageDataMigration():

    def import_facility(self,path,survey_id):
        try:

            file_reader = csv.DictReader(open(path,'r'))
            error_file = csv.writer(open("error_facility.csv","w"))
            id_file = csv.writer(open('ids_facility.csv',"w"))
            thematic_area_helper = {1:108,2:110,3:110}
            services_helper = {1:35,2:33,3:38}
            for row in file_reader:
                try:
                    id_record = row.values()
                    facility_type = MasterLookUp.objects.get(parent__slug='facility-type',cry_admin_id=row.get('FacilityTypeID'))
                    facility_sub_type = MasterLookUp.objects.get(parent__parent__slug='facility-type',
                                                                 parent__cry_admin_id=row.get('FacilityTypeID'),cry_admin_id=row.get('FacilitySubTypeID'))
                    facility_info = {'name':row.get('FacilityName'),
                                     'facility_type_id':facility_type.id,
                                     'facility_subtype_id':facility_sub_type.id,
                                     'partner_id':Partner.objects.get(partner_id=row.get('PartnerID').replace(" ","")).id,
                                     'uuid':str(uuid4()),
                                     'cry_admin_id':row.get('FacilityCode'),
                                     'created':datetime.utcnow(),
                                     'modified':datetime.utcnow(),
                                     'jsondata':{},
                                     }
                    facility = Facility.objects.create(**facility_info)
                    facility_info['facility_type_id'] = [facility_type.id]
                    facility_info['facility_subtype_id'] = [facility_sub_type.id]
                    del facility_info['created']
                    del facility_info['modified']
                    try:

                        b = Boundary.objects.get(boundary_level=7,
                                             cry_admin_id=row.get('CRYLocationID').replace(" ", ""))
                        facility_info['boundary_id'] = [b.id] if b else []
                        Address.objects.create(content_type_id=29,object_id=facility.id,address1=b.name,boundary=b)
                    except Exception as e:
                        error_file.writerow(row.values())
                        print e.message," ",row.get('CRYLocationID')

                    thematic_area= [int(i) for i in row.get('ThematicID').split(",")] if row.get('ThematicID') else []

                    services= [int(i) for i in row.get('ServiceID').split(",")] if row.get('ServiceID') else []

                    facility_info['thematic_area']=str(thematic_area)
                    facility_info['services']=str(services)

                    facility.jsondata = facility_info
                    facility.save()
                    facility.thematic_area.add(*thematic_area)
                    facility.services.add(*services)
                    facility.save()

                    # app_data = AppAnswerData.objects.create(survey_id=survey_id)
                    # cluster  = [{'facility':{'id':facility.id,'facility_type_id':4}}]
                    # JsonAnswer.objects.create(survey_id=survey_id,
                    #       response=row,app_answer_data=app_data,cluster=cluster)

                    id_record.append(facility.id)
                    id_file.writerow(id_record)

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print("inside create",e.message," ",exc_tb.tb_lineno)

                    error_file.writerow(row.values())
        except Exception as e:
            print(e.message)


    def import_beneficiary(self,path,survey_id):
        try:
            reader = csv.DictReader(open(path,'r'))
            error_file = csv.writer(open("error_child.csv","w+"))
            id_file = csv.writer(open('ids_benf.csv',"w+"))
            for row in reader:
                try:
                    id_record = row.values()
                    partner = Partner.objects.get(partner_id=row.get('partner_id').replace(" ",""))
                    parent = Beneficiary.objects.get(beneficiary_type_id=2,cry_admin_id=row.get('household_id'))
                    mother = Beneficiary.objects.get_or_none(beneficiary_type_id=3,cry_admin_id=row.get('mother_id'))

                    beneficiary_info = {'name':row.get('name'),
                                     'beneficiary_type_id':4,
                                     'partner_id':partner.id,
                                     'parent_id':parent.id,
                                     'uuid':str(uuid4()),
                                     'jsondata':{'':''},
                                     'cry_admin_id':row.get('cry_admin_id')
                                     }
                    beneficiary = Beneficiary.objects.create(**beneficiary_info)
                    beneficiary_info['gender'] = ["male"] if int(row.get('gender')) == 1 else ["female"]
                    #beneficiary_info['gender']=["female"]
                    beneficiary_info['age'] = [str(row.get('age'))]
                    beneficiary_info['alias_name'] = [""]#[row.get("AliasName")]
                    beneficiary_info['mother_uuid'] = [str(mother.uuid) if mother else ""]
                    beneficiary_info['date_of_birth']=[str(row.get('DOB')).replace("/","-")]
                    beneficiary_info['dob_option']=["true"]
                    beneficiary_info['partner'] = str(partner)
                    beneficiary_info['contact_no'] = str([str(row.get('phoneNumber'))])
                    beneficiary_info['address']=[{
                        'address_0':{
                            'address_1':row.get('address1'),
                            'address_2':row.get('address2'),
                            'pincode':row.get('pincode'),
                            'proof_id':"349",
                            'boundary_id':row.get('boundary_id')
                        }
                    }]
                    beneficiary.jsondata = beneficiary_info
                    beneficiary.save()
                    boundary = Boundary.objects.get(boundary_level=7,cry_admin_id=row.get('Hamlet_ID'))
                    add = Address.objects.create(office=1,pincode=row.get('pincode'),address1=row.get('address1'),address2=row.get('address2'),                            content_type_id=27,object_id=beneficiary.id,boundary_id=boundary.id)
                    print add.id,row.get('cry_admin_id')
                    id_record.append(beneficiary.id)
                    id_file.writerow(id_record)
                except Exception as e:
                    print(e.message)
                    error_file.writerow(row.values())
        except Exception as e:
            print(e.message)