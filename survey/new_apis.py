from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from survey.models import *
from survey.custom_decorators import *
from survey.monkey_patching import *
from masterdata.models import *
from beneficiary.models import *
from facilities.models import *
import os
from datetime import datetime, timedelta
from django.db.models import Q
from django.apps import apps
from survey.capture_sur_levels import convert_string_to_date
import pytz
from ccd.settings import HOST_URL
from partner.models import PartnerBoundaryMapping

@csrf_exempt
def blocklist(request):
    if request.method == 'POST':


        blocks = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        bl = Block.objects.all()
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            bl = bl.filter(modified__gt=updated)
            flag = False
        bl = bl.filter().order_by('modified')[:100]
        for j in bl:
            blocks.append({'id': j.id,
                           'block_code': str(j.code) if j.code else "",
                           'survey_id': j.survey.id,
                           'block_order': j.order if j.order else 0,
                           'block_name': j.name,
                           'active': j.active,
                           'language_id': 1,
                           'updated_time': datetime.strftime(j.modified, '%Y-%m-%d %H:%M:%S.%f'),
                           'extra_column1': "",
                           'extra_column2': 0,
                           })
        if blocks:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Block": blocks, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent","Block":[] }
        else:
            res = {"status": 0,
                   "message": "No Blocks tagged for this user","Block":[] }
        return JsonResponse(res)


@csrf_exempt
def languageblocklist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        updatedtime = request.POST.get("updatedtime")
        request.POST.get("count")
        lang_blocks = []
        flag = ""
        lang_bl = Block.objects.filter().exclude(language_code={})
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_bl = lang_bl.filter(modified__gt=updated)
            flag = False
        lang_bl = lang_bl.filter().order_by('modified')[:100]
        for lb in lang_bl:
            for lang,l_text in lb.language_code.iteritems():
                lan_obj = Language.objects.get(id=int(lang))
                lang_blocks.append({'id': int(lb.id),
                                    'block_pid': int(lb.id),
                                    'block_name': l_text,
                                    'language_id': int(lan_obj.code),
                                    'updated_time': datetime.strftime(lb.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                    'extra_column1': str(lan_obj.name),
                                    'extra_column2': 0, })
        if lang_blocks:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageBlock": lang_blocks, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", "LanguageBlock":[]}
        else:
            res = {"status": 0,
                   "message": "No blocks of different language has been tagged to this user","LanguageBlock":[] }
        return JsonResponse(res)


@csrf_exempt
def assessmentlist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")


        flag = ""
        metrics_quest = []
        updatedtime = request.POST.get("updatedtime")
        metrics = Question.objects.filter(is_grid=True)
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            metrics = metrics.filter(modified__gt=updated)
            flag = False
        metrics = metrics.filter().order_by('modified')[:100]
        for met in metrics:
            metrics_quest.append({'id': int(met.id),
                                  'assessment': met.text,
                                  'question_pid': met.parent.id if met.parent else "",
                                  'active': met.active,
                                  'mandatory': int(met.mandatory),
                                  'group_validation': met.get_question_validation() if met.get_question_validation() else "",
                                  'survey_id': int(met.block.survey.id),
                                  'language_id': 1,
                                  'updated_time': datetime.strftime(met.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                  'extra_column1': "",
                                  'extra_column2': 0,
                                  'qtype': met.qtype if met.qtype else "", })
        if metrics_quest:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Assessment": metrics_quest, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent","Assessment":[] }
        else:
            res = {"status": 0,
                   "message": "No grid questions tagged for this user","Assessment":[] }
        return JsonResponse(res)


@csrf_exempt
def languageassessmentlist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")



        flag = ""

        updatedtime = request.POST.get("updatedtime")
        metrics = Question.objects.filter(is_grid=True)
        metrics_lang = []
        met_lang = QuestionLanguageTranslation.objects.filter(
            question__in=metrics)
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            met_lang = met_lang.filter(modified__gt=updated)
            flag = False
        met_lang = met_lang.filter().order_by('modified')[:100]
        for ml in met_lang:
            metrics_lang.append({'id': int(ml.id),
                                 'assessment': ml.text,
                                 'assessment_pid': int(ml.question.id),
                                 'language_id': int(ml.language.id),
                                 'updated_time': datetime.strftime(ml.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                 'extra_column1': str(ml.language.name),
                                 'extra_column2': ml.integer_field, })
        if metrics_lang:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageAssessment": metrics_lang, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No grid questions of different language has been tagged to this user", }
        return JsonResponse(res)


