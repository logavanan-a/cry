from ast import literal_eval
from datetime import datetime
import os
from masterdata.models import *
from common_methods import *
from userroles.models import UserRoles
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from uuid import uuid4
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey
from survey.manager import (
    AnswerQuerySet, SurveyStatusQuerySet, KpiReportQuerySet, DefaultLanguage
)
from django.core.exceptions import ValidationError
from constants import LEVEL_CHOICES
from django.apps import apps
from simple_history.models import HistoricalRecords
from django.contrib.postgres.fields import JSONField
from beneficiary.models import *
from facilities.models import (Facility,)

VALIDATION_TYPE = (('R', 'Required'), ('O', 'Optional'),)

## DataEntryLevel models
class DataEntryLevel(BaseContent):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    def __unicode__(self):
        # sets name as unicode
        return self.name

    def save(self, *args, **kwargs):
        # Customise save method
        self.slug = slugify('%s' % (
            self.name))
        super(DataEntryLevel, self).save(*args, **kwargs)


class LocationTypes(BaseContent):
    level_name = models.CharField(max_length=25)
    level_code = models.PositiveIntegerField()
    level_api = JSONField(blank=True, null=True)

    def __unicode__(self):
        return str(self.level_name or '')


class SurveyDataEntryConfig(BaseContent):
    survey = models.ForeignKey('survey')
    is_profile = models.BooleanField(default=True)
    # to store location or beneficairy types
    content_type1 = models.ForeignKey(
        ContentType, related_name="for_loc_bt_or_ft")
    object_id1 = models.PositiveIntegerField()
    genericForeignKey1 = GenericForeignKey('content_type1', 'object_id1')
    # to store facility or beneficairy sub type
    content_type2 = models.ForeignKey(
        ContentType, blank=True, null=True, related_name="for_facilty_bt")
    object_id2 = models.PositiveIntegerField(blank=True, null=True)
    genericForeignKey2 = GenericForeignKey('content_type2', 'object_id2')

    def __unicode__(self):
        return str(self.survey)


class Survey(BaseContent):
    #                                                     survey
    # tagging datacentre through survey
    INLINE_CHOICES = (('0', 'Normal'), ('1', 'Inline'))
    # survey period
    # eg: Daily based survey or weekly based survey
    PERIODICITY_CHOICES = (
        ('0', '---NA---'), ('1', 'Daily'), ('2', 'Weekly'),
        ('3', 'Monthly'), ('4', 'Quarterly'), ('5', 'Half Yearly'),
        ('6', 'Yearly'))
    # Del_Choices:Data Entry Level Choices
    DEL_CHOICES = (
        ('1', 'State'), ('2', 'District'), ('3', 'Taluk'),
        ('4', 'GramaPanchayath'), ('5', 'Village'), ('6', 'Hamlet'),
        ('7', 'HouseHold'), ('8', 'Plot'), ('9', 'Entity'),  # add b f c
    )
    SURVEY_TYPE_CHOICES = (
        (0, 'Static Survey'), (1, 'Dynamic Survey'),(2,'Periodic Survey'),
    )
    DISPLAY_CHOICES = (('single', 'single'), ('multiple', 'multiple'))
    # Fields for survey
    name = models.CharField(max_length=100)
    survey_type = models.IntegerField(choices=SURVEY_TYPE_CHOICES, default=0)
    data_entry_level = models.ForeignKey(DataEntryLevel)
    inline = models.CharField(
        max_length=20, choices=INLINE_CHOICES, default='1')
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_("order"),)
    display_type = models.CharField(
        default='multiple', choices=DISPLAY_CHOICES, max_length=25)
    piriodicity = models.CharField(
        'Periodicity',
        default='0', max_length=2, choices=PERIODICITY_CHOICES)
    expiry_age = models.PositiveIntegerField(default=0, blank=True, null=True)
    theme = models.ForeignKey(MasterLookUp,null=True)
    is_auto_fill = models.BooleanField(default=False,blank=True)
    survey_auto_fill = models.BooleanField(default=False,blank=True)
    survey_fill = models.ForeignKey('self',blank=True,null=True,related_name='fill_survey')

    def save(self, *args, **kwargs):
        # Customise save method
        self.slug = slugify('%s-%s' % (
            self.name, str(uuid4().int)[:4]))
        super(Survey, self).save(*args, **kwargs)

    #                                                         survey
    def __unicode__(self):
        # sets name as unicode
        return self.name

    def questions(self):
        # filtering all survey questions based on blocks
        return Question.objects.filter(block__survey=self, active=2)

    def onlyquestions(self):
        # filtering survey questions based on blocks
        return Question.objects.filter(block__survey=self, active=2, is_grid=False)

    def get_blocks(self):
        # filtering survey questions based on blocks
        return Block.objects.filter(survey=self, active=2)

    def get_final_block(self):
        # filtering survey questions based on blocks
        block_orders = Block.objects.filter(
            survey=self, active=2).values_list('order', flat=True)
        max_block = max(block_orders)
        return max_block

    def del_nicely(self):
        # Data Entry Level in words.
        return filter(lambda x: self.data_entry_level in x,
                      Survey.DEL_CHOICES)[0][1]

    def location_level(self):
        # Parent Level of DEL in words.
        # importing get_level from survey views
        from survey.views.survey_common_methods import get_level
        return get_level(self.del_nicely(), 'prev', True)

    @staticmethod
    def has_taken(party, date=None):
        # Check is survey started for a date
        return bool(Answer.objects.filter(
            content_type=ContentType.objects.get_for_model(party.__class__),
            object_id=party.id,
            data_level=date,)
        )

    def get_survey_type(self):
        sbmobj = SurveyBeneficiaryMap.objects.get_or_none(survey=self)
        cttype_obj = None
        if sbmobj:
            try:
                cttype = apps.get_model(
                    app_label="beneficiary", model_name=sbmobj.content_type1.model)
                cttype_obj = cttype.objects.get(id=sbmobj.object_id1)
            except:
                pass
        return cttype_obj

    def has_answers(self):
        # bool returns true or false
        # this returns whether particular block survey questions has answers
        return bool(JsonAnswer.objects.filter(active=2, survey=self))

    def export(self):
        # Export questions and choices into an html
        # Exported thing can be given to deo
        info = '<h2>\t\t%s<br/>\t\t%s</h2>' % (self.name, '-' * len(self.name))
        for q in Question.objects.filter(block__survey=self, qtype__in='CSR'):
            info += '<h3><br/><br/>%s<br/>%s<br/></h3>' % (
                q.text, '-' * len(q.text))
            for c in q.get_choices():
                info += '\t%s: %s<br/>' % (c.code, c.text)
        info += '''
        <font color="red"><br/><br/><b>Warning:</b> Before using this information, verify that choices in same question does not have same code.<br/>  If there are such choices, edit those choices and then export again.</font>
        '''
        return info

    def number_of_responses(self):
        return Answer.objects.filter(question__block__survey=self).values_list('creation_key', flat=True).distinct().count()

    def latest_sync(self):
        return Answer.objects.filter(question__block__survey=self).values_list('submission_date', flat=True).latest('submission_date')

    def latest_user(self):
        return Answer.objects.filter(question__block__survey=self).values_list('user__first_name', flat=True).latest('id')

    def is_skip_survey(self):
        choices = Choice.objects.filter(
            active=2, skip_question__id__gt=0, question__block__survey=self)
        return True if choices else False

    def identify_skip_question(self):
        choice = Choice.objects.filter(
            active=2, skip_question__id__gt=0, question__block__survey=self).order_by('question__id', 'code')
        return choice[0].question

    def get_next_skip_question(self, prev_skip):
        choice = Choice.objects.filter(active=2, question__code__gt=prev_skip, question__block__survey=self).order_by(
            'skip_question__id', 'skip_question__code').exclude(skip_question=None).first()
        return choice.skip_question.code if choice else None

    def get_prev_skip_question(self, pres_skip):
        choice = Choice.objects.filter(active=2, question__code__lt=pres_skip, question__block__survey=self).order_by(
            'skip_question__id', 'skip_question__code').exclude(skip_question=None).first()
        return choice.question.code if choice else None

    def get_survey_depth(self):
        skip_questions = list(set(Choice.objects.filter(
            question__block__survey=self,active=2 , question__active = 2).values_list('skip_question', flat=True)))
        survey_questions = Question.objects.filter(block__survey=self)
        skip_questions.remove(None)
        depths = []
        for sq in skip_questions:
            ques = survey_questions.filter(active=2,id=sq)
            if ques:
                depths.append(ques[0].get_depth())
        # [Question.objects.get_or_none(
        #     active=2, id=i).get_depth() for i in skip_questions]
        return max(depths) if depths else 0

    def get_draft_answers(self):
        skip_questions = list(set(Choice.objects.filter(
            active=2,question__block__survey=self).values_list('skip_question', flat=True)))
        skip_questions.remove(None)
        questions = Question.objects.filter(
            block__survey__id=self.id, mandatory=True).exclude(id__in=skip_questions)
        if questions:
            first_id = questions.first().id
            last_id = questions.last().id
            json_answer = JsonAnswer.objects.filter(active=2,
                survey=self).values_list('response', 'id')
            exclude_list = []
            for el, ek in json_answer:
                if not (el.get(str(first_id)) and el.get(str(last_id))):
                    exclude_list.append(ek)
            return exclude_list
        return []

    def get_extended_profile_questions(self):
        questions = Question.objects.filter(active=2,is_profile=True,block__survey=self)
        return questions

    def validate_configuration(self):
        for ques in Question.objects.filter(active=2,block__survey=self,qtype__in=['S','C','R'],mandatory=True):
            if not ques.get_choices():
                return False
        return True

    def get_periodic_questions(self):
        q_id = Question.objects.filter(active=2,display=True,block__survey__id=self.id).values_list('id',flat=True)
        return ",".join([str(i) for i in q_id])

    def get_survey_rule_engine(self):
        reobj = {}
        try:
            obj = DetailedUserSurveyMap.objects.get_or_none(survey_id=self,active=2)
            if obj and obj.rule_engine:
                reobj = obj.rule_engine
            else:
                reobj = ''
        except:
            reobj = {'Please check survey rule engine config'}
        return reobj

