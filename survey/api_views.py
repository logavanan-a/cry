from uuid import uuid4
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
from survey.models import *
from survey.custom_decorators import *
from django.db import transaction
from masterdata.models import *
from django.core.mail import send_mail
from beneficiary.models import BeneficiaryType
import os,sys,json
import pytz
from ccd.settings import HOST_URL
from django.contrib.auth.models import User
from views.survey_views import get_piriodicity_value

def get_time_difference(tabtime):
    # Returns the time difference the tab time and the current server time
    message, response_type = '', 2
    if tabtime:
        tabtime_obj = datetime.strptime(tabtime, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        diff = current_time - tabtime_obj
        diff_time = divmod(diff.days * 86400 + diff.seconds, 60)
        message = "The server time and tab time is more than "+str(diff_time[0])+" minutes "+str(diff_time[1])+" seconds"
        if diff_time[0] < 10:
            response_type = 1
    else:
        message = "Tab time not sent"
    return {'message':message,'response_type':response_type}


def get_alaram_frequency(userid=''):
    frequency = 15
    if userid and UserTimeIntervals.objects.filter(user__id=int(userid)).exists():
        frequency = UserTimeIntervals.objects.get(user__id=int(userid)).frequency
    return frequency


@csrf_exempt
def alarm_frequency(request):
    user_id = request.POST.get("uId")
    alarm = get_alaram_frequency(user_id)
    response ={"alaramFrequency":alarm}
    return JsonResponse(response)


@csrf_exempt
@validate_user
def applogin(request,**kwargs):
    # User model method get_latest_survey_versions is a method which return
    # survey version with piriodicity (common method)
    response, message, error_msg,response_type,userrole_obj = {}, '', '',None,None
    if request.method == 'POST' and kwargs.get('status',False):
        tabtime = request.POST.get('tabtime')
        user = kwargs.get('user')
        time_data = get_time_difference(tabtime)
        message = time_data.get('message','')
        response_type = time_data.get('response_type')
        appdetails_obj = AppLoginDetails(user=request.user,
                                        surveyversion=request.POST.get('surveyversion'),
                                        lang_code=request.POST.get('lang_code'),
                                        tabtime=request.POST.get('tabtime') \
                                            if request.POST.get('tabtime') else None,
                                        sdc=request.POST.get('sdc') \
                                                if request.POST.get('sdc') else 0,
                                        itype=request.POST.get('ltype'),
                                        version_number=request.POST.get('version_number'))
        appdetails_obj.save()
        userrole_obj = UserRoles.objects.get(user=user)
        role_names = [i.name.lower() for i in userrole_obj.role_type.all()]
        app_roles = ['community organizer']
        version_update = VersionUpdate.objects.filter().latest('id')
        updateapk ={"forceUpdate": str(version_update.force_update),
                    "appVersion": int(version_update.version_code),
                    "updateMessage": "New update available, download from playstore",
                    "link": HOST_URL+"/static/android/releases/cry.apk"}
        if bool(set(role_names)&set(app_roles)) :
            response.update({
                'message' : "Logged in successfully",
                'uId' : user.id,
                'partner_id':get_user_partner(userrole_obj),
            })
        elif [i.name.lower() for i in userrole_obj.role_type.all()] in ['data center cordinator','admin']:
            response.update({
                    'message' : "District Coordinator or admin Logged in",
                    'uId' : user.id,
                    'partner_id':get_user_partner(userrole_obj),
                })
        response.update({'updateAPK':updateapk,'activeStatus':userrole_obj.active,'forceLogout':0,})
    else:
        response_type = 0
        error_msg = kwargs.get('error_msg','')
        response.update({'message':error_msg})

    response.update({'responseType' : response_type, 'updates':24,'master_data_file_url':HOST_URL+'/static/partner_masterdata/'+str(get_user_partner(userrole_obj))+'_masterdata.txt'})

    return JsonResponse(response)

def get_user_partner(userrole_obj):
    try:
        return int(userrole_obj.partner.id)
    except:
        return 0


@csrf_exempt
def surveylist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        if not user_id.isdigit() or user_id == '':
            res = {"status":0, \
               "message":"Enter a valid user id",}
            return JsonResponse(res)
        status, message = 2, 'Survey list sent successfully'

        proj_levellist = list(ProjectLevels.objects.filter().values_list('name',flat=True).order_by('name'))
        proj_levels = ",".join(proj_levellist)
        res = { 'status':status,
                "message": "survey list sent successfully",
                "application_levels": str(proj_levels),
                'surveyDetails':get_latest_survey_versions(user_id)
        }
        users = DetailedUserSurveyMap.objects.filter().values_list('user__user__id',flat=True)
        if not int(user_id) in users:
            res = {"status":0, \
               "message":"User does not exists","surveyDetails":[],"application_levels":""}
        return JsonResponse(res)


@csrf_exempt
@validate_post_method
def cluster_list(request):
   if request.method == 'POST':
      response = {}
      user_id = request.POST.get("u_id")
      sur_id = request.POST.get("survey_id")

      user = User.objects.filter(id=int(user_id))
      survey = Survey.objects.filter(id=int(sur_id))
      if user and survey:
           usersurvey_list = UserSurveyMap.objects.active_items()\
                             .filter(user__user__id=int(user_id),survey__id=int(sur_id))
           for i in usersurvey_list:
               res = i.get_cluster()#function is in monkey_patching.py
               response = {
                    "clusters" : res,
                }
           response.setdefault('status',1)
           response.setdefault("message","success")
           response.setdefault("clusterVersion",1)
      else:
           response.setdefault('status',0)
           response.setdefault("message","failure")
      return JsonResponse(response)


@csrf_exempt
@validate_post_method
@validate_user_version
@write_to_log
def add_survey_answers(request, **kwargs):
    # Implemented bulk create
    # Before start of bulk create
    # Start time st = datetime.now()
    # End time et = datetime.now()
    # Difference diff = et - st
    # Print the time print st,"=====>",et,"========>",diff

    response, status, error_msg, response_type,res_id = {}, False, '', 0,0
    message, latestversion = '', 1.0
    version = float(request.POST.get('av',0.0))
    app_error_msg= ''
    if version < 25.0:
        app_error_msg='Please update your app'
        message = app_error_msg
    if request.method == 'POST' and kwargs.get('status',False) and not app_error_msg:
        try:
            with transaction.atomic():
                app_answer_obj = ""
                answers_list = None
                try:
                    answers_list = eval(str(request.POST.get('answers_array')))
                except:
                    answers_list = eval(request.POST.get('answers_array'))
                cluster_id = request.POST.get('cluster_id')
                cluster_key = request.POST.get('clusterKey')
                beneficiary = request.POST.get('beneficiary_id')
                beneficiary_type_id= request.POST.get('beneficiary_type_id')
                facility_type_id=request.POST.get('facility_type_id')
                facility = request.POST.get('facility_id')
                response_id = request.POST.get('response_id')
                image_info = eval(str(request.POST.get('image_info')))
                image_list = request.FILES
                image_array = match_media_array(image_info, image_list)
                user = User.objects.get(id=int(request.POST.get('uId')))
                survey_ids = request.POST.get('t_id')
                creation_key = request.POST.get('survey_uuid')
                created = pytz.utc.localize(datetime.strptime(request.POST.get('captured_date')+" 01:01:01.1000",'%Y-%m-%d %H:%M:%S.%f'))
                if not response_id:
                    obj = create_app_answer_data(request)
                    app_answer_obj = update_operator_details(request, obj)
                    media_params = {'image_array':image_array, 'app_answer_obj':app_answer_obj, \
                                'cluster_id':cluster_id, 'cluster_key':cluster_key}
                    create_media_answers(user, **media_params)
                ans_params = {'answers_list':answers_list, 'app_answer_obj':app_answer_obj, \
                                'cluster_id':cluster_id, 'beneficiary':beneficiary,
                                'facility':facility,'survey_ids':survey_ids,
                                'beneficiary_type_id':beneficiary_type_id,
                                'facility_type_id':facility_type_id,
                              'response_id':response_id,'created':created,'creation_key':creation_key}
                status,res_id = create_answers(user, **ans_params)
                vns = request.POST.get('vn')
                latestversion = get_version_updates(survey_ids,vns)
                response_type,status = 1, True
                message = "Success"
        except Exception as e:
            error_msg = str(e.message)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            #print(exc_type, fname, exc_tb.tb_lineno)
            message = exc_tb.tb_lineno
    elif not app_error_msg:
        message = error_msg or kwargs.get('error_msg','')
    response = {'status':status,'error_msg':error_msg, \
                'responseType':response_type,'message':message,\
                'latestappversion':"1.0", 'surveyDetails': latestversion,\
                'latestdbversion':"1.0",'app_db_ve':"1.0",\
                "primary_key":int(res_id),\
                "response_id":int(res_id)}
    return JsonResponse(response)


def create_app_answer_data(request):
    # Create App answer object the primary key of this will be tagged
    # to each answer record of one specific survey
    obj = AppAnswerData.objects.create(latitude=request.POST.get('la'),
                                        longitude=request.POST.get('lo'),
                                        version_number=request.POST.get('vn'),
                                        app_version=request.POST.get('av'),
                                        language_id=request.POST.get('l_id'),
                                        imei=request.POST.get('imei'),
                                        survey_id=request.POST.get('t_id'),
                                        mode=request.POST.get('mode'),
                                        part2_charge=request.POST.get('part2_charge'),
                                        f_sy=request.POST.get('f_sy'),
                                        gps_tracker=request.POST.get('gps_tracker'),
                                        survey_status=request.POST.get('survey_status'),
                                        reason=request.POST.get('reason'),
                                        sample_id=request.POST.get('sample_id'),
                                        cluster_id=request.POST.get('cluster_id'),
                                        interface=2,
                                        active=0)
    start_date = request.POST.get('sd')
    end_date = request.POST.get('ed')
    created_on = request.POST.get('created_on')
    sp_s_o = request.POST.get('sp_s_o')
    obj.start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M:%S") if start_date else None
    obj.end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M:%S") if end_date else None
    obj.created_on = datetime.strptime(created_on,"%Y-%m-%d %H:%M:%S") if created_on else None
    obj.sp_s_o = datetime.strptime(sp_s_o,"%Y-%m-%d %H:%M:%S") if sp_s_o else None
    obj.save()
    return obj


def update_operator_details(request, obj):
    operator_details = eval(str(request.POST.get('OperatorDetails')))
    if isinstance(operator_details,dict):
        op_details = dict((k.lower(),v) for k,v in operator_details.iteritems())
        for k,v in op_details.items():
            if hasattr(obj,k):
                setattr(obj,k,v)
        obj.network_type = op_details.get('networktype')
        obj.phone_number = op_details.get('phoneno')
        obj.stoken_sent = op_details.get('stoken')
        obj.save()
    return obj


def match_media_array(image_info=[],image_list=[]):
    # Map Two different list sent as feeds
    # image_info contains question id and time
    # image_list contains question id and image
    # Map two different list of dictionary and make a final dictionary
    # with question id, time, image/video/attachment/audio file
    for i in image_info:
        for k,v in i.items():
            for x,y in image_list.items():
                update_dict(i,x,y,v)
    return image_info


def update_dict(i,x,y,v):
    # Mutable dictionary is updated here
    # The final dictionary is changed
    try:
        if int(v) == int(x):
            i.update({'image':y})
            image_list.pop(x)
    except:
        pass
    return True


def create_answers(user, **ans_params):
    insertion_list, qids_list = [], []
    answers_list = ans_params.get('answers_list')
    app_answer_obj = ans_params.get('app_answer_obj')
    cluster_id = ans_params.get('cluster_id')
    creation_key = ans_params.get('creation_key')
    
    response_id = ans_params.get('response_id')
    ben_uuid = ans_params.get('beneficiary')
    beneficiary_type = int(ans_params.get('beneficiary_type_id'))
    facility_type = int(ans_params.get('facility_type_id'))
    fac_uuid = ans_params.get('facility')
    if str(ben_uuid) != '0':
        beneficiary = Beneficiary.objects.filter(uuid=ben_uuid).latest('created').id
    else:
        beneficiary = 0
    if str(fac_uuid) != '0':
        facility = Facility.objects.get(uuid=fac_uuid).id
    else:
        facility = 0
    survey_ids = ans_params.get('survey_ids')
    #creation_key = str(uuid4())
    survey = Survey.objects.get(id=survey_ids)
    surveyconfig = SurveyDataEntryConfig.objects.get(survey__id=survey_ids)
    periodicity_value = get_piriodicity_value(survey.id)
    if survey.data_entry_level.slug == 'facility' and not surveyconfig.is_profile:
        cluster = [{"facility":{"facility_type_id":facility_type,"id":facility},
                    "beneficiary":{"beneficiary_type_id": beneficiary_type, "id":beneficiary}}]
        cluster.append({'periodicity_value' : periodicity_value})
    else:

        field_resolver = {'beneficiary':'beneficiary_type_id','facility':'facility_type_id'}
        survey_data_level = survey.data_entry_level.slug
        if survey_data_level == 'location':

            cluster = [{"boundary":{"boundary_type_id": 0,"id":int(cluster_id)}}]
            cluster.append({'periodicity_value' : periodicity_value})
        else:
            id_value = facility if survey_data_level == "facility" else beneficiary
            type_value = facility_type if survey_data_level == "facility" else beneficiary_type
            
            cluster = [{survey_data_level:{field_resolver.get(survey_data_level):type_value,'id':id_value}}]
            cluster.append({'periodicity_value' : periodicity_value})
    survey = Survey.objects.get(id=int(survey_ids))
    questions = Question.objects.filter(block__survey=survey,active=2)

    resp_dict = question_answer_dict(questions,answers_list)

    if not response_id:
        #check and insert the changed periodictiy date while saving
        ansobj = JsonAnswer.objects.create(user=user,creation_key=creation_key,\
                                survey=survey,response=resp_dict,cluster=cluster)
	ansobj.app_answer_data = int(app_answer_obj.id)
	ansobj.created = ans_params.get('created')
	ansobj.save()
    else:
        ansobj = JsonAnswer.objects.get(id=int(response_id))
        ansobj.response = resp_dict
        ansobj.save()
    return (True,ansobj.id)

def question_answer_dict(questions,answers_list):
    resp_dict ={}
    for ques in questions:
        try:
            if ques.qtype == 'D':
                date_str=answers_list.get(str(ques.id))[0].values()[0].replace('\\/','-')
                date_fmt = date_str.split('-')
                date_fmt.reverse()
                date_rev = date_fmt[0]+'-'+date_fmt[1]+'-'+date_fmt[2]
                resp_dict[ques.id] = date_rev
            elif ques.qtype in ['S','R'] and ques.master_choice == False:
                resp_dict[ques.id]=int(answers_list.get(str(ques.id))[0].values()[0])
            elif ques.qtype in ['S','R'] and ques.master_choice == True:
		resp_dict[ques.id]=answers_list.get(str(ques.id))[0].values()[0]
	    else:
                resp_dict[ques.id]=answers_list.get(str(ques.id))[0].values()[0]
        except:
            pass
    return resp_dict


def create_media_answers(user, **media_params):
    #Creating media (Answer) Files
    
    media_list = media_params.get('image_array')
    key = media_params.get('cluster_key')
    cluster_id = media_params.get('cluster_id')
    app_answer_obj = media_params.get('app_answer_obj')
    if media_list and app_answer_obj:
        for mediadict in media_list:
            qu_suq_id = mediadict.get('subq') if mediadict.get('subq') else mediadict.get('qid')
            content_type = ContentType.objects.get(model__iexact=key)
            qobj = Question.objects.get(id=int(qu_suq_id))
            media_obj = Media.objects.create(user=user, question=qobj,\
                                                content_type=content_type, \
                                                object_id=int(cluster_id))
            if qobj.qtype in ['I']:
                media_obj.image = mediadict.get('image')
            else:
                media_obj.sfile = mediadict.get('image')
            anson = mediadict.get('time')
            ansdt = datetime.strptime(anson,"%Y-%m-%d %H:%M:%S") if anson else None
            media_obj.app_answer_on = ansdt
            media_obj.app_answer_data = int(app_answer_obj.id)
            media_obj.save()
    return True


@csrf_exempt
def app_logout(request):
    logout(request)
    return JsonResponse({'message':'logout Successfully'})


@csrf_exempt
@validate_post_method
def fetch_version_updates(request, **kwargs):
    q_list, c_list, b_list, table_updates = [], [], [], []
    lang_list, lab_list, qlu_list, chlu_list, blu_list = [], [], [], [], []
    response, response_type, message, latest_version = {}, 0, '',''
    if request.method == 'POST':
        user_id = request.POST.get('uId')
        survey_details = eval(str(request.POST.get('surveyDetails')))
        survey_ids = [i.get('survey_id') for i in survey_details]
        for syvdict in survey_details:
            vn = syvdict.get('vn', 1.00)
            survey_id = syvdict.get('survey_id')
            resdict = get_question_answer_list(vn, survey_id)
            q_list = q_list + resdict['qu']
            c_list = c_list + resdict['ch']
            b_list = b_list + resdict['bl']
            qlu_list = qlu_list + resdict['qlu']
            chlu_list = chlu_list + resdict['chlu']
            blu_list = blu_list + resdict['blu']
        # Labels and Language are common irrespective of survey
        # Hence language and lables are outside for loop
        language_list = Language.objects.active_items()
        lang_list = language_updates(language_list, survey_ids)
        applabel_ids = list(set(AppLabel.objects.active_items().values_list('id',flat=True)))
        if request.POST.get('lastUpdate'):
            up_labels_dt = request.POST.get('lastUpdate')
            dt = datetime.strptime(up_labels_dt,"%d-%m-%Y %H:%M:%S")
            label_language_list = LabelLanguageTranslation.objects.active_items().filter(applabel__id__in= applabel_ids).filter(created__gte=dt)
        else:
            label_language_list = LabelLanguageTranslation.objects.active_items().filter(applabel__id__in= applabel_ids)
        lab_list = label_updates(label_language_list)
        table_updates = get_table_updates(q_list, c_list, b_list, lang_list, lab_list, qlu_list, chlu_list, blu_list)
        message, response_type = "Retrieved Successfully", 1
    else:
        message = kwargs.get('error_msg','')
    try:
        language_id = Language.objects.get(name__iexact="English").id
    except:
        language_id = 1
    response = {'responseType':response_type, 'message':message, \
                 'tables':table_updates, 'defaultLanguage':language_id,\
                 'surveyDetails':get_latest_survey_versions(user_id)}
    return JsonResponse(response)


def get_question_answer_list(vn, survey_id):
    # Retrieves the updated question and choices vn = 1.00 if float(vn) == 0.0 else vn
    qu, ch, bl = [], [], []
    question_list, choice_list, block_list = [], [], []
    language_list, qlt_list, chl_list, applabel_ids = [], [], [], []
    qlu, chlu, blu = [], [], []
    version_list = Version.objects.filter(survey__id=int(survey_id)).order_by('-id')
    vn = {0.0:1.00}.get(float(vn),vn)
    if len(version_list) >= 1 and float(version_list[0].version_number) >= float(vn):
        version_list.latest('id').version_number
        version_obj = version_list[0]
        version_diff = abs(float(version_obj.version_number) - float(vn))
        if (float(vn) >= 1.0 and float(version_diff) <= 0.05 and \
                    float(version_obj.version_number) >= 1.0) or float(vn) == 1.00:
            question_list = Question.objects.filter(block__survey__id=int(survey_id))
            choice_list = Choice.objects.filter(question__block__survey__id = int(survey_id))
            block_list = Block.objects.filter(survey__id = int(survey_id))

        elif float(vn) >= 1.0 and len(version_list) >= 1:
            last_id = int(version_list.latest('id').id)
            up_version = version_list.filter(version_number = vn)
            version_id = int(up_version[0].id) if len(up_version) >= 1 else 0
            version_list = version_list.filter(id__gte=version_id,id__lte=last_id)
            result_ids = get_ids(version_list)
            qids_list, chids_list = result_ids['qids_list'], result_ids['chids_list']
            question_list = Question.objects.filter(id__in = qids_list)
            choice_list = Choice.objects.filter(id__in = chids_list)
            block_list = Block.objects.filter(survey__id = int(survey_id))
        language_id = Language.objects.get_default_language().id
        qu = question_updates(question_list, version_obj, language_id)
        ch = choice_updates(choice_list, version_obj, language_id)
        bl = block_updates(block_list, version_obj, language_id)
        # Question Language / Choice Language / Language without
        # any version is done Here
        qlt_list = QuestionLanguageTranslation.objects.filter(question__block__survey__id=int(survey_id))
        chl_list = ChoiceLanguageTranslation.objects.filter(choice__question__block__survey__id=int(survey_id))
        bl_list = BlockLanguageTranslation.objects.filter(block__survey__id=int(survey_id))
        qlu = question_language_updates(qlt_list)
        chlu = choice_language_updates(chl_list)
        blu = block_language_updates(bl_list)

    return {'qu':qu, 'ch':ch, 'bl':bl, 'qlu':qlu, 'chlu':chlu, 'blu':blu}


def get_ids(version_list=[]):
    qids_list, chids_list, blids_list, syids_list = [], [], [], []
    for vs in version_list:
        if vs.content_type.model.lower() == 'question':
            qids_list.append(int(vs.object_id))
        elif vs.content_type.model.lower() == 'choice':
            chids_list.append(int(vs.object_id))
        elif vs.content_type.model.lower() == 'block':
            blids_list.append(int(vs.object_id))
        elif vs.content_type.model.lower() == 'survey':
            syids_list.append(int(vs.object_id))
    return {'qids_list':qids_list, 'chids_list':chids_list, \
            'blids_list':blids_list,'syids_list':syids_list}


def question_updates(question_list,version_obj, language_id=''):
    # Question Type Text(1), (Old)Select(3), Radio(4), Checkbox(2), Date(5)
    # New Changes as on 29-12-2015 (New)Select(10)
    res = [[qu.id, qu.code, qu.get_question_code(), qu.block.survey.id, \
            qu.block.id, qu.parent.id if qu.parent else None,\
            qu.text, None, version_obj.version_number,\
            qu.get_question_status(), "", "", language_id,\
            version_obj.get_action(**{'obj':qu})]
            for qu in question_list if qu.question_check()]
    return res


def choice_updates(choice_list, version_obj, language_id=''):
    res = [[ch.id, ch.question.id, ch.get_answer_code(), ch.text, \
            ch.active, ch.get_choice_skip_code(),
            ch.question.get_question_validation(),
            ch.get_answer_flag(), language_id, \
            version_obj.get_action(**{'obj':ch})]
            for ch in choice_list]
    return res


def block_updates(block_list, version_obj, language_id=''):
    res = [[bl.id, bl.block_type, bl.name, language_id, bl.active] for bl in block_list]
    return res


def language_updates(language_list=[], survey_ids=[]):
    # Language Updates without version updates
    # Survey Id is mandatory for feeds
    # id, lang_code, lang_shortcut, language, typology_code, action
    sml_list, l_id = [], []
    sml_list = SurveyLanguageMap.objects.active_items().filter(survey__id__in=survey_ids)
    language_ids = list(set(sml_list.values_list('language__id', flat=True)))
    language_list = Language.objects.filter(id__in=language_ids)
    for lang in language_list:
        qlt = QuestionLanguageTranslation.objects.filter(language__id=int(lang.id))
        if qlt.count() >= 1:
            l_id.append(int(lang.id))
    sml_list = sml_list.filter(language__id__in = l_id)
    res = [[lang.id, lang.code, "", lang.name, sml.survey.id, ""] for sml in sml_list for lang in sml.language.all()]
    return res


def label_updates(label_language_list=[]):
    # Returns the label with multiple languages
    res = [[l.id, l.applabel.name, l.text, l.language.id, l.created.strftime("%d-%m-%Y %H:%M:%S"), l.active] for l in label_language_list]
    return res


def question_language_updates(qlt_list=[]):
    # Returns the question language translations
    res = [[q.id, q.question.id, q.text, q.other_text, "", q.language.id, q.active] for q in qlt_list]
    return res


def choice_language_updates(chl_list=[]):
    # Returns the choice language text
    res = [[ch.id, ch.choice.id, ch.text, ch.get_language_validation(), ch.language.id, ch.active] for ch in chl_list]
    return res


def block_language_updates(bl_list=[]):
    res = [[bl.id, bl.block.id, bl.text, bl.language.id, bl.active] for bl in bl_list]
    return res


def get_table_updates(qu=[], ch=[], bl=[], lang_list=[], lab_list=[], qlu_list=[], chlu_list=[], blu_list=[]):
    question_columns = ['id','q_code','ans_type','typology_code',\
                        'block_id','sub_question', 'qn_en', 'q_validation','version_number','active', \
                        'ht_en', 'in_en', 'l_id', 'action']
    choice_columns = ['id', 'q_id','ans_code','an_en', 'active','skip_code','v_en', 'ans_flag', 'l_id', 'action']
    block_columns = ['id','block_code','b_en','l_id','active']
    qlanguage_columns = ["_ID", "QID", "QUESTION", "HELPTEXT", "TOOLTIP", "LID", "action"]
    clanguage_columns = ["_ID", "OID", "ANSWER", "VALIDATION", "LID", "action"]
    blanguage_columns = ["_ID", "BID", "BLOCKNAME", "LID", "action"]
    language_columns =  ["id", "lang_code", "lang_shortcut", "language", "typology_code", "action"]
    label_language_columns =  ["_ID", "LABLE", "LANGUAGELABLE", "LID", "CURRENTDATE", "action"]
    table_updates = [{'tName':'Question', 'columns':question_columns, 'values':qu},\
                    {'tName':'Answer','columns':choice_columns, 'values':ch},\
                    {'tName':'Block','columns':block_columns, 'values':bl},\
                    {'tName':"LanguageQuestion",'columns':qlanguage_columns, 'values':qlu_list},\
                    {'tName':"LanguageOptions",'columns':clanguage_columns, 'values':chlu_list},\
                    {'tName':"Language",'columns':language_columns, 'values':lang_list},\
                    {'tName':"LanguageBlock",'columns':blanguage_columns, 'values':blu_list},\
                    {'tName':"LanguageLabels",'columns':label_language_columns, 'values':lab_list}]
    return table_updates


def get_latest_survey_versions(user_id):
    # Retrieves latest survey version based on used
    # User based survey and latest version of the user surveys
    version_updates = []
    userrole = UserRoles.objects.get(user__id=int(user_id))
    usersurvey_list = DetailedUserSurveyMap.objects.filter(active=2,user=userrole)
    survey_ids = list(set(usersurvey_list.values_list('survey__id',flat=True)))
    survey_list = Survey.objects.filter(active=2,id__in=survey_ids)
    active_survey_ids = list(set(survey_list.values_list('id',flat=True)))
    version_list = Version.objects.active_items().select_related('survey').filter(survey__id__in = active_survey_ids).order_by('-id')
    version_sids = list(set(version_list.values_list('survey__id',flat=True)))
    for i in version_sids:
        vlist = version_list.filter(survey__id=int(i))
        survey_object = Survey.objects.get(id=int(i))
        ben_ids = ""
        facility_ids = ""
        ben_type = ""
        facility_type = ""
        if len(vlist) >= 1:
            level_objects = list(Levels.objects.filter(survey__id=int(i)).order_by('name'))
            levels = [l.name for l in level_objects]
            levellist = ",".join(levels)
            level_names = {'level2':'state','level3':'district','level4':'block','level5':'gramapanchayath','level6':'village', 'level7':'hamlet'}
            levellabels = []
            for lo in level_objects:
                levellabels.append(level_names[lo.name])
            levellabels = ",".join(levellabels)
            survey_partner = SurveyPartnerExtension.objects.get_or_none(survey__id=int(i),partner=userrole.partner)
            sur_map = SurveyDataEntryConfig.objects.get(survey__id=int(i))
            if sur_map.survey.data_entry_level.id == 3 and sur_map.is_profile == False:
                facility_ids = str(sur_map.object_id1)
                facility_type = MasterLookUp.objects.get(id=int(facility_ids)).name
                ben_ids = str(sur_map.object_id2)
                ben_type = BeneficiaryType.objects.get(id=int(ben_ids)).name
            elif sur_map.survey.data_entry_level.id == 3 and sur_map.is_profile == True:
                facility_ids = str(sur_map.object_id1)
                facility_type = MasterLookUp.objects.get(id=int(facility_ids)).name
            elif sur_map.survey.data_entry_level.id == 1:
                ben_ids = ""
                facility_ids = ""
                facility_type = ""
                ben_type = ""
            else:
                ben_ids = str(sur_map.object_id1)
                ben_type = BeneficiaryType.objects.get(id=int(ben_ids)).name
            user_survey = usersurvey_list.get(survey__id=int(i))
            quest_ids=""
            for s in SurveyQuestions.objects.filter(survey__id=int(i)):
                quest_ids = [str(q) for q in s.questions.ids()]
                quest_ids = ",".join(quest_ids)
            version_obj = vlist.select_related('survey').latest('id')
            vn = version_obj.version_number
            survey_name = version_obj.survey.name

            survey_order = version_obj.survey.order

            if int(version_obj.survey.piriodicity) != 0:
                piriodicity = version_obj.survey.get_piriodicity_display()
            else:
                piriodicity = ""
            pcode = version_obj.survey.piriodicity
            try:
                cluster_version = version_obj.survey.usersurveymap_set.filter(user__user__id=int(user_id),\
                                                                survey__id=int(version_obj.survey.id))[0].get_user_cluster_versions()
                if cluster_version == 0:
                    cluster_version = 1
            except:
                cluster_version = 1
            exp_val = {True:"1",False:"0"}
            version_updates.append({'vn':vn, 'survey_id':i, \
                                    'piriodicity':'1',\
                                    'piriodicity_flag':piriodicity,\
                                    'pcode':pcode, 'pLimit':int(version_obj.survey.expiry_age),\
                                    'pFeature':3,
                                    "clusterVersion":cluster_version,
                                    'b_config': 2,
                                    'q_config': 2,
                                    'survey_order':survey_order,
                                    'rule_engine':str({'isAutoFill':exp_val.get(survey_object.is_auto_fill),
                                                   'questionsToAutofill':survey_object.get_periodic_questions(),
                                                   'survey_json': eval(json.dumps(survey_object.get_survey_rule_engine()))
                                                   }),
                                    'reasonDisagree': 3,
                                    'survey_name':survey_name,
                                    'order_levels':str(levellist),
                                    'beneficiary_ids':ben_ids,
                                    'beneficiary_type':ben_type,
                                    'facility_type':facility_type,
                                    'facility_ids':facility_ids,
                                    'labels':str(levellabels),
                                    'partner_expiry_age':int(survey_partner.expiry_age) if survey_partner else 0,
                                    'summary_qid':quest_ids})
    return version_updates


def get_survey_latest_version(survey_id):
    # Retrieves Latest Survey version based on survey id
    # If no survey version return the default version 1.0
    vn = 1.0
    survey_obj = Survey.objects.get_or_none(id=int(survey_id))
    if survey_obj:
        version_list = Version.objects.filter(survey=survey_obj).order_by('-id')
        if len(version_list) >= 1:
            vn = version_list[0].version_number
    return vn


def get_version_updates(t_id='', vns=''):
    updates = []
    sids_list = t_id.split(',')
    vns_list = vns.split(',')
    if len(sids_list) == len(vns_list):
        updates = [{'survey_id':sid, 'vn':get_survey_latest_version(sid)}
                    for sid in sids_list]
    return updates


@csrf_exempt
def feed_error_log(request):
    status, message = False, ''
    if request.method == 'POST':
        user_id = request.POST.get('uId')
        error_log = request.POST.get('ErrorLog')
        stoken = request.POST.get('sToken')
        user_obj = User.objects.get(id=int(user_id))
        if user_obj:
            logdata(error_log, user_obj, stoken)
            status = True
            message = "ErrorLog Data saved successfully"
    res = {'status':status, 'message':message}
    return JsonResponse(res)


def logdata(error_log, user_obj, stoken):
    from ccd.settings import BASE_DIR
    from django.core.files.base import ContentFile, File
    import time
    unique_time = int(time.time())
    today_date = datetime.now()
    year = today_date.strftime("%Y")
    dt = today_date.strftime("%d")
    m = today_date.strftime("%m")
    hour = today_date.strftime("%H")
    minute = today_date.strftime("%M")
    new_file_path = '%s/static/logfiles/%s/%s/%s' % (BASE_DIR,year,m,dt)
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)
    file_name = "ErrorLog" + "-" + str(user_obj.id) + "-" + str(unique_time) + "-" + year + "-" + m + "-" + dt + ".txt"
    full_filename = os.path.join(BASE_DIR,new_file_path,file_name)
    text_file = open(full_filename, 'wb+')
    text_file.writelines("Date : " + dt + "-" + m + "-" + year + "\n")
    text_file.writelines("Time : "+ hour + "hrs" + ":" + minute + "min" + "\n\n")
    text_file.writelines("Error : "+error_log)
    elog_obj = ErrorLog.objects.create(user=user_obj, stoken=stoken)
    elog_obj.log_file = File(text_file)
    elog_obj.save()
    text_file.close()
    return True