@csrf_exempt
def questionlist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")

        quest_list = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        questions = Question.objects.filter(is_grid=False )

        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            questions = questions.filter(modified__gt=updated)
            flag = False
        questions = questions.filter().order_by('modified')[:500]
        qtype_dict = {'N': 0, 'T': 1, 'S': 6, 'R': 4, 'C': 2, 'D': 5,
                      'G': 7, 'I': 8, 'V': 9, 'Cl': 3, 'GD': 14, 'In': 16}
        for quest in questions:
            quest_list.append({'id': int(quest.id),
                               'question_code': int(quest.code),
                               'answer_type': 'N' if quest.qtype in [11,12] else qtype_dict.get(quest.qtype),
                               "survey_id": int(quest.block.survey.id),
                               "block_id": int(quest.block.id),
                               "sub_question": "",#quest.parent.id if quest.parent else "",
                               "question_text": quest.text,
                               "help_text": quest.help_text,
                               'instruction_text': "",
                               "active": quest.active,
                               "language_id": 1,
                               "mandatory": int(quest.mandatory),
                               "question_order": int(quest.order),
                               "validation": quest.get_question_validation() if quest.get_question_validation() else "",
                               "rule_set": quest.question_based_validation(),
                               "image_path": "",
                               "answer": quest.qtype if quest.qtype else "",
                               "keyword": "",
                               'updated_time': datetime.strftime(quest.modified, '%Y-%m-%d %H:%M:%S.%f'),
                               'extra_column1': "English",
                               'extra_column2': 0,
                               #'other_auto_fill':quest.block.survey.survey_auto_fill,
                               #'other_question_id':quest.question_auto_fill
                               'question_json':quest.api_auto_fill(),
                               #'isMultiSel': 1 if quest.master_choice == True else 0,
                               #'isBen':str(quest.get_master_choice().master_type) if quest.get_master_choice() else "",
                               #'typeCode':str(quest.get_master_choice().code)  if quest.get_master_choice() else ""
                              })
        if quest_list:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Question": quest_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", "Question":[]}
        else:
            res = {"status": 0,
                   "message": "No questions tagged for this user","Question":[] }
        return JsonResponse(res)


@csrf_exempt
def languagequestionlist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")
        flag = ""
        lang_questions = []
        languages = Language.objects.all()
        updatedtime = request.POST.get("updatedtime")
        lang_quest = Question.objects.filter().exclude(language_code={})
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_quest = lang_quest.filter(modified__gt=updated)
            flag = False
        lang_quest = lang_quest.filter().order_by('modified')[:100]
        for lq in lang_quest:
            for lan_id,lan_text in lq.language_code.iteritems():
                lan_obj = languages.get(id=int(lan_id))
                lang_questions.append({'id': int(lq.id),
                                       'question_pid': int(lq.id),
                                       'question_text': lan_text,
                                       'language_id': int(lan_obj.code),
                                       'updated_time': datetime.strftime(lq.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                       'extra_column1': str(lan_obj.name),
                                       'instruction': "",
                                       'help_text': "",
                                       'extra_column2': 0, })
        if lang_questions:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageQuestion": lang_questions, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", "LanguageQuestion":[]}
        else:
            res = {"status": 0,
                   "message": "No questions of different language has been tagged to this user","LanguageQuestion":[] }
        return JsonResponse(res)


@csrf_exempt
def choicelist(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")

        ch_list = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        choice = Choice.objects.all()
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            choice = choice.filter(modified__gt=updated)
            flag = False
        choice = choice.filter().order_by('modified')[:500]
        for ch in choice:

            if ch.skip_question.all():
                val = [str(i.id) for i in ch.skip_question.all().order_by('code')]
                val = ",".join(val)
            elif ch.code == -1:
                val = str(ch.code)
            else:
                val = ""
            ch_list.append({'id': int(ch.id),
                            'question_pid': int(ch.question.id),
                            'option_code': str(ch.code),
                            "option_flag": 1,
                            "skip_code": val,
                            "validation": "",
                            "order":int(ch.order),
                            "option_text": ch.text,
                            "active": ch.active,
                            "language_id": 1,
                            "survey_id": int(ch.question.block.survey.id),
                            "image_path": "",
                            "is_answer": "true",
                            'updated_time': datetime.strftime(ch.modified, '%Y-%m-%d %H:%M:%S.%f'),
                            'extra_column1': "",
                            'extra_column2': 0,
                            'assessment_pid': int(ch.question.id)})
        if ch_list:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Options": ch_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent","Options":[] }
        else:
            res = {"status": 0,
                   "message": "No choices tagged for this user","Options":[] }
        return JsonResponse(res)
