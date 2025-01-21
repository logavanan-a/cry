from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from survey.models import *
from masterdata.models import *
from profiles.models import *
from django.db.models import Q

def responses_dashboard(request):
    responses_count = Answer.objects.filter(active=2).distinct('creation_key').count()
    locations_count = Village.objects.filter(active=2).count()
    districts = District.objects.filter(active=2).exclude(id__in=[9,6])
    users_count = UserProfile.objects.filter(active=2).count()
    surveys_count = Survey.objects.filter(active=2).count()
    # pie chart
    mysore_vil = Village.objects.filter(gramapanchayath__mandal__taluk__district__id=8)
    krish_vil = Village.objects.filter(gramapanchayath__mandal__taluk__district__id=7)
    mysore_res = Answer.objects.filter(active=2,object_id__in=mysore_vil).distinct('creation_key').count()
    krish_res = Answer.objects.filter(active=2,object_id__in=krish_vil).distinct('creation_key').count()
    # donut chart
    sur = Survey.objects.filter(active = 2)
    val = ["Survey","Response"]
    donut_values =[]
    donut_values.append(val)
    for i in sur:
        value =[str(i.name),Answer.objects.filter(question__block__survey_id = i.id).distinct('creation_key').count()]
        donut_values.append(value)
    # bar chart
    bar_val = []
    user = UserProfile.objects.filter(active = 2,designation__name__in=["CDO"])
    for i in user:
        data = Answer.objects.filter(user__id = i.user.id).distinct('creation_key').count()
        if data != 0:
            bar_value = [str(i.user.first_name),int(data)]
            bar_val.append(bar_value)
    bar_val.insert(0, ['User', 'Response'])

    if request.GET.get('districts'):
        dist_id = int(request.GET.get('districts'))
        villages = Village.objects.filter(gramapanchayath__mandal__taluk__district__id=dist_id)
        responses_count = Answer.objects.filter(active=2,object_id__in=villages).distinct('creation_key').count()
        locations_count = villages.count()
        users_count = UserSurveyMap.objects.filter(active=2,village__gramapanchayath__mandal__taluk__district__id=dist_id).distinct('user').count()
        # donut chart
        donut_values =[]
        donut_values.append(val)
        for i in sur:
            value =[str(i.name),Answer.objects.filter(question__block__survey_id = i.id,object_id__in=villages).distinct('creation_key').count()]
            donut_values.append(value)
    return render(request, 'survey/survey_dashboard.html',locals())

def bar_chart(request):

    return render(request,'charts/bar-chart.html',locals())


#code backed from dashboard_api.py
def response_data():
    fac = Facility.objects.filter(active=2, facility_type__active=2)
    fac_type = fac.values_list(
        'facility_type__name', flat=True).distinct()
    bene = Beneficiary.objects.filter(
        active=2, beneficiary_type__active=2)
    bene_types = bene.values_list(
        'beneficiary_type__name', flat=True).distinct()
    queryset = add(list(bene_types), list(fac_type))

    partner_level = [{
        "name": name,
        "value": 0
    } for name in queryset]

    chartdata_bodylist = [{
        "Reached": 0,
        "Indicator": name,
        "Total": 0
    } for name in queryset]

    chartdata_bodylist.append({
        "Reached": 0,
        "Indicator": "Villages",
        "Total": 0
    })

    chartdata_data = [{
        "percentage": 0,
        "total": 0,
        "actual": 0,
        "name": name,
        "backgroundColor": "#ffffff"
    } for name in queryset]

    chartdata_data.append({
        "percentage": 0,
        "total": 0,
        "actual": 0,
        "name": 'Villages',
        "backgroundColor": "#ffffff"
    })

    bene_bodylist = [{
        "Reached": 0,
        "Total": 0,
        "Beneficiary-Type": name
    } for name in bene_types]

    bene_data = [{
        "percentage": 0,
        "total": 0,
        "actual": 0,
        "name":  name,
        "backgroundColor": "#ffffff"
    } for name in bene_types]

    faci_bodylist = [{
        "Reached": 0,
        "Total": 0,
        "Facility-Type": name
    } for name in fac_type]

    faci_data = [{
        "percentage": 0,
        "total": 0,
        "actual": 0,
        "name":  name,
        "backgroundColor": "#ffffff"
    } for name in fac_type]

    response = {'status': 0, 'message': 'Something went wrong.', 'freq': [],
                'data': {
        'partner_level': {'name': 'Partner Level', 'data': partner_level},
        'chart_graph': [
            {'chartdata': {'name': 'Beneficiary / Facility / Villages',
                           'data': chartdata_data,
                           'table_data': {
                               'headerlist': ['Indicator', 'Total', 'Reached'],
                               "display_header": ['Indicator', 'Total', 'Reached'], 'bodylist': chartdata_bodylist}}},
            {'facility': {'name': 'Facility against the Villages.', 'data': faci_data, 'table_data': {
                'headerlist': ['Facility-Type', 'Total', 'Reached'],
                "display_header": ['Facility Type', 'Total', 'Reached'], 'bodylist': faci_bodylist}}},
            {'beneficiary': {'name': 'Beneficiary against the Villages.', 'data': bene_data, 'table_data': {
                'headerlist': ['Beneficiary-Type', 'Total', 'Reached'],
                "display_header": ['Beneficiary Type', 'Total', 'Reached'], 'bodylist': bene_bodylist}}}],
        'user_summary': {'name': 'User Summary', 'table_data': {'headerlist':
                                                                ['Username', 'Responses',
                                                                 'Last-Data-Collected'],
                                                                "display_header":
                                                                ['Username', 'Responses',
                                                                 'Last-Data-Collected'],
                                                                'bodylist': []}}}
    }
    return response

