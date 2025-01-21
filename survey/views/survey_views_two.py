from uuid import uuid4
import calendar
import datetime
from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps
from django.http import JsonResponse
from django.db.models import Max
from survey.serializers import *
from survey.models import *
from userroles.models import UserRoles,UserPartnerMapping
from masterdata.models import (MasterLookUp, Boundary, DocumentCategory)
from facilities.models import Facility
from workflow.models import WorkFlowBatch, WorkFlowSurveyRelation
from dynamic_listing.views import (get_quarter, month_range, get_last_quarter_dates,
                                   get_last_quarter_months, get_last_yearly_months, get_last_half_yearly_dates, get_last_month_date,)
from box import Box
from partner.models import Partner
from .custom_dates import CustomDates
from survey_views import get_user_partner,SurveyResponses
from .custom_dates import CustomDates
from common_methods import convert_list_args_to_str
import csv
from django.http import HttpResponse
from ccd.settings import HOST_URL,BASE_DIR,FY_YEAR
import pytz

class GetCluster(APIView):
    def get(self, request, survey_id, user_id):
        detaileduser = None
        try:
            detaileduser = DetailedUserSurveyMap.objects.get(
                active=2, survey__id=int(survey_id))
        except Exception as e:
            return Response({'status': 0, 'message': e.message})
        survey = Survey.objects.get(active=2, id=survey_id)
        userrole = UserRoles.objects.get(user__id=int(user_id))
        if not int(userrole.id) in detaileduser.user.all().ids():
            return Response({'status': 0, 'message': "User doesnt have permission to do data entry"})
        else:
            surveyconfig = None
            partner = get_user_partner(user_id)
            try:
                surveyconfig = SurveyDataEntryConfig.objects.get(
                    survey__id=int(survey_id))
            except Exception as e:
                return Response({'status': 0, 'message': e.message})
            if survey.data_entry_level.slug == 'facility' and not surveyconfig.is_profile:
                try:
                    facility = MasterLookUp.objects.get(
                        active=2, id=surveyconfig.object_id1)
                    beneficiary = BeneficiaryType.objects.get(
                        active=2, id=surveyconfig.object_id2)
                    cluster1 = apps.get_model('facilities', 'facility').objects.filter(
                        active=2, partner=partner, facility_type=facility).values('id', 'name')
                    cluster2 = apps.get_model('beneficiary', 'beneficiary').objects.filter(
                        active=2, partner=partner, beneficiary_type=beneficiary).values('id', 'name')
                    cl = [{'name': 'facility', 'facility_type_id': surveyconfig.object_id1, 'choice': cluster1}, {
                        'name': 'beneficiary', 'beneficiary_type_id': surveyconfig.object_id2, 'choice': cluster2}]
                    return Response({'status': 2, 'clusters': cl, 'survey_id': survey_id})
                except Exception as e:
                    return Response({'status': 0, 'message': 'Facility or Beneficiary doesnt exist', 'error': e.message})
            elif survey.data_entry_level.slug == 'location':
                state = partner.state
                locations = eval(get_required_level_info(state.id, 7).content).get('locations')
                locations = [self.add_address_level(loc) for loc in locations]
                return Response({'status': 2, 'clusters': [{'name': 'boundary', 'boundary_type_id': '0', 'choice': locations}], 'survey_id': survey_id})
            else:
                model_resolver = {'facility': 'facilities',
                                  'beneficiary': 'beneficiary'}
                field_resolver = {
                    'beneficiary': 'beneficiary_type_id', 'facility': 'facility_type_id'}
                survey_data_level = survey.data_entry_level.slug
                clusters = apps.get_model(model_resolver.get(survey_data_level), survey_data_level)\
                    .objects.filter(active=2, partner=partner, **{field_resolver.get(survey_data_level): surveyconfig.object_id1}).values('id', 'name')
                cl = [{'name': survey_data_level, field_resolver.get(
                    survey_data_level): surveyconfig.object_id1, 'choice': clusters}]
                return Response({'status': 2, 'clusters': cl, 'survey_id': survey_id})

    def add_address_level(self,obj):
        boundary = Boundary.objects.get(id=obj.get('id'))
        name = boundary.name+" / "+str(boundary.parent)+" / "+str(boundary.parent.parent) 
        obj['name']=name
        return obj


class UpdateQuestion(APIView):
    def post(self, request):
        form_data = eval(request.body)
        question = Question.objects.get(id=form_data.get('questionId'),active=2)
        codes = Question.objects.filter(block__survey=question.block.survey,active=2).\
            exclude(id=question.id).values_list('code', flat=True)
        if int(form_data.get('questionCode')) in codes:
            return Response({'status': 0, 'message': 'Code already exist'})
        question.qtype = form_data.get('questionType')
        question.text = form_data.get('questionText')
        question.validation = form_data.get('questionValidation')
        question.mandatory = eval(form_data.get('questionMandatory'))
        question.code = form_data.get('questionCode')
        question.is_profile = eval(form_data.get('questionProfile'))
        question.save()
        return Response({'status': 2, 'message': 'Question Updated Successfully'})

def delete_question_options(qid):
    Choice.objects.filter(question__id=qid).update(active=0)
    return True

