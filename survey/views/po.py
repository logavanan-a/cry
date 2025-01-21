from django.http import HttpResponseRedirect
from survey.models import *
# Import prerequisites



def reset_project_status(request, pid):
    # po can change status
    # if not pid in self.request.user.
    project = Project.objects.get(id=pid)
    status = ProjectStatus.view_status(project)['obj']
    if status.status == '0':
        status.status = '2'
    elif status.status == '2':
        status.status = '0'
    status.save()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
