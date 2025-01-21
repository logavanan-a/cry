from uuid import uuid4
import calendar
import datetime as dt
from math import ceil
from masterdata.views import CustomPagination
from datetime import date, timedelta , datetime
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps
from django.http import JsonResponse
from survey.serializers import *
from reports.serializers import *
from survey.models import *
from userroles.models import UserRoles,UserPartnerMapping
from masterdata.models import (MasterLookUp, Boundary, DocumentCategory)
from .custom_dates import  CustomDates
from facilities.models import Facility
from workflow.models import WorkFlowBatch, WorkFlowSurveyRelation
#from dynamic_listing.views import (get_quarter, month_range, get_last_quarter_dates,
#                                   get_last_quarter_months, get_last_yearly_months, get_last_half_yearly_dates, get_last_month_date,)
from box import Box
from .custom_dates import CustomDates
from ccd.settings import FY_YEAR
import sys
#import datetime
from beneficiary.views import *
from reports.models import ProfileView
# Create your views here.


class SurveyList(generics.ListCreateAPIView):
    
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class BlockCreate(generics.CreateAPIView):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer


class QuestionList(APIView):

    def get(self, request, sid, block_id, skip, choice, lid,c_info):
        "return questions according to block of a survey"
        auto_fill_resp = None
        survey_other = False
        fill_sid = None
        try:
            survey = Survey.objects.get(id=sid)
            if survey.is_auto_fill or survey.survey_auto_fill:
                if survey.survey_auto_fill:
                    fill_sid = survey.survey_fill_id
                    survey_other = True
                    auto_fill_resp = QuestionList.get_latest_info(fill_sid,c_info)
                else:
                    auto_fill_resp = QuestionList.get_latest_info(sid,c_info)
        except:
            return Response({'status': 0, 'message': 'Survey does not exist'})
        res = {"formName": str(survey), "formLevel": str(survey.display_type),
               "formId": survey.id,"language_id":lid}
        survey_blocks = Block.objects.filter(
            active=2, survey__id=sid).order_by('id')
        skip_code = {}
        res['is_skip'] = str(survey.is_skip_survey())
        skip_questions = list(set(Choice.objects.filter(
            question__block__survey=survey , question__active = 2).values_list('skip_question', flat=True)))
        if skip_questions:
            skip_questions.remove(None)
        if survey.is_skip_survey() and int(block_id) == 0:
            skip_code['code__lte'] = survey.identify_skip_question().code
            res['skipping_question'] = survey.identify_skip_question().id
            res['skipping_block'] = survey.identify_skip_question().block.id
            if survey.identify_skip_question().is_survey_end_question():
                res['next_block'] = 0
            survey_blocks = survey_blocks.filter(
                id__lte=survey.identify_skip_question().block.id)
        if str(survey.display_type) == "single":
            if int(block_id) > 0:
                res['next_block'] = survey_blocks.filter(id__gt=int(block_id))[
                    0].id if survey_blocks.filter(id__gt=int(block_id)) else 0
                res['prev_block'] = survey_blocks.filter(id__lt=int(block_id)).order_by(
                    '-id')[0].id if survey_blocks.filter(id__lt=int(block_id)) else 0
                survey_blocks = survey_blocks.filter(id=int(block_id))
            else:
                res['next_block'] = survey_blocks[1].id
                survey_blocks = survey_blocks.filter(id=survey_blocks[0].id)
        if survey.is_skip_survey() and int(block_id) > 0:
            survey_blocks = survey_blocks.filter(id__gte=block_id)
            next_ques = Question.objects.get(
                id=skip,active=2).get_next_set_question(choice)
            skip_code['code__gte'] = next_ques.get('first').code
            skip_code['code__lte'] = next_ques.get('last').code
            res['skipping_question'] = next_ques.get('last').id
            survey_blocks = survey_blocks.filter(id__gte=next_ques.get(
                'first').block.id, id__lte=next_ques.get('last').block.id)
            if next_ques.get('last').is_survey_end_question():
                res['survey_end'] = "True"
                res['next_block'] = 0
        try:
            partner_id = UserRoles.objects.get(user_id=int(request.GET.get('user_id'))).partner.id
        except:
            partner_id = 0
        res["blocks"] = QuestionList.get_questions_block(partner_id,survey_blocks,skip_code,lid,auto_fill_resp,survey_other)
        return Response(res)

    @staticmethod
    def get_latest_info(sid,c_info):
        cluster_query = {}
        c_info = eval(str(c_info).replace("%7B","{").replace("%7D","}").replace("%22","'"))[0]
        if 'beneficiary' in c_info.keys():
            cluster_query['cluster__0__beneficiary__contains'] = c_info[
                'beneficiary']
        elif 'facility' in c_info.keys():
            cluster_query['cluster__0__facility__contains'] = c_info[
                'facility']
        else:
            cluster_query['cluster__0__boundary__contains'] = c_info[
                'boundary']
        answer_obj = JsonAnswer.objects.filter(active=2,survey_id=sid,**cluster_query)
        if answer_obj.exists():
            answer_obj = answer_obj.latest('created')
        return answer_obj if answer_obj else None

    @staticmethod
    def get_questions_block(partner_id,survey_blocks,skip_code,lid,resp,survey_other):
        blocks = []
        for i in survey_blocks:
            block_info = {"id": i.id, "name": str(i)}
            block_questions = Question.objects.filter(
                block__id=i.id, active=2, **skip_code).order_by('code')
            questions = []
            for question in block_questions:
                q_validation = QuestionValidation.objects.get_or_none(question=question)
                question_dict = {"questionType": question.qtype,
                                 "questionMandatory": str(question.mandatory),
                                 "questionLabel": question.question_text_lang(lid.strip('/')), "questionId": question.id,
                                 "questionError": "", "questionAnswer": QuestionList.question_answer_filler(question,resp,survey_other),#resp.response.get(str(question.id)) if question.display and resp else "",
                                 "questionChoice": question.choice_list(partner_id,lid.strip('/')),
                                 "mchoice":str(question.master_choice),
                                 }
                try:
                    question_dict['constraints'] = {"charactersType":
                                                int(question.validation) if int(question.validation) >= 0 else ' ',
                                                    "question_validation":question.parent_id if question.parent_id else question.get_auto_fill_questions(),
                                                    "question_condition":q_validation.validation_condition if q_validation.validation_condition else ""}
                except:
                    question_dict['constraints'] = {"charactersType":
                                                        question.validation if
                                                            question.validation >= 0 else ' ',
                                                    "question_validation": "",
                                                    "question_condition": ""
                                                    }
                questions.append(question_dict)
            block_info["questions"] = questions
            blocks.append(block_info)
        return blocks

    @staticmethod
    def question_answer_filler(question,resp,survey_other):
        if survey_other and resp:
            if question.get_auto_fill_questions():
                try:
                    return resp.response.get(str(question.get_auto_fill_questions[0]))
                except:
                    return ""
                return ""
        elif question.display and resp:
            return resp.response.get(str(question.id)) or ""
        else:
            return ""

