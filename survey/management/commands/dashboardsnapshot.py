from django.core.management.base import BaseCommand
from survey.views.new_dashboard import DashBoardSnapShot

class Command(BaseCommand):

    help = 'Runs crone for DashBoard Data.'

    @staticmethod
    def handle(*args, **options):
        try:
            dashboard_snapshot = DashBoardSnapShot()
            dashboard_snapshot.partner_computation()
        except:
            print("Failed")