empty_response = response_data()


class GetUserDashboardData(CreateAPIView):
    serializer_class = UsersDashBoard

    def get_roles_types(self, slug):
        roles = RoleTypes.objects.filter(
            active=2, slug__iexact=slug).values_list('id', flat=True)
        return roles

    def get_users_partner_name(self, partners_users):
        partners_ = partners_users
        partner_name = lambda y: Partner.objects.get(id=y).name
        users_name = lambda x: User.objects.get(id=x).username
        both_combined = lambda x, y: partner_name(y) + ' - ' + users_name(x)
        response = [{'id': x, 'name': both_combined(
            x, y)} for x, y in partners_]
        return response

    def get_users_roles(self, user_id):
        admin = 0
        response = {'freq': [], 'regional': [],
                    'partner': []}
        freq = [{'id': fq.duration, 'duration': fq.get_duration_display(
        )} for fq in Frequence.objects.filter(active=2).exclude(duration=0)]
        regional = [{'id': fq.id, 'name': fq.name} for fq in MasterLookUp.objects.filter(
            active=2, parent__slug__iexact='region').exclude(slug__iexact='national-ho')]
        users_national = UserRoles.objects.filter(
            active=2, user_type=1, user__id=user_id, role_type__id__in=self.get_roles_types('ceo'), partner__isnull=True)
        users_regional = UserRoles.objects.filter(
            active=2, user_type=1, user__id=user_id, role_type__id__in=self.get_roles_types('regional-coordinator'), partner__isnull=True)
        users_partner = UserRoles.objects.filter(user__id=user_id,
                                                 active=2, user_type=2, partner__isnull=False)
        if users_national:
            admin = 1
            users = UserRoles.objects.filter(
                active=2, user_type=2, partner__isnull=False).distinct()
            partners_users = users.values_list('user__id', 'partner__id')
            response = {'freq': freq, 'regional': regional,
                        'partner': self.get_users_partner_name(partners_users)}
        elif users_regional:
            admin = 0
            reg_head = users_regional[0]
            get_region = reg_head.get_region_name()
            all_dash_response_region = DashBoardResponse.objects.filter(active=2,
                                                                        region_id=get_region['region_id'])
            users_id = all_dash_response_region.values_list(
                'user__id', flat=True).distinct()
            users = UserRoles.objects.filter(
                active=2, user_type=2, user_id__in=users_id, partner__isnull=False).distinct()
            partners_users = users.values_list('user__id', 'partner__id')
            response = {'freq': freq,
                        'partner': self.get_users_partner_name(partners_users)}
        elif users_partner:
            admin = 0
            response = {'freq': freq}
        return response, admin

    def post(self, request, *args, **kwargs):
        admin = 0
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            response = empty_response
            response.update(admin=admin)
            roles_data, admin = self.get_users_roles(data.user_id)
            get_overall_data = DashBoardResponse.objects.get(
                active=2, user__id=data.user_id, schedule__duration=0)
            if get_overall_data:
                response = {'status': 2, 'admin': admin,
                            'message': 'Successfully retrieved the data.', 'data': {}}
                partner_level = get_overall_data.partner_level
                chartdata = get_overall_data.chartdata
                facility = get_overall_data.facility
                beneficiary = get_overall_data.beneficiary
                user_summary = get_overall_data.user_summary
                partner_level.update({'name': 'Partner Level'})
                chartdata.update({'name': 'Beneficiary / Facility / Villages'})
                facility.update({'name': 'Facility'})
                beneficiary.update({'name': 'Beneficiary'})
                user_summary.update({'name': 'User Summary'})
                response['data'] = {'partner_level': partner_level,
                                    'chart_graph': [
                                        {'chartdata': chartdata},
                                        {'facility': facility},
                                        {'beneficiary': beneficiary}],
                                    'user_summary': user_summary}
                response.update(roles_data)
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class FrequenceDashBoard(CreateAPIView):
    serializer_class = FrequenceUsersDashBoard

    def get_users_partner_name(self, users):
        partners_ = UserRoles.objects.filter(
            active=2, user__id__in=users, user_type=2).distinct().values_list('user__id', 'partner__id')
        partner_name = lambda y: Partner.objects.get(id=y).name
        users_name = lambda x: User.objects.get(id=x).username
        both_combined = lambda x, y: partner_name(y) + ' - ' + users_name(x)
        response = [{'id': x, 'name': both_combined(
            x, y)} for x, y in partners_]
        return response

    def filter_partner_based_region(self, region_id):
        get_master_data = DashBoardResponse.objects.filter(
            active=2, user_type=3, region_id=region_id).distinct().values_list('user', flat=True)
        partners = self.get_users_partner_name(get_master_data)
        return partners

    def get_data_filter(self, data):
        key = int(data.get('key', 0))
        user_id = data.get('user_id', 0) or 0
        frequence = int(data.get('frequence', 77)) or 77
        region = int(data.get('region', 0)) or 0
        partner_id = int(data.get('partner_id', 0)) or 0
        get_overall_data = []
        get_master_data = DashBoardResponse.objects.filter(active=2)
        if user_id and region and frequence == 77 and partner_id == 0:
            get_overall_data = get_master_data.filter(
                region_id=region, user_type=2, schedule__duration=0)
        elif user_id and frequence and partner_id and region:
            get_overall_data = get_master_data.filter(
                region_id=region, user__id=partner_id, schedule__duration=frequence, user_type=3)
        elif user_id and region and frequence != 77:
            get_overall_data = get_master_data.filter(
                region_id=region, user_type=2, schedule__duration=frequence)
        elif user_id and region and frequence < 77:
            get_overall_data = get_master_data.filter(
                region_id=region, user_type=2, schedule__duration=frequence)
        elif user_id and frequence < 77 and region == 0:
            get_overall_data = get_master_data.filter(
                user__id=user_id, schedule__duration=frequence)
        elif user_id and region and frequence < 77 and partner_id:
            get_overall_data = get_master_data.filter(
                region_id=region, user__id=partner_id, schedule__duration=frequence)
        elif partner_id != 0 and frequence < 77 and region != 0:
            get_overall_data = get_master_data.filter(
                region_id=region, user__id=partner_id, schedule__duration=frequence, user_type=2)
        elif user_id and region == 0 and frequence < 77 and partner_id:
            get_overall_data = get_master_data.filter(
                user__id=user_id, schedule__duration=0)
        elif user_id and region == 0 and frequence == 77 and partner_id == 0:
            get_overall_data = get_master_data.filter(
                user__id=user_id, user_type=1, schedule__duration=0)
        return get_overall_data

    def post(self, request, *args, **kwargs):
        data = request.data
        freq = [{'id': fq.duration, 'duration': fq.get_duration_display(
        )} for fq in Frequence.objects.filter(active=2).exclude(duration=0)]
        key = int(data.get('key', 0))
        user_id = int(data.get('user_id', 0)) or 0
        frequence = int(data.get('frequence', 77)) or 77
        region = int(data.get('region', 0)) or 0
        partner_id = int(data.get('partner_id', 0)) or 0
        partners = []
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            part = GetUserDashboardData()
            roles_data, admin = part.get_users_roles(user_id)
            partners = roles_data.get('partner')
            response = empty_response
            get_overall_data = self.get_data_filter(data)
            if get_overall_data and key != 1:
                get_overall_data = get_overall_data[0]
                response = {'status': 2, 'freq': freq,
                            'message': 'Successfully retrieved the data.',
                            'data': {}}
                partner_level = get_overall_data.partner_level
                chartdata = get_overall_data.chartdata
                facility = get_overall_data.facility
                beneficiary = get_overall_data.beneficiary
                user_summary = get_overall_data.user_summary
                partner_level.update({'name': 'Partner Level'})
                chartdata.update({'name': 'Reached Out'})
                facility.update({'name': 'Facility'})
                beneficiary.update({'name': 'Beneficiary'})
                user_summary.update({'name': 'User Summary'})
                response['data'] = {'partner_level': partner_level,
                                    'chart_graph': [
                                        {'chartdata': chartdata},
                                        {'facility': facility},
                                        {'beneficiary': beneficiary}],
                                    'user_summary': user_summary}
                response.update(user_id=user_id,
                                frequence=frequence,
                                region=region,
                                partner_id=partner_id, partners=partners)
            else:
                partners = self.filter_partner_based_region(region)
                response = empty_response
                response.update(user_id=user_id,
                                frequence=frequence,
                                region=region,
                                partner_id=partner_id, partner=partners)
        else:
            response.update(errors=serializer.errors)
        return Response(response)
