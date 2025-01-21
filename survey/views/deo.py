from masterdata.models import *
from survey.models import *
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from survey.views.survey_common_methods import validate
from django.views.generic import View
from uuid import uuid4
from django.db.models import get_model
from survey_web_service.models import AppAnswerData
# Import prerequisites

# Redirect deo to dashboard
dashboard = lambda x: render(x, 'survey/deo-dashboard.html')


class SurveyBase(View):

    # Base class for dataentry related views

    #                                        SurveyBase
    def memory(self):

        # Remembers information to be used in other methods
        # Sets attributes of self for reusing

        self.survey = Survey.objects.get(id=self.kwargs['sid'])
        self.date = Date.objects.get_or_none(id=self.kwargs['date'])
        location_class = self.survey.location_level()
        self.level = self.survey.del_nicely()
        self.level_class = get_model('masterdata', self.level)
        self.info = dict(self.request.GET or self.request.POST)
        self.profile = self.request.user.userprofile_set.get()
        if 'pk' in self.kwargs.keys():
            self.location = location_class.objects.get(pk=self.kwargs['pk'])
            self.details = SurveyStatus.view_status(self.survey, self.location, self.date)
        else:
            self.details = SurveyDateStatus.view_status(self.survey, self.date)
        if self.request.method == 'POST':
            self.info.pop('csrfmiddlewaretoken')

    #                                        SurveyBase
    def dispatch(self, request, *args, **kwargs):
        # Dispatch calls memory
        # And check auth
        self.memory()
        if self.is_unauthorised():
            return render(self.request, 'manage/login.html', {
                'msg': "You don't have permission to view this page."
            })
        return super(SurveyBase, self).dispatch(request, *args, **kwargs)


class DeoAuth(object):

    #                                        DeoAuth
    def is_unauthorised(self):
        # Authenticate deos
        return self.location not in UserSurveyMap.get_locations(
            self.request.user.userprofile_set.get(),
            self.survey
        )


class TakeSurvey(DeoAuth, SurveyBase):

    # Deo take survey for a location

    def get(self, *args, **kwargs):
        # Handle get data
        if self.request.user.userprofile_set.get().designation.code == 2:
            # Redirect dcc to view progress
            return HttpResponseRedirect(
                '/survey/dcc/view-progress/%s/%s/%s/%s/' % (
                    level, sid, pk, datalevel)
            )

        ans = Answer.objects.filter(active=2)
        table = ans.collect_participated_rows(
            self.location,
            self.survey,
            self.date
        )

        # Sample format of table
        # {
        #     <Village: Thovinakere>: {
        #         u'1723926038': {
	# 	    <Question: Name - 301>: <Answer: 123>,
	# 	    <Question: Age - 302>: <Answer: 123>,
	# 	    <Question: Gender - 303>: <Answer: Customer Registration System || Gender - 303 || Female>,
        #         }
        #     }
            
        # }

        # Render to template
        # With dict in 3rd arg as context data

        return render(self.request, 'survey/take-survey.html', {
            'survey': self.survey,
            'participants': self.get_partys(),
            'location': self.location,
            'table': table,
            'date': self.date,
            'range': [str(uuid4().int)[:10] for i in xrange(0, 10)],
            'request': self.request,
            'status': int(self.details['status']),
            'stop': self.details['obj'].stop(),
        })

    #                                        TakeSurvey
    def get_partys(self):
        # Get participants of the location
        if self.level.lower() == 'plot':
            return Plot.objects.filter(house_hold__village=self.location)
        elif self.level.lower() == 'hamlet':
            return Hamlet.objects.filter(village=self.location)
        elif self.level.lower() == 'household':
            return HouseHold.objects.filter(village=self.location)
        return UserSurveyMap.get_partys(
            self.request.user.userprofile_set.get(),
            self.survey,
        )
        

    #                                        TakeSurvey
    def post(self, *args, **kwargs):
        # DRY
        return JsonResponse(self._post())

    #                                        TakeSurvey
    def _post(self):

        # Handle the post request
        # If data is not valid, return errors
        # else save and return success

        info = {
            i.split('-')[0]: ','.join(self.info[i])
            for i in self.info.keys()
        }
        creation_key = info.pop('row')
        try:
            party = self.level_class.objects.get(id=info.pop('party'))
        except:
            party = None

        lat = info.pop('lat', None)
        lng = info.pop('lng', None)
        old_reps = [
            getattr(i.get(self.survey.questions().get_or_none(text='Date')), 'text', None)
            for i in Answer.objects.exclude(creation_key=creation_key).collect_rows(party, self.survey, self.date).values()
        ] if info.get('date') else []
        qid = str(getattr(self.survey.questions().get_or_none(text='Date'), 'id', ''))


        if (party and
            self.survey.inline == '0' and
            Answer.objects.collect_rows(party, self.survey, self.date)
        ) or info.get(qid) in old_reps:
            party = 'Duplicate'

        responce = {
            Question.objects.get(id=i): info[i]
            for i in info.keys()
            if info[i] != '[]'
        }

        errors = {q.id: validate(q, a)
                  for (q, a) in responce.items()}

        errors.update({'0': '' if party else
                       'This field should not be left blank'})

        if party == 'Duplicate':
            errors.update({'0': 'This %s already submitted response' %
                           (self.survey.del_nicely())})

        if True in [bool(error) for (qid, error) in errors.items()]:
            return {'errors': errors, 'success': False}

        answers = []
        aad = AppAnswerData.objects.create(interface=0, latitude=lat, longitude=lng,)
        for q, a in responce.items():
            answers.append(Answer.objects.force_create(
                creation_key=creation_key,
                user=self.request.user,
                question=q,
                text=a.strip(),
                content_object=party,
                data_level=self.date,
                app_answer_data=aad.id,
            ))

        return {'errors': errors, 'success': True}


class UpdateStatus(DeoAuth, SurveyBase):

    # Deo can update the status of survey

    def get(self, *args, **kwargs):
        # Virtual urls
        task = self.kwargs['task']
        if task == 'summary':
            return self.summary()
        if task == 'confirm':
            return self.submit()

    def summary(self):
        # View summary
        return render(self.request,
                      'survey/local-survey-summary.html',
                      {'details':self.details, 'del':self.details['obj'].survey.del_nicely()})

    def submit(self):
        # Submit for approval
        status = self.details['obj']
        status.set_status(1)
        return HttpResponseRedirect('/close/')


class DeleteResponse(DeoAuth, SurveyBase):

    # Deactivate a responce

    @staticmethod
    def get(request, *args, **kwargs):
        # Delete a response
        for i in Answer.objects.filter(creation_key=request.GET.get('row')):
            i.active = {'delete': 0, 'undelete': 2}[request.GET.get('task')]
            i.save()
        return JsonResponse({'success': True})
