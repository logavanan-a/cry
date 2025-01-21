from masterdata.models import *
from survey.models import *
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .deo import SurveyBase
# Import prerequisites


class PmAuth(object):

    # Check authentication

    def is_unauthorised(self):
        # Check authentication
        return self.request.user.userprofile_set.get() not in [
            self.survey.project.project_manager,
            self.survey.project.program.program_officer ,
        ]


class ViewProgress(PmAuth, SurveyBase):

    # Pm can view progress of project

    def get(self, *args, **kwargs):
        # Virtual urls
        task = self.kwargs['task']
        if task == 'summary':
            return self.summary()
        if task == 'confirm':
            return self.confirm()

    def summary(self):
        # View summary
        return render(self.request, 'survey/global-survey-summary.html', {
            'details': self.details,
            'location_level': self.details['obj'].survey.location_level().__name__,
            'lock': self.details['lock']
        })

    def confirm(self):
        # Confirm changing status
        status = self.details['obj']
        status.status = '2' if status.status == '0' else '0'
        status.reset_by = self.profile
        status.save()
        return HttpResponseRedirect('/close/')
