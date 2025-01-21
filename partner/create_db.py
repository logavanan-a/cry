from django.db import connection
from django.template.defaultfilters import slugify
import shutil
import os
from shutil import make_archive
from datetime import datetime
import sqlite3
from partner.models import *
from ccd.settings import BASE_DIR, STATIC_URL, HOST_URL
import requests
skeleton = STATIC_URL+"partner_datadase/SurveyLevels.sqlite"
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from masterdata.models import Boundary

@csrf_exempt
def export_db(userid):
    #part_name = slugify(name)
    ptid = UserRoles.objects.get(user_id=int(userid)).partner.id
    os.mkdir(BASE_DIR+"/static/partner_datadase/"+str(ptid))
    
    sourceone = BASE_DIR + "/static/SurveyLevels.sqlite"
    destione = BASE_DIR + "/static/partner_datadase/"+str(ptid)+"/SurveyLevels.sqlite"
    sourcetwo = BASE_DIR + "/static/Convene.sqlite"
    destitwo = BASE_DIR + "/static/partner_datadase/"+str(ptid)+"/Convene.sqlite"
    shutil.copy(sourceone, destione)
    shutil.copy(sourcetwo, destitwo)
    
    
#    path = BASE_DIR + "/static/partner_datadase/SurveyLevels.sqlite"
    path = destione
    
    con = sqlite3.connect(path)
    con.text_factory = str
    cur = con.cursor()
#    cursor = conconnection.cursor()
    ##### SQL QUERIES FOR CHOICE STARTS HERE #####

    ## surveys
    data = {'uId':int(userid)}
    values = requests.post(HOST_URL+'api/survey-list/',data=data)
    surveyvalue = []
    priid = 1
    for i in eval(values.text).get('surveyDetails'):
        surveyvalue.append((priid, i.get('pcode'), i.get('b_config'), '0', i.get('reasonDisagree'), i.get('pLimit'), i.get('survey_name'), i.get('piriodicity'), i.get('survey_id'), i.get('pFeature'), i.get('vn'), i.get('order_levels'), i.get('labels'), i.get('survey_order'), 'null', i.get('q_config'), i.get('beneficiary_ids'), i.get('beneficiary_type'), i.get('summary_qid'), i.get('facility_ids'), i.get('facility_type'), i.get('rule_engine'), i.get('piriodicity_flag')))
        priid += 1
    #add drop query
#    cur.execute('TRUNCATE TABLE Surveys')
    cur.execute('delete from Surveys')
    cur.executemany("INSERT INTO Surveys (id, pCode, bConfig, qCode, reasonDisagree, pLimit, surveyName, Periodicity, surveyId, pFuture, vn, order_levels, labels, survey_display, block_display, qConfig, beneficiary_ids, beneficiary_type, summaryQid, facility_ids, facility_type, rule_engine, PeriodicityFlag) VALUES (?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", surveyvalue)

    ##Beneficiary
    data2 = {'uId':int(userid),'partner_id':ptid,'dumpdb':'True'}
    benevalues = requests.post(HOST_URL+'beneficiary/datewiselisting/',data=data2)
    benvalue = []
    for i in eval(benevalues.text).get('data'):
        level7=level6=level5=level4=level3=level2=level1='null'
        level = Boundary.objects.get_or_none(id=i.get('address')[0].get('bid'))
        if level:
            print level
            try:
                msg = 'msg'
                level7 = level.id
                level6=level.parent.id
                level5=level.parent.parent.id
                level4=level.parent.parent.parent.id
                level3=level.parent.parent.parent.parent.id
                level2=level.parent.parent.parent.parent.parent.id
                level1=level.parent.parent.parent.parent.parent.parent.id
            except Exception as e:
                msg = str(e.message)
                level7=level6=level5=level4=level3=level2=level1='null'
        print level1,level2,level3,level4,level5,level6,msg
        benvalue.append((
        i.get('uuid'),i.get('id'),i.get('modified'),i.get('beneficiary_type'),i.get('name'),i.get('active'),i.get('modified'),\
        i.get('beneficiary_type_id'),i.get('parent'),i.get('partner_id'),i.get('parent_id'),str(i.get('address')),\
        i.get('partner'), map(int,i.get('contact_no')),i.get('age'),'2', i.get('gender'),'',i.get('address')[0].get('bid'),\
        i.get('address')[0].get('llnm'), i.get('puuid'),i.get('date_of_birth'), 'null','null',\
        i.get('dob_option'), i.get('alias_name'),i.get('created'), level1,level2,level3,\
        level4,level5, level6,level7,i.get('muuid')
        ))
    #add drop query
    cur.execute('delete from Beneficiary')
    cur.executemany("INSERT INTO Beneficiary (uuid, server_primary, server_datetime, beneficiary_type, beneficiary_name, active, last_modified, beneficiary_type_id, parent, partner_id, parent_id, address, partner_name, contact_no, age, sync_status, gender, status, least_location_id, least_location_name, parent_uuid, dob, valid_address_proof_id, valid_address_proof_name, dob_option, alias_name, createdDate, level1, level2, level3, level4, level5, level6, level7, motherId) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", benvalue)
    
    ##Facility
    data3 = {'partner_id':ptid}
    facivalues = requests.post(HOST_URL+'facilities/facilitydatewiselisting/',data=data3)
    facivalue = []
    null = 'null'
    for i in eval(facivalues.text).get('data'):
        facivalue.append((
        str(i.get('uuid')),str(i.get('name')),str(i.get('facility_type')),str(i.get('facility_type_id')),str(i.get('facility_subtype')),\
        i.get('facility_subtype_id'),str(i.get('beneficiary_id')),str(i.get('btype')),str(i.get('thematic_area_str')),str(i.get('thematic_area')),\
        i.get('modified'),i.get('modified'),i.get('active'),i.get('boundary_name'),i.get('boundary_id'),\
        i.get('partner'),i.get('address1'),i.get('pincode'),i.get('address2'),i.get('boundary_level'),\
        '2',str(i.get('services')),'null','null',i.get('id'),\
        str(i.get('created')),'null','null','null','null','null','null','null'
        ))
    #add drop query
    cur.execute('delete from Facility')
    cur.executemany("INSERT INTO Facility (uuid, facility_name, facility_type, facility_type_id, facility_subtype, facility_subtype_id, beneficiary_id,btype, thematic_area, thematic_area_id, modified, server_datetime, active, boundary_name, boundary_id, partner_name, address1, pincode, address2, location_level, sync_status, services, status, location_type, server_primary, createdDate, level1, level2, level3, level4, level5, level6, level7) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", facivalue)
    
    ##### SQL QUERIES FOR CHOICE ENDS HERE #####
    con.commit()
    con.close()

    file_name =  BASE_DIR+"/static/partner_datadase/"+str(ptid)
    make_archive(file_name,'zip',root_dir=None,base_dir=BASE_DIR+"/static/partner_datadase/"+str(ptid))
    print ("created")