class GetBeneficiaryRelatedSurvey(APIView):
    def get(self, request, bid):
        try:
            btype = Beneficiary.objects.get(id=bid)
            beneficiary_type = btype.beneficiary_type.id
            beneficiary_survey = SurveyDataEntryConfig.objects.filter(Q(Q(content_type1__model='beneficiary'), Q(object_id1=beneficiary_type)) | Q(
                Q(content_type2__model='beneficiary'), Q(object_id2=beneficiary_type))).values('survey_id', 'survey__name', 'is_profile')
            survey_list = []
            for i in beneficiary_survey:
                switch_profile = {True: "False", False: "True"}
                one_convert = {}
                one_convert['status'] = self.check_if_taken(
                    bid, i['survey_id'])
                one_convert['id'] = i['survey_id']
                one_convert['name'] = i['survey__name']
                one_convert['add_info'] = switch_profile.get(i['is_profile'])
                survey_list.append(one_convert)
            return Response({'survey_list': survey_list})
        except Exception as e:
            return Response({'survey_list': [], 'msg': e.message})

    def check_if_taken(self, bid, sid):
        survey = Survey.objects.get(id=sid)
        answers = JsonAnswer.objects.filter(active=2,
            survey=survey, cluster__0__beneficiary__id=int(bid))
        if not answers or int(survey.piriodicity) == 0:
            return "True"
        answers = answers.latest('created')
        time_delta = {'0': 'd', '1': 'd', '2': 'W',
                      '3': 'm', '4': 'm', '5': 'm', '6': 'y'}
        calling_methods = {'3': CustomDates().current_month_days(),
                           '4': CustomDates().current_fy_quarter_dates(),
                           '5': CustomDates().current_fy_half_year(),
                           '6': CustomDates().fy_dates(int(FY_YEAR))}

        dates = calling_methods.get(survey.piriodicity)
        utc=pytz.UTC

        current = datetime.datetime.now().strftime('%' + str(time_delta.get(survey.piriodicity)))
        previous = answers.created.strftime(
            '%' + str(time_delta.get(survey.piriodicity)))
        condition_list = [(int(current) == int(previous)) and (int(survey.piriodicity) <= 3),
                          (int(survey.piriodicity) == 4) and (
                              (int(previous) - int(current)) < 3),
                          (int(survey.piriodicity) == 5) and (
                              (int(previous) - int(current)) < 6),
                          (int(survey.piriodicity) == 6) and (
                              (int(previous) - int(current)) == 0)
                          ]
        if not answers.created < utc.localize(dates.get('start_date')):#True in condition_list:
            return "False"
        else:
            return "True"

class GetFacilityRelatedSurvey(APIView):
    def get(self, request, fid):
        facility = Facility.objects.get(id=fid)
        ftype = facility.facility_type.id
        facility_survey = SurveyDataEntryConfig.objects.filter(content_type1__model='facility', object_id1=ftype).exclude(
            content_type2__gt=0).values('survey_id', 'survey__name')
        survey_list = []
        for i in facility_survey:
            one_convert = {}
            one_convert['status'] = self.check_if_taken(i['survey_id'], fid)
            one_convert['id'] = i['survey_id']
            one_convert['name'] = i['survey__name']
            survey_list.append(one_convert)
        return Response({"survey_list": survey_list})

    def check_if_taken(self, sid, fid):
        survey = Survey.objects.get(id=sid)
        answers = JsonAnswer.objects.filter(active=2,
            survey=survey, cluster__0__facility__id=int(fid))
        if not answers or int(survey.piriodicity) == 0:
            return "True"
        answers = answers.latest('created')
        time_delta = {'0': 'd', '1': 'd', '2': 'W',
                      '3': 'm', '4': 'm', '5': 'm', '6': 'y'}
        current = datetime.datetime.now().strftime('%' + str(time_delta.get(survey.piriodicity)))
        previous = answers.created.strftime(
            '%' + str(time_delta.get(survey.piriodicity)))
        condition_list = [(int(current) == int(previous)) and (int(survey.piriodicity) <= 3),
                          (int(survey.piriodicity) == 4) and (
                              (int(previous) - int(current)) < 3),
                          (int(survey.piriodicity) == 5) and (
                              (int(previous) - int(current)) < 6),
                          (int(survey.piriodicity) == 6) and (
                              (int(previous) - int(current)) == 0)
                          ]
        if True in condition_list:
            return "False"
        else:
            return "True"

class GetExtendedProfileDetails(GetBeneficiaryRelatedSurvey, GetFacilityRelatedSurvey, APIView):
    def get(self, request, related_type, object_id):
        related_type_helper = {'facility': GetFacilityRelatedSurvey(),
                               'beneficiary': GetBeneficiaryRelatedSurvey()}
        survey_list = related_type_helper.get(related_type).get(
            self.request, object_id).data.get('survey_list')
        thematic_response = {}
        thematics_list = []
        for survey_resp in survey_list:
            survey = Survey.objects.get(id=survey_resp.get('id'))
            extended_profile_question = survey.get_extended_profile_questions()
            latest_response = JsonAnswer.objects.filter(active=2,
                survey=survey, **{'cluster__0__' + related_type + '__id': int(object_id)})
            if latest_response:
                thematics_list.append(str(survey.theme))
                latest_response = latest_response.latest('created')
                survey_list = []
                for epq in extended_profile_question:
                    survey_list.append(self.get_question_answer_dict(epq,latest_response))
                if thematic_response.get(str(survey.theme)):
                    themeatic_prev_resp = thematic_response[str(survey.theme)]
                    themeatic_prev_resp.extend(survey_list)
                    thematic_response[str(survey.theme)] = themeatic_prev_resp
                else:
                    thematic_response[str(survey.theme)] = survey_list
        return Response({'status': 2, 'response': thematic_response, 'thematics': list(set(thematics_list))})

    def get_question_answer_dict(self,epq,latest_response):
        thematic_dic = {}
        if epq.qtype in ['T', 'D']:
            thematic_dic['question'] = str(epq.text)
            try:
                thematic_dic['answer'] = str(
                    latest_response.response[str(epq.id)])
            except:
                thematic_dic['answer'] = ""
        elif epq.qtype in ['S', 'R']:
            choice_text = Choice.objects.get_or_none(
                id=latest_response.response[str(epq.id)],active=2)
            thematic_dic['question'] = str(epq.text)
            thematic_dic['answer'] = str(choice_text.text) if choice_text else str(choice_text)
        return thematic_dic


