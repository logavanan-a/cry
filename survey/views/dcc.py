from survey.models import *
from django.shortcuts import render
from django.http import HttpResponseRedirect
from survey.views.survey_common_methods import *
from common_methods import *
from survey.views.manage_views import SurveyEdit
from .deo import SurveyBase
# Import prerequisites


def view_progress(request, sid, pk, datalevel):
    #-------------------view progress-----------------------------#
    # View progress
    # Dcc can view progress of a survey
    # based on level of survey
    # it can be from state to gramapanchayath level
    #-----------ends---------------------------------#
    survey = Survey.objects.get(pk=sid)
    level = survey.del_nicely()
    level_class = get_model('masterdata.'+get_level(level, 'prev'))
    location = level_class.objects.get(pk=pk)
    participants = [i for i in location.contents()
                    if Answer.objects.filter(question__block__survey__id=sid,
                                             data_level=int(datalevel) or None,
                                             object_id=i.pk)]
    table = create_table(participants, survey, datalevel)
    deo = UserSurveyMap.get_user(survey=survey, location=location)
    status = int(SurveyStatus.view_status(survey, location, Date.objects.get_or_none(id=datalevel))['status'])
    stop = SurveyStatus.view_status(survey, location, Date.objects.get_or_none(id=datalevel))['obj'].stop
    return render(request, 'survey/dcc-view-progress.html', locals())


def choose_location(request, survey_id):
    # Dcc choose the place where they wnat to take survey
    survey = Survey.objects.get(pk=survey_id)
    level = int(survey.data_entry_level)

    info = dict((
        ('countrys',  Country.objects.all()),
        ('states',  State.objects.all()),
        ('districts',  District.objects.all()),
        ('taluks',  Taluk.objects.all()),
        ('mandals',  Mandal.objects.all()),
        ('gramapanchayaths',  GramaPanchayath.objects.all()),
        ('villages',  Village.objects.all()),
        ('hamlets',  Hamlet.objects.all()),
    ) [:level + 1])
    # 'x'--> x.objects.all()

    if survey.survey_type == 1:
        # set datalevel 1
        info['datalevels'] = 1

    if request.method == 'POST':

        # Handle post request

        datalevel = request.POST.get('datalevel') or 0
        info['error'] = bool(survey.survey_type and datalevel == 0)

        level = survey.del_nicely()
        pk = request.POST.get(get_level(level, 'prev').lower())
        info['error'] = bool(pk) or info['error']
        if info.get('error'):
            return render(request, 'survey/choose-location.html', info)

        return render(request, 'redirect-parent.html', {
            'pk': pk,
            'sid': survey_id,
            'datalevel': datalevel
        })
    info['survey'] = survey
    return render(request, 'survey/choose-location.html', info)


def create_table(participants, survey, datalevel):

    # Create dictionary with all info req

    @fail_silently('')
    def get_answer(party, question, inline):
        return [i.responce_nicely()
                for i in Answer.objects.filter(
                        question=question,
                        object_id=party.id,
                        inline=inline,
                )]

    return {
        party: {question.id: [get_answer(party, question, None)]
                for question in survey.questions()}
        for party in participants
    }


def deo_project_map(request, sid, uid):

    # map deo to projects

    usmap, created = UserSurveyMap.objects.get_or_create(
        user_id=uid,
        survey_id=sid
    )
    # redirect after success
    return HttpResponseRedirect(
        '/manage/survey/edit/UserSurveyMap/'+str(usmap.pk)
    )


class DccCan(object):
    # Give permission to dcc
    def dispatch(self, request, *args, **kwargs):
        # Give permission to dcc
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(),
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)


class DccEdit(DccCan, SurveyEdit):
    # Dcc Edit
    pass


def survey_completed(request, sid, lid):
    # Mark survey as completed
    survey = Survey.objects.get(id=sid)
    level = survey.location_level()
    location = level.objects.get(id=lid)

    taken = len([i for i in location.contents()
                 if survey.has_taken(i)])
    total = location.contents().count()
    pending = total - taken
    deo = UserSurveyMap.get_user(survey, location)
    # render to template
    return render(request, 'survey/dcc-confirm-finished.html', locals())


class SurveyPerm(object):

    # Staticmethod to avoid self
    @staticmethod
    def is_unauthorised():
        # Authenticate
        return False


class UpdateStatus(SurveyPerm, SurveyBase):

    # Dcc can update the status of a survey

    def get(self, *args, **kwargs):
        # Virtual urls
        task = self.kwargs['task']
        if task == 'summary':
            return self.summary()
        if task in ['0', '1', '2', '3',]:
            return self.reset(task)

    def summary(self):
        # View summary
        return render(self.request, 'survey/local-survey-summary.html', {
            'details':self.details, 'dcc':True,
            'del':self.details['obj'].survey.del_nicely()
        })
        
    def reset(self, task):
        # reset the status
        status = self.details['obj']
        status.set_status(int(task))
        return HttpResponseRedirect('/close/')
        