class Block(BaseContent):
    #                                                          Block
    # survey is based on blocks
    # so survey is a foreign key
    # Block type is giving as choices

    survey = models.ForeignKey(Survey)
    name = models.CharField(max_length=100, blank=False, null=False)
    order = models.IntegerField(null=True, blank=True)
    code = models.IntegerField(default=0)
    language_code = JSONField(default={},**OPTIONAL)

    def __unicode__(self):
        # sets name as unicode
        return self.name

    def get_questions(self):
        # filtering block based questions
        return Question.objects.filter(block=self, active=2).order_by('id')

    def get_skip_questions_ids(self, order=''):
        final_list = []
        questions = Question.objects.filter(
            block=self, active=2, parent=None).order_by('id')
        for i in questions:
            for j in i.get_choices():
                if j.skip_question or j.code == -1:
                    final_list.append(j.skip_question.id)
        return final_list

    def get_skip_questions(self, order=''):
        final_list = []
        has_next = True
        questions = Question.objects.filter(
            block=self, active=2, parent=None, order__gt=order).order_by('id')
        for i in questions:
            final_list.append(i)
            for j in i.get_choices():
                if j.skip_question or j.code == -1:
                    break
            else:
                continue  # executed if the loop ended normally (no break)
            break
        if len(final_list) == questions.count():
            has_next = False
        return final_list, has_next

    def get_next_questions(self, order=''):
        final_list = []
        has_next = True
        questions = Question.objects.filter(
            block=self, active=2, parent=None, order__gt=order).order_by('id')
        for i in questions:
            final_list.append(i)
            for j in i.get_choices():
                if j.skip_question or j.code == -1:
                    break
            else:
                continue  # executed if the loop ended normally (no break)
            break
        if len(final_list) == questions.count():
            has_next = False
        return final_list, has_next

    def get_last_question_order(self, order=''):
        orders = max([i.order for i in self.get_skip_questions(order)[0]])

        return orders

    def get_block_last_question_order(self, order=''):
        qonj = Question.objects.filter(
            block=self, active=2, parent=None).values_list('order', flat=True)
        max_val = max(qonj)
        return max_val

    def get_parentnone_questions(self):
        # filtering block based questions
        return Question.objects.filter(block=self, active=2, parent=None).order_by('id')

    def get_assessments_questions(self):
        # this function returns block based questions and is ording by id.
        return Question.objects.filter(block=self, active=2).\
            exclude(parent__parent=None).order_by('id')

    def get_assessments_questions_wp(self):
        # filter assessment questions based on block
        return Question.objects.filter(block=self, active=2).order_by('id')

    def get_assessments(self):
        # filtering assessment based on particular block which  are active
        return Assessment.objects.filter(block=self, active=2).\
            order_by('id')


class Question(BaseContent):
    # Question
    # In survey we have multiple type of questions
    # eg for text input: what is your name?
    # eg for select one choice : gender= male or female
    # Radio List:This question type collects input from a list of radio buttons
    # Checkbox list : provides a multi selection check box group
    # that can be dynamically generated with data binding.
    QTYPE_CHOICES = (
        ('T', 'Text Input'), ('S', 'Select One Choice'), ('R', 'Radio List'),
        ('C', 'Checkbox List'), ('D', 'Date'), ('G', 'GPS'), ('I', 'Image'),
        ('V', 'Videos'), ('E', 'Email'), ('Cl','Cluster'),
        ('GD', 'Grid'), ('In', 'Inline'),('N', 'None'),
    )
    # setting validation type option for questions
    VALIDATION_CHOICES = (
        (0, 'Digit'), (1, 'Number'), (2, 'Alphabet'),
        (3, 'Alpha Numeric'), (4, 'No Validation'), (6, 'Mobile Number'),
        (7, 'Landline'), (8, 'Date'), (9, 'Time'), (10, 'Only Alpha Numeric'), (11, 'QuestionBased Validation'),(12,'Auto Calculate'),(13,'Api Call')
    )
    META_TYPE_CHOICES = (
        (0, 'Normal'), (1, 'Village Name'), (2, 'Customer Id'),
        (3, 'Piriodicity'), (4, 'Consent Status'), (5, 'Ruban Code')
    )

    block = models.ForeignKey(Block, verbose_name=_('Blocks'))
    qtype = models.CharField(_('question type'), max_length=2,
                             choices=QTYPE_CHOICES)

    text = models.CharField(_('question text'), max_length=500)
    validation = models.IntegerField(choices=VALIDATION_CHOICES,
                                     blank=True, null=True)
    order = models.IntegerField(null=True, blank=True)
    code = models.IntegerField(default=0)
    help_text = models.CharField(max_length=100, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True,related_name="parent_question")

    mandatory = models.BooleanField(default=True)
    display = models.BooleanField(default=False)
    hidden = models.PositiveIntegerField(default=0)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    is_profile = models.BooleanField(default=False)
    is_grid = models.BooleanField(default=False)
    language_code = JSONField(default={},**OPTIONAL)