def get_res_dict(k,modified_date,user_id,usm,query,res_dict):
    if k == "MetricsQuestionConfiguration":
        result = Question.objects.filter(
            block__survey__id__in=usm, modified__gt=modified_date, is_grid=True)
    elif k == "MetricsQuestionTranslation":
        result = QuestionLanguageTranslation.objects.filter(
            question__block__survey__id__in=usm, modified__gt=modified_date, question__is_grid=True)
    if k == "BlockLanguageTranslation":
        result = Block.objects.filter(survey__id__in=usm, modified__gt=modified_date)
    elif k == "ChoiceLanguageTranslation":
        result = Choice.objects.filter(question__block__survey__id__in=usm, modified__gt=modified_date)
    elif k == "QuestionLanguageTranslation":
        result = Question.objects.filter(
            block__survey__id__in=usm, modified__gt=modified_date)
    else:
        q = {query.get(k): usm, 'modified__gt': modified_date}
        result = apps.get_model('survey', k).objects.filter(**q)
    if result.count() > 0:
        res_dict[k] = True
    else:
        res_dict[k] = False
    return res_dict

@csrf_exempt
def updatedtables(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        partner_id = UserRoles.objects.get(user_id = int(user_id)).partner_id
        usm = list(set(DetailedUserSurveyMap.objects.filter(
        user__user__id=int(user_id)).values_list('survey__id', flat=True)))
        query = {
            "Block": "survey__id__in",
            "BlockLanguageTranslation": "block__survey__id__in",
            "Question": "block__survey__id__in",
            "QuestionLanguageTranslation": "question__block__survey__id__in",
            "Choice": "question__block__survey__id__in",
            "SkipMandatory": "question__block__survey__id__in",
            "ChoiceLanguageTranslation": "choice__question__block__survey__id__in",
        }
        res_dict = {}
        updated_dict = request.POST.get('UpdatedDateTime')
        updated_dict = eval(updated_dict)

        updated_dict["BlockLanguageTranslation"] = updated_dict.pop(
            "LanguageBlock")
        updated_dict["QuestionLanguageTranslation"] = updated_dict.pop(
            "LanguageQuestion")
        updated_dict["MetricsQuestionConfiguration"] = updated_dict.pop(
            "Assessment")
        updated_dict["MetricsQuestionTranslation"] = updated_dict.pop(
            "LanguageAssessment")
        updated_dict["Choice"] = updated_dict.pop("Options")
        updated_dict["ChoiceLanguageTranslation"] = updated_dict.pop("LanguageOptions")
        ben_modified = updated_dict.get("ben_modified")
        if ben_modified:
            updated_dict.pop("ben_modified")
        ben_modified_date = convert_string_to_date(str(ben_modified))
        fac_modified = updated_dict.get("fac_modified")
        if fac_modified:
            updated_dict.pop("fac_modified")
        fac_modified_date = convert_string_to_date(str(fac_modified))
        if ben_modified_date:
            result_ben_unsync = Beneficiary.objects.filter(modified__gt = ben_modified_date , partner_id = partner_id ).count()
        else:
            result_ben_unsync = 0
        if fac_modified_date:
            result_fac_unsync = Facility.objects.filter(modified__gt = fac_modified_date , partner_id = partner_id).count()
        else:
            result_fac_unsync = 0        
        updated_dict.pop("SkipRules")
        updated_dict.pop("LanguageLabels")
        updated_dict.pop("MetricsQuestionConfiguration")
        updated_dict.pop("MetricsQuestionTranslation")
        for k, v in updated_dict.iteritems():
            if v != "":
                modified_date = convert_string_to_date(str(v))
                get_res_dict(k,modified_date,user_id,usm,query,res_dict)
            else:
                res_dict[k] = True
            res_dict["SkipRules"] = False
            res_dict["LanguageLabels"] = False
            res_dict["MetricsQuestionConfiguration"] = False
            res_dict["MetricsQuestionTranslation"] = False
        res_dict["LanguageBlock"] = res_dict.pop("BlockLanguageTranslation")
        res_dict["LanguageQuestion"] = res_dict.pop(
            "QuestionLanguageTranslation")
        res_dict["Assessment"] = res_dict.pop("MetricsQuestionConfiguration")
        res_dict["LanguageAssessment"] = res_dict.pop(
            "MetricsQuestionTranslation")
        res_dict["Options"] = res_dict.pop("Choice")
        res_dict["LanguageOptions"] = res_dict.pop("ChoiceLanguageTranslation")
        
        userprofile_obj = UserRoles.objects.get(user__id=user_id)
        version_update = VersionUpdate.objects.filter().latest('id')
        updateapk = {"forceUpdate": str(version_update.force_update),
                     "appVersion": int(version_update.version_code),
                     "updateMessage": "New update available, download from playstore",
                     "link": "https://play.google.com/store/apps/details?id=org.mahiti.cry"}
        partner_id = userprofile_obj.partner.id
        p_b_m = PartnerBoundaryMapping.objects.filter(partner__id = partner_id)
        if p_b_m:
            gp_ids_list = list(p_b_m.values_list('object_id' , flat = True))
            location_ids =  ",".join(str(i) for i in gp_ids_list)
            boundary_level = "5"
        else:
            location_ids = ""
            boundary_level = ""
        res = {'status': 2,
               'message': 'updated successfully',
               'serverTime':str(datetime.now()),
               'appOfflineTime':180,
               'updatedTables': res_dict,
               'facilityFilterLevel' : 2,
               'beneficiaryFilterLevel' : 7,
	       'ben_unsync': result_ben_unsync,
	       'fac_unsync': result_fac_unsync}
        res.update({'updateAPK': updateapk,
                    'activeStatus': userprofile_obj.active, 'forceLogout': 0, })
        res.update({'location_ids':location_ids})
        res.update({'boundary_level':boundary_level})
        res.update({'state_id':''})
        res.update({'location_creation_date':'2019-04-01 11:11:11.111111'})
    return JsonResponse(res, safe=False)


def skips(surveyid):
    quest = Question.objects.filter(block__survey__id=int(surveyid))
    for qu in quest:
        choices = Choice.objects.filter(question=qu)
        sub_quest = qu.parent
        if qu.parent == None:
            sub_quest = 0
        for ch in choices:
            if ch.skip_question:
                reg_exp = str(qu.id) + ";" + str(sub_quest) + ";=;" + \
                    str(ch.code) + "@" + str(ch.skip_question_id)

                skip_exp, created = SkipMandatory.objects.get_or_create(
                    question=qu, question_validation=reg_exp)


@csrf_exempt
def skipmandatory(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        flag = ""
        usm = list(set(DetailedUserSurveyMap.objects.filter(
            user__user__id=int(user_id)).values_list('survey__id', flat=True)))
        skips = SkipMandatory.objects.filter(
            question__block__survey__id__in=usm).order_by('modified')
        skip_mand = []
        updatedtime = request.POST.get("updatedtime")
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            skips = skips.filter(modified__gt=updated)
            flag = False
        for sk in skips:
            skip_mand.append({'id': int(sk.id),
                              'question_pid': int(sk.question.id),
                              'question_validation': sk.question_validation,
                              'validation_order': 1.0,
                              'skip_or_mandatory': 1,
                              'sub_module_type': sk.sub_module_type if sk.sub_module_type else "",
                              'updated_time': datetime.strftime(sk.modified, '%Y-%m-%d %H:%M:%S.%f'),
                              'extra_column1': sk.char_field1 if sk.char_field1 else "",
                              'extra_column2': sk.integer_field1, })
        if skip_mand:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "SkipMandatory": skip_mand, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent","SkipMandatory":[]}
        else:
            res = {"status": 0,
                   "message": "No skips for this user", "SkipMandatory":[]}
        return JsonResponse(res)


@csrf_exempt
def languagelabel(request):
    if request.method == 'POST':
        lng_lab = []
        flag = ""
        lang_labels = LabelLanguageTranslation.objects.filter(active=2)
        updatedtime = request.POST.get("updatedtime")
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_labels = lang_labels.filter(modified__gt=updated)
            flag = False
        lang_labels = lang_labels.filter().order_by('modified')[:100]
        for ll in lang_labels:
            lng_lab.append({"id": ll.id,
                            "label_key": ll.applabel.name,
                            "label_value": ll.applabel.name.replace('_', ' '),
                            "updated_time": datetime.strftime(ll.modified, '%Y-%m-%d %H:%M:%S.%f'),
                            "extra_column1": ll.other_text if ll.other_text else "",
                            "extra_column2": ll.integer_field, })
        if lng_lab:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageLabels": lng_lab, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No language labels available for this user", }
        return JsonResponse(res)


@csrf_exempt
def languagechoice(request):
    if request.method == 'POST':
        request.POST.get("uId")
        request.POST.get("count")

        flag = ""
        l_ch = []
        updatedtime = request.POST.get("updatedtime")
        lang_ch = Choice.objects.filter().exclude(language_code={})
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_ch = lang_ch.filter(modified__gt=updated)
            flag = False
        lang_ch = lang_ch.filter().order_by('modified')[:500]
        for ch in lang_ch:
            for lan_id,lan_text in ch.language_code.iteritems():

                lan_obj = Language.objects.get(id=int(lan_id))
                l_ch.append({"id": ch.id,
                             "option_pid": ch.id,
                             "question_pid": ch.question.id,
                             "language_id": lan_obj.id,
                             "option_text": lan_text,
                             "validation": "",
                             "updated_time": datetime.strftime(ch.modified, '%Y-%m-%d %H:%M:%S.%f'),
                             "extra_column1": str(lan_obj.name),
                             'extra_column2': 0, })
        if l_ch:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageOptions": l_ch, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent","LanguageOptions":[] }
        else:
            res = {"status": 0,
                   "message": "No choices of different language has been tagged to this user", "LanguageOptions":[]}
        return JsonResponse(res)