class GetBoundaryLevelData(APIView):
    def get(self, request, bid, lid):
        return get_required_level_info(bid, lid)

def get_required_level_info(bid, lid):
    try:
        required_level = int(lid)
        boundary_objects = Boundary.objects.filter(active=2)
        present_boundary = boundary_objects.get(id=bid)
        present_level = int(present_boundary.boundary_level)
        locations = []
        if required_level < 0 or required_level > 7:
            return JsonResponse({'status': 0, 'msg': 'Invalid level reqested..'})
        elif int(required_level) == present_level:
            locations = boundary_objects.filter(
                active=2, parent=present_boundary.parent).values('id', 'name')
            return JsonResponse({'status': 2, 'locations': [], 'msg': 'same levels'})
        elif int(required_level) > present_level:  # 2 to 7 ,
            next_level_objects = [present_boundary.id]
            while present_level <= required_level:
                if required_level == present_level:
                    locations = list(boundary_objects.filter(
                        id__in=next_level_objects).values('id', 'name','object_id'))
                    break
                else:
                    next_level_objects = boundary_objects.filter(
                        parent__id__in=next_level_objects).values_list('id', flat=True)
                    present_level = present_level + 1
            return JsonResponse({'status': 2, 'locations': list(locations), 'msg': 'to get lower levels'})
        elif int(required_level) < present_level:  # 7 to 2
            return JsonResponse({'status': 2, 'locations': upper_level(required_level,present_level,[present_boundary.id],boundary_objects), 'msg': 'to get upper levels'})
    except Exception as e:
        return JsonResponse({'status': 0, 'msg': e.message})

def upper_level(required_level,present_level,upper_level_objects,boundary_objects):
    while required_level <= present_level:
        if required_level == present_level:
            return list(boundary_objects.filter(
                id__in=upper_level_objects).values('id', 'name','object_id'))
        else:
            upper_level_objects = boundary_objects.filter(
                id__in=upper_level_objects).values_list('parent_id', flat=True)
            present_level = present_level - 1


class GetQuestionValidation(APIView):
    def get(self, request, qid):
        try:
            question = Question.objects.get(id=qid,active=2)
            try:
                question_validation = QuestionValidation.objects.get(
                    question__id=qid)
                validation = {
                    'questionValidation': question.validation,
                    'minLength': question_validation.min_value,
                    'maxLength': question_validation.max_value,
                    'validationOption': question_validation.validation_type,
                    'validationMessage': question_validation.message,
                    'question_condition':question_validation.get_validation_condition_display(),
                    'question_validation':question.parent_id if question.validation == 11 else question.get_auto_fill_questions(),
                }
                return Response({'status': 2, 'validation': validation, 'question_id': qid})
            except Exception as e:
                validation = {
                    'questionValidation': question.validation,
                    'minLength': '',
                    'maxLength': '',
                    'validationOption': '',
                    'validationMessage': '',
                    'questionCondition':'',
                    'questionValidation':''
                }
                return Response({'status': 2, 'validation': validation, 'question_id': qid})
        except Exception as e:
            return Response({'status': 0, 'msg': e.message})


class UpdateQuestionValidation(APIView):
    def post(self, request):
        constraints = eval(request.body).get('constraints')
        # update the validation for the question
        question = Question.objects.get(id=constraints.get('questionId'),active=2)
        previous_validation = question.validation
        question.validation = constraints.get('questionValidation')
        question.save()
        # update the question validation for the question
        if question.validation != 4:
            qv, qc = QuestionValidation.objects.get_or_create(question=question)
            qv.min_value = constraints.get('minLength')
            qv.max_value = constraints.get('maxLength')
            qv.validation_type = constraints.get('validationOption')
            qv.message = constraints.get('validationMessage')
            qv.save()
            vald_cdtn = {'greather_than':'>','less_than':'<','greather_than_equal':'>=',\
                            'less_than_equal':'<=','equals':'==','not_equal':'!=','addition':'+',\
                            'subtract':'-','multiple':'*','divide':'/'}
            if int(question.validation) == 11:
                question.parent_id= int(constraints.get('question_validation'))
                question.save()
            elif int(question.validation) in [12,13]:
#                question.question_auto_fill.clear()
                qv.validation_condition = vald_cdtn.get(constraints.get('question_condition'),'')
                qv.save()
                qustn,created = Questionautofill.objects.get_or_create(question=question)
                qustn.question_auto_fill.clear()
                qustn.question_sequence = ""
                qustn.save()
                qustn.question_auto_fill.add(*constraints.get('question_validation'))
                qustn.question_sequence = constraints.get('question_sequence')
                qustn.save()
                #question.save()
    		question.save()
        elif previous_validation != 4 and question.validation == 4:
            QuestionValidation.objects.filter(question=question).delete()
        return Response({'status': 2, 'msg': 'Updated Successfully'})

class GetSkipQuestion(APIView):
    def get(self, request, qid, sid):
        survey_questions = Question.objects.filter(block__survey__id=sid)
        given_question = survey_questions.get(id=qid)
        next_questions = survey_questions.filter(code__gt=given_question.code).\
            values('id', 'text').order_by('code')
        return Response({'status': 2, 'skip_questions': next_questions})

