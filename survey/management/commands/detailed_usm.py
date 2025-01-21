from django.core.management.base import BaseCommand
from survey.views.detailed_user_survey_map import *
from SST.settings import EMAIL_HOST_USER,TEMPLATE_DIRS,BASE_DIR


class Command(BaseCommand):

    help = 'Runs crone for creating detailed user survey map table'

    # C def add_arguments(self, parser):
    # C    parser.add_argument('poll_id', nargs='+', type=int)

    @staticmethod
    def handle(*args, **options):
        detailed_user_survey_map()
