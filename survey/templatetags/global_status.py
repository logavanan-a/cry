from django.template.defaulttags import register
from survey.models import *
from partner.models import *
from masterdata.models import *
from django.contrib.auth.models import *
# Import prerequisites


# Register function as template tag
@register.filter
def global_status(date):
    # Status for all dates
    if type(date).__name__ == 'Date':
        status = SurveyDateStatus.view_status(date.survey, date)
    else:
        status = SurveyDateStatus.view_status(date)
    return status['status_nicely']
        

# Register function as template tag
@register.filter
def get_partners_count(request):
    # No of partners
    partner = Partner.objects.filter(active=2).count()
    return partner


# Register function as template tag
@register.filter
def get_survey_count(request):
    # No of surveys
    survey = Survey.objects.filter(active=2).count()
    return survey


# Register function as template tag
@register.filter
def get_village_count(request):
    # No of villages
    village = Village.objects.filter(active=2).count()
    return village


# Register function as template tag
@register.filter
def get_user_count(request):
    # No of users
    users = User.objects.all().count()
    return users