class QuestionCreate(generics.CreateAPIView):
    serializer_class = QuestionSerializer


class AnswerValidator(APIView):

    def post(self, request):
        response_blocks = eval(str(request.body)).get('blocks')
        status = 2
        try:
            if response_blocks:
                for i in response_blocks:
                    for quest in i.get('questions'):
                        if quest.get('questionMandatory') == 'True':
                            if quest.get('questionType') == 'T' and (not quest.get('questionAnswer') or quest.get('questionAnswer').isspace()):
                                quest['questionError'] = 'This Field is required'
                                status = 0
                            if quest.get('questionType') == 'T' and quest.get('constraints').get('charactersType')==11:
                                qid = quest.get('constraints').get('question_validation')
                                condition = quest.get('constraints').get('question_condition')
                                answer = quest.get('questionAnswer')
                                q_answer = AnswerValidator.get_question_answer(response_blocks,qid)
                                if not eval(str(answer)+str(condition)+str(q_answer)):
                                    status=0
                                    quest['questionError'] = 'Should be '+str(condition)+' '+str(q_answer)

                            elif quest.get('questionType') == 'D':
                                date = ''
                                try:
                                    date = datetime.datetime.strptime(quest.get('questionAnswer'), '%Y-%m-%d').date()
                                except:
                                    pass
                                if not isinstance(date, date):
                                    quest['questionError'] = 'This field should be datetime'
                                    status = 0
                            elif (quest.get('questionType') == 'S' or quest.get('questionType') == 'R') and not quest.get('questionAnswer') :
                                quest['questionError'] = 'Select a Choice'
                                status = 0

            else:
                status = 3
        except:
            status = 2
        return Response({'status': status, 'error': response_blocks})
    @staticmethod
    def get_question_answer(given_answer,qid):
        for i in given_answer:
            for quest in i.get('questions'):
                if int(quest.get('questionId')) == int(qid):
                    return quest.get('questionAnswer')
        return ""

class SaveAnswer(APIView):

    def post(self, request):
        """  API to save the answer  """
        request_body = request.body
        user = get_user(eval(str(request_body)).get('user'))
        if not user:
            return Response({'status': 0, 'message': 'User is not logged in'})
        survey_id = eval(str(request_body)).get('formId')
        language_id = eval(str(request_body)).get('language_id')
        survey = Survey.objects.get(id=survey_id)
        survey_level = eval(str(request_body)).get('formLevel')
        response_blocks = eval(str(request_body)).get('blocks')
        cluster = eval(str(request_body)).get('cluster')
        periodicity_value = get_piriodicity_value(survey_id)
        cluster.append({'periodicity_value' : periodicity_value})
        status = 2
        msg = "Response Created Successfully"
        current_block = None
        next_block = None
        creation_key = None
        cluster_type = get_keys_from_cluster(cluster)[0]
        created_helper = {}
        survey_partner_extension = None
        try:
            user_partner = get_user_partner(user.id)
            survey_partner_extension = SurveyPartnerExtension.objects.get(
                survey__id=survey_id)
        except Exception as e:
            pass

        expiry_age_extension = [int(survey.expiry_age) > 0,
        get_last_periodicity_date(survey_id) + timedelta(days=int(survey.expiry_age)) >= datetime.now(),
        check_if_previous_is_empty(survey_id, cluster_type, cluster[0][cluster_type].get('id'))]
        if not False in expiry_age_extension:
            created_helper['created'] = get_last_periodicity_date(survey_id)

        elif survey_partner_extension:
            # for partner extension
			create_back_date = [get_last_periodicity_date(survey_id) + \
      					timedelta(days=int(survey_partner_extension.expiry_age))>=datetime.now() , \
					 check_if_previous_is_empty(survey_id, cluster_type, cluster[0][cluster_type].get('id')), \
					user_partner.id and survey_partner_extension, \
					int(user_partner.id) in survey_partner_extension.partner.all().ids()]
			if not False in create_back_date:
				created_helper['created'] = get_last_periodicity_date(survey_id)

        if survey_level == "single":
            if eval(str(request_body)).get('creation_key'):
                creation_key = eval(str(request_body)).get(
                    'creation_key').split('_')
                json_answer = JsonAnswer.objects.get(id=creation_key[1])
                creation_key = creation_key[0]
            else:
                creation_key = str(uuid4())
                json_answer = JsonAnswer(survey_id=survey_id, user_id=user.id,interface=0)
        else:
            creation_key = str(uuid4())
            json_answer = JsonAnswer(survey_id=survey_id, user_id=user.id,interface=0)
        if eval(str(request_body)).get('creation_key'):
            creation_key = eval(str(request_body)).get(
                'creation_key').split('_')
            json_answer = JsonAnswer.objects.get(id=creation_key[1])
            creation_key = creation_key[0]
        survey_blocks = Block.objects.filter(
            active=2, survey__id=survey_id).order_by('id')
        if creation_key != None:
            json_resp = {}
            for i in response_blocks:
                if survey_level == "single":
                    current_block = i.get("id")
                    next_block = survey_blocks.filter(id__gt=current_block)[
                        0].id if survey_blocks.filter(id__gt=current_block) else 0
                for quest in i.get('questions'):
                    try:
                        if quest.get('questionType') == 'T':
                            json_resp[int(quest.get('questionId'))
                                      ] = quest.get('questionAnswer')
                        if quest.get('questionType') == 'R' or \
                                quest.get('questionType') == 'S':
                            json_resp[int(quest.get('questionId'))] = int(
                                quest.get('questionAnswer'))
                        if quest.get('questionType') == 'D':
                            json_resp[int(quest.get('questionId'))
                                      ] = quest.get('questionAnswer')
                        if quest.get('questionType') == 'C':
                            json_resp[int(quest.get('questionId'))
                                      ] = quest.get('questionAnswer')
                    except Exception as e:
                        status = 0
                        msg = e.message
            if json_answer.response:
                json_answer.response.update(json_resp)
            else:
                json_answer.response = json_resp
                app_answer_data = AppAnswerData.objects.create(survey_id=survey_id,language_id=language_id)
                json_answer.app_answer_data = app_answer_data.id
            json_answer.cluster = cluster
            json_answer.save()
            JsonAnswer.objects.filter(active=2,
                id=json_answer.id).update(**created_helper)
            res = {'status': status, 'created': msg,'language_id':language_id,
                   'current_block': current_block, 'creation_key': creation_key,
                   'next_block': next_block, 'survey_id': survey_id}
            res['is_skip'] = str(eval(request_body).get('is_skip'))
            if eval(str(eval(request_body).get('is_skip'))):
                if eval(request_body).get('skipping_question') > 0:
                    skip_question = Question.objects.get(
                        id=eval(request_body).get('skipping_question'),active=2)
                    skip_details = json_answer.response.get(skip_question.id)
                    if skip_question.is_survey_end_question():
                        res['next_block'] = 0
                    elif skip_question.qtype in ['S', 'R']:
                        res['skipping_question'] = skip_question.id
                        res['skip'] = skip_question.id
                        res['next_block'] = skip_question.block.id
                        res['choice'] = skip_details
                        if not Choice.objects.get(id=skip_details).skip_question.all():
                            if res['next_block'] != 0 and skip_question.is_survey_regular_end_question():
                                res['next_block'] = 0
                    elif skip_question.qtype in ['T', 'D']:
                        res['skipping_question'] = skip_question.id
                        res['skip'] = skip_question.id
                        res['next_block'] = skip_question.block.id
                        if skip_question.is_survey_end_question():
                            res['next_block'] = 0
                        res['choice'] = 0
            res['creation_key'] = str(creation_key) + '_' + str(json_answer.id)
            return Response(res)
        


