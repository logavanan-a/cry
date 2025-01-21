from django.http import HttpResponseRedirect, HttpResponse
from survey.models import *
from masterdata.models import *
from common_methods import *
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
#from permissions import super_user
from survey.views.forms import SurveyForm
#from django.db.models import get_model
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
#from masterdata.find import Find
from survey.views.survey_common_methods import get_level
from collections import Counter
from collections import OrderedDict
#from partner.models import get_children,Partner
import itertools
# Import prerequisites


# Manage suurvey models
# List add edit activate, deactivate


class Manage(object):

    # Abstract base class to manage all survey models

    @method_decorator(login_required(login_url=('/login/')))
    def dispatch(self, *args, **kwargs):
        # Make sure that superuser is logged in
        return super(Manage, self).dispatch(*args, **kwargs)

    # Model is a property
    @property
    def model(self):
        return apps.get_model({
            'kpitarget': 'partner.KpiTarget',
            'kpishorttermtarget': 'partner.KpiShortTermTarget',
            'question-validation': 'survey_web_service.questionvalidation'
        }.get(self.kwargs['model']) or 'survey.%s' % (
            self.kwargs['model'].capitalize()))

    # Gets the queryset
    def get_queryset(self):

        # Returns the queryset

        model = self.kwargs['model']
        qs = self.model.objects.all()
        try:
            query = {{
                'program': 'partner',
                'kpitarget': 'partner',
                'kpishorttermtarget': 'kpitarget',
                'project': 'program',
                'survey': 'project',
                'block': 'survey',
                'surveysummary': 'survey',
                'date': 'survey',
                'datacentre': 'project',
                'question': 'block',
                'choice': 'question',
                'question-validation': 'question',
            }[model] + '__id': self.kwargs['pid']}
        except:
            query = {}

        try:
            qs = qs.filter(**query)
        except:
            pass

        if model == 'question':
            return qs.exclude(meta_qtype__in=[1,2,3,4]).order_by('order')
        return qs

    def get_context_data(self, **kwargs):
        # Pass additional info to html
        context = super(Manage, self).get_context_data(**kwargs)
        context['model'] = self.kwargs['model']
        if 'pid' in self.kwargs.keys():
            context = self.get_pidrel_context(context)
        return context

    def get_pidrel_context(self, context):
        context['pid'] = self.kwargs['pid']
        if self.kwargs['model'] in ['program', 'kpitarget']:
            from partner.models import Partner
            context['partner'] = Partner.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] == 'kpishorttermtarget':
            from partner.models import KpiTarget
            context['kpitarget'] = KpiTarget.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] == 'project':
            context['program'] = Program.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] in ['survey', 'datacentre']:
            context['project'] = Project.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] in ['block', 'surveysummary', 'date']:
            context['survey'] = Survey.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] == 'question':
            context['bloc'] = Block.objects.get(id=self.kwargs['pid'])
        elif self.kwargs['model'] in ['choice', 'question-validation']:
            context['question'] = Question.objects.get(id=self.kwargs['pid'])
        return context


class ModelNicely(object):

    # Pass a nice name of model to html
    # eg pass Data Centre if model is projectdatacentremap
    # This will be displayed to user

    def get_context_data(self, **kwargs):
        context = super(ModelNicely, self).get_context_data(**kwargs)
        try:
            context['nicemodel'] = {
                'projectdatacentremap': 'Data Centre',
                'projectdccmap': 'Data Centre Cordinator',
                'projectpomap': 'Program Officer',
                'projectpmmap': 'Project Manager',
                'projecthufcmap': 'Huf Cordinator',
                'datacentre': 'Data Centre',
                'dataCentre': 'Data Centre',
                'surveysummary': 'Survey Summary',
                'kpireport': 'Kpi Report',
                'kpitarget': 'Target',
                'kpishorttermtarget': 'Short Term Target',
                'survey': 'Data Collection',
                'Survey': 'Data Collection',
                'sUrvey': 'Data Collection',
                'UserSurveyMap': 'Assign Forms',
                'usersurveymap': 'Assign Forms',
            }[self.kwargs['model']]
        except:
            pass
        return context