#    question_auto_fill = models.ManyToManyField("self",blank=True,symmetrical=False,)
    master_choice = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # save method                                             Question
        # Custom save method for question to set order
        if not self.order:
            try:
                order = Question.objects.filter(
                    block__survey=self.block.survey
                ).order_by('order').reverse()[0].order
            except:
                order = 0
            self.order = int(
                order + 1) if order == int(order) else int(order + 2)
        super(Question, self).save(*args, **kwargs)

    def name(self):
        # returns text
        return self.text

    def __unicode__(self):
        #                                                         Question
        # sets name as unicode
        return "%s - %s---(%s)" % (self.text, self.code, self.block.survey)

    def is_skip_question(self):
        choice = Choice.objects.filter(active=2,question=self)
        if choice:
            for i in choice:
                if i.skip_question.all():
                    return True
            return False
        else:
            return False
        # return True if choice.skip_question.all() else False

    def get_parent_skip_question(self):
        choice = Choice.objects.filter(active=2,skip_question__id=self.id)
        if choice:
            return choice[0].question
        else:
            return choice

    def get_child_survey(self, prev_surveys=[]):
        child_survey = Survey.objects.filter(active=2, parent_survey=self)

        for i in child_survey:
            if i.is_parent():
                prev_surveys.append(i)
                i.get_child_survey(prev_surveys)
            else:
                prev_surveys.append(i)
        return prev_surveys if prev_surveys else []

    def get_full_parent_question(self):
        obj = self
        while obj.get_parent_skip_question():
            obj = obj.get_parent_skip_question()
        return obj

    def get_other_option_choices(self, choice_id):
        question_choices = Choice.objects.filter(active=2, question=self.id)
        previous_code = None
        previous_code = question_choices.exclude(
            id=choice_id).values_list('skip_question', flat=True)
        return max(previous_code)

    def get_depth(self):
        depth = 0
        obj = self
        while obj.get_parent_skip_question():
            depth = depth + 1
            obj = obj.get_parent_skip_question()
        return depth

    def get_parent_at_depth(self, given_depth):
        depth = self.block.survey.get_survey_depth()
        obj = self
        while obj.get_parent_skip_question():

            if depth == given_depth:
                return obj.get_parent_skip_question()
            else:
                depth = depth - 1
                obj = obj.get_parent_skip_question()
        return obj

    def get_skip_back_questions(self):
        
        parent_question = self.get_parent_skip_question()
        if parent_question.get_parent_skip_question():
            ch = Choice.objects.filter(active=2,question=parent_question.get_parent_skip_question(
            ), skip_question__id__gt=parent_question.code).values_list('skip_question', flat=True)
            if ch:
                ch = Question.objects.filter(active=2,id__in=ch)
                ch = get_filter_skip_question(ch)
            elif not ch and not parent_question.get_parent_skip_question():
                survey = Question.objects.get(id=self.id).block.survey
                skip_questions = list(set(Choice.objects.filter(
                    active=2,question__block__survey=survey).values_list('skip_question', flat=True)))
                skip_questions.remove(None)
                ch = Question.objects.filter(active=2,
                    code__gt=parent_question.code, block__survey=self.block.survey).exclude(id__in=skip_questions)
                ch = get_filter_skip_question(ch)
            return ch
        else:
            survey = Question.objects.get(id=self.id).block.survey
            skip_questions = list(set(Choice.objects.filter(
                active=2,question__block__survey=survey).values_list('skip_question', flat=True)))
            skip_questions.remove(None)
            ch = Question.objects.filter(active=2,
                code__gt=parent_question.code, block__survey=self.block.survey).exclude(id__in=skip_questions)
            ch = get_filter_skip_question(ch)
            return ch

    def get_next_set_question(self, choice_id):
        survey = Question.objects.get(id=self.id).block.survey
        skip_questions = list(set(Choice.objects.filter(
            active=2,question__block__survey=survey).values_list('skip_question', flat=True)))
        skip_questions.remove(None)
        quest_depth = self.get_depth()

        if self.get_depth() > 0:

            if int(choice_id) == 0:
                while quest_depth > 0:
                    nxt_ques = Choice.objects.filter(active=2,question=self.get_parent_at_depth(
                        quest_depth - 1), skip_question__id=self.get_parent_skip_question().id).first()
                    if nxt_ques:
                        nxt_ques = nxt_ques.skip_question.filter(
                            active=2,code__gt=self.code)
                        if nxt_ques:
                            return get_filter_skip_question(nxt_ques)
                        else:
                            quest_depth = quest_depth - 1
                    else:
                        quest_depth = quest_depth - 1

                return self.get_skip_back_questions()
            else:
                nxt_ques = Choice.objects.filter(
                    active=2,id=choice_id).values_list('skip_question')
                nxt_ques = get_filter_skip_question(
                    Question.objects.filter(active=2,id__in=nxt_ques).order_by('code'))
                if nxt_ques.get('last') != None:
                    return nxt_ques
                else:
                    quest_depth = self.get_depth()
                    choice = Choice.objects.get(id=choice_id)
                    if choice.skip_question.all():
                        return choice.get_skip_questions()
                    else:
                        while quest_depth > 0:
                            nxt_ques = Choice.objects.filter(active=2,question=self.get_parent_at_depth(
                                quest_depth - 1), skip_question__id=self.get_parent_skip_question().id).first()
                            if nxt_ques:
                                nxt_ques = nxt_ques.skip_question.filter(
                                    active=2,code__gt=self.code)

                                if nxt_ques:
                                    return get_filter_skip_question(nxt_ques)
                                else:
                                    quest_depth = quest_depth - 1
                            else:
                                quest_depth = quest_depth - 1
                        next_set = get_filter_skip_question(Question.objects.filter(
                            active=2,block__survey=survey, code__gt=self.code).exclude(id__in=skip_questions))
                        return next_set
        else:

            if choice_id > 0:
                choice = Choice.objects.get(id=choice_id)
                if choice.skip_question.all():
                    return choice.get_skip_questions()
                else:
                    next_set = get_filter_skip_question(Question.objects.filter(
                        active=2,block__survey=survey, code__gt=self.code).exclude(id__in=skip_questions))
                    return next_set
            return choice.question

    def get_next_question(self, choice_id):
        survey = Question.objects.get(id=self.id).block.survey
        skip_questions = list(set(Choice.objects.filter(
            active=2,question__block__survey=survey).values_list('skip_question', flat=True)))
        skip_questions.remove(None)
        if choice_id == 0:
            if self.get_parent_skip_question().is_skip_question():
                choice = Choice.objects.filter(
                    active=2,question=self.get_parent_skip_question().get_parent_skip_question()).first()
                try:
                    choice = choice.skip_question.filter(code__gt=self.code)
                    for i in choice:
                        if i.is_skip_question():
                            return i
                    if choice.last():
                        return choice.last()
                except:

                    ques = Question.objects.filter(active=2,code__gt=self.get_parent_skip_question(
                    ).code).exclude(id__in=skip_questions).last()
                    return ques if ques else None
        elif self.get_parent_skip_question():
            choice = Choice.objects.filter(Q(question=self) | Q(
                skip_question__id=self.id), id=choice_id,active=2).first()
            if choice:
                choice = choice.skip_question.filter(active=2,code__gt=self.code)
                for i in choice:
                    if i.is_skip_question():
                        return i
                if choice.last():
                    return choice.last()
                else:
                    ques = Question.objects.filter(active=2,code__gt=self.code).exclude(
                        id__in=skip_questions).last()
                    return ques if ques else None
            else:
                ques = Question.objects.filter(active=2,code__gt=self.code).exclude(
                    id__in=skip_questions).last()
                return ques if ques else None
        else:
            choice = Choice.objects.filter(
                active=2,skip_question__id__gt=self.id).first()
            return choice.question

    def get_choices(self):
        #                                                         Question
        # returns choice based on active question and ordered by order
        return Choice.objects.filter(question=self, active=2).order_by('order')

    def get_subquestions(self):
        #                                                         Question
        # returns questions based on parent select
        return Question.objects.filter(parent=self, active=2, is_grid=False).order_by('id')

    def get_assessments(self):
        #                                                         Question
        # returns questions based on parent select
        return Question.objects.filter(parent=self, active=2, is_grid=True).order_by('id')

    def choice_list(self,partner,lid=1):
        choices = Choice.objects.filter(active=2,question__id=self.id)
        ques = Question.objects.get(id=self.id).master_choice ## added newly
        if self.qtype not in ['R','S','C']:
            return []
        elif choices:
            return [{"id": i.id, "choice": i.text if int(lid) ==1 else i.language_code[str(lid)]} for i in choices]
        elif ques == True: ## added newly - from 
            master = MasterChoice.objects.get(question_id=self.id)
            if master.master_type == "FT":
                return [{"id":str(i.id), "choice": i.name } \

                for i in Facility.objects.filter(partner_id=partner, facility_type_id=int(master.code))]
            elif master.master_type == "BF":
                return [{"id":str(i.id), "choice": i.name } \
                for i in Beneficiary.objects.filter(partner_id=partner, beneficiary_type_id=int(master.code))]

            else:
                return [] ## added newly - to
        else:
            return []

    def get_validation(self):
        return QuestionValidation.objects.get_or_none(question_id=self.id)

    def is_survey_end_question(self):
        survey = self.block.survey
        last_question = Question.objects.filter(
            active=2, block__survey=survey).order_by('code').last()
        if int(last_question.id) == int(self.id):
            return True
        else:
            return False

    def is_choice_level_end_question(self):

        return False

    def is_survey_regular_end_question(self):
        survey = self.block.survey
        skip_questions = list(set(Choice.objects.filter(
            active=2,question__block__survey=survey).values_list('skip_question', flat=True)))
        skip_questions.remove(None)
        last_question = Question.objects.filter(
            active=2, block__survey=survey).order_by('code').exclude(id__in=skip_questions).last()
        if int(last_question.id) == int(self.id):
            return True
        else:
            return False

    def question_text_lang(self,lid=1):
        try:
            return self.text if int(lid) == 1 else self.language_code[str(lid)]
        except Exception as e:
            return self.text

    def translation_text(self):
        language_translations = []
        languages = Language.objects.filter(active=2).exclude(name="English").values_list('id',flat=True)
        for l in list(languages):
            l_dic = {}
            l_dic["id"]=l
            l_dic["text"]=self.language_code.get(str(l)) or ""
            language_translations.append(l_dic)
        return language_translations

    def choice_dict(self):
        choices = Choice.objects.filter(active=2,question__id=self.id).values_list('id','text')
        return {i:t for i,t in choices}

    def question_based_validation(self):
        if not self.validation:
            return []
        elif int(self.validation) == 11:
            validation = self.get_validation()
            return [{"data_type":"Number","operator":validation.validation_condition,
                     "value":"","question_id":self.parent_id,"form_id":self.block.survey.id,"error_msg":validation.message}]
        else:
            return []

    def api_auto_fill(self):
        auto_fill = {}
        if self.block.survey.is_auto_fill:
            auto_fill['form_id']=self.block.survey.id
            auto_fill['question_ids'] = str(self.id)
            auto_fill['operator'] = self.get_auto_operator()
            if not auto_fill['question_ids']:
                auto_fill = {}
            return auto_fill
        elif self.block.survey.survey_auto_fill:
            auto_fill['form_id'] = self.block.survey.survey_fill.id
            auto_fill['question_ids'] = ",".join([str(i) for i in self.get_auto_fill_questions()])
            if not auto_fill['question_ids']:
                auto_fill = {}
            return auto_fill
        elif MasterChoice.objects.filter(question=self,active=2).exists():
	    mstyp = {"BF":1,"FT":0}	
            mastr_ch = MasterChoice.objects.get_or_none(question=self,active=2)
            sur = SurveyDataEntryConfig.objects.get(survey_id = self.block.survey.id)
            auto_fill['isMultiSel'] = 1 if self.master_choice == True and self.qtype=='C' else 0
            auto_fill['isBen'] = mstyp.get(mastr_ch.master_type,'') if mastr_ch else ''
            auto_fill['typeCode'] = str(mastr_ch.code)  if mastr_ch else ""
            auto_fill['is_specific'] = 1 if self.master_choice == True and self.qtype=='T' and mastr_ch.master_type == 'BF' and sur.object_id1==2 else 0
            return auto_fill
        else:
            auto_fill['form_id'] = self.block.survey.id
            auto_fill['question_ids'] = ",".join([str(i) for i in self.get_auto_fill_questions()])
            auto_fill['operator'] = self.get_auto_operator()
            if not auto_fill['question_ids']:
                auto_fill = {}
            return auto_fill
                
            
        return {'form_id':0,'question_ids':""}
    
    
    def get_master_choice(self):
        mastr_ch = None
        try:
            mastr_ch = MasterChoice.objects.get_or_none(question=self,active=2)
        except:
            mastr_ch = None
        return mastr_ch

    def get_master_choice(self):
        mastr_ch = None
        try:
            mastr_ch = MasterChoice.objects.get_or_none(question=self,active=2)
        except:
            mastr_ch = None
        return mastr_ch

    def get_auto_fill_questions(self):
        try:
            obj = Questionautofill.objects.filter(question=self).latest('id')
            obj = obj.question_sequence.split(',') if obj.question_sequence else []
        except:
            obj = []
        return obj

    def get_auto_operator(self):
        try:
            l = len(self.get_auto_fill_questions())
            obj = QuestionValidation.objects.get(question = self)
            m = '+' + ',' + ','.join([str(obj.validation_condition) for i in range(l-1)])
        except:
            m = ''
        return m

    class Meta:
        #                                                         Question
        # Don't create a table in database
        # This table is abstract
        ordering = ('block', 'order')

