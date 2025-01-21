from django.http import JsonResponse
from django.views.generic import View
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from survey.models import UserTabDetails, UserTimeIntervals
from django.shortcuts import render
from django.contrib.auth.models import User


def validate_data(view):
    def is_auth(request, *args, **kwargs):
        try:
            if type(eval(request.POST.get('DeviceDetails'))) != list:
                return JsonResponse({'status':False,'message':'Invalid Data'})
        except:
            pass
        return view(request, *args, **kwargs)
    return is_auth


def get_alaram_frequency(userid=''):
    frequency = 15
    if userid and UserTimeIntervals.objects.filter(user__id=int(userid)).exists():
        frequency = UserTimeIntervals.objects.get(user__id=int(userid)).frequency
    return frequency


class CaptureTabInfo(View):

    @method_decorator(csrf_exempt)
    @method_decorator(validate_data)
    def dispatch(self, request, *args, **kwargs):
        return super(CaptureTabInfo, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def convert_date_time(dttime=''):
        dtobj = None
        if dttime:
            dtobj = datetime.strptime(dttime, "%d-%m-%Y %H:%M:%S%p")
        return dtobj

    def post(self, request, *args, **kwargs):
        status, message = False, 'Something went wrong please contact admin'
        response = {}
        post_data = eval(request.POST.get('DeviceDetails'))
        for tbd in post_data:
            userid = tbd.get('userId', '')
            lastcharge = self.convert_date_time(tbd.get('LastChargeTime', ''))
            tbtime = self.convert_date_time(tbd.get('TimeStamp', ''))
            qparam = {'cell_id':tbd.get('CellId'),\
                        'signal_strength':tbd.get('sStrength'),\
                        'charge':tbd.get('Charge'), 'last_chargetime':lastcharge,\
                        'sim_serialnumber':tbd.get('SimSNo'), 'imei_info':tbd.get('IMEI'),\
                        'free_space':tbd.get('FreeSpace'), 'apps':tbd.get('apps'),\
                        'timestamp':tbtime,'latitude':tbd.get('latitude'),\
                        'longitude':tbd.get('longitude'),'n_type':tbd.get('n_type'),\
                        'make':tbd.get('make'),'model':tbd.get('model')
                    }
            if userid and userid.isdigit():
                qparam.update({'userid':int(userid)})
            else:
                qparam.update({'userid':0})
            try:
                UserTabDetails.objects.create(**qparam)
                status, message = True, 'Data saved successfully'
            except Exception as e:
                message = e.message
        alarm = get_alaram_frequency(userid)
        response = {'status':status,'message':message,'alaramFrequency':alarm,}
        return JsonResponse(response)


class UserMapView(View):

    @staticmethod
    def get_user_lat_long(user):
        total, count = 0, 0;
        lat_lang_list = []
        tabdatalist = UserTabDetails.objects.filter(userid=int(user)).exclude(latitude="0.0",\
                                                                longitude="0.0").distinct('latitude','longitude')
        utids = tabdatalist.values_list('id',flat=True)
        user_tabdata_list = UserTabDetails.objects.filter(id__in=utids).order_by('id')[:50]
        total = user_tabdata_list.count()
        for obj in user_tabdata_list:
            count += 1
            if count == 1:
                key = 1
            elif count == total/2:
                key = 2
            elif count == total-1:
                key = 3
            else:
                key = -1
            lat_lang_list.append([str(obj.latitude),str(obj.longitude), key])
        return lat_lang_list

    def get(self, request, *args, **kwargs):
        if request.session.get('previous_user',0):
            del request.session['previous_user']
        user_ids = UserTabDetails.objects.distinct('userid').values_list('userid',flat=True)
        user_list = User.objects.filter(id__in=user_ids)
        return render(request, 'view-users-on-map.html',locals())

    def post(self, request, *args, **kwargs):
        lat_lang_list, previous_lat_lang, response = [], [], {}
        user = request.POST.get('user')
        if request.session.get('previous_user',0):
            previous_lat_lang = self.get_user_lat_long(request.session.get('previous_user'))
        if user and request.is_ajax():
            lat_lang_list = self.get_user_lat_long(user)
            request.session['previous_user'] = user
            response = {'lat_lang_list':lat_lang_list,'previous_lat_lang':previous_lat_lang}
        return JsonResponse(response)






