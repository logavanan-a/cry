import csv
from django.contrib.auth.models import User
from profiles.models import UserProfile
from masterdata.models import (GramaPanchayath,Village)
from .models import UserSurveyMap

def user_survey_data():
    user_file = raw_input('Give the File Path:')
    with open(str(user_file),'rb') as usfile:
        reader = csv.reader(usfile)
        keys = reader.next()
        for row in reader:
            data = dict(zip(keys, row))
            user_id = data.get('UserID')
            survey_id = data.get('SurveyID')
            vill_ids = eval(data.get('VillageIDS'))
            gp_values = [Village.objects.get(id=gp).gramapanchayath.id for gp in vill_ids]
            user_pro = UserProfile.objects.get(user__id = int(user_id))
            user_survey_map, created = UserSurveyMap.objects.update_or_create(
                              user=user_pro,
                              survey_id=int(survey_id),
                              )
            user_survey_map.gramapanchayath.add(*gp_values)
            user_survey_map.village.add(*vill_ids)
            user_survey_map.save()
            