@csrf_exempt
def get_language_app_label(request):
    # This code is not in "USE"
    response_type, message = 0, ''
    response = {}
    if request.method == 'POST':

        applabel_list = AppLabel.objects.active_items()
        labels_array = list(set(applabel_list.order_by('id').values_list('name',flat=True)))
        label_list = LabelLanguageTranslation.objects.active_items()
        label_language_ids = list(set(label_list.values_list('id',flat=True)))
        language_list = Language.objects.active_items().filter(id__in = label_language_ids)
        label_language = [{'langKey':i.name, 'langId':i.id} for i in language_list]
        labels = {i.name:i.get_lables() for i in language_list}
        response = {'labelsArray':labels_array, \
                    'labelLang':label_language,\
                    'languageLables':labels}
    response.update({'message':message,'responseType':response_type})
    return JsonResponse(response)


def create_post_log(request):
    from RubanBridge.settings import BASE_DIR
    from django.core.files.base import ContentFile, File
    today_date = datetime.now()
    year = today_date.strftime("%Y")
    dt = today_date.strftime("%d")
    m = today_date.strftime("%m")
    hour = today_date.strftime("%H")
    minute = today_date.strftime("%M")
    new_file_path = '%s/static/logAnswer/%s/%s/%s' % (BASE_DIR,year,m,dt)
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)
    file_name = "AnswerLog" + "-" + year + "-" + m + "-" + dt + ".txt"
    full_filename = os.path.join(BASE_DIR,new_file_path,file_name)
    if os.path.isfile(full_filename):
        text_file = open(full_filename, 'a')
    else:
        text_file = open(full_filename, 'wb+')
    text_file.writelines("User Id : "+request.POST.get('uId','No User Id'))
    text_file.writelines("\nIMEI : "+request.POST.get('imei','No IMEI number'))
    text_file.writelines("\nCluster Id : "+request.POST.get('cluster_id','No Cluster Id'))
    text_file.writelines("\nCluster Key : "+request.POST.get('clusterKey','No Clster Key'))
    text_file.writelines("\nUnique Id : "+request.POST.get('sample_id','No Sample Id'))
    text_file.writelines("\nLog Date & Time : " + dt + "-" + m + "-" + year + " "+ hour + "hrs" + ":" + minute + "min" + "\n")
    text_file.writelines("\nAnswer Array : "+request.POST.get('answers_array'))
    text_file.writelines("\nOperator Details : "+request.POST.get('OperatorDetails',''))
    text_file.writelines("\n\n\n==================================================\n\n")
    text_file.close()
    return True