class CustomSaving(object):

    # Customise the way in which it is saved

    def form_valid(self, form):

        # If form is valid do certain hooks before saving

        from partner.models import Partner, KpiTarget
        if self.kwargs['model'] in ['date','survey','Project','program', 'block','surveysummary', 'question', 'choice', 'datacentre', 'kpitarget', 'kpishorttermtarget', 'question-validation']:
            self.object = form.save(commit=False)
            self.object.__setattr__(*{
                'date':('survey', Survey.objects.get_or_none(pk=self.kwargs['pid'])),
                'survey':('project', Project.objects.get_or_none(pk=self.kwargs['pid'])),
                'Project':('program', Program.objects.get_or_none(pk=self.kwargs['pid'])),
                'datacentre':('project', Project.objects.get_or_none(pk=self.kwargs['pid'])),
                'program':('partner', Partner.objects.get_or_none(pk=self.kwargs['pid'])),
                'kpitarget':('partner', Partner.objects.get_or_none(pk=self.kwargs['pid'])),
                'kpishorttermtarget':('parent', KpiTarget.objects.get_or_none(pk=self.kwargs['pid'])),
                'block':('survey', Survey.objects.get_or_none(pk=self.kwargs['pid'])),
                'surveysummary':('survey', Survey.objects.get_or_none(pk=self.kwargs['pid'])),
                'question':('block', Block.objects.get_or_none(pk=self.kwargs['pid'])),
                'choice':('question', Question.objects.get_or_none(pk=self.kwargs['pid'])),
                'question-validation':('question', Question.objects.get_or_none(pk=self.kwargs['pid'])),
            }[self.kwargs['model']])
            self.object.save()
        else:
            self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class SurveyList(Manage, ModelNicely, ListView):

    # List instances of models in survey app

    template_name = 'survey/list.html'


class SurveyAdd(SurveyForm, CustomSaving, ModelNicely, Manage, CreateView):

    # Add instances of models in survey app

    template_name = 'survey/add-edit.html'

    def get_success_url(self):
        # Close Fancybox
        return "/close/?msg=%s added successfully." %(self.kwargs['model'].capitalize())

    def get_context_data(self, **kwargs):
        # Return additional info to html
        context = super(SurveyAdd, self).get_context_data(**kwargs)
        context['task'] = 'Add'
        return context


class SurveyEdit(SurveyForm, CustomSaving, ModelNicely, Manage, UpdateView):

    # Edit instances of models in survey app

    template_name = 'survey/add-edit.html'


    def listdiff(self,l1,l2):
        a,b = len(list(l1)),len(list(l2))
        if a < b:
            c = set(l2) - set(l1)
        else:
            c = set(l1) - set(l2)
        return list(c)


    def get_success_url(self):
        # Close Fancybox
        
        if self.kwargs.get('model') == 'UserSurveyMap':
            
            if self.get_object().survey.data_entry_level in '123456789':
                
                return '/manage/survey/edit/usersurveymap/%s/' % self.kwargs.get('pk')
        
        return "/close/?msg=%s edited successfully." %(self.kwargs['model'].capitalize())

    def get_context_data(self, **kwargs):
        # Return additional info to html
        context = super(SurveyEdit, self).get_context_data(**kwargs)
        context['task'] = 'Edit'
        return context


class SurveyActive(Manage, DeleteView):
    # Activate/ Deactivate model instance

    @method_decorator(login_required(login_url="/"))
    def dispatch(self, *args, **kwargs):
        # Activate/ Deactivate model instance
        self.get_object().switch()  # delete()
        return HttpResponseRedirect(self.request.META['HTTP_REFERER'])


class QuestionDisplay(Manage, DeleteView):
    # Display/ Undisplay model instance

#    @method_decorator(super_user)
    def dispatch(self, *args, **kwargs):
        # Display/ Undisplay model instance
        obj = self.get_object()
        obj.display = 2 if obj.display == 0 else 0
        obj.save()
        return HttpResponseRedirect(self.request.META['HTTP_REFERER'])


def map_to_project(request, pk, map_to):

    # Maps an instance on ProjectDataCentreMap etc to a project

    model_to_map = {
        'datacentre': ProjectDataCentreMap,
        'dcc': ProjectDccMap,
        'po': ProjectPoMap,
        'pm': ProjectPmMap,
        'hufc': ProjectHufcMap,
    }[map_to]

    mapper, created = model_to_map.objects.get_or_create(
        project=Project.objects.get(pk=pk))

    return HttpResponseRedirect(
        "/manage/survey/edit/%s/%s" %(model_to_map.__name__.lower(), str(mapper.pk))
    )


