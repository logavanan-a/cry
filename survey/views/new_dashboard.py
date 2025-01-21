from masterdata.models import Boundary,MasterLookUp
from survey.models import JsonAnswer,SurveyDataEntryConfig,DashBoardResponse
from beneficiary.models import BeneficiaryType,Beneficiary
from facilities.models import Facility
from partner.models import Partner
from userroles.models import UserRoles
from .custom_dates import CustomDates
from survey_views_two import get_required_level_info
from django.contrib.auth.models import User
from django.db.models import Max,Q
from survey.views.survey_views_two import get_required_level_info
import os

partner_set = Partner.objects.all()
response_set = JsonAnswer.objects.filter(active=2)
community_organizer_set = UserRoles.objects.all()
beneficiary_set = Beneficiary.objects.filter(active=2)
beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None)
facility_types = MasterLookUp.objects.filter(active=2,parent__slug='facility-type')
facility_set = Facility.objects.filter(active=2)
user_set = User.objects.filter(is_active=True)
boundary_set = Boundary.objects.filter(active=2)

class DashBoardSnapShot():
    @staticmethod
    def get_partner_users(partner):
        partner_users = community_organizer_set.filter(partner=partner , role_type__slug='data-entry-operator')
        return partner_users

    def partner_computation(self):
        t = []
        t1 = []
        user_summary_helper = ['Username','Last-Data-Collected','Responses']
        for pc,partner in enumerate(partner_set):
            partner_users = DashBoardSnapShot.get_partner_users(partner).values_list('user',flat=True)
            if not partner_users:
                continue
            calculation_days = [CustomDates().current_week_days(),
                CustomDates().current_month_days(),CustomDates().current_fy_quarter_dates(),
                CustomDates().current_fy_half_year(),
                CustomDates().current_year_dates('2018'),CustomDates().fy_dates('2017')]
            for c,cd in enumerate(calculation_days):
                user_response_count = []
                partner_data = []
                chart = []
                chart_data = []
                for community_organizer in  partner_users:
                    responses = response_set.filter(user__id =community_organizer,created__gte=cd.get('start_date'),created__lte=cd.get('end_date'))
                    last_collected = None
                    try:
                        last_collected = responses.aggregate(Max('created')).get('created__max').strftime('%Y-%m-%d %H:%M %p')
                    except:
                        last_collected = "N/A"
                    try:
                        user_response_count.append({'Username':user_set.get(id=community_organizer).first_name,
                        'Responses':responses.count(),
                        'Last-Data-Collected':last_collected})
                    except:
                        t1.append(community_organizer)
                        print("new ids" ,t1)
                user_responses = response_set.filter(user__in=partner_users,created__gte=cd.get('start_date'),
                                                     created__lte=cd.get('end_date'))
                partner_data.append(DashBoardSnapShot.get_village_count(user_responses,partner)[0])
                chart.append(DashBoardSnapShot.get_village_count(user_responses,partner)[1])
                chart_data.append(DashBoardSnapShot.get_village_count(user_responses,partner)[2])
                partner_beneficiary_count = DashBoardSnapShot.partner_beneficiary_count(DashBoardSnapShot.get_beneficiary_count(user_responses,partner))
                partner_data.extend(partner_beneficiary_count[0])
                chart.extend(partner_beneficiary_count[1])
                chart_data.extend(partner_beneficiary_count[2])
                partner_facility_count = self.partner_facility_count(DashBoardSnapShot.get_facility_count(user_responses,partner))
                partner_data.extend(partner_facility_count[0])
                chart.extend(partner_facility_count[1])
                chart_data.extend(partner_facility_count[2])
                partner_level = {'data':partner_data,'name':'Partner Level'}
                user_summary = {'table_data':{
                                                        'display_header':user_summary_helper,
                                                        'headerlist':user_summary_helper,
                                                        'bodylist':user_response_count
                                                    },
                                        'name':'User Summary'
                                       }
                chart_graph = {
                        'table_data':{
                                    'display_header':['Indicator','Reached','Total','Others'],
                                    'headerlist':['Indicator','Reached','Total','Others'],
                                    'bodylist':chart
                                },
                        'data':chart_data,
                        'name':'Facility / Beneficiary / Villages'
                            }
                facility = {'table_data':{'display_header':['Indicator','Reached','Total','Others'],
                                                 'headerlist':['Indicator','Reached','Total','Others'],
                                                 'bodylist':partner_facility_count[3]
                                                },
                                    'data':partner_facility_count[4],
                                    'name':'Facility (Reach for District)'
                                   }
                beneficiary = {'table_data':{'display_header':['Indicator','Reached','Total','Others'],
                                                    'headerlist':['Indicator','Reached','Total','Others'],
                                                    'bodylist':partner_beneficiary_count[3]
                                                    },
                                        'data':partner_beneficiary_count[4],
                                        'name':'Beneficiary (Reach for Village)'
                                      }
                dbr,dbrs = DashBoardResponse.objects.get_or_create(partner=partner,periodicity=c+1)
                dbr.partner_level = partner_level
                dbr.user_summary = user_summary
                dbr.chartdata = chart_graph
                dbr.facility = facility
                dbr.beneficiary = beneficiary
                print(user_summary)
                print(partner)
                print(partner.id)
                dbr.save()
            os.system('clear')
            print ("Percentage Completed ..",(pc*100)/partner_set.count())
        os.system('clear')
        print("t" , t)
        print("t1" , t1)
        print ("Dashboard Computation Done..")

    @staticmethod
    def get_village_count(user_responses,partner):
        village_reach = {}
        partner_villages_count = 0
        village_survey = SurveyDataEntryConfig.objects.filter(
                Q(content_type1__model='locationtypes')).values_list('survey',flat=True)
        partner_villages_count = [i[0]['boundary']['id'] for i in list(user_responses.filter(survey__id__in=village_survey).values_list('cluster',flat=True))]
        partner_villages = [i['id']for i in eval(get_required_level_info(partner.state.id,6).content).get('locations') if i]
        partner_villages_count = list(set(partner_villages_count))
        partner_level_count = {'name':'Village','value':len(partner_villages)}
        village_reach = {'Indicator':'Village','Reached':len(partner_villages_count),
                         'Total':len(partner_villages),'Others':0}
        village_reach_chart = {'total':len(partner_villages),'actual':len(partner_villages_count),'name':'Village',
                               'percentage':DashBoardSnapShot.percentage_calculator(len(partner_villages),len(partner_villages_count)),
                               'backgroundColor':'#ff5544','others':0,'others_percentage':0,'others_backgroundColor':''}
        return (partner_level_count,village_reach,village_reach_chart)

    @staticmethod
    def get_beneficiary_count(user_responses,partner):
        beneficary_count = []
        for bt in beneficiary_types:
            village_count,others_count = 0,0
            beneficiary_count = beneficiary_set.filter(active=2,beneficiary_type=bt,partner=partner).count()
            beneficiary_survey = SurveyDataEntryConfig.objects.filter(
                    Q(Q(content_type1__model='beneficiary'),Q(object_id1=bt.id))|Q(Q(content_type2__model='beneficiary'),Q(object_id2=bt.id))).values_list('survey',flat=True)
            beneficiers = []
            for i in list(user_responses.filter(survey_id__in=beneficiary_survey).values_list('cluster',flat=True)):
                try:
                    beneficiers.append(i[0]['beneficiary']['id'])
                except:
                    pass
            try:
                locations = [ eval(i['address'][0])['address_0']['boundary_id']for i in beneficiary_set.filter(id__in=set(beneficiers)).custom_values(['address'])]
            except:
                locations = []
            partner_villages = [i['id']for i in eval(get_required_level_info(partner.state.id,6).content).get('locations')]
            r_locations = Boundary.objects.filter(id__in=locations).distinct('parent').values_list('parent',flat=True)
            for vl in r_locations:
                if vl in partner_villages:
                    village_count = village_count+1
                else:
                    others_count = others_count+1
            beneficary_count.append({bt.name:{'village_count':village_count,'others_count':others_count,
                'beneficiary_count':beneficiary_count,
                'beneficiary_reached':len(list(set(beneficiers))),'partner_villages_count':len(partner_villages)}})
        return beneficary_count

    @staticmethod
    def partner_beneficiary_count(partner_beneficiarys):
        partner_beneficiary_dict = []
        partner_beneficiary_reach = []
        partner_beneficiary_reach_chart = []
        partner_beneficiary_village_reach = []
        partner_beneficiary_village_reach_chart = []
        for bt in beneficiary_types:
            for pb in partner_beneficiarys:
                if bt.name in pb.keys():
                    # To get partner level count
                    partner_beneficiary_dict.append({'name':bt.name,
                            'value':pb.get(bt.name).get('beneficiary_count')})
                    # To get table data
                    partner_beneficiary_reach.append({'Indicator':bt.name,
                        'Reached':pb.get(bt.name).get('beneficiary_reached'),
                        'Total':pb.get(bt.name).get('beneficiary_count'),'Others':0})
                    # To get chart data
                    partner_beneficiary_reach_chart.append({'total':pb.get(bt.name).get('beneficiary_count'),
                            'actual':pb.get(bt.name).get('beneficiary_reached'),
                            'percentage':DashBoardSnapShot.percentage_calculator(pb.get(bt.name).get('beneficiary_count'),
                            pb.get(bt.name).get('beneficiary_reached')),'name':bt.name,'backgroundColor':'#ff4455',
                            'others':pb.get(bt.name).get('others_count'),'others_backgroundColor':"",'others_percentage':0.0})
                    # To get the village table data
                    partner_beneficiary_village_reach.append({'Total':pb.get(bt.name).get('partner_villages_count'),
                            'Reached':pb.get(bt.name).get('village_count'),'Indicator':bt.name,'Others':pb.get(bt.name).get('others_count')})
                    # To get the village chart data
                    partner_beneficiary_village_reach_chart.append({'total':pb.get(bt.name).get('partner_villages_count'),
                            'actual':pb.get(bt.name).get('village_count'),
                            'percentage':DashBoardSnapShot.percentage_calculator(pb.get(bt.name).get('partner_villages_count'),
                                pb.get(bt.name).get('village_count')),'name':bt.name,
                            'backgroundColor':'#ff4455','others':pb.get(bt.name).get('others_count'),
                            'others_backgroundColor':"",'others_percentage':0.00})
        return (partner_beneficiary_dict,partner_beneficiary_reach,
        partner_beneficiary_reach_chart,partner_beneficiary_village_reach,
        partner_beneficiary_village_reach_chart)

    @staticmethod
    def get_facility_count(user_responses,partner):
        facilities_count = []
        for ft in facility_types:
            district_count,others_count = 0,0
            facility_count = facility_set.filter(facility_type=ft,partner=partner,active=2).count()
            facility_survey = SurveyDataEntryConfig.objects.filter(content_type1__model='facility', object_id1=ft.id).exclude(
                content_type2__gt=0).values_list('survey',flat=True)
            if facility_survey:
                facilities = []
                for i in list(user_responses.filter(survey_id__in=facility_survey).distinct('cluster').values_list('cluster',flat=True)):
                    try:
                        facilities.append(i[0]['facility']['id'])
                    except:
                        pass
                try:
                    locations = [ DashBoardSnapShot.partner_facility_district(i['boundary_id'][0]) for i in facility_set.filter(id__in=set(facilities)).custom_values(['boundary_id'])]
                except:
                    locations = []
                partner_districts = [i['id']for i in eval(get_required_level_info(partner.state.id,3).content).get('locations')]
                district_count,others_count = DashBoardSnapShot.location_counter(locations,partner_districts)
                facilities_count.append({ft.name:{'facilities_count':facility_count,
                    'facilities_reached':len(facilities),
                    'district_count':district_count,'others_count':others_count,
                    'partner_districts_count':len(partner_districts)}})
        return facilities_count

    @staticmethod
    def location_counter(location,parent_location):
        location_count,others_count = 0,0
        for loc in set(location):
            if loc in parent_location:
                location_count = location_count +1
            else:
                others_count = others_count + 1
        return (location_count,others_count,)

    @staticmethod
    def partner_facility_district(location_id):
        bd = boundary_set.get(id=location_id)
        if bd.boundary_level > 3:
            return bd.get_parent_locations([])[-3].get('level3_id')
        elif bd.boundary_level == 3:
            return bd.id
        else:
            try:
                return  eval(get_required_level_info(bd.id,3).content).get('locations')[0]['id']
            except Exception as e:
                return 0

    @staticmethod
    def partner_facility_count(partner_facility):
        partner_facility_dict = []
        partner_facility_reach = []
        partner_facility_reach_chart = []
        partner_facility_district_reach_chart = []
        partner_facility_district_reach = []
        for ft in facility_types:
            facility_survey = SurveyDataEntryConfig.objects.filter(content_type1__model='facility', object_id1=ft.id).exclude(
                content_type2__gt=0).values_list('survey',flat=True)
            if facility_survey:
                for pf in partner_facility:
                    if ft.name in pf.keys():
                        # To get the partner facility count
                        partner_facility_dict.append({'name':ft.name,
                        'value':pf.get(ft.name).get('facilities_count')})
                        # To get the facility tabel data
                        partner_facility_reach.append({'Indicator':ft.name,
                            'Reached':pf.get(ft.name).get('facilities_reached'),
                            'Total':pf.get(ft.name).get('facilities_count'),'Others':pf.get(ft.name).get('others_count')})
                        # To get the facility chart data
                        partner_facility_reach_chart.append({'total':pf.get(ft.name).get('facilities_count'),
                                'actual':pf.get(ft.name).get('facilities_reached'),
                                'percentage':DashBoardSnapShot.percentage_calculator(pf.get(ft.name).get('facilities_count'),
                                pf.get(ft.name).get('facilities_reached')),'name':ft.name,'backgroundColor':'#ffdd55',
                                'others':pf.get(ft.name).get('others_count'),'others_percentage':0.0,'others_backgroundColor':0.0})
                        # To get the facility district table
                        partner_facility_district_reach.append({'Total':pf.get(ft.name).get('partner_districts_count'),
                                'Reached':pf.get(ft.name).get('district_count'),'Indicator':ft.name,
                                'Others':pf.get(ft.name).get('others_count')})
                        # To get the facility district chart data
                        partner_facility_district_reach_chart.append({'total':pf.get(ft.name).get('partner_districts_count'),
                                'actual':pf.get(ft.name).get('district_count'),
                                'percentage':DashBoardSnapShot.percentage_calculator(pf.get(ft.name).get('partner_districts_count'),
                                    pf.get(ft.name).get('district_count')),'name':ft.name,
                                'backgroundColor':'#ffdd55','others':pf.get(ft.name).get('others_count'),
                                'others_backgroundColor':"",'others_percentage':0.00})
        return (partner_facility_dict,partner_facility_reach,partner_facility_reach_chart,
                partner_facility_district_reach,partner_facility_district_reach_chart)

    @staticmethod
    def percentage_calculator(base_arg,actual_arg):
        try:
            return int(actual_arg)*100/int(base_arg)
        except:
            return 0.00