class GetSurvey(APIView):
    def get(self, request, sid):
        try:
            survey = Survey.objects.get(id=sid)
            surveydataentry = SurveyDataEntryConfig.objects.get(survey=survey)
            survey_details = {}
            survey_details['name'] = survey.name
            survey_details['data_entry_level'] = survey.data_entry_level.slug
            survey_details['periodicity'] = survey.piriodicity
            survey_details['expiry_age'] = survey.expiry_age
            survey_details['display_type'] = survey.display_type
            survey_details['theme'] = survey.theme.id
            survey_details['is_profile'] = surveydataentry.is_profile
            survey_details['object_id1'] = surveydataentry.object_id1
            survey_details['object_id2'] = surveydataentry.object_id2
            survey_details['blocks'] = Block.objects.filter(
                survey=survey).values('id', 'name', 'order')
            return Response({'status': 2, 'survey_details': survey_details})
        except Exception as e:
            return Response({'status': 0, 'message': 'Survey doesnt exist', 'error': e.message})

class UpdateSurvey(APIView):

    def post(self, request):
        """  API to update a survey  """

        res = {}
        res['status'] = 2
        try:
            form_data = eval(str(request.body))
            sid = form_data.get('survey_id')
            name = form_data.get('survey_name')
            display_type = form_data.get('display_type')
            form_data.get('expiry_age')
            data_entry_level = form_data.get('data_entry_level')
            periodicity = form_data.get('periodicity')
            is_profile = form_data.get('profile')
            theme = MasterLookUp.objects.get(id=form_data.get('theme'))
            is_auto_fill = form_data.get('is_auto_fill',False)
            survey_auto_fill = False
            data_entry_level = DataEntryLevel.objects.get(
                slug=data_entry_level)
            sur = Survey.objects.filter(id=sid)
            sur.update(**{'name': name, 'piriodicity': periodicity,
                          'display_type': display_type, 'data_entry_level': data_entry_level,
                          'theme': theme, 'is_auto_fill':is_auto_fill,'survey_auto_fill':survey_auto_fill})
            blocks = form_data.get('blocks')
            for i in blocks:
                if i['id'] == 'create':
                    i.pop('id')
                    Block.objects.create(survey=sur[0], **i)
                else:
                    Block.objects.filter(id=i['id']).update(**i)
            Block.objects.filter(
                id__in=form_data.get('deleted_blocks')).delete()
            content_type_resolver = {
                'facility': 'facility', 'beneficiary': 'beneficiary', 'location': 'locationtypes'}
            content_type1 = ContentType.objects.get(
                model=content_type_resolver.get(data_entry_level.slug))
            object_id1 = form_data.get('object_id1')

            if data_entry_level.slug == 'facility' and not eval(is_profile):
                # create content type for only facility

                content_type2 = ContentType.objects.get(model='beneficiary')
                object_id2 = form_data.get('object_id2')
                SurveyDataEntryConfig.objects.filter(survey__id=sid).update(**{
                    'is_profile': eval(is_profile), 'content_type1': content_type1, 'object_id1': object_id1,
                    'content_type2': content_type2, 'object_id2': object_id2})
            else:
                SurveyDataEntryConfig.objects.filter(survey__id=sid).update(**{
                    'is_profile': eval(is_profile), 'content_type1': content_type1, 'object_id1': object_id1})
                SurveyDataEntryConfig.objects.filter(survey__id=sid).update(
                    **{'content_type2': '', 'object_id2': 0})
            res['message'] = 'Survey updated successfully'
        except Exception as e:
            res['traceback_error'] = e.message
            res['status'] = 0
        return Response(res)

class ConfigSkip(APIView):
    def post(self, request):
        """ API to configure skip questions """
        form = eval(request.body)
        for i in form:
            choice = Choice.objects.get(id=i.get('id'),active=2)
            choice.skip_question.clear()
            choice.skip_question = i.get('skip_questions')
            choice.save()
        return Response({'status': 2, 'message': 'Skip Configured'})

class PeriodicityValidateNew(APIView):
    def get(self, request, sid, cluster):
        survey = Survey.objects.get(id=sid)
        cluster = eval(cluster)[0]
        cluster_query = {}

        if 'beneficiary' in cluster.keys():
            cluster_query['cluster__0__beneficiary__contains'] = cluster[
                'beneficiary']
        elif 'facility' in cluster.keys():
            cluster_query['cluster__0__facility__contains'] = cluster[
                'facility']
        else:
            cluster_query['cluster__0__boundary__contains'] = cluster[
                'boundary']
        answers = JsonAnswer.objects.filter(active=2,survey=survey, **cluster_query)
        if not answers or int(survey.piriodicity) == 0:
            return Response({'status': 2})
        answers = answers.latest('created')
        time_delta = {'0': 'd', '1': 'd', '2': 'W',
                      '3': 'm', '4': 'm', '5': 'm', '6': 'y'}
        current = datetime.datetime.now().strftime('%' + str(time_delta.get(survey.piriodicity)))
        previous = answers.created.strftime(
            '%' + str(time_delta.get(survey.piriodicity)))
        condition_list = [(int(current) == int(previous)) and (int(survey.piriodicity) <= 3),
                          (int(survey.piriodicity) == 4) and (
                              (int(previous) - int(current)) < 3),
                          (int(survey.piriodicity) == 5) and (
                              (int(previous) - int(current)) < 6),
                          (int(survey.piriodicity) == 6) and (
                              (int(previous) - int(current)) == 0)
                          ]
        if True in condition_list:
            return Response({'status': 0, 'message': 'Response has been already submitted...'})
        else:
            return Response({'status': 2})

