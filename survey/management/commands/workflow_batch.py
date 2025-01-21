import itertools
import time
import json
from django.core.management.base import BaseCommand, CommandError
from partner.models import Partner
from survey.models import Survey, Answer, JsonAnswer
from userroles.models import *
from workflow.models import *


class Command(BaseCommand):

    @staticmethod
    def handle(*args, **kwargs):
        """ Command to create a batch for responses """
        survey_list = Survey.objects.filter(active=2)
        for partner in Partner.objects.filter(active=2):
            users = UserRoles.objects.filter(
                partner=partner).values_list('user', flat=True).distinct()
            print "partner ",partner
            print "users ",users
            for survey in survey_list:
                survey_workflow = WorkFlowSurveyRelation.objects.get_or_none(survey=survey)
                print "workflow ",survey_workflow
     
                if survey_workflow:
                
                    json_responses = JsonAnswer.objects.filter(active=2,survey=survey, user__in=users)
                    tagged_responses = WorkFlowBatch.objects.filter(partner=partner, current_status=survey_workflow).values_list('response_ids', flat=True)
                    tagged_ids = list(set(itertools.chain.from_iterable(tagged_responses)))
                    new_keys = json_responses.exclude(id__in=tagged_ids).values_list('id', flat=True)
                    print "survey"
                    print new_keys
            # store these keys in response batch tag table
                    if new_keys:
                        wfb_name = str(partner.id) + '_' + str(survey.id) + '_' + str(survey_workflow.id) + '_' + time.strftime('%y_%m_%d_%h_%s')
                        se_keys = [i for i in new_keys]
                        WorkFlowBatch.objects.create(name=wfb_name, no_of_response=new_keys.count(
                    ), response_ids=list(se_keys), current_status=survey_workflow, partner=partner)
                        print "batch created"
