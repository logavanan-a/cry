from django.contrib.auth.models import User
import csv
from survey.models import *
from beneficiary.models import *
from facilities.models import *

usr = User.objects.get(id=1)
#[{"beneficiary": {"id": 2338, "beneficiary_type_id": 2}}]
#[{"boundary": {"boundary_type_id": 0, "id": 1136}}]

def import_village_survey_data(file_path,survey_id):
    csv_reader = csv.DictReader(open(file_path,"r"))
    for i in csv_reader:
        if Boundary.objects.filter(cry_admin_id=i.get("LocationID")).count() == 1:
            fac = Boundary.objects.get(cry_admin_id=i.get("LocationID"))
            cluster_info = [{"boundary":{"id":fac.id,"boundary_type_id":0}}]
            resp_dict = i
            del resp_dict['LocationID']
            obj = JsonAnswer.objects.create(user=usr,survey_id=survey_id, cluster=cluster_info, response=resp_dict, active=1, interface=2)
        else:
            print i.get("LocationID")

def import_facility_survey_data(file_path,survey_id):
    csv_reader = csv.DictReader(open(file_path,"r"))
    for i in csv_reader:
        if Facility.objects.filter(cry_admin_id=i.get("FacilityCode")).count() == 1:
            fac = Facility.objects.get(cry_admin_id=i.get("FacilityCode"))
            cluster_info = [{"facility":{"id":fac.id,"facility_type_id":fac.facility_type_id}}]
            resp_dict = i
            del resp_dict['FacilityCode']
            obj = JsonAnswer.objects.create(user=usr,survey_id=survey_id, cluster=cluster_info, response=resp_dict, active=1, interface=2)
        else:
            print i.get("FacilityCode")


def import_beneficiary_survey_data(file_path,survey_id):
    csv_reader = csv.DictReader(open(file_path,"r"))
    for i in csv_reader:
        if Beneficiary.objects.filter(cry_admin_id=i.get("BeneficCode")).count() == 1:
            fac = Beneficiary.objects.get(cry_admin_id=i.get("BeneficCode"))
            cluster_info = [{"beneficiary":{"id":fac.id,"beneficiary_type_id":fac.beneficiary_type_id}}]
            resp_dict = i
            del resp_dict['BeneficCode']
            obj = JsonAnswer.objects.create(user=usr,survey_id=survey_id, cluster=cluster_info, response=resp_dict, active=1, interface=2)
        else:
            print i.get("BeneficCode")
