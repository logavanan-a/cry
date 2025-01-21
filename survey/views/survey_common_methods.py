# Methods commonly used in survey
from constants import levels
#from django.db.models import get_model
from django.apps import apps
from common_methods import *
# Import prerequisites


def get_level(level_in, task=None, get_class=False):

    # Get next / prev level of one level

    try:
        level_in = level_in.__name__
    except:
        level_in = str(level_in)

    x = {None: 0, 'prev': -1, 'next': 1}[task]
    if level_in.lower() in ['household', 'plot','entity'] and task == 'prev':
    
        return apps.get_model('masterdata.Village') if get_class else 'Village'

    for i in range(len(levels)):
        if levels[i].lower() == level_in.lower():
            return apps.get_model('masterdata.'+levels[i+x]) if get_class else levels[i+x]


def _is_float(string):

    # Check if a string is float

    try:
        float(string)
        return True

    except:
        return False


# Collection of validation functions and error msgs
_validation = [
    (lambda x:x.isdigit(), "Enter a digit."),
    (_is_float, "Enter a number."),
    (lambda x:all([i.isalpha() or i.isspace() for i in x]), "Enter english letters only."),
    (lambda x:all([i.isalnum() or i.isspace() for i in x]), "Enter english letters or numbers only."),
    (lambda x:True, ""),
]


def validate(question, responce):

    # Validate response

    if question.mandatory and not responce:
        return 'This field should not be left blank'

    if all([
            question.qtype == 'T',
            question.validation != None,
            responce,
    ]) and not _validation[question.validation][0](responce):
        return _validation[question.validation][1]

    if question.validation in [0, 1]:
        for i in question.questionvalidation_set.all():
            if not i.min_value < float(responce) < i.max_value:
                return i.message

    return ''
