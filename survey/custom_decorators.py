from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from survey.models import *
from userroles.models import *
from ad_auth import auth_ad_user
from ccd.settings import BASE_DIR
from datetime import datetime
import calendar
#from profiles.models import *


def get_imei_user_id(uid):
    l = ["0","0","0","0","0"]
    x = str(uid)
    l[-len(x):] = [i for i in x]
    return "".join(i for i in l)


def validate_user(view):
    def is_auth(request, *args, **kwargs):
        error_msg, status = '', False
        if request.method == 'POST':
            email = request.POST.get('userId')
            password = request.POST.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                partner_user_activated = UserRoles.objects.get(user = user).partner
            if user is None:
                try:
                    ad_user = ADTable.objects.get(username__icontains=email.lower())
                    if int(auth_ad_user(ad_user.email,password)) == 1:
                        ad_password = UserRoles.objects.get(user=ad_user.user).mobile_number
                        ad_mail = ad_user.username
                        #ad_password = ad_user.mobile_number
                        user = authenticate(username=ad_mail,password=ad_password)
                except Exception as e:
                    pass
            if user is None:
                error_msg = "Invalid username or password"
            elif partner_user_activated.active != 2:
                error_msg = "Partner is deactivated"
            elif user.is_active:
                login(request, user)
                imei = request.POST.get('imei',0)
                userimei_obj, created = UserImeiInfo.objects.get_or_create(\
                                                                user = user,\
                                                                imei=imei)
                kwargs['userimei_id'] = get_imei_user_id(userimei_obj.id)
                kwargs['user'] = user
                status = True
            else:
                error_msg = "User is In-active"
        kwargs.update({'status':status, 'error_msg':error_msg})
        return view(request, *args, **kwargs)
    return is_auth



def validate_user_version(view):
    def check_version(request, *args, **kwargs):
        error_msg, status = '', False
        user_id = request.POST.get('uId')
        t_id = request.POST.get('t_id').replace('%2C',',')
        vn = request.POST.get('vn').replace('%2C',',')
        sids_list = [int(i) for i in t_id.split(',')]
        vns_list = [float(i) for i in vn.split(',')]
        res = dict(zip(sids_list,vns_list))
        for k,v in res.items():
            survey_id, vn = k, v
            userrole = UserRoles.objects.filter(user__id=int(user_id))
            survey_access = DetailedUserSurveyMap.objects.filter(user = \
                                                        userrole,survey__id=int(survey_id)).exists()
            if User.objects.filter(id=int(user_id)).exists() and survey_id and survey_access:
                version_list = Version.objects.filter(survey__id = int(survey_id))
                status = True
                if len(version_list) >= 1 and float(version_list.latest('id').version_number) == float(vn):
                    kwargs['latestversion'] = version_list.latest('id').version_number
                else:
                    error_msg = "Version mis-match"
            else:
                error_msg = "User doesnot exist or Survey not taged to user"
        kwargs.update({'status':status, 'error_msg':error_msg})
        return view(request, *args, **kwargs)
    return check_version


def validate_post_method(view):
    def check_method(request, *args, **kwargs):
        error_msg, status = '', False
        if request.method != 'POST':
            res = {'message':'Invalid request'}
            return JsonResponse(res)
        return view(request, *args, **kwargs)
    return check_method

def write_to_log(view):
    def write(request, *args, **kwargs):
        res = view(request, *args, **kwargs)
        current_date = datetime.now()
        year = current_date.year
        month = calendar.month_name[current_date.month]
        date = current_date.day
        new_file_path = '%s/static/logAnswer/%s/%s/%s' % (BASE_DIR, str(year), str(month), str(date))
        if not os.path.exists(new_file_path):
            os.makedirs(new_file_path)
        file_name = "AnswerLog" + "-" + str(year) + "-" + str(month) + "-" + str(date) + ".txt"
        full_filename = os.path.join(BASE_DIR, new_file_path, file_name)
        text_file = None
        false = "False"
        true = "True"
        if os.path.isfile(full_filename):
            text_file = open(full_filename, 'a')
        else:
            text_file = open(full_filename, 'wb+')
        text_file.write("-----"+str(current_date)+"-----")
        text_file.write("\n\n")
        text_file.write("status : "+str(eval(res.content).get('status')))
        text_file.write("\n\n")
        text_file.write("error : "+str(eval(res.content).get('message')))
        text_file.write("\n\n")
        text_file.write("request : "+str(request.POST.dict()))
        text_file.write("\n\n")
        text_file.write("################")
        text_file.write("\n\n")
        text_file.close()
        return res
    return write
