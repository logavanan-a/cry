from math import (ceil,)
import re
from collections import OrderedDict
from itertools import chain
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Q
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView
import attr
from box import Box
from ccd.settings import(REST_FRAMEWORK,)
from masterdata.views import (CustomPagination,)
from survey.models import (Survey,)
from partner.views import (unpack_errors)
from userroles.models import (UserRoles,UserPartnerMapping)
from .models import (WorkState, WorkStateUserRelation,
                     WorkFlow, WorkFlowSurveyRelation, WorkFlowComment, WorkFlowBatch, Comment)
from .serializers import (WorkStateSerializer, WorkFlowSerializer, WorkFlowSurveyRelationSerializer,
                          WorkStateSerializerEdit, WorkFlowSerializerEdit, WorkFlowSurveyRelationSerializerEdit,
                          WorkFlowCommentSerializer, WorkFlowGetStates, WorkFlowBatchSerializer,
                          WorkFlowDetailSerializer, CommentSerializer, WorkFlowPrimarySerializer, WorkFlowDetailBatchSerializer)
# Create your views here.

pg_size = REST_FRAMEWORK.get('DPF_PAGE_SIZE')


@attr.s
class BasicOperation(object):

    def split_value(self, x):
        data = []
        if x != '0':
            data = map(int, x.split(','))
        return data

    def stripmessage(self, errors):
        for i, j in errors.items():
            errors[i] = j
            expr = re.search(r'\w+:', errors[i])
            if expr:
                ik = expr.group().replace(':', '')
                errors[ik] = errors.pop(i)
                errors[ik] = re.sub(r'\w+:', '', errors[ik])
            return errors


