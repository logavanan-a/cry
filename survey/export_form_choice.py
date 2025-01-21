import csv
from .models import Survey,Question,Choice
from django.contrib.auth.models import User
from userroles.models import UserRoles
from partner.models import Partner
from masterdata.models import MasterLookUp
from service.models import *
import os
import zipfile
from django.core.mail.message import EmailMessage


def export_form_choices(form_id=None):
    try:
        survey = Survey.objects.get(id=form_id)
        form_questions = Question.objects.filter(active=2,block__survey=survey).order_by('code')
        choice_questions = form_questions.filter(qtype__in=['R','S'])
        form_choices = Choice.objects.filter(active=2,question__in=choice_questions)
        form_file = file("/forms_and_choices/"+str(survey)+"_"+str(survey.id)+"_questions.csv","w")
        question_writer = csv.writer(form_file)
        question_writer.writerow([])
        question_id = [" "," "]
        question_id.extend(form_questions.values_list('id',flat=True))
        question_writer.writerow(question_id)
        question_text = [" Partner "," Beneficiary/Facilty "]
        question_text.extend(form_questions.values_list('text',flat=True))
        question_writer.writerow(question_text)
        question_type = [" "," "]
        question_type.extend([question.get_qtype_display() for question in form_questions ])
        question_writer.writerow(question_type)
        form_file.close()
        choice_form = file("/forms_and_choices/"+str(survey)+"_"+str(survey.id)+"_choices.csv","w")
        choice_writer = csv.writer(choice_form)
        choice_writer.writerow([])
        choice_writer.writerow(["Question","Question Id","Question Type","choice Id","Choice"])
        for question in choice_questions:
            for choice in form_choices.filter(question=question):
                choice_writer.writerow([str(choice.question.text),str(choice.question.id),str(choice.question.get_qtype_display()),str(choice.id),str(choice.text)])
            choice_writer.writerow([])
        return str(survey)+" Form questions and choices exported "
    except Exception as e:
        return e.message

def export_form_single(form_id=None):
    survey_objects = Survey.objects.filter(active=2)

    form_file = file("forms_and_choices/survey_single.csv", "w")

    question_writer = csv.writer(form_file)
    for survey in survey_objects:
        form_questions = Question.objects.filter(active=2,block__survey=survey).order_by('code')
        question_writer.writerow([str(survey)])

        question_writer.writerow(["Form Id","Form Name","Question Id","Question Text","Choice Id","Choice Text"])
        for i in form_questions:
            question_info = [str(survey.id),str(survey),str(i.id),str(i.text)]
            if i.qtype in ['S','R']:
                for choice in i.choice_list():
                    question_info.append(str(choice.get('id')))
                    question_info.append(str(choice.get('choice')))
                    question_writer.writerow(question_info)
                    question_info = [str(survey.id),str(survey),str(i.id),str(i.text)]
            else:
                question_info.append("")
                question_info.append("")
                question_writer.writerow(question_info)
        question_writer.writerow([""])

def partner_details_export():
    partner_writer = csv.writer(open('partner_details','w'))
    values_list = ['id','name','partner_id','region','state']
    partner_writer.writerow(values_list)
    for p in Partner.objects.all():
        partner_writer.writerow([str(p.id),str(p.name),str(p.partner_id),str(p.region),str(state)])


def import_regional_language(sid,typ,lid,path):
    question = Question.objects.filter(active=2,block__survey__id=sid)
    file = open(path,'r')
    reader = csv.reader(file)
    for i in reader:
        if i[0]:
            try:
                one_question = question.get(id=i[0])
                one_question.language_code[str(lid)]=i[2]
                one_question.save()
            except Exception as e:
                pass
    print ("imported ")

def import_partner_users(partner_short_name,partner_id,role_type,role_id,cnt):
    file = open('feb_user_logins.csv','a')
    writer = csv.writer(file)
    for i in range(1,cnt):
        try:
            #create user object
            username = str(partner_short_name).lower()+"."+str(role_type).lower()+str(i)
            user = User.objects.create_user(username,username+"@gmail.com","cry@2018")
            user.first_name = partner_short_name+" "+role_type+" "+str(i)
            user.save()
            #create user role
            user_role = UserRoles.objects.create(title=0,user_id=user.id,partner_id=partner_id,
                        organization_unit__id=1,user_type=2,mobile_number="9876543210")
            user_role.role_type.add(int(role_id))
            user_role.save()
            partner = Partner.objects.get(id=partner_id)
            writer.writerow([str(partner),str(user.username),"cry@2018",str(role_type)])
        except Exception as e:
            pass
    writer.writerow([])
    file.close()

def export_location_level(level,level_type):
    level_file = open('level_'+str(level)+'_'+str(level_type)+'.csv','w')
    level_writer = csv.writer(level_file)
    level_objects = Boundary.objects.filter(boundary_level=level,object_id=level_type)
    level_writer.writerow(['id','Name',' ','Parent Id','Parent Name'])
    for lo in level_objects:
        level_writer.writerow([str(lo.id),str(lo),' ',str(lo.parent.id),str(lo.parent)])
    level_file.close()


def print_child(child_list,count,out_list):
    count = count
    out_list = []
    for i in child_list:
        out_list.append([" " for z in range(0,count)]+[i['id'],i['name']])
        if i['child']:
            print_child(i['child'],count+1)
    return out_list

def export_master_lookup():
    ml = MasterLookUp.objects.get(slug='facility-type')
    ml_file = open('facility_export.csv','w')
    ml_writer = csv.writer(ml_file)
    for x in ml.get_child():
        ml_writer.writerow([x['id'],x['name']])
        if x['child']:
            for z in print_child(x['child'],1,[]):
                ml_writer.writerow(z)

def export_services():
    services = Service.objects.filter(active=2).values_list('id','name')
    s_writer = csv.writer(open('services_export.csv','w'))
    for i in services:
        s_writer.writerow(list(i))


def send_form_single_attachment():
    try:
        os.remove('forms_single.zip')
    except:
        pass
    survey = Survey.objects.filter(active=2)
    with zipfile.ZipFile('forms_single.zip','w') as forms_zip:
        for i in survey:
            forms_zip.write("forms_and_choices/"+str(i)+"_"+str(i.id)+".csv")
    email = EmailMessage()
    email.subject = "Forms and choices zip file"
    email.body = "PFA for forms and choices in single file inside zip file"
    email.from_email = "ahanasupport@mahiti.org"
    email.to = [ "mallik.sai@mahiti.org", ]
    email.attach_file('forms_single.zip')
    email.send()

