from django.http import JsonResponse
from masterdata.models import Boundary,MasterLookUp
from datetime import datetime
from userroles.models import UserRoles,OrganizationLocation
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import pytz
import re
from ccd.settings import DATABASES

def pagination(request, plist):
    paginator = Paginator(plist, 60)
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

@csrf_exempt
def get_parent_levels(request,level):
    try:
        url_level = level
        userrole = UserRoles.objects.get(user__id=request.POST.get('uid'))
        orguser = OrganizationLocation.objects.get(user__id=userrole.id)
        tagged_locations = Boundary.objects.filter(boundary_level=7)
        modified_obj = request.POST.get("modified_date")
        if modified_obj:
            modified_date = convert_string_to_date(modified_obj)
            tagged_locations = tagged_locations.filter(modified__gt=modified_date,boundary_level=7)
        parent_locations = []
        tagged_locations = tagged_locations.order_by('modified')
        usm_obj = pagination(request, tagged_locations)
        for tl in usm_obj.object_list:
            location = Boundary.objects.get(id=tl.id)
            one_location_level = {}
            one_location_level['modified_date']=datetime.strftime(location.modified, '%Y-%m-%d %H:%M:%S.%f')
            one_location_level['name']=str(location.name)

            try:
                urban_rural = MasterLookUp.objects.get(id=location.object_id)
                one_location_level['location_type']=str(urban_rural.name)
            except:
                one_location_level['location_type']=""
            one_location_level['level'+str(orguser.organization_level)+'_id']=location.id

            for loc in location.get_parent_locations([]):
                for key,value in loc.items():
                    one_location_level[str(key)]=int(value)
            parent_locations.append(one_location_level)

        if level != orguser.organization_level:
            required_level = []
            for pl in parent_locations:
                level_dict = {}
                level = pl.get('level'+str(url_level)+'_id')
                required_boundary = Boundary.objects.get(id=level)
                level_dict['modified_date']=datetime.strftime(required_boundary.modified, '%Y-%m-%d %H:%M:%S.%f')
                level_dict['name']=str(required_boundary.name)
                try:
                    rural = MasterLookUp.objects.get(id=required_boundary.object_id)
                    level_dict['location_type']=str(rural.name)
                except:
                    level_dict['location_type']=""
                level_dict['level'+str(required_boundary.boundary_level)+'_id']=required_boundary.id

                level_dict.update(get_level_dict(required_boundary))
                required_level.append(level_dict)
            parent_locations = []
            parent_locations = required_level
        parent_locations = [dict(t) for t in set([tuple(d.items()) for d in parent_locations])]
        if parent_locations:
            return JsonResponse({'status':2,'Level '+str(url_level):parent_locations,"total_count":len(parent_locations),\
                       "records_per_page":usm_obj.paginator.per_page,\
                       "page_count":usm_obj.paginator.num_pages,})
        else:
            return JsonResponse({"status":2, \
               "message":"Data already sent",})
    except Exception as e:
        return JsonResponse({'status':0,'message':"User does not exist"})

import psycopg2
def level_seven(val):
    value = val
    conn = psycopg2.connect(host=DATABASES.get('default').get('HOST'),database=DATABASES.get('default').get('NAME'),\
    user=DATABASES.get('default').get('USER'), password=DATABASES.get('default').get('PASSWORD'))
    cursor = conn.cursor()
    cursor.execute("select m1.id country_id,m2.id state_id,m3.id district_id,m4.id mandal_id,m5.id village_id,m6.id six_id,m7.id hamlet_id from masterdata_boundary m7 join masterdata_boundary m6 on m6.id = m7.parent_id join masterdata_boundary m5 on m5.id = m6.parent_id join masterdata_boundary m4 on m4.id = m5.parent_id join masterdata_boundary m3 on m3.id = m4.parent_id join masterdata_boundary m2 on m2.id = m3.parent_id join masterdata_boundary m1 on m1.id = m2.parent_id where m7.id=%s;" %(value))
    nofam = cursor.fetchall()
    conn.close()
    key = ('level1_id','level2_id','level3_id','level4_id','level5_id','level6_id','level7_id')
    value = sum(tuple(nofam),())
    location = dict(zip(key,value))
    return location