class WorkStateView(ListCreateAPIView):
    queryset = WorkState.objects.filter(active=2).order_by('-id')
    serializer_class = WorkStateSerializer
    bo = BasicOperation()

    def list(self, request, *args, **kwargs):
        get_wsu = lambda x: WorkStateUserRelation.objects.filter(workstate=x)
        queryset = [{'id': ws.id, 'name': ws.name, 'order': ws.order,
                     'users': ','.join(get_wsu(ws)[0].users.filter(is_active=True).values_list('username', flat=True)) if get_wsu(ws) else ''}
                    for ws in self.get_queryset().order_by('-id')]
        if request.query_params.get('key', 1):
            get_page = ceil(
                float(self.get_queryset().count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            status, message = (
                2, 'Successfully Retreieved') if queryset else (0, 'No Data')
            return paginator.get_paginated_response(result_page, status, message, 27, get_page)
        return Response(queryset)

    def validate(self, ws, data):
        response = {'status': 2}
        wsu = WorkStateUserRelation.objects.filter(active=2)
        if wsu.filter(workstate=ws, users__id__in=self.bo.split_value(data.users)):
            response.update(
                {"status": 0, "name": "already workstate relation contain workstate {workstate} by this user {users}.".format(**data.to_dict())})
        return response

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = Box(request.data)
        get_dict = data.to_dict()
        response = {'status': 0, 'message': 'Something went wrong.'}
        serializer = self.get_serializer(data=get_dict)
        if serializer.is_valid():
            ws = self.perform_create(serializer)
            get_response = self.validate(ws, data)
            if get_response.get('status'):
                wsu = WorkStateUserRelation.objects.create(workstate=ws)
                wsu.users.add(*self.bo.split_value(data.users))
                response = {'status': 2, 'message': 'Successfully created.'}
            else:
                ws.delete()
                response.update(self.bo.stripmessage(get_response))
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)

    def post(self, request, *args, **kwargs):
        """
        To Create the WorkState.
        ---
        parameters:
        - name: users
          description: Pass users by comma separeted ids.
          required: true
          type: string
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class WorkStateViewEdit(RetrieveUpdateDestroyAPIView):
    queryset = WorkState.objects.filter(active=2).order_by('-id')
    serializer_class = WorkStateSerializerEdit
    bo = BasicOperation()

    def retrieve(self, request, *args, **kwargs):
        get_wsu = lambda x: WorkStateUserRelation.objects.filter(
            workstate=x).order_by('-id')
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data.update({'users': get_wsu(instance)[0].users.filter(
            is_active=True).values_list('id', flat=True) if get_wsu(instance) else []})
        data.update({'users_name': get_wsu(instance)[0].users.filter(
            is_active=True).values_list('username', flat=True) if get_wsu(instance) else []})
        return Response(data)

    def validate_data(self, instance, data):
        data = Box(data)
        response = {'status': 2, 'name': "No Data."}
        if data.name != instance.name and int(data.order) != int(instance.order):
            if self.get_queryset().filter(name__iexact=data.name, order=int(data.order)):
                response = {'status': 0,
                            'name': "already workstate contain name or order."}
        elif data.name != instance.name:
            if self.get_queryset().filter(name__iexact=data.name):
                response = {'status': 0,
                            'name': "already name is their."}
        elif int(data.order) != int(instance.order):
            if self.get_queryset().filter(order=int(data.order)):
                response = {'status': 0,
                            'name': "already order is their."}
        return response

    def perform_update_(self, instance, data):
        get_wsu = lambda x: WorkStateUserRelation.objects.filter(workstate=x)
        get_validate = self.validate_data(instance, data)
        if get_validate.get('status'):
            serializer = self.get_serializer(
                instance, data=data, partial=False)
            if serializer.is_valid():
                if get_wsu(instance):
                    get_wsu(instance)[0].users.clear()
                    get_wsu(instance)[0].users.add(
                        *self.bo.split_value(data.get('users', '')))
                serializer.save()
        return get_validate

    def put(self, request, *args, **kwargs):
        """
        To Create the WorkState.
        ---
        parameters:
        - name: users
          description: Pass users by comma separeted ids.
          required: true
          type: string
          paramType: form
        """
        response = {'status': 0, 'message': 'Something went wrong.'}
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False)
        if serializer.is_valid():
            response_ = self.perform_update_(instance, data=request.data)
            if response_.get('status'):
                response = {'status': 2,
                            'message': 'Successfully updated the data.'}
            else:
                response = response_
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)

    def delete(self, request, *args, **kwargs):
        get_wsu = lambda x: WorkStateUserRelation.objects.filter(workstate=x)
        instance = self.get_object()
        instance.switch()
        get_wsu(instance)[0].switch() if get_wsu(instance) else ''
        response = {'status': 0,
                    'message': 'Successfully Deleted the WorkState'}
        return Response(response)


class ListingData(APIView):

    def split_values(self, data):
        users_data = []
        split_name = data.get('user_name')
        if split_name:
            get_name = split_name.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.username} for u in User.objects.filter(
                is_active=True, username__istartswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def work_state_result(self, data):
        users_data = []
        split_name = data.get('user_name')
        if split_name:
            get_name = split_name.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.workstate.name} for u in
                                   WorkStateUserRelation.objects.filter(active=2, workstate__name__istartswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def survey_name_result(self, data):
        users_data = []
        split_name = data.get('user_name')
        if split_name:
            get_name = split_name.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.name} for u in
                                   Survey.objects.filter(active=2, name__istartswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

    def get(self, request, *args, **kwargs):
        """
        Provide Key to Get Users, WorkStateUserRelation and Survey.
        ---
        parameters:
        - name: key
          description: Pass key 1 or 2 or 3 or 4 respectively.
          required: false
          type: string
          paramType: form
        - name: user_name
          description: Pass name.
          required: false
          type: string
          paramType: form
        """
        data = request.query_params
        key = data.get('key', 0)
        listing = {'1': self.split_values(data),
                   '2': self.work_state_result(data),
                   '3': self.survey_name_result(data),
                   '4': self.split_values(data),
                   0: {'status': 0, 'message': 'Key is not provided.'}}
        get_data = listing.get(key)
        return Response(get_data)


class WorkFlowView(ListCreateAPIView):
    queryset = WorkFlow.objects.filter(active=2).order_by('-id')
    serializer_class = WorkFlowSerializer
    bo = BasicOperation()

    def update_list_dict(self, wtf):
        get_obj = {"id": wtf.id, "name": wtf.name,
                   "flow_state": ','.join(wtf.flow_state.filter(active=2).values_list('workstate__name', flat=True))
                   if wtf.flow_state.filter(active=2) else ''}
        get_obj.update(wtf.get_survey_wf())
        return get_obj

    def list(self, request, *args, **kwargs):
        queryset = [self.update_list_dict(wtf) for wtf in self.get_queryset()]
        if request.query_params.get('key', 1):
            get_page = ceil(
                float(self.get_queryset().count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            status, message = (
                2, 'Successfully Retreieved') if queryset else (0, 'No Data')
            return paginator.get_paginated_response(result_page, status, message, 28, get_page)
        return Response(queryset)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        get_dict = data.to_dict()
        serializer = self.get_serializer(data=get_dict)
        if serializer.is_valid():
            get_object = self.perform_create(serializer)
            if self.bo.split_value(data.flow_state):
                get_object.flow_state.add(
                    *self.bo.split_value(data.flow_state))
            tag_survey, created = WorkFlowSurveyRelation.objects.get_or_create(
                workflow=get_object, survey_id=data.survey_id)
            get_object.tag_id = tag_survey.id
            get_object.save()
            response = {'status': 2, 'message': 'Successfully created.'}
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)

    def post(self, request, *args, **kwargs):
        """
        To Create the Workflow.
        ---
        parameters:
        - name: flow_state
          description: Pass work state by comma separeted ids.
          required: true
          type: string
          paramType: form
        - name: survey_id
          description: Pass survey id.
          required: true
          type: integer
          paramType: form
        """
        return self.create(request, *args, **kwargs)


class WorkFlowViewEdit(RetrieveUpdateDestroyAPIView):
    queryset = WorkFlow.objects.filter(active=2).order_by('-id')
    serializer_class = WorkFlowSerializerEdit
    bo = BasicOperation()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.switch()
        return Response({"status": 0, "message": "Successfully deleted the object."})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data.update({"flow_state": instance.flow_state.filter(active=2).values_list(
            'id', flat=True) if instance.flow_state.filter(active=2) else [],
            "flow_state_name": instance.flow_state.filter(active=2).values_list(
                'workstate__name', flat=True) if instance.flow_state.filter(active=2) else ''})
        data.update(instance.get_survey_wf())
        return Response(data)

    def validate_data(self, instance, data):
        response = {'status': 2, 'name': "No Data."}
        if data.name != instance.name:
            if self.get_queryset().filter(Q(name__iexact=data.name)):
                response = {'status': 0,
                            'name': "already workflow contain name."}
        return response

    def perform_update(self, instance, data):
        get_wtf_validate = self.validate_data(instance, data)
        if get_wtf_validate.get('status'):
            serializer = self.get_serializer(
                instance, data=data.to_dict(), partial=False)
            if serializer.is_valid():
                instance.flow_state.clear()
                if self.bo.split_value(data.flow_state):
                    instance.flow_state.add(
                        *self.bo.split_value(data.flow_state))
                get_obj = serializer.save()
                tag_survey, created = WorkFlowSurveyRelation.objects.get_or_create(
                    workflow=get_obj, survey_id=data.survey_id)
                get_obj.tag_id = tag_survey.id
                get_obj.save()
        return get_wtf_validate

    def update(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            get_wtf = self.perform_update(instance, data)
            if get_wtf.get('status'):
                response = {'status': 2,
                            'message': 'Successfully Updated the object.'}
            else:
                response = get_wtf
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)

    def put(self, request, *args, **kwargs):
        """
        To Create the Workflow.
        ---
        parameters:
        - name: flow_state
          description: Pass work state by comma separeted ids.
          required: true
          type: string
          paramType: form
        - name: survey_id
          description: Pass survey id.
          required: true
          type: integer
          paramType: form
        """
        return self.update(request, *args, **kwargs)


class WorkFlowSurveyRelationView(ListCreateAPIView):
    queryset = WorkFlowSurveyRelation.objects.filter(active=2).order_by('-id')
    serializer_class = WorkFlowSurveyRelationSerializer
    bo = BasicOperation()

    def list(self, request, *args, **kwargs):
        queryset = [{"id": wfsr.id, "work_name": wfsr.workflow.name if wfsr.workflow else '',
                     "survey_name": wfsr.survey.name if wfsr.survey else '',
                     "start_date": wfsr.start_date.strftime("%Y-%m-%d") if wfsr.start_date else '',
                     "end_date": wfsr.end_date.strftime("%Y-%m-%d") if wfsr.end_date else '',
                     }
                    for wfsr in self.get_queryset()]
        if request.query_params.get('key', 1):
            get_page = ceil(
                float(self.get_queryset().count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            status, message = (
                2, 'Successfully Retreieved') if queryset else (0, 'No Data')
            return paginator.get_paginated_response(result_page, status, message, 29, get_page)
        return Response(queryset)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        response = {'status': 0, 'message': 'Something went wrong.'}
        if serializer.is_valid():
            self.perform_create(serializer)
            response = {
                'status': 2, 'message': 'Successfully configured survey and workflow.'}
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)


class WorkFlowSurveyRelationViewEdit(RetrieveUpdateDestroyAPIView):
    queryset = WorkFlowSurveyRelation.objects.filter(active=2).order_by('-id')
    serializer_class = WorkFlowSurveyRelationSerializerEdit
    bo = BasicOperation()

    def validate_data(self, instance, data):
        response = {'status': 2, 'name': "No Data."}
        if data.workflow != instance.workflow and data.survey != instance.survey:
            if self.get_queryset().filter(workflow=data.workflow, survey=data.survey):
                response = {
                    'status': 0, 'name': "already workflow and survey is configured."}
        return response

    def perform_update(self, instance, data):
        get_wtf_validate = self.validate_data(instance, data)
        if get_wtf_validate.get('status'):
            serializer = self.get_serializer(
                instance, data=data.to_dict(), partial=False)
            if serializer.is_valid():
                serializer.save()
        return get_wtf_validate

    def update(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            get_wtf = self.perform_update(instance, data)
            if get_wtf.get('status'):
                response = {'status': 2,
                            'message': 'Successfully Updated the object.'}
            else:
                response = get_wtf
        else:
            response.update(self.bo.stripmessage(
                unpack_errors(serializer.errors)))
        return Response(response)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.switch()
        return Response({"status": 0, "message": "Successfully deleted the object."})


class GetStates(CreateAPIView):
    queryset = WorkFlowSurveyRelation.objects.filter(active=2)
    serializer_class = WorkFlowGetStates

    def create(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.',
                    'name': 'No User or Survey exists.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            user_to_native = map(int, [data.user_id])
            response = OrderedDict()
            getwfc = WorkFlowComment.objects.filter(batch__current_status__survey__id=data.survey_id,
                                                    batch__id=data.batch_id,
                                                    next_tag_user__id__in=user_to_native).order_by('-id')
            if getwfc:
                get_survey = getwfc[0]
                work_flow_id = get_survey.batch.current_status.workflow.id
                get_workflow_stat = get_survey.batch.current_status.workflow.get_users_work_state()
                get_curren_state = get_workflow_stat.get(
                    int(data.user_id)).get('curr_state_id')
                get_workflow_pre_nxt = get_survey.batch.current_status.workflow.previous_next_state(
                    get_curren_state)
                response.update({'status': 2,
                                 'message': 'Successfully retrieved the list.'})
                response.update(get_workflow_stat.get(
                    int(data.user_id)))
                response.update(get_workflow_pre_nxt)
                response.update(get_survey.get_batch_id())
            else:
                wf = self.get_queryset().filter(survey__id=data.survey_id,
                                                workflow__flow_state__users__id__in=user_to_native)
                if wf:
                    get_survey = wf[0]
                    work_flow_id = get_survey.workflow.id
                    get_workflow_stat = get_survey.workflow.get_users_work_state()
                    get_curren_state = get_workflow_stat.get(
                        int(data.user_id)).get('curr_state_id')
                    get_workflow_pre_nxt = get_survey.workflow.previous_next_state(
                        get_curren_state)
                    response.update({'status': 2,
                                     'message': 'Successfully retrieved the list.'})
                    response.update(get_workflow_stat.get(
                        int(data.user_id)))
                    response.update(get_workflow_pre_nxt)
            end_key = get_flat_count = 0
            getwfc_status = WorkFlowComment.objects.filter(batch__current_status__survey__id=data.survey_id,
                                                           batch__id=data.batch_id,
                                                           batch__current_status__workflow__id=work_flow_id).count()
            get_flow_stat = WorkFlowSurveyRelation.objects.filter(
                survey__id=data.survey_id, workflow__id=work_flow_id).order_by('-id')
            if get_flow_stat:
                get_flat_count = get_flow_stat[
                    0].workflow.flow_state.filter(active=2).count()
            if getwfc_status == get_flat_count:
                end_key = 1
            response.update(end_key=end_key)
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(response)


class WorkFlowCommentView(ListCreateAPIView):
    queryset = WorkFlowComment.objects.filter(active=2)
    serializer_class = WorkFlowCommentSerializer
    serializer_class_secondary = CommentSerializer

    def create_curr_state(self, data, msg, cmt):
        new_data = data
        next_tag_user = new_data.get('next_tag_user')
        previous_tag_user = new_data.get('previous_tag_user')
        batch = WorkFlowBatch.objects.get(id=new_data.get('batch'))
        if new_data.get('previour_state') == '0':
            curr_state = WorkStateUserRelation.objects.get(
                id=new_data.get('curr_state'))
        elif new_data.get('previour_state') != '0' and new_data.get('status') == '3':
            curr_state = WorkStateUserRelation.objects.get(
                id=new_data.get('curr_state'))
        else:
            curr_state = WorkStateUserRelation.objects.get(
                id=new_data.get('previour_state'))
        prime, created = WorkFlowComment.objects.get_or_create(
            batch=batch, curr_state=curr_state)
        new_status = prime.status
        get_previous_states = batch.current_status.workflow.get_previous_state_values()
        get_next_states = batch.current_status.workflow.get_next_level_value()
        if cmt != 7:
            prime.status = new_data.get('status')
        if new_data.get('commented_to') == '0':
            prime.status = new_data.get('status')
        if new_data.get('status') == '3' and new_data.get('commented_to') == '0':
            prime.status = new_data.get('status')
        if new_data.get('commented_to') == '0' and created is False:
            prime.status = new_status
        if new_data.get('previous_tag_user') != '0' and msg == 0:
            prime.curr_user_id = new_data.get('previous_tag_user')
        else:
            prime.curr_user_id = new_data.get('curr_user')
        if new_data.get('commented_to') == '0' and new_data.get('previous_tag_user') != '0':
            prime.curr_user_id = new_data.get('previous_tag_user')
            prime.status = new_status
        if next_tag_user != '0':
            prime.next_tag_user_id = new_data.get('next_tag_user')
        if not prime.previous_tag_user_id:
            if previous_tag_user != '0':
                prime.previous_tag_user_id = previous_tag_user
        if get_previous_states.get(curr_state.id):
            prime.prevsiour_state_id = get_previous_states.get(curr_state.id)
        if get_next_states.get(curr_state.id):
            prime.next_state_id = get_next_states.get(curr_state.id)
        prime.save()
        return created, prime.id

    def just_commenting(self, new_data):
        curr_state_alias, prime_id = self.create_curr_state(new_data, 1, 7)
        previous_tag_user = new_data.get('previous_tag_user')
        next_tag_user = new_data.get('next_tag_user')
        batch = WorkFlowBatch.objects.get(id=new_data.get('batch'))
        curr_state = WorkStateUserRelation.objects.get(
            id=new_data.get('curr_state'))
        prime, created = WorkFlowComment.objects.get_or_create(
            batch=batch, curr_state=curr_state)
        if new_data.get('status') == '3':
            prime.status = new_data.get('status')
        prime.save()
        get_previous_states = batch.current_status.workflow.get_previous_state_values()
        get_next_states = batch.current_status.workflow.get_next_level_value()
        second = Comment.objects.create(curr_state=curr_state)
        second.comment = new_data.get('comment')
        second.workflow_cmt_id = prime_id
        second.status = new_data.get('status')
        second.curr_user_id = new_data.get('curr_user')
        if next_tag_user != '0':
            second.next_tag_user_id = new_data.get('next_tag_user')
        if previous_tag_user != '0':
            second.previous_tag_user_id = new_data.get('previous_tag_user')
        if get_previous_states.get(curr_state.id):
            second.previour_state_id = get_previous_states.get(curr_state.id)
        if get_next_states.get(curr_state.id):
            prime.next_state_id = get_next_states.get(curr_state.id)
        if new_data.get('commented_by') != '0':
            second.commented_by_id = int(new_data.get('commented_by'))
        if new_data.get('commented_to') != '0':
            second.commented_to_id = int(new_data.get('commented_to'))
        second.save()
        return second.id

    def perform_create(self, serializer, serializer_child, data):
        # next state with default status 0
        prime = second = 0
        if data.get('commented_to') == '0' or data.get('status') == '3':
            self.just_commenting(data)
        else:
            self.create_curr_state(data, 0, 1)
            new_data = data
            new_data.pop('types')
            comment = new_data.pop('comment')
            status = new_data.pop('status')
            curr_user = new_data.pop('curr_user')
            previous_tag_user = new_data.pop('previous_tag_user')
            next_tag_user = new_data.pop('next_tag_user')
            new_data.pop('previour_state')
            new_data.pop('next_state')
            batch = WorkFlowBatch.objects.get(id=new_data.get('batch'))
            curr_state = WorkStateUserRelation.objects.get(
                id=new_data.get('curr_state'))
            prime, created = WorkFlowComment.objects.get_or_create(
                batch=batch, curr_state=curr_state)
            get_previous_states = batch.current_status.workflow.get_previous_state_values()
            get_next_states = batch.current_status.workflow.get_next_level_value()
            prime.status = 0
            prime.curr_user_id = curr_user
            if next_tag_user != '0':
                prime.next_tag_user_id = next_tag_user
            if not prime.previous_tag_user_id:
                if previous_tag_user != '0':
                    prime.previous_tag_user_id = previous_tag_user
            if get_previous_states.get(curr_state.id):
                prime.previour_state_id = get_previous_states.get(
                    curr_state.id)
            if get_next_states.get(curr_state.id):
                prime.next_state_id = get_next_states.get(curr_state.id)
            prime.save()
            second = Comment.objects.create(curr_state=curr_state)
            second.comment = comment
            second.workflow_cmt = prime
            second.status = status
            second.curr_user_id = curr_user
            if next_tag_user != '0':
                second.next_tag_user_id = next_tag_user
            if previous_tag_user != '0':
                second.previous_tag_user_id = previous_tag_user
            if get_previous_states.get(curr_state.id):
                second.previour_state_id = get_previous_states.get(
                    curr_state.id)
            if get_next_states.get(curr_state.id):
                prime.next_state_id = get_next_states.get(curr_state.id)
            if data.get('commented_by') != '0':
                second.commented_by_id = int(data.get('commented_by'))
            if data.get('commented_to') != '0':
                second.commented_to_id = int(data.get('commented_to'))
            second.save()
        return prime, second

    def create(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong'}
        data = Box(request.data)
        get_dict = data.to_dict()
        serializer = self.get_serializer(data=get_dict)
        serializer_child = self.serializer_class_secondary(data=get_dict)
        if serializer.is_valid() and serializer_child.is_valid():
            response = {'status': 2, 'message': 'Successfully created.'}
            primary, secondary = self.perform_create(
                serializer, serializer_child, get_dict)
        else:
            response.update(unpack_errors(serializer.errors))
            response.update(unpack_errors(serializer_child.errors))
        return Response(response)


class WorkFlowCommentEdit(RetrieveUpdateDestroyAPIView):
    queryset = WorkFlowComment.objects.filter(active=2)
    serializer_class = WorkFlowCommentSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.switch()
        return Response({"status": 0, "message": "Successfully deleted the object."})


class WorkFlowBatchView(ListAPIView):
    queryset = WorkFlowBatch.objects.filter(active=2)
    serializer_class = WorkFlowBatchSerializer

    def list(self, request, *args, **kwargs):
        data = request.query_params
        user_id = int(data.get('user_id', 17))
        queryset_ = [{'batch_id': wb.id, 'batch_name': wb.name, 'no_of_response': wb.no_of_response,
                      'partner': wb.partner.name, 'partner_id': wb.partner.id,
                      'survey_id': wb.current_status.survey.id,
                      'survey_name': wb.current_status.survey.name, 'status': wb.get_completion_status(),
                      'users': wb.get_users_all_states()}
                     for wb in self.get_queryset()]
        queryset = queryset_
        if user_id:
            queryset = []
            partner_list = self.get_user_partner_list(user_id)
            for u_id in queryset_ :
                if user_id in u_id.get('users') and u_id.get('partner_id') in partner_list:
                    queryset.append(u_id)
        if request.query_params.get('key', 1):
            get_page = ceil(
                float(self.get_queryset().count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            status, message = (
                2, 'Successfully Retreieved') if queryset else (0, 'No Data')
            return paginator.get_paginated_response(result_page, status, message, 30, get_page)
        return Response(queryset)

    def get_user_partner_list(self,u_id):
        try:
            return [UserRoles.objects.get(user__id=u_id).partner.id]
        except:
            try:
                return UserPartnerMapping.objects.get(user__id=u_id).partner.filter(active=2).all().values_list('id',flat=True)
            except:
                return []

class WorkFlowCurrentDetail(CreateAPIView):
    queryset = WorkFlowComment.objects.filter(active=2)
    serializer_class = WorkFlowDetailSerializer

    def post(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            response = {'status': 2, 'message': 'Successfully data retrieved'}
            get_data = self.get_queryset().filter(curr_user__id=data.user_id,
                                                  batch__current_status__workflow__id=data.workflow_id)
            if get_data:
                get_response = get_data[0]
                response.update(get_response.get_current_status())
            else:
                response.update(name='No Data for the User.')
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(response)


class WorkFlowPrimaryComment(CreateAPIView):
    queryset = Comment.objects.filter(active=2)
    serializer_class = WorkFlowPrimarySerializer

    def post(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            get_zero = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                curr_state__id=data.previour_state,
                commented_to__isnull=True).order_by('-id')
            get_first = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.curr_user,
                curr_state__id=data.curr_state_id,
                commented_to__isnull=True).order_by('-id')
            get_second = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.previous_user,
                curr_state__id=data.previour_state,
                commented_to__isnull=True).order_by('-id')
            get_third = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.next_user,
                curr_state__id=data.next_state,
                commented_to__isnull=True).order_by('-id')
            get_fourth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.curr_user,
                commented_to__id=data.next_user,
                curr_state__id=data.next_state,
                previour_state__id=data.curr_state_id,
            ).order_by('-id')
            get_fifth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.next_user,
                commented_to__id=data.curr_user,
                curr_state__id=data.curr_state_id).order_by('-id')
            get_sixth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.previous_user,
                commented_to__id=data.curr_user,
                previour_state__id=data.previour_state).order_by('-id')
            get_seventh = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.curr_user,
                commented_to__id=data.previous_user,
                curr_state__id=data.previour_state).order_by('-id')
            get_eigth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                curr_state__id=data.next_state).order_by('-id')
            query1 = list(set(list(get_first))) + \
                list(set(list(get_second)))
            query2 = list(set(list(get_third))) + list(set(list(get_zero)))
            query3 = list(set(list(get_fourth))) + \
                list(set(list(get_fifth)))
            query4 = list(set(list(get_sixth))) + \
                list(set(list(get_seventh)))
            query5 = list(set(list(get_eigth)))
            get_ = list(set(query1 + query2 +
                            query3 + query4 + query5))
            get_.sort(key=lambda x: x.id, reverse=True)
            if get_:
                response = {'status': 2,
                            'message': 'Successfully data retrieved'}
                get_data = [q.get_current_status() for q in get_]
                response.update(data=get_data)
            else:
                response.update(name='No Data for the WorkFlow.')
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(response)


class WorkFlowBatchPrimary(CreateAPIView):
    queryset = WorkFlowComment.objects.filter(active=2)
    serializer_class = WorkFlowDetailBatchSerializer
    sub_queryset = Comment.objects.filter(active=2)

    def get_level_status(self, data):
        response = {}
        com = self.get_queryset().filter(batch__id=data.batch.id,
                                         curr_state__id=data.curr_state.id)
        sub_com = self.sub_queryset.filter(workflow_cmt__batch__id=data.batch.id,
                                           previour_state__id=data.curr_state.id)
        com_approved = self.get_queryset().filter(batch__id=data.batch.id,
                                                  curr_state__id=data.curr_state.id, status=2)
        if com:
            get_pre_nxt = com[
                0].batch.current_status.workflow.get_previous_state_values()
            response['next'] = com[
                0].next_level_check()
            response['previous'], response['approved'] = com[
                0].get_next_level_status_val()
            response['previous_state_users'] = com[0].previous_tag_user.id if com[
                0].previous_tag_user else 0
        elif sub_com:
            get_pre_nxt = sub_com[
                0].workflow_cmt.batch.current_status.workflow.get_previous_state_values()
            response['next'] = sub_com[
                0].workflow_cmt.next_level_check()
            response['previous'] = 1 if get_pre_nxt.get(
                data.curr_state.id) else 0
            response['approved'] = 0
            response['previous_state_users'] = sub_com[
                0].previous_tag_user.id if sub_com[0].previous_tag_user else 0
        elif com_approved:
            get_pre_nxt = com_approved[
                0].batch.current_status.workflow.get_previous_state_values()
            response['next'] = com_approved[
                0].next_level_check()
            response['previous'], response['approved'] = com[
                0].get_next_level_status_val()
            response['previous_state_users'] = com_approved[
                0].previous_tag_user.id if com_approved[0].previous_tag_user else 0
        else:
            response['next'] = 0
            response['previous'] = 0
            response['approved'] = 0
            response['previous_state_users'] = 0
        return response

    def post(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            get_ = self.get_queryset().filter(
                batch__id=data.batch_id, curr_user__id=data.user_id).order_by('-id')
            if get_:
                response = {'status': 2,
                            'message': 'Successfully data retrieved'}
                full_data = get_[0]
                get_data = full_data.get_current_status()
                get_types = full_data.batch.current_status.workflow.get_buttons_status()
                response['button_status'] = get_types.get(
                    int(full_data.curr_state.id), 0)
                response.update(get_data)
                response.update(self.get_level_status(full_data))
            else:
                user_to_native = map(int, [data.user_id])
                wf = WorkFlowSurveyRelation.objects.filter(active=2, survey__id=data.survey_id,
                                                           workflow__flow_state__users__id__in=user_to_native)
                if wf:
                    get_batch = WorkFlowBatch.objects.get(id=data.batch_id)
                    get_survey = wf[0]
                    
                    get_workflow_stat = get_survey.workflow.get_users_work_state()
                    get_curren_state = get_workflow_stat.get(
                        int(data.user_id)).get('curr_state_id')
                    get_workflow_pre_nxt = get_survey.workflow.previous_next_state(
                        get_curren_state)
                    response.update({'status': 2,
                                     'message': 'Successfully retrieved the list.'})
                    response.update(get_workflow_stat.get(
                        int(data.user_id)))
                    response.update(get_workflow_pre_nxt)
                    response.update(get_batch.get_current_batch_status())
                    get_work = self.get_queryset().filter(batch__id=data.batch_id,
                                                          previour_state__id=get_curren_state)
                    if get_work:
                        response['previous_state_users'] = ""
                        response['previous_tag_user_id'] = 0
                        response['previous_tag_user_name'] = ''
                        response['next'] = 0
                        response['previous'] = 0
                        response['approved'] = 0
                        response['com_btn'] = 1
                        response['next_user'] = 0
                    else:
                        response['next'] = 1 if not get_workflow_pre_nxt.get(
                            'previour_state_id') else 0
                        response['previous'] = 0
                        response['approved'] = 0
                        response['com_btn'] = 0
                        response['previous_state_users'] = ""
                        response['previous_tag_user_id'] = 0
                        response['previous_tag_user_name'] = ''
                        response['next_user'] = 0
                else:
                    response.update(name='No Data for the WorkFlow.')
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(response)


class WorkFlowBatchPlainDetail(CreateAPIView):
    queryset = WorkFlowBatch.objects.filter(active=2)
    serializer_class = WorkFlowDetailBatchSerializer

    def post(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            get_ = self.get_queryset().filter(id=data.batch_id).order_by('-id')
            if get_:
                response = {'status': 2,
                            'message': 'Successfully data retrieved'}
                get_data = get_[0].get_current_batch_status()
                response.update(get_data)
            else:
                response.update(name='No Data for the Batch.')
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(response)