class PeriodicityValidate(APIView):
    def get(self,request,sid,cluster):
        try:
            survey = Survey.objects.get(id=sid)
            calling_methods = {'3': CustomDates().current_month_days(),
                               '4': CustomDates().get_fy_last_quarter(int(FY_YEAR)),
                               '5': CustomDates().current_fy_half_year(),
                               '6': CustomDates().fy_dates(int(FY_YEAR))}
            periodicity_dates = calling_methods.get(survey.piriodicity)
            cluster = eval(cluster)[0]
            cluster_query = {}
	    cluster_name = ""
            if 'beneficiary' in cluster.keys():
                cluster_query['cluster__0__beneficiary__contains'] = cluster[
                    'beneficiary']
                cluster_name = Beneficiary.objects.get(id=cluster['beneficiary']['id']).name
            elif 'facility' in cluster.keys():
                cluster_query['cluster__0__facility__contains'] = cluster[
                    'facility']
                cluster_name = Facility.objects.get(id=cluster['facility']['id']).name
            else:
                cluster_query['cluster__0__boundary__contains'] = cluster[
                    'boundary']
                cluster_name = Boundary.objects.get(id=cluster['boundary']['id']).name
            answers = JsonAnswer.objects.filter(active=2,created__gte=periodicity_dates.get('start_date'),
                            created__lte=periodicity_dates.get('end_date'),
                            survey=survey, **cluster_query).exists()
            if not answers:
                return Response({'status':2,'cluster_name':cluster_name})
            return Response({'status':0, 'message':'Response has been already submitted...'})
        except Exception as e:
            return Response({'status':0, 'message':'Response has been already submitted...'})


class GetResponse(APIView):
    def get(self, request, bid):
        wfb = WorkFlowBatch.objects.get(id=bid)
        skip_questions = list(set(Choice.objects.filter(
            question__block__survey=wfb.current_status.survey,active=2).values_list('skip_question', flat=True)))
        skip_questions.remove(None)
        survey_questions = Question.objects.filter(active=2,block__survey=wfb.current_status.survey).exclude(
            id__in=skip_questions).values_list('id', 'text', 'qtype')[:5]
        DocumentCategory.objects.create(name=str(survey_questions))
        json_answers = JsonAnswer.objects.filter(active=2,
            id__in=wfb.response_ids).values_list('response', flat=True)
        responses = []
        display_headers = [i[1] for i in survey_questions]
        for j in json_answers:
            one_res = {}
            for i in survey_questions:
                if i[2] in ['R', 'S']:
                    get_choice = Choice.objects.get_or_none(
                        id=j.get(str(i[0])),active=2)
                    if get_choice:
                        one_res[i[1]] = get_choice.text
                else:
                    one_res[i[1]] = j.get(str(i[0]))
            responses.append(one_res)
        return Response({'status': 2, 'data': responses, 'headers': display_headers, 'display_headers': display_headers})

class GetAdditionalFacilityInfo(APIView):
    def get(self, request, uid, sid):
        try:
            partner = get_user_partner(uid)
            srvdatacnfg = SurveyDataEntryConfig.objects.get(survey__id=sid)
            if not srvdatacnfg.is_profile:
                facilities = Facility.objects.filter(
                    partner=partner, facility_type__id=srvdatacnfg.object_id1).values('id', 'name')
                cl = [
                    {'name': 'facility', 'facility_type_id': srvdatacnfg.object_id1, 'choice': facilities}]
                return Response({'status': 3, 'clusters': cl, 'survey_id': srvdatacnfg.survey.id})
            return Response({'status': 2})
        except:
            return Response({'status': 0})

class CheckUserPermission(APIView):
    def get(self, request, sid, uid):
        detaileduser = DetailedUserSurveyMap.objects.get(
            active=2, survey__id=int(sid))

        userrole = UserRoles.objects.get(user__id=int(uid))
        if not int(userrole.id) in detaileduser.user.all().ids():
            return Response({'status': 0, 'message': "User doesnt have permission to do data entry"})
        else:
            return Response({'status': 2})

class GetPartnerExtensionParameters(APIView):
    def get(self, request, spid):
        exisurvey = SurveyPartnerExtension.objects.all().exclude(
            id=spid).values_list('survey_id', flat=True)
        partner_list = Partner.objects.filter(active=2).values('id', 'name')
        for i, v in enumerate(partner_list):
            partner_list[i]['label'] = v.get('name')
            partner_list[i]['value'] = v.get('id')
            del partner_list[i]['name']
            del partner_list[i]['id']
        survey_list = Survey.objects.filter(active=2).exclude(
            id__in=exisurvey).values('id', 'name')
        return Response({'status': 2, 'partner_list': partner_list, 'survey_list': survey_list})

class CreatePartnerExtension(APIView):
    def post(self, request):
        """
        Api to create PartnerExtension for a partner
        ---
        parameters:
        - name: survey
          description: Pass survey id
          required: true
          type: integer
          paramType: integer
        - name: partner
          description: Pass list of user ids
          required: true
          type: list
          paramType: list
        - name: expiry_age
          description: pass extended age
          required: true
          type: integer
          paramType: integer
        """
        create_query = {}
        partner = [Partner.objects.get(id=i)
                   for i in eval(request.data.get('partner'))]
        create_query['survey'] = Survey.objects.get(
            id=request.data.get('survey'))
        create_query['expiry_age'] = request.data.get('expiry_age')
        spe = SurveyPartnerExtension(**create_query)
        spe.save()
        spe.partner = partner
        spe.save()
        return Response({'status': 2})