@csrf_exempt
def appissuetracker(request):
    try:
        usr = request.POST.get('userId')
        issue = request.POST.get('issue_key')
        desc = request.POST.get('description')
        if usr and issue and desc:
            obj = AppIssueTracker.objects.create(
                userid=usr, description=desc, module=issue)
            obj.save()
            status = 'Success'
            msg = 'Remarks submitted sucessfully'

        else:
            status = 'Failure'
            msg = 'Some values are missing'
    except:
        status = 'Failure'
        msg = 'Something went wrong'
    response = {'message': msg, 'status': status}
    return JsonResponse(response)


@csrf_exempt
def responses_list(request):
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        updatedtime = request.POST.get("serverdatetime")
        partner_obj = UserRoles.objects.get(user_id=int(user_id)).partner
        user_list = UserRoles.objects.filter(partner=partner_obj).values_list('user',flat=True)
        res_list = []
        flag = ""
        ben_uuid = ""
        fac_uuid = ""
        cluster_id = ""
        cluster_level = ""
        responses = JsonAnswer.objects.filter(active=2,user__in=user_list)
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            responses = responses.filter(submission_date__gt=updated)
            flag = False
        responses = responses.filter().order_by('submission_date')[:100]
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
                             "cluster_id":cluster_id,
                             "cluster_level":cluster_level,
                             "survey_id": int(res.survey.id),
                             "collected_date": datetime.strftime(res.created, '%Y-%m-%d'),
                             "active": res.active,
                             "server_date_time": datetime.strftime(res.submission_date, '%Y-%m-%d %H:%M:%S.%f'),
                             "response_dump": str(res_dump)})
        if res_list:
            res = {'status': 2,
                   'message': "Success",
                   "ResponsesData": res_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No responses for this user", }
        return JsonResponse(res)


@csrf_exempt
def response_details(request):
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        response_id = request.POST.get("responseid")
        if response_id and user_id:
            answer = JsonAnswer.objects.get(user_id=user_id, id=response_id)
            answers = answer.response
            try:
                lang_id = AppAnswerData.objects.get(id=int(answer.app_answer_data)).language_id
            except:
                lang_id = 0
            res = {'status': 2, 'message': "Success", "language_id":int(lang_id),"response": answers}
        else:
            res = {"status": 0, "message": "Both user id and response id is mandatory"}
        return JsonResponse(res, safe=False)


@csrf_exempt
def languagelist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uid")
        updatedtime = request.POST.get("updatedtime")
        usl = []
        flag=""
        user_state = UserRoles.objects.get(user_id=int(user_id)).partner.state
        user_lang = Language.objects.filter(states=user_state)
#        if updatedtime:
#            updated = convert_string_to_date(updatedtime)
#            user_lang = user_lang.filter(modified__gt=updated)
#            flag = False
        for ul in user_lang:
            usl.append({"id": int(ul.id),
                        "language_code": int(ul.code),
                        "language_name": ul.name,
                        "active": ul.active,
                        "updated_date": datetime.strftime(ul.modified, '%Y-%m-%d %H:%M:%S.%f')})
        if usl:
            res = { 'status':2,\
                    'message':"Success",\
                    "regional_language": usl,}
        elif flag == False:
            res = { "status":2, \
                    "message":"Data already sent",}
        else:
            res= { "status":0, \
                    "message":"No languages has been tagged to this user",}
        return JsonResponse(res)
