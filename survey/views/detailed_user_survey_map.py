from django.http import HttpResponseRedirect, HttpResponse
from survey.models import *
from masterdata.models import *
from profiles.models import *
from django.http import JsonResponse
from datetime import datetime,timedelta


def listdiff(l1,l2):
    a,b = len(list(l1)),len(list(l2))
    if a < b:
        c = set(l2) - set(l1)
    else:
        c = set(l1) - set(l2)
    return list(c)


def detailed_user_survey_map():
    start_time = datetime.now()
    latest_crone =  UsmCronTracker.objects.latest('start_time').start_time
    usm_obj = UserSurveyMap.objects.filter(active=2)
    gusm=[]
    masterdata_list = {"entity":['village','gramapanchayath','mandal','taluk','district','state','country'],
                       "village":['gramapanchayath','mandal','taluk','district','state','country'],
                       "gramapanchayath":['mandal','taluk','district','state','country'],
                       "mandal":['taluk','district','state','country'],
                       "taluk":['district','state','country'],
                       "district":['state','country'],
                       "state":['country'],
                           }
    for i in usm_obj:
        gusm.extend(i.history.filter(modified__gt=latest_crone).order_by('user').distinct('user','survey'))
    for gu in gusm:

        data_level = gu.survey.get_data_entry_level_display().lower()
        vill = getattr(gu.history_object,data_level).ids()
        content_type = ContentType.objects.get(name__iexact=str(data_level))
        for v in vill:
            dusm_obj,created = DetailedUserSurveyMap.objects.get_or_create(user=gu.user, survey=gu.survey, content_type=content_type, object_id=v,level=str(data_level))

            obj = get_model('masterdata',data_level).objects.get(id=v)
            prsnt_level = data_level
            nxt_level = masterdata_list.get(prsnt_level)

            for nx_level in nxt_level:
                DetailedUserSurveyMap.objects.get_or_create(user=gu.user, survey=gu.survey, content_type=ContentType.objects.get(name__iexact=str(nx_level)), object_id=getattr(obj,nx_level).id,level=str(nx_level))

                obj = get_model('masterdata',nx_level).objects.get(id=getattr(obj,nx_level).id)

    end_time = datetime.now()
    UsmCronTracker.objects.create(start_time=start_time,end_time=end_time)


def usm_count():
    users=UserProfile.objects.filter(active=2,designation__code__in=[1,5])
    for us in users:
        UserSurveyMap.objects.filter(user=us)
        for sur in Survey.objects.filter(active=2):
            DetailedUserSurveyMap.objects.filter(user=us,survey=sur,level="village").count()