class PartnerExtensionDetail(APIView):
    def get(self, request, spid):
        spe = SurveyPartnerExtension.objects.get(id=spid)
        return Response({'status': 2, 'survey': spe.survey.id, 'partner': spe.partner.all().ids(), 'expiry_age': spe.expiry_age})

class PartnerExtensionUpdate(APIView):
    def post(self, request):
        """ API to update the survey partner extension
        ---
        parameters:
        - name: id
          description: Pass survey partner extension id
          required: true
          type: integer
          paramType: integer
        - name: survey
          description: Pass survey id here
          required: true
          type: integer
          paramType: integer
        - name: partner
          description: Pass partner id
          required: true
          type: integer
          paramType: integer
        - name: expiry_age
          description: Pass expiry age
          required: true
          type: integer
          paramType: integer
        """
        try:
            spe = SurveyPartnerExtension.objects.get(id=request.data.get('id'))
            spe.survey = Survey.objects.get(id=request.data.get('survey'))
            spe.partner = [Partner.objects.get(
                id=i) for i in eval(request.data.get('partner'))]
            spe.expiry_age = int(request.data.get('expiry_age'))
            spe.save()
            return Response({'status': 2, 'message': 'Updated successfully...'})
        except Exception as e:
            return Response({'status': 0, 'message': e.message})

class SurveyPartnerExtensionListing(APIView):
    def get(self, request):
        spe_list = SurveyPartnerExtension.objects.filter(
            active=2).values('id', 'survey__name')
        for i, v in enumerate(spe_list):
            spe_list[i]['name'] = v['survey__name']
            del spe_list[i]['survey__name']
        return Response({'status': 2, "spe_list": spe_list})

class GetFilterRelatedSurvey(APIView):
    def get(self, request, model_name, object_id):
        survey_list = []
        if model_name == 'beneficiary':
            survey_list = SurveyDataEntryConfig.objects.filter(Q(Q
                                                                 (content_type1__model='beneficiary'), Q(object_id1=object_id))
                                                               | Q(Q(content_type2__model='beneficiary'),
                                                                   Q(object_id2=object_id))).values('survey_id', 'survey__name')
        elif model_name == 'facility':
            survey_list = SurveyDataEntryConfig.objects.filter(
                content_type1__model='facility', object_id1=object_id).exclude(
                content_type2__gt=0).values('survey_id', 'survey__name')
        return Response({'status': 2, 'survey_list': survey_list})

def get_regional_states(region_id):
    boundary = Boundary.objects.filter(region__id=region_id).values('id','name')
    return {'boundary':boundary}

def get_regional_partner(region_id):
    boundary = Boundary.objects.filter(region__id=region_id).values_list('id',flat=True)
    regional_partners = Partner.objects.filter(state__id__in=boundary,active=2).values('id','name')
    return {'regional_partners':regional_partners}

class GetResponseDraftView(APIView):
    def get(self,request,response_id):
        try:
            json_answer = JsonAnswer.objects.get(id=response_id)
            survey_id = json_answer.survey.id
            questions = Question.objects.filter(active=2,block__survey__id=survey_id).order_by('code')
            resp_dic = get_response_dict(json_answer,questions)
            return Response({'status':2,'response':resp_dic})
        except Exception as e:
            return Response({'status':0,'msg':e.message})

