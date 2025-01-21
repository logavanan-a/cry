from __future__ import unicode_literals
from collections import OrderedDict
from itertools import chain
import pytz
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from masterdata.models import (BaseContent,)
from constants import (OPTIONAL,)
# Create your models here.


class WorkState(BaseContent):
    name = models.CharField(max_length=100, **OPTIONAL)
    order = models.PositiveIntegerField(default=0, **OPTIONAL)
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return "{0} | {1}".format(self.name if self.name else 'N/A', self.order)


class WorkStateUserRelation(BaseContent):
    workstate = models.ForeignKey(WorkState, **OPTIONAL)
    users = models.ManyToManyField('auth.User', **OPTIONAL)

    def __unicode__(self):
        return '{0} and {1}'.format(self.workstate.name if self.workstate else 'N/A', ','.join([u.username for u in self.users.all()]) if self.users.all() else 'N/A')


class WorkFlow(BaseContent):
    name = models.CharField(max_length=100, **OPTIONAL)
    slug = models.SlugField(max_length=50, **OPTIONAL)
    created_by = models.ForeignKey('auth.User', **OPTIONAL)
    start_date = models.DateTimeField(**OPTIONAL)
    end_date = models.DateTimeField(**OPTIONAL)
    flow_state = models.ManyToManyField(WorkStateUserRelation, **OPTIONAL)
    tag_id = models.PositiveIntegerField(default=0, **OPTIONAL)

    def __unicode__(self):
        return "{0} | {1}".format(self.name if self.name else 'N/A', self.created_by.username if self.created_by else 'N/A')

    def get_users_work_state(self):
        get_users = {usr.id: {'curr_state_name': fs.workstate.name, 'curr_state_id': fs.id}
                     for fs in self.flow_state.filter(active=2) for usr in fs.users.all()}
        return get_users

    def get_buttons_status(self):
        flow_state_ = self.flow_state.filter(
            active=2).order_by("workstate__order").values_list('id', flat=True)
        result = {}
        for k, v in enumerate(flow_state_):
            if k == 0:
                result[v] = 0
            elif k == len(flow_state_) - 1:
                result[v] = 2
            else:
                result[v] = 1
        return result

    def previous_next_state(self, curr_state_id):
        get_work_name = lambda x: WorkStateUserRelation.objects.get(
            id=x) if x else ''
        get_work_users = lambda u: [
            {'id': usr.id, 'name': usr.username} for usr in u.users.all()] if u else []
        flow_state_ = self.flow_state.filter(
            active=2).order_by("workstate__order")
        get_flow_state = [fs_.id for fs_ in flow_state_]
        get_index_curr = get_flow_state.index(curr_state_id)
        get_index_previous = get_index_curr - 1
        get_index_next = get_index_curr + 1
        if get_index_previous == -1:
            previour_state = 0
            previour_state_name = ''
        else:
            previour_state = get_flow_state[get_index_previous]
            previour_state_name = get_work_name(
                previour_state).workstate.name if get_work_name(previour_state) else ''
        if get_index_next <= len(get_flow_state):
            if get_index_next in (ind for ind, _ in enumerate(get_flow_state)):
                next_state = get_flow_state[get_index_next]
                next_state_name = get_work_name(
                    next_state).workstate.name if get_work_name(next_state) else ''
            else:
                next_state = 0
                next_state_name = ''
        else:
            next_state = 0
            next_state_name = ''
        final_state = OrderedDict()
        final_state.update({'previour_state_id': previour_state, 'previour_state_name': previour_state_name,
                            'previous_state_users': get_work_users(get_work_name(previour_state)),
                            'next_state_id': next_state, 'next_state_name': next_state_name,
                            'next_state_users': get_work_users(get_work_name(next_state))}
                           )
        get_finale = self.get_buttons_status().get(int(curr_state_id), 0)
        final_state.update(button_status=get_finale)
        return final_state

    def get_previous_state_values(self):
        flow_state_ = self.flow_state.filter(
            active=2).order_by("workstate__order").values_list('id', flat=True)
        result = {}
        for k, v in enumerate(flow_state_):
            if k == 0:
                result[v] = 0
            else:
                result[v] = flow_state_[k - 1]
        return result

    def get_next_level_value(self):
        flow_state_ = self.flow_state.filter(
            active=2).order_by("workstate__order").values_list('id', flat=True)
        response = {}
        k = 0
        for e, v in enumerate(flow_state_):
            k += 1
            if k < len(flow_state_):
                response[v] = flow_state_[k]
            else:
                response[v] = 0
        return response

    def get_survey_wf(self):
        response = {'survey_id': 0, 'survey_name': ''}
        get_wf = WorkFlowSurveyRelation.objects.filter(
            id=self.tag_id).order_by('-id')
        if get_wf:
            pena = get_wf[0]
            response = {'survey_id': [pena.survey.id],
                        'survey_name': pena.survey.name}
        return response


