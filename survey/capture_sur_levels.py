from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from datetime import datetime
from survey.models import *
from survey.custom_decorators import *
from django.db import transaction
#from profiles.models import *
from masterdata.models import *
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import os
import pytz


def pagination(request, plist):
    paginator = Paginator(plist, 1)
    page = request.GET.get('page', '')
    try:
        plist = paginator.page(page)
    except PageNotAnInteger:
        plist = paginator.page(1)
    except EmptyPage:
        plist = paginator.page(paginator.num_pages)
    return plist

def convert_string_to_date(string):
    date_object = ''
    try:
        date_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    except:
        date_object = None
    if not date_object:
        try:
            date_obj = datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f')
            date_object = datetime(int(date_obj.year),int(date_obj.month),int(date_obj.day),int(date_obj.hour),int(date_obj.minute),int(date_obj.second),int(date_obj.microsecond),pytz.UTC)
        except:
            date_object = None
    return date_object

#dictd = {'country':1, 'state':2, 'district':3, 'taluk':4, 'gramapanchayath':5, 'village':6}
#model_dict = {'country':Country,'state':State, 'district':District, 'taluk':Taluk, 'gramapanchayath':GramaPanchayath, 'village':Village}
#level_dict = {'country':'level1_id','state':'level2_id', 'district':'level3_id', 'taluk':'level4_id', 'gramapanchayath':'level5_id', 'village':'level6_id'}
#key_dict = {'country':'Level 1','state':'Level 2', 'district':'Level 3', 'taluk':'Level 4', 'gramapanchayath':'Level 5', 'village':'Level 6'}

## Demographic level
#@csrf_exempt
#def levellist(request, key=''):
#    
#    if request.method == 'POST':
#        user_id = request.POST.get("uid")
#        flag=""
#        if not user_id.isdigit() or user_id == '':
#            res = {"status":0, \
#               "message":"Enter a valid user id",}
#            return JsonResponse(res)
#        usm_obj = OrganizationLocation.objects.filter(user__user__id=int(user_id)).distinct('object_id')
#        modified_obj = request.POST.get("modified_date")
#        if modified_obj:
#            modified_date = convert_string_to_date(modified_obj)
#            usm_obj = usm_obj.filter(modified__gt=modified_date)
#            flag = False
#        status, message = 2, 'Success'
#        ctry=[]
#        usm_obj = pagination(request, usm_obj)
#        ma = []
#        for i in usm_obj:
#            lev=i.diff_levels_id()[::-1]
#            fdict = {}
#            level_obj = None
#            for counter, kl in enumerate(lev):
#                fkey = 'level'+str(counter+1)+'_id'
#                if not int(counter+1) > dictd.get(key):
#                    fdict.update({fkey:kl})
#            try:
#                level_obj= model_dict.get(key).objects.get(id=fdict.get(level_dict.get(key)))
#            except:
#                pass
#            if level_obj:
#                if not level_obj.id in ma:
#                    ctsp = { "id":level_obj.id,\
#                              "name": level_obj.name,\
#                              "modified_date":datetime.strftime(level_obj.modified, '%Y-%m-%d %H:%M:%S.%f'), \
#                              "active": level_obj.active, \
#                           }
#                    ctsp.update(fdict)
#                    ctry.append(ctsp)
#                ma.append(level_obj.id)
#        if ctry:
#            res = {key_dict.get(key):ctry ,\
#                   "status":status, \
#                   "message":message,\
#                   "total_count":len(ctry),\
#                   "records_per_page":usm_obj.paginator.per_page,\
#                   "page_count":usm_obj.paginator.num_pages,}
#        elif flag == False:
#            res = { "status":2, \
#                    "message":"Data already sent",}
#        else:
#            res= { "status":0, \
#                    "message":"No Locations for this user",}
#        users = UserLocation.objects.filter().values_list('user__user__id',flat=True)
#        if not int(user_id) in users:
#            res = {"status":0, \
#               "message":"User does not exists",}
#        return JsonResponse(res)




## parent child api
#@csrf_exempt
#def parent_child_info(request):
#    if request.method == 'POST':
#        status, message = 2, 'Success'
#        user_id = request.POST.get("uid")
#        if not user_id.isdigit() or user_id == '':
#            res = {"status":0, \
#               "message":"Enter a valid user id",}
#            return JsonResponse(res)
##        usm_obj = DetailedUserSurveyMap.objects.filter(user__id=int(user_id)).distinct('survey')
##        surveys =[]
##        
##        modified_obj = request.POST.get("modified_date")
##        if modified_obj:
##            modified_date = convert_string_to_date(modified_obj) + timedelta(days=1)
##            usm_obj = DetailedUserSurveyMap.objects.filter(user__id=int(user_id),modified__gt=modified_date).distinct('survey')
##        usm_obj = pagination(request, usm_obj)
##        for i in usm_obj:
##            sur_level = Survey.objects.get(id=int(i.survey_id))
##            level = str(sur_level.data_entry_level.name)
##            dusm = DetailedUserSurveyMap.objects.filter(user__id=int(user_id),survey__id=int(i.survey_id))
##            child_ids =[]
##            for j in dusm:
##                child_ids.append(j.object_id)
##            if level == "State":
##                order = "level2"
##            elif level == "District":
##                order = "level3"
##            elif level == "Taluk":
##                order = "level4"
##            elif level == "GramaPanchayath":
##                order = "level5"
##            elif level == "Village":
##                order = "level6"
##            
##            surveys.append({"id":i.id ,\
##                            "parent_id":i.survey_id ,\
##                            "child_id": "",\
##                            "order_level": order,\

##                            "active":i.active,\
##                            "modified_date":datetime.strftime(i.modified, '%Y-%m-%d %H:%M:%S')})
#        res = {
##                "parent_child":surveys ,\
#               "status":status, \
#               "message":message,\
##               "total_count":usm_obj.paginator.count,\
##               "records_per_page":usm_obj.paginator.per_page,\
##               "page_count":usm_obj.paginator.num_pages,
#               }
#        users = DetailedUserSurveyMap.objects.filter().values_list('user__id',flat=True)
#        if not int(user_id) in users:
#            res = {"status":0, \
#               "message":"User does not exists",}
#        return JsonResponse(res)