CHOICE_TYPE = (("BF", 'Beneficiary',),("FT", 'Facility',),)
class MasterChoice(BaseContent):
    question = models.ForeignKey(Question, blank=True, null=True)
    master_type =models.CharField(choices=CHOICE_TYPE, max_length=50, blank=True, null=True)
    code = models.CharField(max_length=60, blank=True, null=True)

    def __unicode__(self):
        return self.master_type


class Questionautofill(BaseContent):
    question = models.ForeignKey(Question, blank=True, null=True,related_name="autofill_parent_question")
    question_auto_fill = models.ManyToManyField(Question,blank=True,symmetrical=False,related_name="autofillquestion")
    question_sequence = models.CharField(max_length=500, blank=True, null=True)
    
    def __unicode__(self):
        return str(self.id)


class Choice(BaseContent):
    #                                                          choice
    # question has choices
    question = models.ForeignKey(Question, related_name='choices',
                                 verbose_name=_('question'), blank=True, null=True)
    text = models.CharField(_('choice text'), max_length=500)
    code = models.IntegerField()
    order = models.FloatField(blank=True)
    skip_question = models.ManyToManyField(Question, related_name='skip_question',
                                           blank=True)
    language_code = JSONField(default={},**OPTIONAL)

    def save(self, *args, **kwargs):
        self.order = self.code
        super(Choice, self).save(*args, **kwargs)

    def name(self):
        #                                                          choice
        # returns text
        return self.text

    def get_skip_questions(self):
        choice = None
        skip_questions = Choice.objects.get(
            id=self.id).skip_question.all().order_by('code')
        for i in skip_questions:
            choice = i
            if i.is_skip_question():
                break
        return {'first': skip_questions.first(), 'last': choice}

    def get_assessment(self):
        try:
            return MetricsQuestionConfiguration.objects.get(m_question=self.question).id
        except:
            return 0

    def copy(self, commit=True, question=None):
        #                                                          choice
        # Create a copy of given item and save in database
        if commit and commit != True:
            question = commit
        new_choice = super(Choice, self).copy(commit)
        if question:
            new_choice.question = question
        if commit:
            new_choice.save()
        return new_choice

    def translation_text(self):
        language_translations = []
        languages = Language.objects.filter(active=2).values_list('id',flat=True)
        for l in languages:
            l_dic = {"id":l}
            l_dic["text"]=self.language_code.get(str(l))
            language_translations.append(l_dic)
        return language_translations

    def __unicode__(self):
        #                                                          choice
        # sets name as unicode
        try:
            return "%s || %s || %s" % (self.question.block.survey, self.question, self.text)
        except:
            return "%s || %s || %s" % (self.question.block.survey, self.question.id, self.text)

    class Meta:
        # Don't create a table in database
        # This table is abstract
        ordering = ('question', 'order')