def get_ruban_level_code(key, cluster_id):
    rbcode = ''
    if key.lower() == 'village':
        village_obj = Village.objects.get(id=int(cluster_id))
        rbcode = str(village_obj.gramapanchayath.taluk.district.state.code) + str(village_obj.gramapanchayath.mandal.taluk.district.code)
    elif key.lower() == 'gramapanchayath':
        g_obj = GramaPanchayath.objects.get(id=int(cluster_id))
        rbcode = str(g_obj.code) + str(g_obj.taluk.district.state.code)

    elif key.lower() == 'taluk':
        t_obj = Taluk.objects.get(id=int(cluster_id))
        rbcode = str(t_obj.code) + str(t_obj.district.state.code)
    elif key.lower() == 'district':
        d_obj = District.objects.get(id=int(cluster_id))
        rbcode = str(d_obj.code) + str(d_obj.state.code)
    elif key.lower() == 'state':
        s_obj = State.objects.get(id=int(cluster_id))
        rbcode = str(s_obj.code) + str(s_obj.country.code)
    elif key.lower() == 'country':
        c_obj = Country.objects.get(id=int(cluster_id))
        rbcode = str(c_obj.code)
    return rbcode


@csrf_exempt
def check_network_connectivity(request):
    status, message = 0, 'Error in connection'
    if request.method == 'POST':
        time = request.POST.get('time')
        device_id = request.POST.get('dId')
        user_id = request.POST.get('uId')
        try:
            user_obj = User.objects.get(id=int(user_id))
        except:
            user_obj = None
            message = "Invalid User"
        if time and device_id and user_obj:
            time_obj = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
            NetworkConnectionStatus.objects.create(time=time_obj,
                                                    device_id=device_id,
                                                    user=user_obj)
            status = 1
            message = "All test passed !"
    return JsonResponse({'status':status,'message':message})



@csrf_exempt
def dblog(request):
    status, message = False, 'Error while pushing the database'
    if request.method == 'POST':
        user_id = request.POST.get('uId')
        dbfile = request.FILES.get('dbfile')
        
        user_obj = User.objects.get(id=int(user_id))
        if user_obj and dbfile:
            DataBaseLog.objects.create(user=user_obj,log_file=dbfile)
            status = True
            message = "Data Base saved successfully"
    res = {'status':status, 'message':message}
    return JsonResponse(res)
