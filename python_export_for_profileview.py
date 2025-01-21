from django.utils import timezone
import pytz
from collections import OrderedDict
import datetime
import dateutil
from facilities.models import *
from masterdata.models import *
from survey.models import *
from reports.models import *


def aaganwadi_profile(pid):
    from django.utils import timezone
    import pytz
    import datetime
    import dateutil
    answer = []
    count = 0
    response_count = 0
    test = 0

    b = Facility.objects.filter(partner_id = pid , facility_type_id = 262)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'SubType' , 'Location' , 'Total Children']
        name = i.name.encode('utf-8')
        subtype = int(i.facility_subtype_id)
        subtype_name = MasterLookUp.objects.get(id = subtype).name.encode('utf-8')
        location = jsondata.get('boundary_id')
        if location is not None and type(location) is list :
            location = location[0]
        elif location is not None:
            location = location
        location_name = Boundary.objects.get(id = int(location)).name.encode('utf-8')
        j = JsonAnswer.objects.filter(cluster__0__facility__id = int(i.id) , survey_id = 3)
        if j:
            submission = j[0].submission_date
            for k in j:
                if k.submission_date >= submission:
                    submission = k.submission_date
                    json_id = k.id
            json = j.get(id = json_id)
            jsonid = json.id
            total_children_1 = json.response.get('124').encode('utf-8') if json.response.get('124') else 0
            total_children_2 = json.response.get('121').encode('utf-8') if json.response.get('121') else 0
            total_children = total_children_1 + total_children_2
        else:
            jsonid = 0
            submission = timezone.now()
            total_children = 0
        dict1 = {}
        dict1 = {'Name':name , 'SubType': subtype_name,'Location' : location_name ,'Total_children':total_children}
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('Count===========================COUNT' , count)
            print dict1
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "FAC" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.facility_type_id ,  submission_date = submission)
            
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            print dict1
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()
            print p.profile_info


def healthcenter_profile(pid):
    from django.utils import timezone
    import pytz
    import datetime
    import dateutil

    answer = []
    count = 0
    response_count = 0
    test = 0

    b = Facility.objects.filter(partner_id = pid , facility_type_id = 286)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'SubType' , 'Location' ]
        name = i.name.encode('utf-8')
        subtype = int(i.facility_subtype_id)
        subtype_name = MasterLookUp.objects.get(id = subtype).name.encode('utf-8')
        location = jsondata.get('boundary_id')
        if location is not None and type(location) is list :
            location = location[0]
        elif location is not None:
            location = location
        location_name = Boundary.objects.get(id = int(location)).name.encode('utf-8')
        submission = timezone.now()
        jsonid = 0
        dict1 = {}
        dict1 = {'Name' : name ,'SubType': subtype_name,'Location': location_name}
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('Count===========================COUNT' , count)
            print dict1
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "FAC" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.facility_type_id ,  submission_date = submission)
            
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()

def school_profile(pid):
    from django.utils import timezone
    import pytz
    import datetime
    import dateutil

    answer = []
    count = 0
    response_count = 0
    test = 0
    j = JsonAnswer.objects.filter(survey_id = 55)
    b = Facility.objects.filter(partner_id = pid , facility_type_id = 294)
    j = JsonAnswer.objects.filter(survey_id = 37)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'SubType' , 'Location' , '48' , '76']
        name = i.name.encode('utf-8')
        subtype = int(i.facility_subtype_id)
        subtype_name = MasterLookUp.objects.get(id = subtype).name.encode('utf-8')
        location = jsondata.get('boundary_id')
        if location is not None and type(location) is list :
            location = location[0]
        elif location is not None:
            location = location
        if location is None:
            location_name = None
        else:
            location_name = Boundary.objects.get(id = int(location)).name.encode('utf-8')
        j = JsonAnswer.objects.filter(cluster__0__facility__id = int(i.id) , survey_id = 2)
        if j:
            submission = j[0].submission_date
            for k in j:
                if k.submission_date >= submission:
                    submission = k.submission_date
                    json_id = k.id
            json = j.get(id = json_id)
            jsonid = json.id
            category_of_school = json.response.get('48') if json.response.get('48') else None
            if category_of_school:
                category_text = Choice.objects.get(id = int(category_of_school)).text.encode('utf-8')
            else:
                category_text = None
            total_children = json.response.get('76').encode('utf-8') if json.response.get('76') else None
        else:
            jsonid = 0
            submission = timezone.now()
            category_text = None
            total_children = None
        dict1 = {}
        dict1 = {'Name' : name , 'SubType':subtype_name,'Location':location_name,'48' : category_text,'76': total_children}
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('count==========================================COUNT' , count)
            print dict1
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "FAC" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.facility_type_id ,  submission_date = submission)
            
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()


def household_profile(pid):
    from django.utils import timezone
    import pytz
    from collections import OrderedDict
    import datetime
    import dateutil

    answer = []
    count = 0
    response_count = 0
    test = 0
    j = JsonAnswer.objects.filter(survey_id = 55)
    b = Beneficiary.objects.filter(partner_id = pid , beneficiary_type_id = 2)
    j = JsonAnswer.objects.filter(survey_id = 37)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'Gender' , 'DOB' , 'Age']
        name = jsondata.get('name') if jsondata.get('name') else None
        if name is not None and type(name) is list :
            name = name[0].encode('utf-8')
        elif name is not None:
            name = name.encode('utf-8')
        gender = jsondata.get('gender') if jsondata.get('gender') else None
        if gender is not None and type(gender) is list :
            gender = gender[0].encode('utf-8')
        elif gender is not None:
            gender = gender.encode('utf-8')
        dob = jsondata.get('date_of_birth')[0].encode('utf-8') if jsondata.get('date_of_birth') else None
        isvalidDate = True
        jsonid = 0
        submission = i.modified
        try:
            d = datetime.datetime.strptime(str(dob), '%m-%d-%Y').date()
            now = datetime.datetime.utcnow()
            now = now.date()
            age = dateutil.relativedelta.relativedelta(now, d)
            age = age.years
        except  ValueError:
            isvalidDate = False

        if not isvalidDate:
            dob = None
            age = None
        dict1 = OrderedDict()
        dict1 = OrderedDict([('Name' , name) , ('Gender' , gender ), ('DOB' , dob) , ('Age' , age)])
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('count==========================================COUNT' , count)
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "BEN" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.beneficiary_type_id ,  submission_date = submission)
            
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()