class JsonAnswer(BaseContent):
    INTERFACE_TYPES = (('0','Web'),('1','App'),('2','Migrated Data'))
    user = models.ForeignKey(User, related_name='jsonanswers',
                             verbose_name=_('jsonuser'),
                             blank=True, null=True)
    creation_key = models.CharField(max_length=60, blank=True, null=True)
    submission_date = models.DateTimeField(auto_now=True)
    survey = models.ForeignKey(Survey, blank=True, null=True)
    app_answer_on = models.DateTimeField(blank=True, null=True)
    app_answer_data = models.PositiveIntegerField(blank=True, null=True)
    response = JSONField(default={})
    cluster = JSONField(default={})
    interface = models.CharField(choices=INTERFACE_TYPES,default=1,max_length=2)
    history = HistoricalRecords()

    def __unicode__(self):
        # Unicode for answer
        return str(self.survey) + '__' + str(self.user)

    def get_aad(self):
        return AppAnswerData.objects.get(id=self.app_answer_data)

    def get_partner(self):
        try:
            partner_id = UserRoles.objects.get(user=self.user).partner.id
        except:
            partner_id  = None
        return partner_id

    def get_beneficiary(self):
        bene_type = bene_id = loc_id = 0
        get_response = self.cluster[0].get('beneficiary', 0) or 0
        if get_response:
            bene_type, bene_id = get_response.get(
                'beneficiary_type_id', 0), get_response.get('id', 0)
            if bene_type and bene_id:
                try:
                    loc = Beneficiary.objects.get(id=bene_id)
                    new_dict = literal_eval(loc.jsondata['address'][0])
                    loc_id = int(new_dict.values()[0].get(
                        'boundary_id', 0) or 0)
                except:
                    pass
        return bene_type, bene_id, loc_id

    def convert_into_object(self, data_json):
        try:
            data = literal_eval(data_json)
        except:
            data = data_json
        return data

    def facility_village_id(self, loc_dic, key, default=0):
        found = loc_dic.get(key, [''])
        if found[0]:
            found = int(found[0])
        else:
            found = default
        return found

    def get_facility(self):
        fac_type = fac_id = boundary_id = 0
        get_response = self.cluster[0].get('facility', 0) or 0
        if get_response:
            fac_type, fac_id = get_response.get(
                'facility_type_id', 0), get_response.get('id', 0)
            if fac_type and fac_id:
                try:
                    loc = Facility.objects.get(id=fac_id)
                    boundary_id = self.facility_village_id(
                        self.convert_into_object(loc.jsondata), 'boundary_id')
                except:
                    pass
        return fac_type, fac_id, boundary_id