def export(request, sid):
    # Export a survey as html
    return HttpResponse(
        Survey.objects.get(id=sid).export()
    )


def sudo_dcc(request, centre_id):

    centre = DataCentre.objects.get(id=centre_id)
    deos = centre.deo.all()
    surveys = centre.survey_set.all()
    return render(request, 'survey/assign-dataentry.html', locals())


def survey_summary(request):
    surveys = [i for i in Survey.objects.filter(active=2)
             if Answer.objects.filter(question__block__survey=i).exists()
             if Question.objects.filter(block__survey=i, meta_qtype=0, active=2, qtype__in='CRS')]
    questions=Question.objects.filter(qtype__in ='CRS', meta_qtype=0)
    choices=Choice.objects.all()
    countries=Country.objects.all()
    states=State.objects.all()
    districts=District.objects.all()
    taluks=Taluk.objects.all()
    mandals=Mandal.objects.all()
    gramapanchayaths=GramaPanchayath.objects.all()
    villages=Village.objects.all()
    users=User.objects.all()
    return render(request, 'survey/pie-chart.html', locals()) 

def chart_info(request):
    question = Question.objects.get(id=request.GET.get('question_id'))
    if request.GET.get('sec_question_id') == '' and request.GET.get('user_id') == '' and request.GET.get('start_date') == '' and request.GET.get('end_date') == '':
        first_ans = Answer.objects.filter(question__id=request.GET.get('question_id'))
        choice_counter= Counter([getattr(i.choice, 'text', 'None')
                                 for i in first_ans])
        counter_lsformat = [[i, choice_counter[i]] for i in choice_counter]
    #answer for first filter-By survey
    elif request.GET.get('sec_question_id') != '' and request.GET.get('user_id') == '' and request.GET.get('start_date') == '' and request.GET.get('end_date') == '':
        fil_question = Question.objects.get(id=request.GET.get('sec_question_id'))
        sec_qans = Answer.objects.filter(question=fil_question)

        if fil_question.qtype == 'C':
            sec_qans = sec_qans.filter(multy_choice__id=request.GET.get('cid'))
        elif fil_question.qtype in 'RS':
            sec_qans = sec_qans.filter(choice__id=request.GET.get('cid'))
        keys = sec_qans.values_list('creation_key', flat=True)
        answers = set(Answer.objects.filter(creation_key__in=keys, question__id=request.GET.get('question_id')))
        if question.qtype == 'C':
            choice_counter = Counter([i.multy_choice.all() for i in answers if i.multy_choice.all()])
            tup = tuple(choice_counter)
            response = [i.text for i in list(itertools.chain(*tup))]
            response = Counter(response)
            counter_lsformat = [[i, response[i]] for i in response]
        elif question.qtype in 'RS':
            choice_counter = Counter([i.choice for i in answers if i.choice])
            counter_lsformat = [[i.text, choice_counter[i]] for i in choice_counter]
    # answer for second filter-By user
    elif request.GET.get('user_id') != None and request.GET.get('sec_question_id') == '' and request.GET.get('start_date') == '' and request.GET.get('end_date') == '':
        users = User.objects.get(id=int(request.GET.get('user_id')))
        user_ans = Answer.objects.filter(user=users,question__id=request.GET.get('question_id'))
        
        choice_counter= Counter([getattr(i.choice, 'text', 'None')
                             for i in user_ans])
        counter_lsformat = [[i, choice_counter[i]] for i in choice_counter]
    # answer for third filter-By date range
    elif request.GET.get('start_date') != None and request.GET.get('end_date') != None :
        time_answers = Answer.objects.filter(created__range=(request.GET.get('start_date'),request.GET.get('end_date')),question__id=request.GET.get('question_id'))
        choice_counter= Counter([getattr(i.choice, 'text', 'None')
                                 for i in time_answers])
        counter_lsformat = [[i, choice_counter[i]] for i in choice_counter]
    sums = float(sum([(choice_counter[i]) for i in choice_counter]))

    percentage = {i: (choice_counter[i]*100)/sums for i in choice_counter}
    
    tables = [[getattr(i, 'text', i), percentage[i]] for i in percentage]
    data = {'data':counter_lsformat, 'question':'%s' %question.text, 'tables':tables}
    return JsonResponse(data, safe=False)
