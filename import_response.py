from django.contrib.auth.models import User
import csv
from survey.models import *
from beneficiary.models import *
from facilities.models import *
from datetime import datetime

tod = datetime.today()
#usr = User.objects.get(id=1)
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
    missed_data = []
    for i in csv_reader:
        if Beneficiary.objects.filter(cry_admin_id=i.get("BeneficCode")).count() == 1:
            fac = Beneficiary.objects.get(cry_admin_id=i.get("BeneficCode"))
            cluster_info = [{"beneficiary":{"id":fac.id,"beneficiary_type_id":fac.beneficiary_type_id}}]
            resp_dict = i
            del resp_dict['BeneficCode']
            usr = User.objects.get(id=1)
            obj = JsonAnswer.objects.create(user=usr,survey_id=survey_id, cluster=cluster_info, response=resp_dict, active=1, interface=2)
        else:
            missed_data.append({"ben":i.get("BeneficCode"),"response":i})
            print i.get("BeneficCode")
    print missed_data,JsonAnswer.objects.filter(survey_id=survey_id,active=1).count()


def ques_impo():
    files = raw_input("Enter your file path : ")
    #import ipdb; ipdb.set_trace()
    with open(files,'rb') as fil:
        reader = csv.reader(fil)
        keys = reader.next()
        missed_ids = []
        for row in reader:
            data = dict(zip(keys, row))
            #blk = eval(data.get('Code'))
            if Question.objects.filter(id=data.get('ID') , active = 2).exists():
                q = Question.objects.get(id=data.get('ID'))
                print q
#                if blk.keys():
#                    for k,v in blk.items():
#                        try:
#                            q.language_code[k]=str(q.text) + " - " + v
#                            q.save()
#                            print str(q.id) + "-"+ "imported"
#                        except Exception as e:
#                            msg = str(e.message)
#                            print (msg)
#                            missed_ids.append(q.id)
#        print (missed_ids)
                try:
                    language_gujrati = data.get('Odiya')
                    q.language_code['7'] = language_gujrati
                    q.save()
                except Exception as e:
                            msg = str(e.message)
                            print (msg)
                            missed_ids.append(q.id)
        print (missed_ids)
#                q.language_code = eval(dict(blk))
#                q.save()


def choice_impo():
    files = raw_input("Enter your file path : ")
    with open(files,'rb') as fil:
        reader = csv.reader(fil)
        keys = reader.next()
        missed_ids = []
        for row in reader:
            data = dict(zip(keys, row))
            #blk = eval(data.get('Code'))
            if Choice.objects.filter(id=data.get('ID') ,active = 2).exists():
                q = Choice.objects.get(id=data.get('ID'))
                print q
#                if blk.keys():
#                    for k,v in blk.items():
#                        try:
#                            q.language_code[k]=str(q.text) + " - " + v
#                            q.save()
#                            print str(q.id) + "-"+ "imported"
#                        except Exception as e:
#                            msg = str(e.message)
#                            print (msg)
#                            missed_ids.append(q.id)
#        print (missed_ids)
                try:
                    language_gujarati = data.get('Odiya')
                    q.language_code['7'] = language_gujarati
                    q.save()
                except Exception as e:
                            msg = str(e.message)
                            print (msg)
                            missed_ids.append(q.id)
        print (missed_ids)

from django.contrib.auth.models import User
from uuid import uuid4
from userroles.models import *
from partner.models import *
## User imported in cry server for testing purpose only.
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
            if Partner.obects.filter(partner_id=part).exists():
                partid = Partner.obects.filter(partner_id=part).latest('id')
                userobj = User.objects.create_user(username=username,first_name=fname, email=mail)
                userobj.set_password('cry@2018')
                userobj.is_active=True
                userobj.save()
                activation = ResetActivation.objects.create(key=uuid4().hex, user=userobj)
                orguni = OrganizationUnit.objects.get(id=1)
                rotype = RoleTypes.objects.get(id=1)
                userrolesobj = UserRoles.objects.create(user=userobj, USER_TYPE_CHOCES=2, title=0, organization_unit=orguni)
                userrolesobj.partner = partid
                userrolesobj.role_type.add(rotype)
                userrolesobj.save()
                print "Succuessfully created %d" %(userrolesobj.id)
            else:
                print "Not existed" (part,username)


#smart_str("".join(b.jsondata.get('alias_name')))
from django.utils.encoding import smart_str
from django.contrib.contenttypes.models import ContentType
#export
def benefic_export():
    value = raw_input("enter the Benefic-type:")
    with open('child_reports.csv','wb') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(['name', 'cry_admin_id', 'partner_id','household_id','mother_id', 'age', 'address1', 'address2',\
        'pincode', 'Hamlet_ID', 'phoneNumber', 'gender','DOB'])
        for b in Beneficiary.objects.filter(beneficiary_type_id=int(value)).order_by('id'):
            ct = ContentType.objects.get_for_model(Beneficiary)
            if filter(None,b.jsondata.get('mother_uuid')):
                mother = Beneficiary.objects.get(beneficiary_type_id=3,uuid=str(''.join(b.jsondata.get('mother_uuid')))).cry_admin_id
            else:
                mother = 'None'
            spamwriter.writerow([smart_str(b.name),smart_str(b.cry_admin_id),smart_str(b.partner.partner_id),\
            smart_str(Beneficiary.objects.get(beneficiary_type_id=2,id=b.jsondata.get('parent_id')).cry_admin_id),\
            smart_str(mother),\
            smart_str("".join(b.jsondata.get('age'))),smart_str("".join(b.jsondata.get('address')[0].get('address_0').get('address_1'))),\
            smart_str("".join(b.jsondata.get('address')[0].get('address_0').get('address_2'))),\
            smart_str("".join(b.jsondata.get('address')[0].get('address_0').get('pincode'))),\
            smart_str(Address.objects.filter(content_type=ct,object_id=b.id).latest('id').boundary.cry_admin_id),\
            smart_str(re.sub('[^A-Za-z0-9]+', '', b.jsondata.get('contact_no'))),\
            smart_str("".join(b.jsondata.get('gender'))),\
            smart_str("".join(b.jsondata.get('date_of_birth')))])