class Answer(BaseContent):

    user = models.ForeignKey(User, related_name='answers',
                             verbose_name=_('user'),
                             blank=True, null=True)
    question = models.ForeignKey(Question, related_name='answers', blank=True, null=True,
                                 verbose_name=_('question'),
                                 )

    text = models.TextField(_('answer text'), blank=True, null=True)
    choice = models.ForeignKey(Choice, blank=True, null=True)
    multy_choice = models.ManyToManyField(Choice,
                                          blank=True,
                                          related_name="multy_answer_set")
    date = models.DateField(blank=True, null=True)
    creation_key = models.CharField(max_length=50, blank=True, null=True)

    submission_date = models.DateTimeField(auto_now=True)
    inline = models.PositiveIntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    app_answer_on = models.DateTimeField(blank=True, null=True)
    app_answer_data = models.PositiveIntegerField(blank=True, null=True)
    objects = AnswerQuerySet.as_manager()
    metrics = models.ForeignKey(Question, blank=True, null=True)

    def __unicode__(self):
        # Unicode for answer
        if self.text:
            return self.text or str(self.date or self.choice.text or
                                    '[%s]' % ', '.join([i.text for i in self.multy_choice.all()])) or ' '
        else:
            return ''

    def responce(self):
        # Nice representation for response
        # Depending on type of question

        if self.text:
            return self.text
        elif self.date:
            return "{:%m/%d/%Y}".format(self.date)
        elif self.multy_choice.all():
            return [i.pk for i in self.multy_choice.all()]
        elif self.choice:
            return self.choice.pk

    def get_aad(self):
        from survey_web_service.models import AppAnswerData
        return AppAnswerData.objects.get(id=self.app_answer_data)

    def responce_nicely(self):
        # Nice representation for response
        # Depending on type of question
        if self.multy_choice.all():
            return ', '.join([i.text for i in self.multy_choice.all()])
        elif self.choice:
            return self.choice.text
        return self.responce()

    def force_save(self, *args, **kwargs):

        try:
            obj = Answer.objects.get(
                question=self.question,
                content_type=self.content_type,
                object_id=self.object_id,
                data_level=self.data_level,
                inline=self.inline,
                creation_key=self.creation_key,
            )
            obj.delete()
        except:
            pass

        ans = self.text
        self.text = None
        self.choice = None
        self.date = None

        qt = self.question.qtype

        if qt == 'T':
            self.text = ans
        elif qt == 'S' or qt == 'R':
            if ans:
                self.choice = Choice.objects.get(pk=ans)
        elif qt == 'C':
            self.save()
            for i in self.multy_choice.all():
                self.multy_choice.remove(i)
            if ans:
                for i in [i for i in ans.split(',') if i]:
                    choice = Choice.objects.get(pk=int(i))
                    self.multy_choice.add(choice)
        elif qt == 'D':
            from datetime import datetime
            self.date = datetime.strptime(ans, "%m/%d/%Y") if ans else None

        self.save()


class ProjectSurvey(BaseContent):

    # Connects Program to survey
    # Project have a project manager

    name = models.CharField(max_length=100)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        # Unicode of project
        return self.name


class DataCentre(BaseContent):

    # DataCentre is a team of a dcc and deos
    # Projects can be assigned to dcs

    name = models.CharField(max_length=100)
    deo = models.ManyToManyField('userroles.UserRoles',
                                 related_name='data_centre',
                                 blank=True)
    project = models.ForeignKey('ProjectSurvey')
    cordinator = models.ForeignKey('userroles.UserRoles',
                                   related_name='datacentre',
                                   blank=True, null=True)

    def __unicode__(self):
        # Unicoe of dc
        return self.name

    def deolist(self):
        # List of deos in a datacenter
        return ', '.join(map(
            lambda x: x.user.first_name.capitalize(),
            self.deo.all()
        ))


class DetailedUserSurveyMap(BaseContent):
    LEVEL_CHOICES = (
        (0, 'Application level'), (1, 'Location level'),
    )
    user = models.ManyToManyField(UserRoles)
    survey = models.ForeignKey('Survey')

    level = models.IntegerField(choices=LEVEL_CHOICES, blank=True, null=True)
    rule_engine = JSONField(blank=True, null=True)

    def __unicode__(self):
        # unicode for DetailedUserSurveyMap
        return str(self.survey)


class SurveyPartnerExtension(BaseContent):
    survey = models.ForeignKey(Survey)
    partner = models.ManyToManyField(Partner)
    expiry_age = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return str(self.survey) + '__' + str(self.expiry_age)


class UsmCronTracker(BaseContent):
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)


class Language(BaseContent):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    char_field1 = models.CharField(max_length=500, blank=True, null=True)
    char_field2 = models.CharField(max_length=500, blank=True, null=True)
    integer_field1 = models.IntegerField(default=0)
    integer_field2 = models.IntegerField(default=0)
    states = models.ManyToManyField(Boundary,**OPTIONAL)

    def __unicode__(self):
        return self.name


