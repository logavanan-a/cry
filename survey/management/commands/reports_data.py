from django.core.management.base import BaseCommand
from reports.report_views import savereportdata

class Command(BaseCommand):
    '''The class must be named Command, and subclass BaseCommand
    Create __init__.py files in both to signal that these are packages.
    In your package directory, create management and 
    management/commands subdirectories. The names matter.
    This is for updating the json of all the partner reports
    A command must define handle()'''

    @staticmethod
    def handle(*args, **options):

        """ Command """

        savereportdata()