def mother_profile(pid):
    from django.utils import timezone
    import pytz
    from collections import OrderedDict
    import datetime
    import dateutil

    answer = []
    count = 0
    response_count = 0
    test = 0
    j = JsonAnswer.objects.filter(survey_id = 55)
    b = Beneficiary.objects.filter(partner_id = pid , beneficiary_type_id = 3)
    j = JsonAnswer.objects.filter(survey_id = 37)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'Head of Household' , 'DOB' , 'Age']
        name = jsondata.get('name') if jsondata.get('name') else None
        if name is not None and type(name) is list :
            name = name[0].encode('utf-8')
        elif name is not None:
            name = name.encode('utf-8')
        household_id = i.parent_id 
        name_of_household = Beneficiary.objects.get(id = household_id).name
        head_of_household = name_of_household.encode('utf-8') if name_of_household else None
        dob = jsondata.get('date_of_birth')[0].encode('utf-8') if jsondata.get('date_of_birth') else None
        isvalidDate = True
        jsonid = 0
        submission = i.modified
        try:
            d = datetime.datetime.strptime(str(dob), '%m-%d-%Y').date()
            now = datetime.datetime.utcnow()
            now = now.date()
            age = dateutil.relativedelta.relativedelta(now, d)
            age = age.years
        except  ValueError:
            isvalidDate = False

        if not isvalidDate:
            dob = None
            age = None
        dict1 = OrderedDict()
        dict1 = OrderedDict([('Name' , name) , ('Head of Household' , head_of_household ), ('DOB' , dob) , ('Age' , age)])
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('count==========================================COUNT' , count)
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "BEN" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.beneficiary_type_id ,  submission_date = submission)
            
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()


def child_profile(pid):
    from django.utils import timezone
    import pytz
    from collections import OrderedDict
    import datetime
    import dateutil
    answer = []
    count = 0
    response_count = 0
    test = 0
    j = JsonAnswer.objects.filter(survey_id = 55)
    b = Beneficiary.objects.filter(partner_id = pid , beneficiary_type_id = 4)
    j = JsonAnswer.objects.filter(survey_id = 37)
    for i in b:
        jsondata = i.jsondata
        question = ['Name' , 'Head of Household' , 'DOB' , 'Age' , '155' , '159']
        name = jsondata.get('name') if jsondata.get('name') else None
        if name is not None and type(name) is list :
            name = name[0].encode('utf-8')
        elif name is not None:
            name = name.encode('utf-8')
        household_id = i.parent_id 
        name_of_household = Beneficiary.objects.get(id = household_id).name
        head_of_household = name_of_household.encode('utf-8') if name_of_household else None
        dob = jsondata.get('date_of_birth')[0].encode('utf-8') if jsondata.get('date_of_birth') else None
        isvalidDate = True
        try:
            d = datetime.datetime.strptime(str(dob), '%m-%d-%Y').date()
            now = datetime.datetime.utcnow()
            now = now.date()
            age = dateutil.relativedelta.relativedelta(now, d)
            age = age.years
        except  ValueError:
            isvalidDate = False

        j = JsonAnswer.objects.filter(cluster__0__beneficiary__id = i.id , survey_id = 37)
        if j:
            submission = j[0].submission_date
            for k in j:
                if k.submission_date >= submission:
                    submission = k.submission_date
                    json_id = k.id
            json = j.get(id = json_id)
            jsonid = json.id
            father_name = json.response.get('155').encode('utf-8') if json.response.get('155') else None
            mother_name = json.response.get('159').encode('utf-8') if json.response.get('159') else None
            
        else:
            jsonid = 0
            submission = timezone.now()
            father_name = None
            mother_name = None
        if not isvalidDate:
            dob = None
            age = None
        dict1 = {}
        dict1 = {"Name":name,"Head of Household":head_of_household,"DOB": dob ,"Age": age , '155' : father_name ,'159':mother_name}
        p = ProfileView.objects.filter(ben_fac_loc_id = i.id)
        if not p:
            print 'NEW OBJECT CREATED'
            print('partner==============================================partner',pid)
            count += 1
            print('count==========================================COUNT' , count)
            ProfileView.objects.create(jsonid = jsonid , uuid_lid = i.uuid , type_name = "BEN" , ben_fac_loc_id = i.id , profile_info = dict1 , partner_id = i.partner_id , type_id = i.beneficiary_type_id , submission_date = submission )
        else:
            response_count += 1
            print "Speed is running damn fast"
            print('partner==============================================partner',pid)
            print('response_count==========================================response_count' , response_count)
            p = p[0]
            p.profile_info = dict1
            p.submission_date = submission
            p.jsonid = jsonid
            p.save()
        

def profileview_run():
    b = Beneficiary.objects.values_list('partner_id').distinct()
    b = list(b)
    for i in b:
        school_profile(i[0])
        print('partner ==================== partner ======================= parnter ============'  , i)
        healthcenter_profile(i[0])
        print('partner ==================== partner ======================= parnter ============'  , i)
        aaganwadi_profile(i[0])
        print('partner ==================== partner ======================= parnter ============'  , i)

