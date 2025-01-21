# Not to be confused with django forms
# Contains abstract cbvs to overide form classes
from django import forms
#from profiles.models import UserProfile
from survey.views.survey_common_methods import get_level
from constants import levels
from django.apps import apps
#from survey.models import UserSurveyMap


# Field dict
# Specify which field is required for which model
# One model can have multiple fields with multiple names
# Case insensitivity of get_model method is 'misused'


def find_masterdata(self):
    return [self.get_object().level.lower()]


FIELDS = {

    'projectdatacentremap' : ['data_centres'],
    'projectdccmap'        : ['data_centre_cordinator'],
    'projectpomap'         : ['programme_officer'],
    'projectpmmap'         : ['project_manager'],
    'projecthufcmap'       : ['huf_cordinator'],
    
    'survey'     : ['name', 'data_entry_level', 'piriodicity'],
    'Survey'     : ['name', ],
    'sUrvey'     : ['data_centres'],
    'program'    : ['name','start_date','end_date','description'],
    'kpitarget'    : ['kpi','target','notes'],
    'kpishorttermtarget'    : ['target','level','level_code','year','quarter','notes'],
    'Program'    : ['program_officer',],
    'date'       : ['_name','date'],
    'surveysummary':['listing_order','level','value1','value2'],
    'block'      : ['name',],
    'question'   : ["qtype", "text",
                    "validation", "order", "code",
                    "help_text", "parent", "mandatory",],
    'qUestion'   : ["text",
                    "validation", "order", "code",
                    "help_text", "parent", "mandatory",],
    'Question'   : ['category'],
    'choice'     : ['text', 'order', 'code', 'skip_question'],
    'question-validation'     : ['validation_type','max_value', 'min_value', 'message'],
    
    'project'    : ['name', 'start_date', 'end_date', 'level'],
    'Project'    : ['name', 'start_date',
                    'end_date', 'level'],
    'projEct'    : ['country'],
    'projecT'    : ['project_manager', ],
    # 'projecT'    : ['data_centres'],
    'projeCt'    : ['programme_officer', 'project_manager',
                    'huf_cordinator'],

    'projEct': find_masterdata,
    
    'datacentre' : ['name',],
    'dataCentre' : ['cordinator'],
    'Datacentre' : ['deo'],
    'kpi': ['name', 'order', 'system_uom', 'units', ],
    'kpitarget': ['partner', 'kpi', 'level', 'level_code', 'qrt1_mq',
                  'qrt2_jq', 'qrt3_sq', 'qrt4_dq', 'qtr_yr'],


}


class SurveyForm(object):

    # Not to be confused with django forms
    # Abstract cbvs to overide form classes

    def get_form_class(self):
        # Gets the form class
        # If model name not in field dict, normal procedure will occur
        try:
            self.fields = FIELDS[self.kwargs['model']]
        except:
            if self.kwargs['model'] == 'UserSurveyMap':
                self.fields = [get_level(self.get_object().survey.del_nicely(), 'prev').lower()]
            if self.kwargs['model'] == 'usersurveymap':
                self.fields = [get_level(self.get_object().survey.del_nicely()).lower()]
        if hasattr(self.fields, '__call__'):
            self.fields = self.fields(self)
        return super(SurveyForm, self).get_form_class()


    def get_form(self, form_class):

        form = super(SurveyForm, self).get_form(form_class)

        # if self.kwargs['model'] == 'UserSurveyMap':
        #     field = get_level(self.get_object().survey.del_nicely(), 'prev').lower()
        #     level_class = get_model('masterdata', field)
        #     form.fields[field].queryset = level_class.objects.exclude(id__in=[
        #         j.id
        #         for usmap in UserSurveyMap.objects.filter(survey=self.get_object().survey).exclude(user=self.get_object().user)
        #         for j in usmap.__getattribute__(field).all()
        #     ])

        if self.kwargs['model'] == 'usersurveymap':
            field = get_level(self.get_object().survey.del_nicely()).lower()

            form.fields[field].queryset = apps.get_model(
                'masterdata', get_level(self.get_object().survey.del_nicely())
            ).objects.filter(**{get_level(self.get_object().survey.del_nicely(), 'prev').lower() + '__in': self.get_object().location.all()})

        if self.kwargs['model'] == 'question':
            # Alter queryset
            form.fields['parent'].queryset =\
            form.fields['parent'].queryset.filter(block__id = self.kwargs['pid'])
        elif self.kwargs['model'] in ['dataCentre', ]:
            # Alter queryset
            form.fields['cordinator'].queryset =\
            form.fields['cordinator'].queryset.filter(partner = form.instance.project.program.partner)
        elif self.kwargs['model'] == 'projeCt':
            # Alter queryset
            form.fields['programme_officer'].queryset =\
            form.fields['programme_officer'].queryset.filter(partner = form.instance.program.partner)

            # Alter queryset
            form.fields['project_manager'].queryset =\
            form.fields['project_manager'].queryset.filter(partner = form.instance.program.partner)

            # Alter queryset
            form.fields['huf_cordinator'].queryset =\
            form.fields['huf_cordinator'].queryset.filter(partner = form.instance.program.partner)

        elif self.kwargs['model'] == 'Datacentre':
            # Alter queryset
            form.fields['deo'].queryset =\
            form.fields['deo'].queryset.filter(partner = form.instance.project.program.partner)
        elif self.kwargs['model'] == 'sUrvey':
            # Alter queryset
            form.fields['data_centres'].queryset =\
            form.fields['data_centres'].queryset.filter(project = form.instance.project)
        return form


    def _post(self, request, *args, **kwargs):
        # POST
        # Validate from date and to date time
        from datetime import datetime
        if self.kwargs['model'] in ['project', 'Project'] and \
           datetime.strptime(request.POST['start_date'], "%Y-%m-%d") >\
           datetime.strptime(request.POST['end_date'], "%Y-%m-%d"):

            form_class = self.get_form_class()
            form = self.get_form(form_class)
            form.add_error('end_date', 'End date should not be before start date.')
            self.object = None
            return self.form_invalid(form)

        if self.kwargs['model'] in ['choice']:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            question_obj = Question.objects.get(id=int(self.kwargs.get('pid')))
            if kwargs.get('pk',False):
                if Choice.objects.filter(question=question_obj,code=request.POST.get('code')).exclude(pk=int(kwargs.get('pk'))).exists():
                    form.add_error('code', 'Code already exists with the selected question')
                    self.object = None
                    return self.form_invalid(form)
                elif Choice.objects.filter(question=question_obj,\
                                            text__iexact=self.request.POST.get('text')\
                                            ).exclude(pk=int(kwargs.get('pk'))).exists():
                    form.add_error('text', 'Choice already exists with the selected question')
                    self.object = None
                    return self.form_invalid(form)
            else:
                if Choice.objects.filter(question=question_obj,code=request.POST.get('code')).exists():
                    form.add_error('code', 'Code already exists with the selected question')
                    self.object = None
                    return self.form_invalid(form)
                elif Choice.objects.filter(question=question_obj,text__iexact=self.request.POST.get('text')).exists():
                    form.add_error('text', 'Choice already exists with the selected question')
                    self.object = None
                    return self.form_invalid(form)

        return super (SurveyForm,self).post(self, request, *args, **kwargs)


    def post(self, request, *args, **kwargs):
        # If an exception occur, neglect it and do normal procedure
        try:
            return self._post(request, *args, **kwargs)
        except:
            return super(SurveyForm
            , self).post(request, *args, **kwargs)
