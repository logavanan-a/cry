from django.core.management.base import BaseCommand, CommandError

import django
import datetime
import os
import csv
from masterdata.models import *
import pdb
from collections import OrderedDict
from django.db.models import Count
from uuid import uuid4
from django.template.defaultfilters import slugify


class Command(BaseCommand):

    """ Command To generate Data Entry Operators History in csv format."""
    @staticmethod
    def handle(*args, **options):

        adcount,ncount,klass_avail = 0,0,{}
        csv_path = raw_input('Enter the csv file path: ')
        reader=csv.reader(open(csv_path,'rb'), delimiter=',')
        fields=reader.next()
        klass_no = int(raw_input('''
                Enter which level you wnat to import
                1. Country
                2. State
                3. District
                4. Taluk
                5. Mandal
                6. GramaPanchayath
                7. Village
            '''))
        klass_avail = {
                1: Country,
                2: State,
                3: District,
                4: Taluk,
                5: Mandal,
                6: GramaPanchayath,
                7:Village
            }
        for i,item in enumerate(reader):
            items = zip(fields,item)

            items_dict = {}
            items_dict = dict(items)

            klass = klass_avail[klass_no]
            parent = klass_avail[klass_no - 1]
            try:
                dist= parent.objects.get(id = items_dict['parent'])
                kw = Parent.__name__.lower()
                klass.objects.create(**{kw: dist,'name':items_dict['name'],'display_name':items_dict['Display name']})
                
            except Exception as e:
                pass