class SurveyLanguageTranslation(BaseContent):
    survey = models.ForeignKey(
        Survey, related_name='surveylanguagetranslation')
    language = models.ManyToManyField(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class QuestionLanguageTranslation(BaseContent):
    question = models.ForeignKey(
        Question, related_name='questionlanguagetranslation')
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class ChoiceLanguageTranslation(BaseContent):
    choice = models.ForeignKey(
        Choice, related_name='choicelanguagetranslation')
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class BlockLanguageTranslation(BaseContent):
    block = models.ForeignKey(Block, related_name='blocklanguagetranslation')
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class MetricsQuestionLanguage(BaseContent):
    metrics = models.ForeignKey(
        Question, related_name='MetricsQuestionLanguage')
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class UserLanguage(BaseContent):
    user = models.ForeignKey(User)
    language = models.ForeignKey(Language)

    def __unicode__(self):
        return "%s - %s" % (self.user, self.language.name)


class SkipMandatory(BaseContent):
    question = models.ForeignKey(Question)
    question_validation = models.CharField(
        max_length=255, blank=True, null=True)
    sub_module_type = models.CharField(max_length=255, blank=True, null=True)
    char_field1 = models.CharField(max_length=500, blank=True, null=True)
    char_field2 = models.CharField(max_length=500, blank=True, null=True)
    integer_field1 = models.IntegerField(default=0)
    integer_field2 = models.IntegerField(default=0)

    def __unicode__(self):
        return self.question_validation


class UserCluster(BaseContent):
    REPORT_CHOICES = (
        (1, 'Daily',),
        (2, 'Weekly',),
        (3, 'Monthly',),
    )
    CATEGORY_CHOICES = (
        (1, 'Activity',),
        (2, 'Tracking',),
    )
    cluster_name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ManyToManyField(User)
    primary_email = models.CharField(max_length=500, blank=True, null=True)
    secondary_email = models.CharField(max_length=1000, blank=True, null=True)
    bcc = models.CharField(max_length=1000, blank=True, null=True)
    report_type = models.IntegerField(
        choices=REPORT_CHOICES, blank=True, null=True)
    report_subject = models.CharField(max_length=500, blank=True, null=True)
    category = models.IntegerField(
        choices=CATEGORY_CHOICES, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.cluster_name, self.report_type)


class AppLoginDetails(BaseContent):
    user = models.ForeignKey(User)
    surveyversion = models.CharField(max_length=10, blank=True, null=True)
    lang_code = models.CharField(max_length=10, blank=True, null=True)
    tabtime = models.DateTimeField(blank=True, null=True)
    sdc = models.PositiveIntegerField(default=0)
    itype = models.CharField(max_length=10, blank=True, null=True)
    version_number = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return self.user.username


class AppAnswerData(BaseContent):
    interface = models.IntegerField(default=0, choices=(
        (0, 'Web'), (2, 'Android App'),
    ))
    latitude = models.CharField(max_length=255, blank=True, null=True)
    longitude = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    version_number = models.CharField(max_length=10, blank=True, null=True)
    app_version = models.CharField(max_length=10, blank=True, null=True)
    language_id = models.CharField(max_length=10, blank=True, null=True)
    imei = models.CharField(max_length=100, blank=True, null=True)
    survey_id = models.CharField(max_length=50, blank=True, null=True)
    mode = models.CharField(max_length=50, blank=True, null=True)
    part2_charge = models.CharField(max_length=50, blank=True, null=True)
    f_sy = models.CharField(max_length=50, blank=True, null=True)
    gps_tracker = models.CharField(max_length=10, blank=True, null=True)
    survey_status = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    sp_s_o = models.DateTimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    cluster_id = models.CharField(max_length=50, blank=True, null=True)
    cell_id = models.CharField(max_length=100, blank=True, null=True)
    signal_strength = models.CharField(max_length=50, blank=True, null=True)
    lac = models.CharField(max_length=50, blank=True, null=True)
    mcc = models.CharField(max_length=50, blank=True, null=True)
    mnc = models.CharField(max_length=50, blank=True, null=True)
    la = models.CharField(max_length=50, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    network_type = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    chargeleft = models.CharField(max_length=20, blank=True, null=True)
    charge_connected = models.CharField(max_length=50, blank=True, null=True)
    last_chargetime = models.CharField(max_length=50, blank=True, null=True)
    sim_serialnumber = models.CharField(max_length=100, blank=True, null=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)
    is_cus_rom = models.CharField(max_length=50, blank=True, null=True)
    pe_r = models.CharField(max_length=50, blank=True, null=True)
    ospr = models.CharField(max_length=50, blank=True, null=True)
    lqc = models.CharField(max_length=50, blank=True, null=True)
    sdc = models.CharField(max_length=50, blank=True, null=True)
    dom_id = models.CharField(max_length=50, blank=True, null=True)
    survey_part = models.CharField(max_length=50, blank=True, null=True)
    c_status = models.CharField(max_length=50, blank=True, null=True)
    stoken_sent = models.CharField(max_length=255, blank=True, null=True)
    sample_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.PositiveIntegerField(default=0, choices=(
        (0, '------'), (1, 'Valid'), (2, 'Invalid'),
    ))
    description = models.TextField(null=True)

    def __unicode__(self):
        return str(self.id)


class Version(BaseContent):
    survey = models.ForeignKey(Survey)
    version_number = models.CharField(max_length=255, blank=True, null=True)
    create_by = models.ForeignKey(User, blank=True, null=True)
    changes = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    def __unicode__(self):
        return '%s || %s || %s' % (self.survey, self.version_number, self.changes)

    def get_action(self, **kwargs):
        status = ''
        obj = kwargs.get('obj')
        if float(self.version_number) == 0.0:
            status = 'C'
        elif float(self.version_number) >= 0.1 and obj:
            model_name = obj.__class__.__name__.lower()
            version_list = Version.objects.filter(survey=self.survey)
            vs_list = version_list.filter(content_type__model__iexact=model_name,
                                          object_id=int(obj.id)).order_by('-id')
            if len(vs_list) >= 1:
                status = vs_list[0].action
            else:
                status = 'C'
        return status


class SurveySkip(BaseContent):
    survey = models.ForeignKey(Survey, related_name='survey')
    skipto_survey = models.ForeignKey(
        Survey, blank=True, null=True, related_name='skipto_survey')
    question = models.ForeignKey(Question, blank=True, null=True)
    skip_level = models.CharField(max_length=255, blank=True, null=True)

VALIDATION_CONDITIONS = (('>','Greather Than'),('<','Less Than'),
     ('>=','Greather Than Equal'),('<=','Less Than Equal'),('==','Equals'),('!=','Not Equal'),
     ('+','Addition'),('-','Subtraction'),('*','Multiplication'),('/','Division'),
     ('past','Past Date'),('current','Current Date'),('future','Future Date'),('any date','Any Date'))
class QuestionValidation(BaseContent):
    question = models.ForeignKey(Question)
    validation_type = models.CharField(
        max_length=255, blank=True, null=True, choices=VALIDATION_TYPE)
    max_value = models.CharField(max_length=255, blank=True, null=True)
    min_value = models.CharField(max_length=255, blank=True, null=True)
    validation_condition = models.CharField(choices=VALIDATION_CONDITIONS,
                                    max_length=255, blank=True, null=True)
    other_text2 = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.question.__unicode__()

    def clean(self):
        if (float(self.min_value) or 0) > (float(self.max_value) or float('inf')):
            raise ValidationError({
                'min_value': 'Min value should be less than max value',
            })


class Validations(BaseContent):
    validation_type = models.CharField(
        max_length=255, blank=True, null=True, choices=VALIDATION_TYPE)
    max_value = models.CharField(max_length=255, blank=True, null=True)
    min_value = models.CharField(max_length=255, blank=True, null=True)
    other_text1 = models.CharField(max_length=255, blank=True, null=True)
    other_text2 = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    def __unicode__(self):
        return '%s - %s' % (self.id, self.object_id)

    def clean(self):
        if (float(self.min_value) or 0) > (float(self.max_value) or float('inf')):
            raise ValidationError({
                'min_value': 'Min value should be less than max value',
            })


class ChoiceValidation(BaseContent):
    choice = models.ForeignKey(Choice)
    validation_type = models.CharField(
        max_length=255, blank=True, null=True, choices=VALIDATION_TYPE)
    max_value = models.CharField(max_length=255, blank=True, null=True)
    min_value = models.CharField(max_length=255, blank=True, null=True)
    other_text1 = models.CharField(max_length=255, blank=True, null=True)
    other_text2 = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)


class SurveyLog(BaseContent):
    create_by = models.ForeignKey(User)
    log_value = models.CharField(max_length=255, blank=True, null=True)
    version = models.ForeignKey(Version)
    other_text = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.create_by.username


class Media(BaseContent):
    user = models.ForeignKey(User, related_name='media', verbose_name=_('user'),
                             blank=True, null=True)
    question = models.ForeignKey(Question, related_name='media',
                                 verbose_name=_('question'))
    submission_date = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to='static/%Y/%m/%d', blank=True, null=True)
    sfile = models.FileField(
        upload_to='static/surveyfiles/%Y/%m/%d', blank=True, null=True)
    app_answer_on = models.DateTimeField(blank=True, null=True)
    app_answer_data = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return '%s - %s' % (self.id, self.object_id)


class UserImeiInfo(BaseContent):
    user = models.ForeignKey(
        User, related_name='imei_info', verbose_name=_('user'))
    imei = models.CharField(max_length=15)

    class Meta:
        unique_together = ('user', 'imei')


class ErrorLog(BaseContent):
    user = models.ForeignKey(User)
    stoken = models.CharField(max_length=255, blank=True, null=True)
    log_file = models.FileField(
        upload_to='static/logfiles/%Y/%m/%d', blank=True, null=True)


class AppLabel(BaseContent):
    name = models.CharField(max_length=255)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    other_text = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name


class LabelLanguageTranslation(BaseContent):
    applabel = models.ForeignKey(AppLabel)
    text = models.CharField(max_length=255)
    language = models.ForeignKey(Language)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)


class SurveyLanguageMap(BaseContent):
    survey = models.ForeignKey(Survey, related_name="swssurvey")
    language = models.ManyToManyField(Language)


class QuestionLanguageValidation(BaseContent):
    questionvalidation = models.ForeignKey(QuestionValidation)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)


class NetworkConnectionStatus(BaseContent):
    time = models.DateTimeField()
    device_id = models.CharField(max_length=255)
    user = models.ForeignKey(User)