def level_six(val):
    value = val
    conn = psycopg2.connect(host=DATABASES.get('default').get('HOST'),database=DATABASES.get('default').get('NAME'),\
    user=DATABASES.get('default').get('USER'), password=DATABASES.get('default').get('PASSWORD'))
    cursor = conn.cursor()
    cursor.execute("select m1.id country_id,m2.id state_id,m3.id district_id,m4.id mandal_id,m5.id village_id,m6.id six_id from masterdata_boundary m6 join masterdata_boundary m5 on m5.id = m6.parent_id join masterdata_boundary m4 on m4.id = m5.parent_id join masterdata_boundary m3 on m3.id = m4.parent_id join masterdata_boundary m2 on m2.id = m3.parent_id join masterdata_boundary m1 on m1.id = m2.parent_id where m6.id=%s;" %(value))
    nofam = cursor.fetchall()
    conn.close()
    key = ('level1_id','level2_id','level3_id','level4_id','level5_id','level6_id')
    value = sum(tuple(nofam),())
    location = dict(zip(key,value))
    return location

def level_five(val):
    value = val
    conn = psycopg2.connect(host=DATABASES.get('default').get('HOST'),database=DATABASES.get('default').get('NAME'),\
    user=DATABASES.get('default').get('USER'), password=DATABASES.get('default').get('PASSWORD'))
    cursor = conn.cursor()
    cursor.execute("select m1.id country_id,m2.id state_id,m3.id district_id,m4.id mandal_id,m5.id village_id from masterdata_boundary m5 join masterdata_boundary m4 on m4.id = m5.parent_id join masterdata_boundary m3 on m3.id = m4.parent_id join masterdata_boundary m2 on m2.id = m3.parent_id join masterdata_boundary m1 on m1.id = m2.parent_id where m5.id=%s;" %(value))
    nofam = cursor.fetchall()
    conn.close()
    key = ('level1_id','level2_id','level3_id','level4_id','level5_id')
    value = sum(tuple(nofam),())
    location = dict(zip(key,value))
    return location

def level_four(val):
    value = val
    conn = psycopg2.connect(host=DATABASES.get('default').get('HOST'),database=DATABASES.get('default').get('NAME'),\
    user=DATABASES.get('default').get('USER'), password=DATABASES.get('default').get('PASSWORD'))
    cursor = conn.cursor()
    cursor.execute("select m1.id country_id,m2.id state_id,m3.id district_id,m4.id mandal_id from masterdata_boundary m4 join masterdata_boundary m3 on m3.id = m4.parent_id join masterdata_boundary m2 on m2.id = m3.parent_id join masterdata_boundary m1 on m1.id = m2.parent_id where m4.id=%s;" %(value))
    nofam = cursor.fetchall()
    conn.close()
    key = ('level1_id','level2_id','level3_id','level4_id')
    value = sum(tuple(nofam),())
    location = dict(zip(key,value))
    return location

#levels api
@csrf_exempt
def get_levels(request,level):
    try:
        n=500
        url_level = level
        UserRoles.objects.get(user__id=request.POST.get('uid'))

        tagged_locations = Boundary.objects.filter(boundary_level=int(url_level))
        modified_obj = request.POST.get("modified_date")
        if modified_obj:
            modified_date = convert_string_to_date(modified_obj)
            tagged_locations = tagged_locations.filter(modified__gt=modified_date)
        parent_locations = []
        tagged_locations = tagged_locations.order_by('modified')[:int(n)]
        
        for location in tagged_locations:
            if url_level == "7":
                one_location_level = level_seven(location.id)
            elif url_level == "6":
                one_location_level = level_six(location.id)
            elif url_level == "5":
                one_location_level = level_five(location.id)
            elif url_level == "4":
                one_location_level = level_four(location.id)
            else:
                one_location_level = dict(pair for d in location.get_parent_locations([]) for pair in d.items())
                one_location_level['level'+str(url_level)+'_id']=int(location.id)
#            location = Boundary.objects.get(id=tl.id)
#            one_location_level = {}
#            for loc in location.get_parent_locations([]):
#                for key,value in loc.items():
#                    one_location_level[str(key)]=int(value)
            one_location_level['name']=re.sub(r'[^\x00-\x7F]+','',location.name).strip()
            one_location_level['active']=str(location.active)
            one_location_level['modified_date']=datetime.strftime(location.modified, '%Y-%m-%d %H:%M:%S.%f')
            try:
                rural = MasterLookUp.objects.get(id=location.object_id)
                one_location_level['location_type']=str(rural.name)
            except:
                one_location_level['location_type']=""
            parent_locations.append(one_location_level)
        if len(parent_locations) == int(n):
            flag = 2
        else:
            flag = 1
        if parent_locations:
            return JsonResponse({'status':2,'Level '+str(url_level):parent_locations,'flag':flag,
                       })
        else:
            return JsonResponse({"status":2, \
               "message":"Data already sent",})
    except Exception as e:
        return JsonResponse({'status':0,'message':"Something went wrong"})



def get_level_dict(required_boundary):
    level_dict = {}
    for loc in required_boundary.get_parent_locations([]):
        for key,value in loc.items():
            level_dict[str(key)] = int(value)
    return level_dict