class WorkFlowSurveyRelation(BaseContent):
    start_date = models.DateTimeField(**OPTIONAL)
    end_date = models.DateTimeField(**OPTIONAL)
    workflow = models.ForeignKey(WorkFlow, **OPTIONAL)
    survey = models.ForeignKey('survey.Survey', **OPTIONAL)

    def __unicode__(self):
        return '{0} and {1}'.format(self.workflow.name if self.workflow else 'N\A', self.survey.name if self.survey else 'N\A')


# CRON Job
class WorkFlowBatch(BaseContent):
    # partner_name + survey_response_count + survey_name
    name = models.CharField(max_length=100, **OPTIONAL)
    current_status = models.ForeignKey(WorkFlowSurveyRelation, **OPTIONAL)
    no_of_response = models.PositiveIntegerField(default=0, **OPTIONAL)
    response_ids = JSONField(default=[])
    partner = models.ForeignKey('partner.Partner', **OPTIONAL)

    def __unicode__(self):
        return '{0} and {1}'.format(self.name or 'N/A', self.partner.name if self.partner else 'N\A')

    def get_current_batch_status(self):
        response = {'batch_id': self.id,
                    'batch_name': self.name,
                    'workflow_id': self.current_status.workflow.id,
                    'workflow_name': self.current_status.workflow.name,
                    'survey_name': self.current_status.survey.name if self.current_status else '',
                    'survey_id': self.current_status.survey.id if self.current_status else '', }
        return response

    def get_completion_status(self):
        status = {0: 'Open', 1: 'Closed', 2: 'In-Progress'}
        end_key = 0
        getwfc_status = WorkFlowComment.objects.filter(batch__id=self.id, batch__current_status__survey__id=self.current_status.survey.id,
                                                       batch__current_status__workflow__id=self.current_status.workflow.id, status=3)
        if getwfc_status:
            end_key = status.get(1)
        else:
            end_key = status.get(0)
        return end_key

    def get_users_all_states(self):
        all_users = []
        wf = self.current_status.workflow.flow_state.filter(active=2)
        if wf:
            all_users_ = [u.users.all().values_list(
                'id', flat=True) for u in wf]
            all_users = list(chain.from_iterable(all_users_))
        return all_users

WORKFLOW_STATUS = ((0, 'Denied'), (1, 'Approved'),
                   (2, 'Final State'), (3, 'Completed'))