class DataBaseLog(BaseContent):
    user = models.ForeignKey(User)
    stoken = models.CharField(max_length=255, blank=True, null=True)
    log_file = models.FileField(
        upload_to='static/dbfiles/%Y/%m/%d', blank=True, null=True)


class TrackAnswerReportDump(BaseContent):
    surveyid = models.IntegerField()
    startid = models.CharField(max_length=255, blank=True, null=True)
    endid = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)


class UserTabDetails(BaseContent):
    userid = models.IntegerField()
    cell_id = models.CharField(max_length=255, blank=True, null=True)
    signal_strength = models.CharField(max_length=255, blank=True, null=True)
    charge = models.CharField(max_length=255, blank=True, null=True)
    last_chargetime = models.DateTimeField(blank=True, null=True)
    sim_serialnumber = models.CharField(max_length=255, blank=True, null=True)
    imei_info = models.CharField(max_length=255, blank=True, null=True)
    free_space = models.CharField(max_length=255, blank=True, null=True)
    apps = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    latitude = models.CharField(max_length=255, blank=True, null=True)
    longitude = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    n_type = models.CharField(max_length=255, blank=True, null=True)
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)


class UserTimeIntervals(BaseContent):
    user = models.ForeignKey(User, unique=True)
    frequency = models.IntegerField()


class Levels(BaseContent):
    name = models.CharField(max_length=255, blank=True, null=True)
    survey = models.ForeignKey(Survey)
    content_type = models.ForeignKey(ContentType)
    order = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.name


class ProjectLevels(BaseContent):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    order = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.name


class SurveyBeneficiaryMap(BaseContent):
    survey = models.ManyToManyField(Survey)
    # for saving beneficairy
    content_type1 = models.ForeignKey(ContentType, blank=True, null=True)
    object_id1 = models.PositiveIntegerField(blank=True, null=True)
    # for saving facility
    content_type2 = models.ForeignKey(
        ContentType, blank=True, null=True, related_name="for_facilty")
    object_id2 = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        if self.content_type1:
            return '%s - %s - %s' % (self.id, self.content_type1.model, self.object_id1)
        else:
            return '%s - %s - %s' % (self.id, self.content_type2.model, self.object_id2)


class SurveyQuestions(BaseContent):
    survey = models.ForeignKey(Survey)
    questions = models.ManyToManyField(Question, blank=True)


class AppIssueTracker(BaseContent):
    userid = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    module = models.CharField(max_length=255, blank=True, null=True)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    other_text1 = models.CharField(max_length=255, blank=True, null=True)
    help_text1 = models.IntegerField(default=0)
    help_text2 = models.IntegerField(default=0)

    def __unicode__(self):
        return self.userid

class VersionUpdate(BaseContent):
    version_code = models.IntegerField(default=0)
    version_name = models.CharField(max_length=100, blank=True, null=True)
    force_update = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return str(self.version_code)


# pass question list to filter according upto skip question
def get_filter_skip_question(question_list):
    last_question = question_list.last()
    for i in question_list:
        if i.is_skip_question():
            last_question = i
            break
    return {'first': question_list.first(), 'last': last_question}


def make_dir(instance, filename):
    d_ = datetime.now().date()
    year, month, day = d_.year, d_.month, d_.day
    path_ = 'static/survey_dump_files/'
    path_file = path_ + '{0}/{1}/{2}/{3}'.format(year, month, day, filename)
    return path_file


class SurveyRestore(BaseContent):
    survey_user = models.ForeignKey(
        'auth.User', related_name='survey_restore_user', **OPTIONAL)
    name = models.CharField(max_length=200, **OPTIONAL)
    restore_file = models.FileField(
        upload_to=make_dir, **OPTIONAL)
    level = models.PositiveIntegerField(default=0)
    content_type = models.ForeignKey(ContentType, **OPTIONAL)
    object_id = models.PositiveIntegerField(default=0)
    exported = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name or 'Pradam'

    def location_name(self):
        get_location = ''
        if self.object_id:
            get_location = MasterLookUp.objects.get(id=self.object_id).name
        return get_location

    def get_dump_data(self, loc_id):
        response = {'headers': [], 'response': []}
        get_dump = SurveyDump.objects.filter(
            survey_restore=self, boundary__id__in=loc_id)
        if get_dump:
            response['headers'] = get_dump[0].response.keys()
            response['response'] = [get_data.response for get_data in get_dump]
        return response

    def get_parent_child_destory(self):
        response = {'status': 0, 'message': 'Deactivated the data'}
        self.switch()
        sd = SurveyDump.objects.filter(survey_restore=self)
        if sd:
            s_ = sd[0]
            s_.switch()
        return response


class SurveyDump(BaseContent):
    survey_restore = models.ForeignKey(SurveyRestore, **OPTIONAL)
    response = JSONField(default={})
    boundary = models.ForeignKey(
        Boundary, related_name='survey_dump_location', **OPTIONAL)

    def __unicode__(self):
        return self.survey_restore.name


class ColorCode(BaseContent):
    beneficiary = models.ForeignKey(BeneficiaryType, **OPTIONAL)
    master = models.ForeignKey(MasterLookUp, **OPTIONAL)
    color = models.CharField(max_length=100, **OPTIONAL)

    def __unicode__(self):
        return self.color

FREQEUNCEY = [(0, 'Current Week'), (1, 'Current Month'), (2, 'Current Quarter'), (3, 'Current Half-Yearly'),
              (4, 'Yearly'), (5, 'Financial Year')]


class Frequence(BaseContent):
    duration = models.IntegerField(choices=FREQEUNCEY, **OPTIONAL)
    name = models.CharField(max_length=100, **OPTIONAL)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

USER_TYPE_CHOCES = ((1, 'CEO'), (2, 'Regional Head'), (3, 'Partner'),)

class DashBoardResponse(BaseContent):
    user_type = models.IntegerField(choices=USER_TYPE_CHOCES, **OPTIONAL)
    schedule = models.ForeignKey(Frequence, **OPTIONAL)
    user = models.ForeignKey('auth.User', **OPTIONAL)
    region_id = models.IntegerField(**OPTIONAL)
    partner_level = JSONField(**OPTIONAL)
    chartdata = JSONField(**OPTIONAL)
    facility = JSONField(**OPTIONAL)
    beneficiary = JSONField(**OPTIONAL)
    user_summary = JSONField(**OPTIONAL)
    partner = models.ForeignKey(Partner,**OPTIONAL)
    periodicity = models.PositiveIntegerField(**OPTIONAL)

    def __unicode__(self):
        return '{0} and {1}'.format(self.partner.name if self.partner else '', self.periodicity)


class SamAndMam(BaseContent):
    gender_choices = (('Male','Male'),('Female','Female'))
    gender = models.CharField(choices=gender_choices,default='Male',max_length=8)
    height = models.CharField(max_length=5)
    v_1 = models.CharField(max_length=5)
    v_2 = models.CharField(max_length=5)
    v_3 = models.CharField(max_length=5,blank=True,null=True)
    v_4 = models.CharField(max_length=5,blank=True,null=True)

    def __unicode__(self):
        return str(self.gender)+str(self.height)
