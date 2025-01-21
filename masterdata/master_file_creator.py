from beneficiary.models import *
from facilities.models import *
from partner.models import *
from masterdata.models import MasterLookUp,Boundary
from survey.models import Survey,Question,JsonAnswer
from userroles.models import UserRoles,UserPartnerMapping
import thread
from datetime import datetime

class MasterDataFile():

    #run this method to create the master data file
    @staticmethod
    def create_dump_files():
        for partner in Partner.objects.filter(active=2):
            MasterDataFile.create_partner_dump_file(partner)

    @staticmethod
    def create_partner_dump_file(partner):
        beneficiary = MasterDataFile.get_partner_beneficiary(partner)
        facility = MasterDataFile.get_partner_facility(partner)
        responses = MasterDataFile.get_partner_responses(partner)
        master_file = open("static/partner_masterdata/"+str(partner.id)+"_masterdata.txt",'w+')
        master_file.write(str({"status":2,"responsesData":responses,"beneficiaries":beneficiary,
                               "facilities":facility}))
        master_file.close()

    @staticmethod
    def get_partner_beneficiary(partner):
        beneficiary_dict = []
        for beneficiary_type in BeneficiaryType.objects.filter(active=2):#1
            data_query = ['code', 'parent', 'parent_id', 'tempid', 'alias_name', 'beneficiary_type_id',
                          'beneficiary_type', 'active', 'partner', 'partner_id', 'id', 'uuid', 'name','created','modified','mother_uuid','data_of_birth','dob_option','gender','btype','age','cry_admin_id','contact_no']
            beneficiary = Beneficiary.objects.filter(partner=partner,beneficiary_type=beneficiary_type).order_by("created").custom_values(data_query)
            for index,one_record in enumerate(beneficiary):#2
                [beneficiary[index].update({dq:""}) for dq in data_query if not dq in beneficiary[index].keys()]
                beneficiary[index].update({"address":MasterDataFile.get_beneficiary_address_list(beneficiary[index].get('id'))})
                beneficiary_parent = None
                if beneficiary[index].get('parent_id'):
                    beneficiary_parent = Beneficiary.objects.get_or_none(id=beneficiary[index].get('parent_id'))
                beneficiary[index].update({"parent_uuid":beneficiary_parent.id if beneficiary_parent else ""})
                one_record = MasterDataFile.list_to_one_element(one_record)
                beneficiary_dict.append(one_record)
        return beneficiary_dict

    @staticmethod
    def get_beneficiary_address_list(bid):
        address_list = []
        for a in Address.objects.filter(object_id=bid).order_by('office'):
            address_dict = {}
            address_dict['least_location_name'] = str(a.boundary)
            address_dict['boundary_id'] = int(a.boundary.id) if a.boundary else ""
            address_dict['location_level'] = int(a.boundary.boundary_level) if a.boundary else ""
            address_dict['pincode'] = str(a.pincode)
            address_dict['address_id'] = int(a.id)
            address_dict['address1'] = str(a.address1.encode('ascii', 'ignore'))
            address_dict['address2'] = str(a.address2)
            address_dict['proof_id'] = int(a.proof_id) if a.proof else ""
            address_dict['primary'] = int(a.office) if a.office else ""
            address_list.append(address_dict)
        return address_list

    @staticmethod
    def get_partner_facility(partner):
        data_query = ['beneficiary_id','facility_subtype_id','address1','address2','btype','pincode',
'modified','facility_subtype','active','partner','tempid','partner_id','id','name','uuid','created',
'facility_type','parent_id','facility_type_id','boundary_id']
        partner_facility = []
        for ft in MasterLookUp.objects.filter(parent__slug='facility-type').order_by('cry_admin_id'):#1
            facilities = Facility.objects.filter(facility_type=ft,partner=partner).custom_values(data_query)
            for facility in facilities:#2
                fac = Facility.objects.get(id=facility.get('id'))
                facility.update({'thematic_area':fac.thematic_area.ids() if fac.thematic_area else []})#5
                facility.update({'services':fac.services.ids() if fac.services else []})#5
                try:
                    facility.update({'boundary_level':Boundary.objects.get(id=fac.jsondata.get('boundary_id')[0]).boundary_level})
                    facility.update({'boundary_id':int(fac.jsondata.get('boundary_id')[0])})
                except:
                    facility.update({'boundary_level':7})
                    facility.update({'boundary_id':4485})
                facility = MasterDataFile.list_to_one_element(facility)
                partner_facility.append(facility)
        return partner_facility

    @staticmethod
    def list_to_one_element(one_object):
        exclude_list = ['thematic_area','services','address']
        switch_active = {'Active':2,'Inactive':0}
        one_object['active']=switch_active.get(one_object['active'])
        int_converter = ['beneficiary_type_id','id','partner_id','facility_type_id','facility_subtype_id','parent_id']
        for i in one_object.keys():#1
            if i not in exclude_list:#2
                if isinstance(one_object[i],list):#4
                    one_object[i]=str(one_object[i][0])
                if i in int_converter:#4
                    one_object[i]=int(one_object[i]) if one_object[i] else 0
        return one_object


    @staticmethod
    def get_partner_responses(partner):
        user_list = UserRoles.objects.filter(partner=partner).values_list('user', flat=True)
        res_list = []
        flag = ""
        ben_uuid = ""
        fac_uuid = ""
        cluster_id = ""
        cluster_level = ""
        responses = JsonAnswer.objects.filter(user__in=user_list,active=2)
        for res in responses:
            if res.cluster:
                try:
                    ben_cluster = res.cluster[0].get('beneficiary')
                    ben_id = int(ben_cluster.get('id'))
                    beneficiary = Beneficiary.objects.get_or_none(id=ben_id)
                    if beneficiary:
                        ben_uuid = str(beneficiary.uuid)
                except:
                    ben_uuid = ""
                try:
                    fac_cluster = res.cluster[0].get('facility')
                    faci_id = int(fac_cluster.get('id'))
                    facility = Facility.objects.get_or_none(id=faci_id)
                    if facility:
                        fac_uuid = str(facility.uuid)
                except:
                    fac_uuid = ""

            if res.survey.data_entry_level.name == "Location":
                try:
                    boundary = Boundary.objects.get(id=res.cluster[0].get('boundary').get('id'))
                    cluster_id = str(boundary.id)
                    cluster_level = str(boundary.boundary_level)
                except:
                    cluster_id = ""
                    cluster_level = ""
            res_dump = {}
            for i in res.response.keys():
                try:
                    res_dump[str(i)] = str(res.response.get(i))
                except:
                    res_dump[str(i)] = res.response.get(i).encode('utf-8')
            res_list.append({"response_id": res.id,
                             "survey_uuid": res.creation_key if res.creation_key else "",
                             "bene_uuid": ben_uuid,
                             "faci_uuid": fac_uuid,
                             "cluster_id": cluster_id,
                             "cluster_level": cluster_level,
                             "survey_id": int(res.survey.id),
                             "collected_date": datetime.strftime(res.created, '%Y-%m-%d'),
                             "active": res.active,
                             "server_date_time": datetime.strftime(res.submission_date, '%Y-%m-%d %H:%M:%S.%f'),
                             "response_dump": str(res_dump)})
        return res_list