def get_piriodicity_value(survey_id):
        d = datetime.now()
        if (d.month-1)//3:
            fy = d.strftime('%b') + '-' + str(d.year)
            qy = 'Q'+ str((d.month-1)//3) + '-' + str(d.year)
        else:
            fy = d.strftime('%b') + '-' + str(d.year-1)
            qy = 'Q'+ str((d.month-1)//3 + 4) + '-' + str(d.year-1)
        
        s = Survey.objects.get(id = survey_id).get_piriodicity_display()
        if s == 'Quarterly':
            return qy
        elif s == 'Yearly':
            return fy.split('-')[1]
        elif s == 'Monthly':
            return fy



            
class UpdateAnswer(APIView):

    def post(self, request):
        """   API to update the response  """
        request_body = request.body
        user = get_user(eval(str(request_body)).get('user'))
        if not user:
            return Response({'status': 0, 'message': 'User is not logged in'})
        survey_id = eval(str(request_body)).get('formId')
        survey = Survey.objects.get(id=survey_id)

        response_blocks = eval(str(request_body)).get('blocks')
        language_id = eval(str(request_body)).get('language_id')

        status = 2
        msg = "Response Updated Successfully"
        res = {}
        creation_key = eval(str(request_body)).get('creation_key')
        if creation_key.isspace() or creation_key == None:
            return Response({'status': 0, 'msg': 'No Creation key to update',
                             'traceback_error': 'Pass Creation Key to update'})
        if str(survey.display_type) == "single":
            res['survey_id'] = survey_id
            survey_blocks = Block.objects.filter(
                active=2, survey__id=survey_id).order_by('id')
            if int(response_blocks[0]['id']) > 0:
                res['next_block'] = survey_blocks.filter(id__gt=int(response_blocks[0]['id']))[
                    0].id if survey_blocks.filter(id__gt=int(response_blocks[0]['id'])) else 0
                res['prev_block'] = survey_blocks.filter(id__lt=int(response_blocks[0]['id'])).order_by(
                    '-id')[0].id if survey_blocks.filter(id__lt=int(response_blocks[0]['id'])) else 0
                res['creation_key'] = creation_key
            else:
                res['next_block'] = survey_blocks[1].id
                res['creation_key'] = creation_key
        json_answer = JsonAnswer.objects.get(id=creation_key)
        update_resp = {}
        for i in response_blocks:
            for quest in i.get('questions'):
                try:
                    if quest.get('questionType') == 'T':
                        update_resp[str(quest.get('questionId'))
                                    ] = quest.get('questionAnswer')
                    elif quest.get('questionType') == 'R' or \
                            quest.get('questionType') == 'S':
                        update_resp[str(quest.get('questionId'))] = int(
                            quest.get('questionAnswer'))
                    elif quest.get('questionType') == 'D':
                        update_resp[str(quest.get('questionId'))
                                    ] = quest.get('questionAnswer')
                except Exception as e:
                    status = 0
                    msg = e.message
        if json_answer.response:
            json_answer.response.update(update_resp)
        else:
            json_answer.response = update_resp
        json_answer.save()
        res['status'] = status
        res['created'] = msg
        res['is_skip'] = str(eval(request_body).get('is_skip'))
        res['creation_key'] = creation_key
        res['language_id'] = language_id
        if eval(str(eval(request_body).get('is_skip'))) and eval(request_body).get('skipping_question') > 0:
            skip_question = Question.objects.get(
                id=eval(request_body).get('skipping_question'),active=2)

            skip_details = json_answer.response.get(str(skip_question.id))
            if skip_question.is_survey_end_question():
                res['next_block'] = 0
            elif skip_question.qtype in ['S', 'R']:
                res['skipping_question'] = skip_question.id
                res['skip'] = skip_question.id
                res['next_block'] = skip_question.block.id
                res['choice'] = skip_details
                if not Choice.objects.get(id=skip_details).skip_question.all() and (res['next_block'] != 0 and skip_question.is_survey_regular_end_question()):
                    res['next_block'] = 0
            elif skip_question.qtype in ['T', 'D']:
                res['skipping_question'] = skip_question.id
                res['skip'] = skip_question.id
                res['next_block'] = skip_question.block.id
                res['choice'] = 0
        return Response(res)


class SurveyResponses(APIView):

    def post(self, request):
        """
        Survey responses api
        ---
        parameters:
        - name: survey_id
          description: To display survey responses
          required: true
          type: integer
          paramType: form
        - name: user_details
          description : Pass the logged in user id
          required: true
          type: json
          paramType: json
        """
        msg = ""
        status = 2
        response_list = []
        user_details = eval(request.data.get('user_details'))
        try:
            if 'user_id' in user_details.keys() and get_user_partner(user_details.get('user_id')):
                partner_user = get_user_partner(user_details.get('user_id')).get_partner_deo()
            elif 'partner_id' in user_details.keys():
                partner_user = Partner.objects.get(id=user_details.get('partner_id')).get_partner_deo()
            survey = Survey.objects.get(id=int(request.data.get('survey_id')))
            skip_questions = list(set(Choice.objects.filter(
                question__block__survey=survey).values_list('skip_question', flat=True)))
            if skip_questions:
                skip_questions.remove(None)
            questions = Question.objects.filter(
                active=2, block__survey=survey).exclude(id__in=skip_questions)[:3]
            json_answers = JsonAnswer.objects.filter(active=2,survey=survey,user__id__in=partner_user)
            answers = Answer.objects.filter(question__block__survey=survey,
                                            question=questions,).order_by('creation_key', 'created')
            header_list = [quest.text for quest in questions]
            cluster_head = ""
            answers = json_answers.order_by('-id')
            app_answers = AppAnswerData.objects.filter(id__in=answers.values_list('app_answer_data',flat=True))
            for ck in answers.values_list('id',flat=True):
                rlid = 1
                try:
                    rlid = int(app_answers.get(id=answers.get(id=ck).app_answer_data).language_id)
                except Exception as e:
                    pass
                one_response = {'id': ck, 'survey_id': survey.id, 'language_id':int(rlid)}
                cluster_resp = json_answers.get(id=ck).cluster
                cluster_info = self.get_cluster_info(cluster_resp)
                one_response[cluster_info['cluster_header'].capitalize()] = cluster_info['cluster_string']
                cluster_head = cluster_info['cluster_header'].capitalize()
                for ques in questions:
                    if ques.qtype in ['S', 'R', 'C'] and ques.master_choice == False:
                        choice = Choice.objects.get_or_none(
                            id=json_answers.get(id=ck).response.get(str(ques.id)))
                        one_response[str(ques.text)] = str(choice.text) if choice else str(choice)
                    elif ques.qtype in ['S', 'R', 'C'] and ques.master_choice == True:
                        mc = str(json_answers.get(id=ck).response.get(str(ques.id))).split(',')
                        master = MasterChoice.objects.get(question_id=ques.id)
                        if master.master_type == "FT":
                            ans = [i.name for i in Facility.objects.filter(Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                        elif master.master_type == "BF":
                            ans = [i.name for i in Beneficiary.objects.filter(Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                        one_response[str(ques.text)] =  ",".join(ans) if ans else ""
                    elif ques.qtype == 'C' and ques.master_choice == False:
                        mc = str(json_answers.get(id=ck).response.get(str(ques.id))).split(',')
                        ans = [i.text for i in Choice.objects.filter(id__in=mc,question=ques)]
                        one_response[str(ques.text)] =  ",".join(ans) if ans else ""
                    else:
                        one_response[str(ques.text)] = json_answers.get(
                            id=ck).response.get(str(ques.id))
                response_list.append(one_response)
            header_list.insert(0,cluster_head)
            data = response_list
            get_page = ceil(float(len(data)) / float(10))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(data, request)
            data = paginator.get_paginated_response(result_page, 2,'retrieved successfully', 34,  get_page).data
            data['header_list'] = header_list
            data['survey_name'] = survey.name
        except Exception as e:
            status = 0
            msg = e.message
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return Response({'status': status, 'msg': exc_tb.tb_lineno})
        return Response({'status': status, 'responses': response_list, 'header_list': header_list, 'survey_name': survey.name, })

    def get_cluster_info(self,cluster):
        replacer = {'facility':'facilities','boundary':'masterdata','beneficiary':'beneficiary'}
        cluster_key = cluster[0].keys()
        cluster_header = "/".join(cluster_key)
        cluster_string = []
        for ck in cluster_key:
            cluster_string.append(str(apps.get_model(replacer.get(ck),ck).objects.get_or_none(id=cluster[0][ck].get('id'))))
        cluster_string = "/".join(cluster_string)
        return {"cluster_string":cluster_string,"cluster_header":cluster_header}


class SurveyList(APIView):

    def get(self, request, user_id):
        survey_list = Survey.objects.select_related('data_entry_level__name').filter(active=2).order_by('order')
        data = [{'edit' : i.has_answers(),
                     'id' : i.id,
                     'name' : i.name,
                     'periodicity' : i.get_piriodicity_display(),
                     'form_level' : i.data_entry_level.name,
        }
        for i in survey_list]
        return Response({'status': 2, 'survey_list': data})

    def get_user_roles(self, user_id):
        user = User.objects.get(id=user_id)
        user_role = UserRoles.objects.get(user=user)
        role = [ur.slug for ur in user_role.role_type.all()]
        return {'role_list': role, 'is_admin': user.is_superuser}


class SurveyBlockList(APIView):

    def post(self, request):
        """
        Get Survey Blocks
        ---
        parameters:
        - name: survey_id
          description: Pass Survey Id
          required: true
          type: integer
          paramType: form
        """
        status = 2
        block_list = []
        data = request.data
        sid = data.get('survey_id')
        survey = None
        try:
            survey = Survey.objects.get(id=int(sid))
            block_list = Block.objects.filter(
                active=2, survey=survey).values('id', 'name')
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': 'Error while fetching Blocks', 'traceback_error': e.messge})
        return Response({'status': status, 'block_list': block_list, 'survey': survey.name})


class ResponseView(APIView):

    def post(self, request):
        """
        pass survey id and creation_key to get a response
        ---
        parameters:
        - name: survey_id
          description: Pass survey id
          required: true
          type: integer
          paramType: form
        - name: creation_key
          description: Pass creation key
          required: true
          type: string
          paramType: form
        - name: block_id
          description: pass block id for single level survey
          required: true
          type: integer
          paramType: integer
        - name: skip
          description: pass skip code here
          required: true
          type: integer
          paramType: integer
        - name: choice
          description: pass skip code here
          required: true
          type: integer
          paramType: integer
        - name: language_id
          description: pass language id here
          required: true
          type: integer
          paramType: integer
        """
        sid = int(request.data.get('survey_id'))
        creation_key = request.data.get('creation_key')
        block_id = request.data.get('block_id')
        skip = request.data.get('skip')
        choice = request.data.get('choice')
        lid = request.data.get('language_id')
        uid = request.data.get('user_id')
        status = 2
        res = {}
        try:
            survey = Survey.objects.get(id=sid)
            answers = JsonAnswer.objects.get(id=int(creation_key))
            res = {"formName": str(survey), "formLevel": str(survey.display_type),
                   "formId": survey.id,"language_id":lid}
            cluster = answers.cluster[0]
            cluster_name = ""
            if 'beneficiary' in cluster.keys():
                cluster_name = Beneficiary.objects.get(id=cluster['beneficiary']['id']).name
            elif 'facility' in cluster.keys():
                cluster_name = Facility.objects.get(id=cluster['facility']['id']).name
            else:
                cluster_name = Boundary.objects.get(id=cluster['boundary']['id']).name

            survey_blocks = Block.objects.filter(
                active=2, survey=survey).order_by('id')
            if str(survey.display_type) == "single":
                res['survey_id'] = sid
                if int(block_id) > 0:
                    res['next_block'] = survey_blocks.filter(id__gt=int(block_id)).order_by(
                        'id')[0].id if survey_blocks.filter(id__gt=int(block_id)) else 0
                    res['prev_block'] = survey_blocks.filter(id__lt=int(block_id)).order_by(
                        '-id')[0].id if survey_blocks.filter(id__lt=int(block_id)) else 0
                    survey_blocks = survey_blocks.filter(id=int(block_id))
                else:
                    res['next_block'] = survey_blocks[1].id
                    survey_blocks = survey_blocks.filter(id=survey_blocks[0].id)
            skip_code = {}
            res['is_skip'] = str(survey.is_skip_survey())
            if survey.is_skip_survey() and int(block_id) == 0:
                skip_code['code__lte'] = survey.identify_skip_question().code
                res['skipping_question'] = survey.identify_skip_question().id
                res['skipping_block'] = survey.identify_skip_question().block.id
                if survey.identify_skip_question().is_survey_regular_end_question():
                    res['next_block'] = 0
                survey_blocks = survey_blocks.filter(
                    id__lte=survey.identify_skip_question().block.id)
            if str(survey.display_type) == "single":
                if int(block_id) > 0:
                    res['next_block'] = survey_blocks.filter(id__gt=int(block_id))[
                        0].id if survey_blocks.filter(id__gt=int(block_id)) else 0
                    res['prev_block'] = survey_blocks.filter(id__lt=int(block_id)).order_by(
                        '-id')[0].id if survey_blocks.filter(id__lt=int(block_id)) else 0
                    survey_blocks = survey_blocks.filter(id=int(block_id))
                else:
                    res['next_block'] = survey_blocks[1].id
                    survey_blocks = survey_blocks.filter(id=survey_blocks[0].id)
            if survey.is_skip_survey() and int(block_id) > 0:
                survey_blocks = survey_blocks.filter(id__gte=block_id)
                next_ques = Question.objects.get(
                    id=skip,active=2).get_next_set_question(choice)
                skip_code['code__gte'] = next_ques.get('first').code
                skip_code['code__lte'] = next_ques.get('last').code
                res['skipping_question'] = next_ques.get('last').id
                survey_blocks = survey_blocks.filter(id__gte=next_ques.get(
                    'first').block.id, id__lte=next_ques.get('last').block.id)
                if next_ques.get('last').is_survey_end_question:
                    res['survey_end'] = "True"
                    res['next_block'] = 0
            blocks = []

            for i in survey_blocks:
                block_info = {"id": i.id, "name": str(i)}
                block_questions = Question.objects.filter(block__id=i.id,active=2, **skip_code).\
                    exclude(qtype='G')
                questions = []
                for question in block_questions:
                    ans = ""
                    q_validation = QuestionValidation.objects.get_or_none(question=question)
                    try:
                        if question.qtype == 'T' and question.master_choice == False :
                            ans = answers.response.get(str(question.id))

                        elif question.qtype in ['C','R','S','T'] and question.master_choice == True:
                            mc = str(answers.response.get(str(question.id))).split(',')
                            master = MasterChoice.objects.get(question_id=question.id)
                            if master.master_type == "FT":
                                try:
                                    ans = [{"id":str(i.id), "text": i.name } for i in Facility.objects.filter(Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                                except:
                                    ans = [{"id":str(i.id), "text": i.name } for i in Facility.objects.filter(Q(cry_admin_id__in=mc)|Q(uuid__in=mc))]
                            elif master.master_type == "BF":
                                try:
                                    ans = [{"id":str(i.id), "text": i.name } for i in Beneficiary.objects.filter(Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                                except:
                                    ans = [{"id":str(i.id), "text": i.name } for i in Beneficiary.objects.filter(Q(cry_admin_id__in=mc)|Q(uuid__in=mc))]
                        elif question.qtype == 'C' and question.master_choice == False:
                            mc = str(answers.response.get(str(question.id))).split(',')
                            ans = [{"id": i.id, "text": i.text} for i in Choice.objects.filter(id__in=mc,question=question)]

                        else:
                            ans = [answers.response.get(str(question.id)," ")]
                    except:
                        ans = " "
                    try:
                        partner_id = UserRoles.objects.get(user_id=int(uid)).partner.id
                    except:
                        partner_id = 0
                    question_dict = {"questionType": question.qtype,
                                     "questionMandatory": str(question.mandatory),
                                     "questionLabel": question.question_text_lang(lid),
                                     "questionId": question.id,
                                     "questionError": "", "questionAnswer": ans,
                                     "questionChoice": question.choice_list(partner_id,1),
                                     "mchoice":str(question.master_choice),
                                     }
                    try:
                        question_dict['constraints'] = {"charactersType":
                                                int(question.validation) if int(question.validation) >= 0 else ' ',
                                                    "question_validation":question.parent_id if question.parent_id else question.get_auto_fill_questions(),
                                                    "question_condition":q_validation.validation_condition if q_validation.validation_condition else ""}
                    except:
                        question_dict['constraints'] = {"charactersType":
                                                        question.validation if
                                                            question.validation >= 0 else ' ',
                                                    "question_validation": "",
                                                    "question_condition": ""
                                                    }
                    questions.append(question_dict)
                block_info["questions"] = questions
                blocks.append(block_info)
            res["blocks"] = blocks
        except Exception as e:
            status = 0
            msg = e.message
            return Response({'status': status, 'msg': msg})
        return Response({'status': status, 'res': res, 'creation_key': creation_key, 'task': 'update','cluster_name':cluster_name})


class CreateQuestion(APIView):

    def post(self, request):
        status = 2
        form_data = eval(str(request.body))
        block_id = form_data.get('blockId')
        try:
            block = Block.objects.get(id=block_id)
            survey_question_codes = Question.objects.filter(
                block__survey=block.survey).values_list('code', flat=True)
            if int(form_data.get('questionCode')) in survey_question_codes:
                 return Response({'status': 0, 'msg': 'Code already exist...', 'traceback_error': 'Code already exist...'})
            q = Question.objects.create(block=block, qtype=form_data.get('questionType'),
                                        text=form_data.get('questionLabel'),
                                        validation=form_data.get(
                                            'constraints').get('charactersType'),
                                        mandatory=eval(form_data.get(
                                            'questionMandatory')),
                                        code=form_data.get('questionCode'), order=form_data.get('questionCode'),
                                        is_profile=eval(form_data.get('questionProfile')),master_choice=eval(form_data.get('masterProfile')))
            if form_data.get('questionType') in ['S', 'C', 'R']:
                given_choices = form_data.get('questionChoice')
                for choice in given_choices:
                    Choice.objects.create(question=q,
                                          text=choice.get('choiceLabel'),
                                          order=choice.get('choiceValue'),
                                          code=choice.get('choiceShortCode'))
            if eval(form_data.get('masterProfile')) == True:
                MasterChoice.objects.create(question=q,
                                            master_type=form_data.get('categoryType')[0].get('type'),
                                            code=form_data.get('categoryType')[0].get('id'))
            if form_data.get('questionType') == 'T' and q.validation != 4  and eval(form_data.get('masterProfile')) == False:
                constraints = form_data.get('constraints')
                vald_cdtn = {'greather_than':'>','less_than':'<','greather_than_equal':'>=',\
                            'less_than_equal':'<=','equals':'==','not_equal':'!=','addition':'+',\
                            'subtract':'-','multiple':'*','divide':'/'}
                qv = QuestionValidation.objects.get_or_create(question=q,
                    min_value=constraints.get('minLength'),
                    max_value=constraints.get('maxLength'),
                    validation_type=constraints.get('validationOption'),
                    message=constraints.get('validationMessage'),
#                    validation_condition=constraints.get('question_condition'))
                    validation_condition=vald_cdtn.get(constraints.get('question_condition')))
                if int(q.validation) == 11:
                    qv.validation_condition = vald_cdtn.get(constraints.get('question_condition'))
                    qv.save()
                    q.parent_id = int(constraints.get('question_validation'))
                    q.save()
                elif int(q.validation) in [12,13]:
                    qustn,created = Questionautofill.objects.get_or_create(question=q)
                    qustn.question_auto_fill.clear()
                    qustn.save()
                    qustn.question_auto_fill.add(*constraints.get('question_validation'))
                    qustn.question_sequence = constraints.get('question_sequence')
                    qustn.save()
                    q.save()
            if form_data.get('questionType') == 'D' and q.validation == "8":
                constraints = form_data.get('constraints')
                QuestionValidation.objects.create(question=q,min_value=constraints.get('minDate'),\
                max_value=constraints.get('maxDate'),message=constraints.get('validationMessage'),\
                validation_condition=constraints.get('question_condition'))
                q.save()
            return Response({'status': status, 'msg': 'Question created Successfully','parent_id':q.parent_id,'id':q.id})
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': 'Error while creating Question', 'traceback_error': e.message})
        return Response({'status': status, 'msg': 'Question created Successfully'})


class GetBlockQuestions(APIView):
    def post(self, request):
        """
        Api to get questions of a block
        ---
        parameters:
        - name: block_id
          description: pass block id
          required: true
          type: integer
          paramType: integer
        """
        status = 2
        block = None
        try:
            block = Block.objects.get(id=int(request.data.get('block_id')))
            questions = Question.objects.filter(block=block).order_by('code').values(
                'id', 'text', 'qtype', 'validation', 'code', 'mandatory', 'is_profile','master_choice','active')
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': 'Error while fetching questions', 'traceback_error': e.message})
        return Response({'status': status, 'questions': questions, 'block': block.name})


class GetSurveyQuestions(APIView):

    def post(self, request):
        """
        Api to get Questions of survey
        ---
        parameters:
        - name: survey_id
          description: Pass survey id
          required: true
          type: integer
          paramType: integer
        """
        sid = int(request.data.get('survey_id'))
        status = 2
        try:
            survey = Survey.objects.get(id=sid)
            questions = Question.objects.filter(block__survey=survey,active=2).values('id', 'text')
            maincategory = [{"BF":"Beneficiary","FT":"Facility"}] ## capture type of beneficairy in question - from (added newly)
            subcategory = []
            subs = {}
            subs["BF"]=list(BeneficiaryType.objects.filter(active=2).values('id', 'name'))
            subs["FT"]=list(MasterLookUp.objects.filter(parent_id=261,active=2).values('id', 'name'))
            subcategory.append(subs) ## capture type of beneficairy in question - to
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': e.message})
        return Response({'status': status, 'questions': questions, 'maincategory':maincategory, 'subcategory':subcategory })


class GetQuestionDetail(APIView):

    def get(self, request, question_id):
        """
        Api to get particular question
        """

        status = 2
        try:
            Question.objects.get(id=int('question_id'),active=2)
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': 'Error while fetching question', 'traceback_error': e.message})
        return Response({'status': status})


class GetQuestionOptions(APIView):
    def get(self, request, question_id):
        """
        Api to get options of a question
        """
        question = None
        status = 2
        choice_list = []
        try:
            question = Question.objects.get(id=int(question_id),active=2)
            choice_list = Choice.objects.filter(question=question).values('id', 'text','active')
            for c, cl in enumerate(choice_list):
                choice_list[c]['skip_question'] = Choice.objects.get(
                    id=cl.get('id'),active=2).skip_question.all().ids()
            maincategory = [{"BF":"Beneficiary","FT":"Facility"}] ## capture type of beneficairy in question - from (added newly)
            subcategory = []
            subs = {}
            subs["BF"]=list(BeneficiaryType.objects.filter(active=2).values('id', 'name'))
            subs["FT"]=list(MasterLookUp.objects.filter(parent_id=261,active=2).values('id', 'name'))
            subcategory.append(subs)
            main = None
            sub = None
            if question.master_choice == True:
                mchoice = MasterChoice.objects.get(question=question,question__active=2)
                main = mchoice.master_type
                sub = mchoice.code ## capture type of beneficairy in question - to
                
        except Exception as e:
            status = 0
            return Response({'status': status, 'msg': 'Error fetching options', 'traceback_error': e.message})
        return Response({'status': status, 'choices': choice_list, \
        'question': question.text, 'maincategory':maincategory, 'subcategory':subcategory, 'maincategory_id':main, 'subcategory_id':sub, 'master_choice':question.master_choice })


class CreateQuestionOptions(generics.CreateAPIView):
    queryset = Choice.objects.filter(active=2)
    serializer_class = ChoiceSerializer

    def post(self, request):
        """
        API to create options for question
        """
        obj = ChoiceSerializer(data=request.data)
        if obj.is_valid():
            obj.save()
            return Response({'status': 2})
        else:
            return Response({'status': 0, 'errors': obj.errors})


class GetOption(generics.RetrieveUpdateAPIView):
    queryset = Choice.objects.filter(active=2)
    serializer_class = ChoiceSerializer
    lookup_field = 'id'

    def get(self, request, id):
        choice = Choice.objects.get(id=int(id),active=2)
        choice_attr = {}
        choice_attr['question'] = str(choice.question.id)
        choice_attr['text'] = choice.text
        choice_attr['code'] = choice.code
        choice_attr['order'] = choice.order
        choice_attr['survey'] = choice.question.block.survey.id
        return Response({'status': 2, 'choice': choice_attr})

    def perform_update(self, serializer):
        instance = serializer.save()
        return instance

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial', False)
        instance = self.get_object()
        response = {'status': 0, 'message': 'Something went wrong'}

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                'status': 2, 'message': 'Successfully updated the instance.', 'data': serializer.data}
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class DeoList(APIView):
    def get(self, request):
        deo_list = UserRoles.objects.filter(
            active=2, role_type__slug='data-entry-operator').distinct('partner').values_list('partner',flat=True)
        partner_list = Partner.objects.filter(id__in=deo_list)
        return Response({'status': 2, 'deo_list': [{'label': partner.name, 'value': partner.id} for partner in partner_list]})


class UserSurveyMap(generics.CreateAPIView):
    queryset = DetailedUserSurveyMap.objects.filter(active=2)
    serializer_class = UserSurveyMapSerializer

    def post(self, request):
        obj = UserSurveyMapSerializer(data=request.data)
        try:
            if obj.is_valid():
                get_object = None
                try:
                    partner = Partner.objects.filter(active=2)
                    get_object = DetailedUserSurveyMap.objects.get(
                        survey__id=request.data.get('survey'))
                    l = []
                    if type(eval(request.data.get('user').replace("+",""))) in [int]:
                        l.append(eval(request.data.get('user').replace("+","")))
                    partner_ids = [int(i) for i in eval(request.data.get('user').replace("+",""))]\
                        if type(eval(request.data.get('user').replace("+",""))) in [tuple, list] else l
                    partners = partner.filter(id__in=partner_ids)
                    partners_deo = []
                    for i in partners:
                        partners_deo.extend(i.get_deo())
                    get_object.user.add(*partners_deo)
                    get_object.level = request.data.get('level')
                    get_object.save()
                except Exception as e:
                    get_object = obj
                    get_object.save()
                return Response({'status': 2, 'msg': 'object created'})
            else:
                return Response({'status': 0, 'error_msg': obj.errors})
        except Exception as e:
            return Response({'status': 0, 'error_msg': e.message})

class GetUserSurveyMap(APIView):
    def get(self, request, survey_id):
        """
        API to get one DetailedUserSurveyMap
        """
        status = 2
        info = {}
        try:
            survey_map = DetailedUserSurveyMap.objects.get(
                survey__id=int(survey_id))
            info['survey'] = survey_map.survey.name
            info['user_list'] = survey_map.user.all().distinct('partner').values_list('partner',flat=True)

            info['level'] = survey_map.level
        except Exception as e:
            status = 0
            return Response({'status': status, 'error_msg': e.message, 'survey': Survey.objects.get(id=int(survey_id)).name})
        return Response({'status': status, 'info': info})


class GetFaciltyTypes(APIView):
    def get(self, request):
        """ API to get facility types """
        facility_types = MasterLookUp.objects.filter(
            parent__slug="facility-type").values('id', 'name')
        return Response({'status': 2, 'facility_types': facility_types})


class GetLocationTypes(APIView):
    def get(self, request):
        """ API to get location types  """
        location_types = LocationTypes.objects.filter(
            active=2).order_by('-id').values('id', 'level_name')
        return Response({'status': 2, 'location_types': location_types})

class GetDataEntryLevels(APIView):
    def get(self, request):
        """ API to get data entry levels  """
        data_entry_levels = DataEntryLevel.objects.filter(
            active=2).order_by('-id').values('id', 'name', 'slug')
        return Response({'status': 2, 'data_entry_levels': data_entry_levels})

class CreateSurvey(APIView):
    def post(self, request):
        """  API to create a survey   """

        res = {}
        res['status'] = 2
        try:
            form_data = eval(str(request.body))
            name = form_data.get('survey_name')
            display_type = form_data.get('display_type')
            data_entry_level = form_data.get('data_entry_level')
            periodicity = form_data.get('periodicity')
            expiry_age = form_data.get('expiry_age')
            is_profile = form_data.get('profile')
            blocks_info = form_data.get('blocks')
            is_auto_fill = False
            survey_auto_fill = False
            theme = MasterLookUp.objects.get(id=form_data.get('theme'))
            data_entry_level = DataEntryLevel.objects.get(
                slug=data_entry_level)
            sur = Survey.objects.create(**{'name': name, 'piriodicity': periodicity,
                                           'display_type': display_type, 'data_entry_level': data_entry_level, 'theme': theme,'is_auto_fill':is_auto_fill,'survey_auto_fill':survey_auto_fill})
            content_type_resolver = {
                'facility': 'facility', 'beneficiary': 'beneficiary', 'location': 'locationtypes'}
            content_type1 = ContentType.objects.get(
                model=content_type_resolver.get(data_entry_level.slug))
            object_id1 = form_data.get('object_id1')
            if data_entry_level.slug == 'facility' and not eval(is_profile):
                content_type2 = ContentType.objects.get(model='beneficiary')
                object_id2 = form_data.get('object_id2')
                SurveyDataEntryConfig.objects.create(**{'survey': sur,
                                                        'is_profile': eval(is_profile), 'content_type1': content_type1, 'object_id1': object_id1,
                                                        'content_type2': content_type2, 'object_id2': object_id2})
            else:
                SurveyDataEntryConfig.objects.create(**{'survey': sur,
                                                        'is_profile': eval(is_profile), 'content_type1': content_type1, 'object_id1': object_id1})
            for i in blocks_info:
                Block.objects.create(survey=sur, **i)
            res['message'] = 'Survey Created Successfully'
        except Exception as e:
            res['traceback_error'] = e.message
            res['status'] = 0
        return Response(res)

def get_user(u_id):
    try:
        return User.objects.get(id=u_id)
    except:
        return None

def get_user_partner(u_id):
    try:
        return UserRoles.objects.get(user__id=u_id).partner
    except:
        try:
            return UserPartnerMapping.objects.get(user__id=u_id).partner.filter(active=2).all()
        except Exception as e:
            return []

def get_user_partner_list(u_id):
    user = User.objects.get(id = u_id)
    if user.is_superuser:
        partner = Partner.objects.filter(active=2)
        return partner
    else:
        partner = UserRoles.objects.get(user__id=u_id).partner
        if partner:
            return [partner]
        else:
            try:
                return UserPartnerMapping.objects.get(user__id=u_id).partner.filter(active=2).all()
            except:
                return []

def check_if_previous_is_empty(sid, cluster, cid):
    survey = Survey.objects.get(id=sid)
    calling_methods = {'3': CustomDates().previous_month_days(),
                       '4': CustomDates().get_fy_last_quarter(int(FY_YEAR)),
                       '5': CustomDates().current_fy_half_year(),
                       '6': CustomDates().fy_dates(int(FY_YEAR)-1)}

    dates = calling_methods.get(survey.piriodicity)

    cluster_helper = {"cluster__0__" + cluster + "__id": int(cid)}
    responses = JsonAnswer.objects.filter(active=2,
        survey=survey, created__gte=dates.get('start_date'),
        created__lte=dates.get('end_date'), **cluster_helper)
    is_first_response = JsonAnswer.objects.filter(active=2,
        survey=survey, **cluster_helper)

    if responses or (not responses and (not is_first_response or is_first_response.count() < 1)):
        return False
    elif not responses: #and is_first_response.count() > 1:
        return True
    return True


def copy_get_last_periodicity_date(sid):
    survey = Survey.objects.get(id=sid)
    calling_methods = {'3': month_range(get_last_month_date()),
                       '4': get_last_quarter_dates(datetime.datetime.now()),
                       '5': get_last_half_yearly_dates(datetime.datetime.now()),
                       '6': get_last_yearly_months()}
    dates = calling_methods.get(survey.piriodicity)
    last_date = datetime.datetime.strptime(dates.get('last_date').strftime(
        '%Y-%m-%d') + " 0:0:0.1000", "%Y-%m-%d %H:%M:%S.%f")
    return last_date

def get_last_periodicity_date(sid):
    import datetime
    survey = Survey.objects.get(id=sid)
    calling_methods = {'3':CustomDates().previous_month_days(),
                       '4':CustomDates().get_fy_last_quarter(int(FY_YEAR)),
                       '5':CustomDates().current_fy_half_year(),
                       '6':CustomDates().fy_dates(int(FY_YEAR)-1)
                       }
    dates = calling_methods.get(survey.piriodicity)
    last_date = datetime.datetime.strptime(dates.get('end_date').strftime('%Y-%m-%d')+" 00:00:00.1000","%Y-%m-%d %H:%M:%S.%f")
    return last_date

def get_keys_from_cluster(cluster=None):
    keys = []
    for one_cluster in cluster:
        keys.append(one_cluster.keys())
    if 'beneficiary' in keys or ('beneficiary' in keys and 'facility' in keys ):
        return 'beneficiary'
    else:
        return keys[0]

class GetUserPartner(APIView):
    def get(self,request,user_id):
        try:
            user = UserRoles.objects.get(user__id=user_id)
            user_partner = []
            if user.user_type == 2:
                user_partner.append(user.partner)
        except:
            return Response({})

class MasterChoiceSearch(APIView):
    def get(self,request):
        data = []
        try:
            value = request.GET.get('key')
            partner = UserRoles.objects.get(user__id=int(request.GET.get('user_id'))).partner.id
            ques = Question.objects.get(id=request.GET.get('qid'),active=2)
            cluster = request.GET.get('cluster')
            cluster_data = eval(cluster)[0]
            if ques.master_choice == True:
                master = MasterChoice.objects.get(question_id=ques.id,question__active=2)
                if master.master_type == "FT":
                    data = [{"id":i.id, "text": i.name } \
                    for i in Facility.objects.filter(active = 2 , partner_id=partner,name__icontains=value,facility_type_id=int(master.code))]
                elif master.master_type == "BF":
                    household_survey_forms = SurveyDataEntryConfig.objects.get(survey_id = ques.block.survey.id)
                    if household_survey_forms.object_id1 == 2:
                        beneficiary_id = cluster_data.get('beneficiary').get('id')
                        data = [{"id":i.id, "text": i.name }for i in Beneficiary.objects.filter(partner_id=partner,name__icontains=value,beneficiary_type_id=int(master.code) , parent_id = int(beneficiary_id))]
                    else:
                        data = [{"id":i.id, "text": i.name } \
                    for i in Beneficiary.objects.filter(partner_id=partner,name__icontains=value,beneficiary_type_id=int(master.code))]
            else:
                data = []
        except Exception as e:
	    msg = str(e.message)	
            return Response({'status': 0,'messge':msg,'result':data})
        return Response({'status': 2,'messge':'Successfully Retreived','result':data})        

class ProfileViewWebApp(APIView):
    def get(self , request , cluster):
       #the request.POST = [{"beneficiary":{"beneficiary_type_id":2,"id":118029}}]
        cluster_data = eval(cluster)[0]
        request_data = cluster_data
        res = []
        if request_data.get('beneficiary'):
            beneficiary_id = request_data.get('beneficiary').get('id')
            p = ProfileView.objects.filter(ben_fac_loc_id = beneficiary_id)
            if len(p) == 0:
                res = []
            else:
                profile_info = p[0].profile_info
                for k,v in profile_info.items():
                    dic = {}
                    if str(k).isdigit():
                        dic.update({'label' : Question.objects.get(id = int(str(k))).text})
                        if v is None:
                            dic.update({'label_response' : ""})
                        else:
                            dic.update({'label_response' : v})
                    else:
                        dic.update({'label' : k})
                        dic.update({'label_response' : v})
                    res.append(dic)
        return Response({'status':2,'res':res})

class profileViewAndroidApp(APIView):
    serializer_class =  ProfileViewSerializer
    
    def post(self , request):
        modified_on = ''
        try:
            modified_on = request.data['modified_dates']
        except:
            pass
        date_object = convert_string_to_date(modified_on)
        if date_object is None:
            p = ProfileViewSerializer(ProfileView.objects.filter(partner_id = request.POST.get('partner_id')).order_by('modified')[:500],many=True)
        else:
            p = ProfileViewSerializer(ProfileView.objects.filter(modified__gt=date_object , partner_id = request.POST.get('partner_id')).order_by('modified')[:500],many=True)
       
        
        return JsonResponse({'status':2 , 'res' : p.data})