def get_response_dict(json_answer,questions):
    one_response = []
    for ques in questions:
        if ques.qtype in ['S', 'R'] and ques.master_choice == False and json_answer.response.get(str(ques.id)):
            choice = Choice.objects.get_or_none(id=json_answer.response.get(str(ques.id)),active=2)
            one_response.append((str(ques.text) ,str(choice.text) if choice else str(choice)))
        elif ques.qtype in ['C','R','S','T'] and ques.master_choice == True and json_answer.response.get(str(ques.id)):
            mc = str(json_answer.response.get(str(ques.id))).split(',')
            master = MasterChoice.objects.get(question_id=ques.id,active=2)
            if master.master_type == "FT":
                try:
                    ans = [i.name for i in Facility.objects.filter(Q(uuid__in=mc)|Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                except:
                    ans = [i.name for i in Facility.objects.filter(Q(uuid__in=mc)|Q(cry_admin_id__in=mc))]
                if ans:
                    ans = ",".join(ans)
                else:
                    ans = ""
                one_response.append((str(ques.text) ,ans))
            elif master.master_type == "BF":
                try:
                    ans = [i.name for i in Beneficiary.objects.filter(Q(uuid__in=mc)|Q(cry_admin_id__in=mc)|Q(id__in=mc))]
                except:
                    ans = [i.name for i in Beneficiary.objects.filter(Q(uuid__in=mc)|Q(cry_admin_id__in=mc))]
                if ans:
                    ans = ",".join(ans)
                else:
                    ans = ""
                one_response.append((str(ques.text) ,ans))
        elif ques.qtype == 'C' and ques.master_choice == False and json_answer.response.get(str(ques.id)):
            mc = str(json_answer.response.get(str(ques.id))).split(',')
            ans = [i.text for i in Choice.objects.filter(id__in=mc,question=ques,active=2)]
            if ans:
                ans = ",".join(ans)
            else:
                ans = ""
            one_response.append((str(ques.text) ,ans))
        else:
            one_response.append((str(ques.text),json_answer.response.get(str(ques.id))))
    return one_response


class GetRegionalStates(APIView):
    def get(self,request,region):
        try:
            region = MasterLookUp.objects.get(slug=region)
            region_dict = {}
            if region.slug != 'national-ho':
                region_dict['region']=region
            states = Boundary.objects.filter(active=2,boundary_level=2,**region_dict).order_by('name').values('id','name')
            return Response({'status':2,'states':states})
        except Exception as e:
            return Response({'status':0,'msg':'Invalid Region','error':e.message})

class AutoQuestionCode(APIView):
    def get(self,request,form_id):
        next_code = None
        try:
            next_code = (int(Question.objects.filter(block__survey__id=form_id).aggregate(Max('code')).get('code__max')))+1
        except:
            next_code = 101
        return Response({'status':2,'auto_qcode':next_code})

class LanguageList(APIView):
    def get(self,request):
        languages = Language.objects.filter(active=2).exclude(name="English").values('id','name')
        return Response({'status':2,'languages':languages})

class BatchPivotView(APIView):

    def get(self,request,batch_id):

        workflow = WorkFlowBatch.objects.get(id=batch_id)
        profile_questions = Question.objects.filter(active=2,block__survey=workflow.current_status.survey,is_profile=True).order_by('code')
        if not profile_questions:
            profile_questions = Question.objects.filter(active=2,block__survey=workflow.current_status.survey).order_by('code')[:5]

        json_answers = JsonAnswer.objects.filter(active=2,id__in=workflow.response_ids).values_list('response',flat=True)
        json_answers = JsonAnswer.objects.filter(active=2,id__in=workflow.response_ids)
        pivot_view = self.convert_json_to_pivot_response(json_answers,profile_questions)
        pivot_view_keys = pivot_view[0].keys()
        dimensions = [{'value':i,'title':i} for i in pivot_view_keys]
        return Response({'status':2,'pivot_view':pivot_view,'dimensions':dimensions})

    def convert_json_to_pivot_response(self,json_responses,questions):
        pivot_response = []
        for response in json_responses:
            one_res = {}
            one_res['user']=str(response.user)

            for question in questions:
                if question.qtype in ['S','R','C']:
                    one_res[question.text] = question.choice_dict()[response.response[str(question.id)]]
                else:
                    one_res[question.text]=response.response[str(question.id)]
            pivot_response.append(one_res)
        return pivot_response

class StatePartnerList(APIView):
    def post(self,request):
        """
        Get Partners of state
        ---
        parameters:
        - name: state_id
          description: pass state ids to get the partners
          required: true
          type: list
          paramType: list
        - name: user_id
          description: pass the user id here
          required: true
          type: integer
          paramType: integer
        """
        partners_list = UserPartnerMapping.objects.get(user_id=request.data.get('user_id')).partner.all()
        partners = partners_list.filter(active=2,state__id__in=eval(request.data.get('state_id'))).values('id','name','state')
        return Response({'status':2,'partner':partners})

class FormExport(APIView):
    def get(self,request,form_id,user_id):
        partner = None
        try:
            partner = UserRoles.objects.get(user_id=user_id).partner
            if not partner:
                raise Exception('No Partner')
        except Exception as e:
            return Response({'status':0,'message':'User dont have permission to export..'})
        partner_user = partner.get_partner_deo()
        survey = Survey.objects.get(id=form_id)
        file = open(BASE_DIR+'/static/response_csv/'+str(survey)+"_"+str(partner.id)+".csv","w+")
        file_name = str(file.name).split('/')[-1]
        csv_writer = csv.writer(file)
        questions = Question.objects.filter(active=2, block__survey=survey).order_by('code')
        headers_list = list(questions.values_list('text',flat=True))
        headers_list.insert(0,str(survey.data_entry_level))
        csv_writer.writerow(headers_list)
        json_answers = JsonAnswer.objects.filter(active=2,survey=survey,user__id__in=partner_user)
        answers = json_answers.order_by('-id').values_list('id',flat=True)
        for ck in answers:
            one_answer = json_answers.get(id=ck)
            one_response = []
            cluster = SurveyResponses().get_cluster_info(one_answer.cluster).get('cluster_string')
            one_response.append(cluster)
            for q in questions:
                if q.qtype in ['S', 'R', 'C']:
                    choice = Choice.objects.get_or_none(
                        id=one_answer.response.get(str(q.id)),active=2)
                    one_response.append(str(choice.text) if choice else str(choice))
                else:
                    one_response.append(one_answer.response.get(str(q.id)))
            csv_writer.writerow(one_response)
        file.close()
        return Response({'status':2,'download':HOST_URL+'/static/response_csv/'+file_name})

class GetRegionalTranslations(APIView):
    def get(self,request,model_name,object_id):
        try:
            model_class = ContentType.objects.get(model=model_name).model_class()
            model_object = model_class.objects.get(id=object_id)
            language_trans = model_object.translation_text()
            return Response({'status':2,'translation_text':language_trans,'name':model_object.text})
        except Exception as e:
            return Response({'status':0,'message':e.message})

class RegionalTranslations(APIView):
    def post(self,request):
        """
        API to save the translations
        ---
        parameters:
        - name: model_name
          description: pass the model name as per the content type
          required: true
          type: string
          paramType: string
        - name: object_id
          description: pass the object id
          required: true
          type: integer
          paramType: integer
        - name: translation_text
          description: pass the translation dictionary
          required: true
          type: dictionary
          paramType: dictionary
        """
        try:
            model_class = ContentType.objects.get(model=request.data.get('model_name')).model_class()
            model_object = model_class.objects.get(id=request.data.get('object_id'))
            translations = eval(request.data.get('translation_text'))
            translation_dict = {}
            for translation in translations:
                translation_dict[translation.get('id')]=translation.get('text')
            model_object.language_code = translation_dict
            model_object.save()
            return Response({'status':2,'message':'Language Translations added successfully...'})
        except Exception as e:
            return Response({'status':0,'message':'Something went wrong...'})

class GetPreviousQuestions(APIView):
    def get(self,request,qcode,sid):
        try:
            previous_questions = Question.objects.filter(block__survey__id=sid,active=2,code__lt=qcode).order_by('code').values('id','text')
            return Response({'status':2,'questions':previous_questions})
        except Exception as e:
            return Response({'status':0})

class GetQuestionDependentValue(APIView):
    def get(self,request,qid,cid):
        try:
            p_question = Question.objects.get(id=qid,active=2).parent_id
            answer = JsonAnswer.objects.get(id=cid)
            value = answer.response.get(str(p_question))
            return Response({'status':2,'value':value})
        except Exception as e:
            return Response({'status':0,'value':''})

def identify_sam_mam(child_id,height,weight):
    gender = Beneficiary.objects.get(beneficiary_type_id=4,id=child_id).jsondata.get('gender').title()
    sam_object = SamAndMam.objects.get(gender=gender,height=height)
    values = {1:sam_object.v_1,2:sam_object.v_2,3:sam_object.v_3,4:sam_object.v_4}
    values_list = values.values()
    value = min(values_list,key=lambda x:abs(x-weight))
    for k,v in values:
        if v == value:
            if v <= 2:
                return "Normal"
            elif v >2 and v<=3:
                return "Mam"
            elif v>3:
                return "Sam"
            else:
                return "Dont Know"

class DeactivateChoice(APIView):
    def post(self,request,cid):
        try:
            c = Choice.objects.get(id=cid)
            if request.POST.get('key') == 'dec':
                c.active=0
                msg = 'Choice deactivated...'
            if request.POST.get('key') == 'act':
                c.active=2
                msg = 'Choice Activated...'
            c.save()
            status = 2
        except:
            status = 0
            msg = 'Something went wrong'
        return Response({'status':status,'message':msg})


class DeactivateQuestion(APIView):
    def post(self,request,qid):
        try:
            q = Question.objects.get(id=qid)
            if request.POST.get('key') == 'dec':
                q.active=0
                msg = 'Question deactivated...'
            if request.POST.get('key') == 'act':
                q.active=2
                msg = 'Question Activated...'
            q.save()
            status = 2
        except:
            status = 0
            msg = 'Something went wrong'
        return Response({'status':status,'message':msg})



from MutantApp.models import *
from django.apps import apps
from partner.models import *
class MutantSurveyReportExport(APIView):
    def get(self,request,form_id,user_id,table):
        
        survey = Survey.objects.get(id=form_id)
        file = open(BASE_DIR+'/static/response_csv/'+str(survey)+".csv","w+")
        file_name = str(file.name).split('/')[-1]
        csv_writer = csv.writer(file)
        dict_table = {"SLI":"school_level_information_2","ACI":"anganwadi_centre_information_3",\
                    "LM":"lactating_mothers_60","GM":"growth_monitoring_47",\
                    "CVI":"child_vaccination_and_immuniza_49","PW":"pregnant_women_57"}
        model = apps.get_model('MutantApp', dict_table.get(table))
        headers_list = [str(f.verbose_name) for f in model._meta.get_fields()]
        csv_writer.writerow(headers_list)
        answers = model.objects.all()
	if request.GET.get('part'):
            part = Partner.objects.get(id=request.GET.get('part'))
            fac = list(set(Facility.objects.filter(partner=part).values_list('id',flat=True)))
            answers = answers.filter(facility__in=fac)
        for ck in answers:
            csv_writer.writerow([ck])
        file.close()
        return Response({'status':2,'download':HOST_URL+'/static/response_csv/'+file_name})
        
        
#class EditQuestion(APIView):
#    def post(self , request):
#        try:
#            qid = request.GET.get('qid')
#            ques = Question.objects.get(id = qid)
#            res = {'status' : 2}
#            data = {}
#            if ques.qtype == T and ques.master_choice == False and ques.validation != 4:
#                pass
#                

class CreateEditBlock(APIView):
	def post(self , request):
		try:
			survey_id = request.POST.get('survey_id')
			block_name = request.POST.get('block_name')
			code = request.POST.get('block_code')
			order = request.POST.get('block_order')
			if Block.objects.filter(code = code , survey_id = survey_id).exists():
				return Response({'status':0 , 'message':'Code Already Exists'}) 
			else:
				survey = Survey.objects.get(id = survey_id)
				Block.objects.create(name = block_name , code = code , survey = survey , order = order)
				return Response({'status':2 , 'message':'Block Created Successfully'})
		except:
			return Response({'status':0 , 'message':'Something went wrong'})


class EditUpdateBlock(APIView):
	def get(self , request ):
		try:
			survey_id = int(request.GET.get('survey_id'))
			block_id = int(request.GET.get('block_id'))
			block_object = Block.objects.get(id = block_id , survey_id = survey_id)
			return Response({'status':2 , 'message':'You are in edit View' , 'res' : {'block_id' : block_object.id , 'block_name': str(block_object.name) , 'block_code' : int(block_object.code) , 'block_order': int(block_object.order) , 'survey_id' : block_object.survey.id}})
		except Exception as e:
			return Response({'status':0 , 'message':e.message , 'res' : None})
	
	def post(self , request):
		try:
			block_id = request.POST.get('block_id')
			survey_id = request.POST.get('survey_id')
			block_obj = Block.objects.get(id = block_id , survey_id = survey_id)
			block_obj.name = request.POST.get('block_name')
			block_obj.code = request.POST.get('block_code' , 0)
			block_obj.order = request.POST.get('block_order' , 0)
			block_obj.save()
			return Response({'status':2 , 'message' : 'Successfully updated'})
		except:
			return Response({'status':0 , 'message' : 'Something went wrong'})
		
