from django.shortcuts import render
from django.template.defaultfilters import slugify
from functools import wraps
from django.views.generic import View
# Import Prerequisites


# functions that are used frequently all over application


def close(request):
    # Close a fancy box
    # To close a fancy box, redirect it to '/close' url
    return render(request, 'close.html',
                  {'msg': request.GET['msg']}
                  if 'msg' in request.GET.keys() else{})


def sub_domain(request=None):

    # Get the sub domain

    if not request:
        from constants import data
        request = data.get('request')
    if not request:
        return 'hufpartners'

    subd = request.META['HTTP_HOST'].lower().split('.')
    i = 0
    if subd[0] == 'www':
        i = i + 1
    codeobj = slugify(subd[i])

    return codeobj


def fail_silently(arg=None):

    # A decorator
    # If this is put on top of function,
    # exceptions won't be raised in that function.
    # If exception is raised, it will return the arg supplied

    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                return arg
        return inner

    return decorator


def allowed_subdomain(user):

    # Take use as argument and return the subdomain where they can login
    # returns '*' for superuser and None if user is not authenticated

    return '*'


def auto_as_view(cbv):

    # Take a class which is a view as an argument and
    # returns the function which would be got by 'as_view ing it'
    new = wraps(cbv)(cbv.as_view())
    new._original = cbv
    return new


class Object(object):

    # Convert dictionary to an object

    def __init__(self, kwargs_dict):
        for i in kwargs_dict:
            setattr(self, i, kwargs_dict[i])

    @property
    def hash(self):
        # hash
        return self.__hash__()


class OrganiseView(View):

    # Specify urls as a method
    # and it will run curresponding function

    def dispatch(self, *args, **kwargs):
        self.info = self.request.GET or self.request.POST
        return getattr(self, self.urls[self.kwargs.get('task')])()


def this_or_zero(this):
    return this or 0

def convert_list_args_to_str(lis=[]):
    return [str(i) for i in lis]


d = {'Q1':[4,5,6],'Q2':[7,8,9],'Q3':[10,11,12],'Q4':[1,2,3]}

def get_fincal_yr(mnth,yr):
    q = ''
    try:
        if d.get(mnth) and mnth in ['Q1','Q2','Q3']:
            q = str(mnth)+'-' + str(yr)
        elif d.get(mnth) and mnth == 'Q4':
            q = str(mnth)+'-' + str(int(yr)+1)
    except Exception as e:
        q = str(e.message)
    return q