#Child Annual Information 37 2,91,607
#Child Education 50 1,29,081
#House Hold Information 55 1,54,551
#Labour and Migration 48 80,029
#School Education Retention 51 1,11,648
#Village Information 54 1,693


import re
from survey.models import JsonAnswer

#Export Jsondata
def house_data():
    with open('Labour_and_Migration.csv','wb') as csvfile:
        spamwriter = csv.writer(csvfile)
        qids = ["Cry Admin Id","Beneficiary Name","Partner Id","Partner Name",]
        s = Survey.objects.get(id=48)
        qids.extend([str(t.text) for t in s.questions()])
        spamwriter.writerow(qids)
        count = 0
        print JsonAnswer.objects.filter(survey=s,active=1).count()
        for i in JsonAnswer.objects.filter(survey=s,active=1).order_by('-id')[10000:20000]:
            ansrow = []
            ansrow.append(str(Beneficiary.objects.get(id=i.cluster[0].get("beneficiary").get('id')).cry_admin_id))
            ansrow.append(str(Beneficiary.objects.get(id=i.cluster[0].get("beneficiary").get('id')).id))
            ansrow.append(Beneficiary.objects.get(id=i.cluster[0].get("beneficiary").get('id')).partner_id)
            ansrow.append(str(Beneficiary.objects.get(id=i.cluster[0].get("beneficiary").get('id')).partner.name))
            for j,k in sorted(i.response.items()):
                if j.isdigit():
                    q = Question.objects.get(id=j)
                    if q.qtype in ['R','S']:
                        if Choice.objects.filter(id=k).exists():
                            ans = Choice.objects.get(id=k).text
                        else:
                            ans ="N/A"
                    elif q.qtype in ["D"]:
                        ans = str(k)
                    else:
#                        ans = k.encode('ascii', 'ignore')
#                        ans = re.sub('[^A-Za-z0-9 ]+', '', k)
#                        ans=re.sub(r'[^\x00-\x7F]+','',k)
#                        ans = filter(str.isalnum, str(k))
                        ans = str(k.encode('ascii', 'ignore'))
                        
                    ansrow.append(ans)
            count +=1
            print i.cluster,count
            spamwriter.writerow(ansrow)
        print "created"




#Export Qustion
def export_questionlist():
    with open('Question_list'+str(tod.date())+'.csv','wb') as csvfile:
        spamwriter = csv.writer(csvfile)
        qids = ["Form Id","Form Name","Question Id","Question Name","Question Type","Question Acitve Status","Telugu","Hindi","Tamil","Kannada","Bangla","Odiya","Assamese - Ahomia"]
        spamwriter.writerow(qids)
        count = 0
        for i in Question.objects.all().order_by('id'):
            spamwriter.writerow([
                smart_str(i.block.survey.id),
                smart_str(i.block.survey.name),
                smart_str(i.id),
                smart_str(i.text),
                smart_str(i.qtype),
                smart_str(i.active),
                smart_str(i.language_code.get('2','')),
                smart_str(i.language_code.get('3','')),
                smart_str(i.language_code.get('4','')),
                smart_str(i.language_code.get('5','')),
                smart_str(i.language_code.get('6','')),
                smart_str(i.language_code.get('7','')),
                smart_str(i.language_code.get('8','')),
                smart_str(i.language_code.get('9','')),
                smart_str(i.language_code.get('10',''))
                ])
        print "Question Exported"


def export_choicelist():
    with open('Choice_list'+str(tod.date())+'.csv','wb') as csvfile:
        spamwriter = csv.writer(csvfile)
        qids = ["Form Id","Form Name","Question Id","Question Name","Question Type","Question Active Status","Choice Id","Choice Text","Choice Active Status","Telugu","Hindi","Tamil","Kannada","Bangla","Odiya","Assamese - Ahomia"]
        spamwriter.writerow(qids)
        count = 0
        for i in Choice.objects.all().order_by('id'):
            spamwriter.writerow([
                smart_str(i.question.block.survey.id),
                smart_str(i.question.block.survey.name),
                smart_str(i.question.id),
                smart_str(i.question.text),
                smart_str(i.question.qtype),
                smart_str(i.question.active),
                smart_str(i.id),
                smart_str(i.text),
                smart_str(i.active),
                smart_str(i.language_code.get('2','')),
                smart_str(i.language_code.get('3','')),
                smart_str(i.language_code.get('4','')),
                smart_str(i.language_code.get('5','')),
                smart_str(i.language_code.get('6','')),
                smart_str(i.language_code.get('7','')),
                smart_str(i.language_code.get('8','')),
                smart_str(i.language_code.get('9','')),
                smart_str(i.language_code.get('10',''))
                ])
        print "Choice Exported"