class WorkFlowComment(BaseContent):
    status = models.IntegerField(choices=WORKFLOW_STATUS, **OPTIONAL)
    batch = models.ForeignKey(WorkFlowBatch, **OPTIONAL)
    curr_user = models.ForeignKey(
        'auth.User', related_name='commented_user', **OPTIONAL)
    curr_state = models.ForeignKey(
        WorkStateUserRelation, related_name='workflow_curr_state', **OPTIONAL)
    previous_tag_user = models.ForeignKey(
        'auth.User', related_name='tagged_user', **OPTIONAL)
    previour_state = models.ForeignKey(
        WorkStateUserRelation, related_name='workflow_previous', **OPTIONAL)
    next_tag_user = models.ForeignKey(
        'auth.User', related_name='next_tagged_user', **OPTIONAL)
    next_state = models.ForeignKey(
        WorkStateUserRelation, related_name='workflow_next', **OPTIONAL)

    def __unicode__(self):
        return '{0}'.format(self.batch.name if self.batch else 'N\A')

    def get_final_state(self):
        com_btn = 1
        get_last = self.batch.current_status.workflow.flow_state.filter(
            active=2).order_by('workstate__order')
        if get_last:
            last = list(get_last)[-1]
            work = WorkFlowComment.objects.filter(
                active=2, curr_state=last, status=3)
            if work:
                com_btn = 0
        return com_btn

    def get_previous_state_user(self, previour_state,  previous_tag_user):
        if previour_state and previous_tag_user:
            previous_user = previous_tag_user.username
        else:
            previous_user = ''
        return previous_user

    def get_current_status(self):
        data = {}
        response = {'batch_id': self.batch.id,
                    'batch_name': self.batch.name,
                    'self_id': self.id,
                    'status': self.status,
                    'com_btn': self.get_final_state(),
                    'workflow_id': self.batch.current_status.workflow.id,
                    'workflow_name': self.batch.current_status.workflow.name,
                    'survey_name': self.batch.current_status.survey.name if self.batch else '',
                    'survey_id': self.batch.current_status.survey.id if self.batch else '',
                    'curr_state_id': self.curr_state.id if self.curr_state else 0,
                    'curr_state_name': self.curr_state.workstate.name if self.curr_state else '',
                    'previour_state_id': self.previour_state.id if self.previour_state else 0,
                    'previour_state_name': self.previour_state.workstate.name if self.previour_state else '',
                    'previous_tag_user_id': self.previous_tag_user.id if self.previous_tag_user else 0,
                    'previous_tag_user_name': self.get_previous_state_user(self.previour_state, self.previous_tag_user),
                    'next_state_id': self.next_state.id if self.next_state else 0,
                    'next_state_name': self.next_state.workstate.name if self.next_state else '',
                    'next_tagged_user_id': self.next_tag_user.id if self.next_tag_user else 0,
                    'next_tagged_user_name': self.next_tag_user.username if self.next_tag_user else '',
                    }
        if self.curr_state == self.next_state:
            data = {'next_state_id': 0,
                    'next_state_name': '',
                    'next_tagged_user_id': 0,
                    'next_tagged_user_name': ''}
        response.update(data)
        return response

    def get_batch_id(self):
        return {'batch_id': self.batch.id if self.batch else 0}

    def next_level_check(self):
        if self.previour_state:
            get = WorkFlowComment.objects.filter(
                curr_state__id=self.previour_state.id)
            if get:
                get = get[0]
                if get.status == 0 and self.status == 0 and self.next_state is None:
                    next_ = 0
                elif get.status == 1 and self.status == 1 and self.next_state is None:
                    next_ = 1
                elif get.status == 1 and self.status == 0 and self.next_state is None:
                    next_ = 0
                elif get.status == 1 and self.status == 1:
                    next_ = 0
                elif get.status == 1 and self.status == 0:
                    next_ = 1
                elif get.status == 0 and self.status == 0:
                    next_ = 0
                elif get.status == 1 and self.status == 3 and self.next_state is None:
                    next_ = 0
                else:
                    next_ = 0
        elif self.status == 1:
            next_ = 0
        elif self.status == 0:
            next_ = 1
        else:
            next_ = 0
        return next_

    def get_next_level_status_val(self):
        """This is for coding purpose."""
        previous, approve = 0, 0
        if self.previour_state:
            get = WorkFlowComment.objects.filter(
                curr_state__id=self.previour_state.id)
            if get:
                get = get[0]
                if get.status == 0 and self.status == 0 and self.next_state is None:
                    previous, approve = 0, 0
                elif get.status == 1 and self.status == 1 and self.next_state is None:
                    previous, approve = 1, 0
                elif get.status == 1 and self.status == 0 and self.next_state is None:
                    previous, approve = 1, 1
                elif get.status == 1 and self.status == 1:
                    previous, approve = 0, 0
                elif get.status == 1 and self.status == 0:
                    previous, approve = 1, 0
                elif get.status == 0 and self.status == 0:
                    previous, approve = 0, 0
                elif get.status == 1 and self.status == 3 and self.next_state is None:
                    previous, approve = 0, 0
                else:
                    previous, approve = 0, 0
        elif self.status == 1:
            previous, approve = 0, 0
        elif self.status == 0:
            previous, approve = 0, 0
        else:
            previous, approve = 0, 0
        return previous, approve


