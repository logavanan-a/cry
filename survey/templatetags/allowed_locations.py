from django.template.defaulttags import register
from survey.models import *
# Import Prerequisites


@register.filter
def allowed_locations(user, survey):
    # Allowed locations of a user for a survey
    return UserSurveyMap.get_locations(user=user.userprofile_set.get(), survey=survey)