COMMENT_TYPE = ((0, 'Single'), (1, 'TL'), (2, 'PM'), (3, 'Universal'))


class Comment(BaseContent):
    status = models.IntegerField(choices=WORKFLOW_STATUS, **OPTIONAL)
    workflow_cmt = models.ForeignKey(WorkFlowComment, **OPTIONAL)
    types = models.IntegerField(choices=COMMENT_TYPE, **OPTIONAL)
    commented_by = models.ForeignKey(
        'auth.User', related_name='commented_by_user_work_flow', **OPTIONAL)
    commented_to = models.ForeignKey(
        'auth.User', related_name='commented_to_user_work_flow', **OPTIONAL)
    comment = models.TextField(**OPTIONAL)
    curr_user = models.ForeignKey(
        'auth.User', related_name='comm_commented_user', **OPTIONAL)
    curr_state = models.ForeignKey(
        WorkStateUserRelation, related_name='commented_workflow_curr_state', **OPTIONAL)
    previous_tag_user = models.ForeignKey(
        'auth.User', related_name='commented_tagged_user', **OPTIONAL)
    previour_state = models.ForeignKey(
        WorkStateUserRelation, related_name='commented_workflow_previous', **OPTIONAL)
    next_tag_user = models.ForeignKey(
        'auth.User', related_name='commented_next_tagged_user', **OPTIONAL)
    next_state = models.ForeignKey(
        WorkStateUserRelation, related_name='commented_workflow_next', **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return str(self.id)

    def get_previous_state_user(self, previour_state,  previous_tag_user):
        if previour_state and previous_tag_user:
            previous_user = previous_tag_user.username
        else:
            previous_user = ''
        return previous_user

    def converted_native(self, created):
        time_zone = created.replace(
            tzinfo=pytz.utc)
        convert_time = time_zone.astimezone(pytz.timezone('Asia/Kolkata'))
        time = convert_time.strftime('%b %d, %Y, %I:%M %p')
        return time

    def get_current_status(self):
        response = {'batch_id': self.workflow_cmt.batch.id,
                    'types': self.get_types_display(),
                    'id': self.id,
                    'status': self.status,
                    'commented_by': self.commented_by.username if self.commented_by else '',
                    'comment': self.comment,
                    'date_time': self.converted_native(self.created),
                    'survey_name': self.workflow_cmt.batch.current_status.survey.name if self.workflow_cmt.batch else '',
                    'survey_id': self.workflow_cmt.batch.current_status.survey.id if self.workflow_cmt.batch else '',
                    'curr_state_id': self.curr_state.id if self.curr_state else 0,
                    'curr_state_name': self.curr_state.workstate.name if self.curr_state else '',
                    'curr_user_name': self.workflow_cmt.curr_user.username,
                    'previour_state_id': self.previour_state.id if self.previour_state else 0,
                    'previour_state_name': self.previour_state.workstate.name if self.previour_state else '',
                    'next_state_id': self.next_state.id if self.next_state else 0,
                    'next_state_name': self.next_state.workstate.name if self.next_state else '',
                    'previous_tag_user_id': self.previous_tag_user.id if self.previous_tag_user else 0,
                    'previous_tag_user_name': self.get_previous_state_user(self.previour_state, self.previous_tag_user),
                    'next_tagged_user_id': self.next_tag_user.id if self.next_tag_user else 0,
                    'next_tagged_user_name': self.next_tag_user.username if self.next_tag_user else '', }
        return response
