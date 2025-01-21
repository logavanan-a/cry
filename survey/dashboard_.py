"""Dashboard Cron."""
from __future__ import division
from ast import literal_eval
import datetime
from collections import (namedtuple,)
from copy import deepcopy
import re
from django.contrib.auth.models import User
from beneficiary.models import (Beneficiary, BeneficiaryType)
from facilities.models import (Facility,)
from masterdata.models import (Boundary, MasterLookUp)
from partner.models import (Partner,)
from userroles.models import (UserRoles, RoleTypes, EmploymentDetail)
from .models import (JsonAnswer, Frequence, DashBoardResponse, ColorCode)

Q1, Q2 = [1, 2, 3], [4, 5, 6]
Q3, Q4 = [7, 8, 9], [10, 11, 12]


class DurationFrequency(object):

    def __init__(self):
        self.today = datetime.datetime.now().date()
        self.year = self.today.year

    def get_current_week_dates(self):
        today = self.today
        dates = [today + datetime.timedelta(days=i)
                 for i in range(0 - today.weekday(), 7 - today.weekday())]
        return dates, self.year, 1

    def get_current_month(self):
        return self.today.month, self.year, 2

    def get_current_quarter(self):
        month = self.today.month
        get_quar = [x for x in [Q1, Q2, Q3, Q4] if month in x][0]
        return get_quar, self.year, 3

    def get_current_half_quarter(self):
        month = self.today.month
        first_half = Q1 + Q2
        second_half = Q3 + Q4
        get_half_quar = [x for x in [
            first_half, second_half] if month in x][0]
        return get_half_quar, self.year, 4

    def get_financial_year(self):
        date = self.today
        # initialize the current year
        year_of_date = date.year
        # initialize the current financial year start date
        financial_year_start_date = datetime.datetime.strptime(
            str(year_of_date) + "-04-01", "%Y-%m-%d").date()
        if date < financial_year_start_date:
            return datetime.date(financial_year_start_date.year - 1, 4, 1), datetime.date(financial_year_start_date.year, 3, 31), 6
        else:
            return datetime.date(financial_year_start_date.year, 4, 1), datetime.date(financial_year_start_date.year + 1, 3, 31), 6

    def get_current_year(self):
        curr_year = self.year
        convert_date = datetime.date
        first_day = convert_date(curr_year, 1, 1)
        last_day = convert_date(curr_year, 12, 31)
        return first_day, last_day, 5


def get_levels_down_data(parent_id, next_level):
    wanted_level = next_level
    all_location = Boundary.objects.filter(active=2)
    all_levels = {}
    get_parent = Boundary.objects.get(id=parent_id)
    par_level = get_parent.boundary_level
    level = par_level + 1
    list_parent = [parent_id]
    if par_level == level:
        get_location = all_location.filter(
            parent__id__in=list_parent, boundary_level=level).values_list('id', flat=True)
        all_levels[par_level] = get_location
    else:
        all_levels[par_level] = list_parent
        while par_level < wanted_level:
            loc = all_levels.get(par_level)
            get_location = all_location.filter(
                parent__id__in=loc, boundary_level=level).values_list('id', flat=True)
            par_level += 1
            all_levels[par_level] = get_location
            level += 1
    return all_levels.get(wanted_level)


def get_levels_upper_data(child_id, upper_level):
    wanted_level = upper_level
    all_location = Boundary.objects.filter(active=2)
    all_levels = {}
    par_level, get_parent = all_location.filter(
        id=child_id).values_list('boundary_level', 'parent_id')[0]
    level = par_level - 1
    list_parent = [get_parent]
    all_levels[level] = list_parent
    while level > wanted_level:
        loc = all_levels.get(level)
        get_location = all_location.filter(
            id__in=loc, boundary_level=level).values_list('parent__id', flat=True)
        level -= 1
        all_levels[level] = get_location
    return all_levels.get(wanted_level)


class DashBoardData(object):

    next_level = 6
    tot_villages = 0
    tot_villages_list = []
    reach_out_header = ['Indicator', 'Total', 'Reached', 'Others']
    beneficiary_header = ['Beneficiary-Type', 'Total', 'Reached', 'Others']
    facility_header = ['Facility-Type', 'Total', 'Reached', 'Others']
    freq = DurationFrequency()

    def get_partner(self, partner_id):
        part = Partner.objects.get_or_none(
            active=2, id=partner_id, state__isnull=False)
        return part, part.region.id

    def get_all_partners_of_user_bound(self):
        users = UserRoles.objects.filter(
            active=2, user_type=2, partner__isnull=False).distinct()
        partners_users = users.values_list('user__id', 'partner__id')
        return partners_users

    def get_all_users_partner_data(self, part):
        headers = ['Username', 'Responses', 'Last-Data-Collected']
        user_data = {'name': 'Users Summary', 'table_data': {'headerlist': headers,
                                                             "display_header": ['Username', 'Responses',
                                                                                'Last-Data-Collected'],
                                                             'bodylist': []}}
        users = UserRoles.objects.filter(
            active=2, user_type=2, partner=part)
        partners_users = users.values_list('user__id', flat=True)
        user_add = user_data.get('table_data').get('bodylist')
        for uid in partners_users:
            users_dict = {}
            cool_json = JsonAnswer.objects.filter(
                active=2, user__id=uid).order_by('-id')
            users_dict['Username'] = User.objects.get(id=uid).username
            users_dict['Responses'] = cool_json.count()
            if cool_json:
                data_ = cool_json[0].created.strftime('%d/%m/%Y  %I:%M %p')
            else:
                data_ = 'N/A'
            users_dict[
                'Last-Data-Collected'] = data_
            user_add.append(users_dict)
        return user_data

    def partner_bound_villages(self, part):
        villages_id = []
        if part is not None:
            villages_id = get_levels_down_data(part.state.id, self.next_level)
        return villages_id

    def retrieve_village_id(self, loc_dict):
        new_dict = literal_eval(re.sub(r'\w+=', '', loc_dict))
        return int(new_dict.values()[0].get('boundary_id', 0) or 0)

    def convert_into_object(self, data_json):
        try:
            data = literal_eval(data_json)
        except:
            data = data_json
        return data

    def get_total_beneficiary_for_partner(self, part):
        if part is not None:
            all_villages = []
            bene = Beneficiary.objects.filter(
                active=2, beneficiary_type__active=2)
            bene_types = bene.values_list(
                'beneficiary_type__id', flat=True).distinct()
            beneficiary = {b: {'boundary_id': [], 'id': [], 'total': 0}
                           for b in bene_types}
            for bt in bene_types:
                bene_tot = bene.filter(
                    beneficiary_type__id=bt, partner=part).distinct()
                boundary_id = []
                for loc in bene_tot:
                    boundary_id.append(self.retrieve_village_id(
                        self.convert_into_object(loc.jsondata)['address'][0]))
                beneficiary[bt] = {'total': bene_tot.count(
                ), 'id': list(bene_tot.values_list('id', flat=True)), 'boundary_id': boundary_id}
                all_villages.extend(boundary_id)
            beneficiary['all_villages'] = all_villages
        return beneficiary

    def facility_village_id(self, loc_dic, key, default=0):
        found = loc_dic.get(key, [''])
        if found[0]:
            found = int(found[0])
        else:
            found = default
        return found

    def get_total_facility_for_partner(self, part):
        if part is not None:
            all_villages = []
            fac = Facility.objects.filter(active=2, facility_type__active=2)
            fac_type = fac.values_list(
                'facility_type__id', flat=True).distinct()
            facility = {b: {'boundary_id': [], 'id': [], 'total': 0}
                        for b in fac_type}
            for ft in fac_type:
                fac_tot = fac.filter(
                    facility_type__id=ft, partner=part).distinct()
                boundary_id = [self.facility_village_id(
                    self.convert_into_object(loc.jsondata), 'boundary_id') for loc in fac_tot]
                facility[ft] = {'total': fac_tot.count(
                ), 'id': list(fac_tot.values_list('id', flat=True)), 'boundary_id': boundary_id}
                all_villages.append(boundary_id)
            facility['all_villages'] = all_villages
        return facility

    def get_percentage_achieved(self, a, b):
        try:
            per = (len(set(a) & set(b)) / float(len(set(a) | set(b)))) * 100
        except ZeroDivisionError as e:
            per = 0
        return per

    def get_others_villages_for_facility_beneficiary(self, bene_hamlets, facility_hamlet, part):
        universal_villages = []
        all_hamlets = []
        bene_hamlets.extend(facility_hamlet)
        for k in bene_hamlets:
            if isinstance(k, int) and k:
                all_hamlets.append(k)
            elif isinstance(k, list) and k:
                for new_list in k:
                    all_hamlets.append(new_list)
        for vill in all_hamlets:
            get_id = get_levels_upper_data(vill, self.next_level)
            if get_id:
                universal_villages.extend(list(get_id))
        return list(set(universal_villages))

    def get_overall_data(self, users, tot_beneficiary, tot_facility, villages_id, region, users_mod, get_ans, frequence):
        partner_level = {'data': deepcopy([])}
        chart_data = {'name': 'Beneficiary / Facility / Villages',
                      'data': deepcopy([]), 'table_data': {
                          'headerlist': self.reach_out_header,
                          "display_header": ['Indicator', 'Total', 'Reached', 'Others'],
                          'bodylist': deepcopy([])}}
        beneficiary_data = {'name': 'Beneficiary against the Villages.', 'data': deepcopy([]),
                            'table_data': {
            'headerlist': self.beneficiary_header,
            "display_header": ['Beneficiary Type', 'Total', 'Reached', 'Others'],
            'bodylist': deepcopy([])}}
        facility_data = {'name': 'Facility against the Villages.', 'data': deepcopy([]),
                         'table_data': {
            'headerlist': self.facility_header,
            "display_header": ['Facility Type', 'Total', 'Reached', 'Others'],
            'bodylist': deepcopy([])}}
        bene = Beneficiary.objects.filter(
            active=2, beneficiary_type__active=2)
        bene_types = bene.values_list(
            'beneficiary_type__id', flat=True).distinct()
        beneficiary = {b: deepcopy({'boundary_id': [], 'id': [], 'total': 0})
                       for b in bene_types}
        fac = Facility.objects.filter(active=2, facility_type__active=2)
        fac_type_ = fac.values_list(
            'facility_type__id', flat=True).distinct()
        facility = {b: deepcopy({'boundary_id': [], 'id': [], 'total': 0})
                    for b in fac_type_}
        master_bene_dict = dict(ColorCode.objects.all(
        ).values_list('beneficiary__name', 'color'))
        master_facili_dict = dict(
            ColorCode.objects.all().values_list('master__name', 'color'))
        bene_fac_hamlets = []
        for ans in get_ans:
            bene_type, bene_id, bene_loc = ans.get_beneficiary()
            fac_type, fac_id, fac_loc = ans.get_facility()
            if bene_type and bene_id:
                b_id = beneficiary.get(bene_type).get('id')
                b_id.append(bene_id)
                b_loc = beneficiary.get(bene_type).get('boundary_id')
                b_loc.append(bene_loc)
                bene_fac_hamlets.append(bene_loc)
            if fac_type and fac_id:
                f_id = facility.get(fac_type).get('id')
                f_id.append(fac_id)
                f_loc = facility.get(fac_type).get('boundary_id')
                f_loc.append(fac_loc)
                bene_fac_hamlets.append(fac_loc)
        # partner level data
        for bene_data in beneficiary.keys():
            new_dict = {}
            get_bene = BeneficiaryType.objects.get(id=bene_data)
            new_dict['name'] = get_bene.name
            new_dict['value'] = len(
                list(set(beneficiary.get(get_bene.id).get('id'))))
            partner_level.get('data').append(new_dict)
        for fac_data in facility.keys():
            new_dict = {}
            get_fac = MasterLookUp.objects.get(id=fac_data)
            new_dict['name'] = get_fac.name
            new_dict['value'] = len(
                list(set(facility.get(get_fac.id).get('id'))))
            partner_level.get('data').append(new_dict)
        # end of partner level data
        # reach out
        # Villages Details
        parent_villages = []
        for hamlet in bene_fac_hamlets:
            get_vill = get_levels_upper_data(hamlet, 6)
            if get_vill:
                parent_villages.extend(get_vill)
        villages_dict = {}
        villages_table = {}
        villages = villages_id
        villages_set = set(villages)
        tot_assigned_villages = list(villages_set & set(parent_villages))
        reached_village = len(list(set(tot_assigned_villages)))
        tot_villages = len(list(set(villages)))
        color = master_facili_dict.get('Village')
        village_percent = self.get_percentage_achieved(
            villages, list(set(parent_villages)))
        cd = chart_data.get('data')
        villages_dict['name'] = 'Villages'
        villages_dict['backgroundColor'] = color
        villages_dict['actual'] = reached_village
        villages_dict['total'] = tot_villages
        villages_dict['percentage'] = village_percent
        tot_others = list(set(parent_villages) - set(villages_set))
        villages_others = self.get_percentage_achieved(
            villages, tot_others)
        villages_dict['others'] = len(tot_others)
        villages_dict[
            'others_percentage'] = villages_others
        villages_dict['others_backgroundColor'] = '#80f441'
        cd.append(villages_dict)
        body_list_vil = chart_data.get('table_data').get('bodylist')
        villages_table['Indicator'] = 'Villages'
        villages_table['Total'] = tot_villages
        villages_table['Reached'] = reached_village
        villages_table['Others'] = len(tot_others)
        body_list_vil.append(villages_table)
        partner_level.get('data').append(
            {'name': 'Villages', 'value': reached_village})
        # Village Details End
        # Beneficiary Details
        master_beneficiary = tot_beneficiary
        for bene_data in beneficiary.keys():
            get_bene = BeneficiaryType.objects.get(id=bene_data)
            name = get_bene.name
            master_dict = {}
            table_dict = {}
            bene_mast_loc = {}
            bene_mast_table = {}
            mas = master_beneficiary.get(bene_data).get('id')
            loc = beneficiary.get(bene_data).get('id')
            tot_assigned_beneficiary = list(set(mas) & set(loc))
            reached_beneficiary = len(list(set(tot_assigned_beneficiary)))
            tot_beneficiary_ = len(list(set(mas)))
            color = 'blue'
            beneficiary_percentage = self.get_percentage_achieved(mas, loc)
            master_dict['name'] = name
            master_dict['backgroundColor'] = master_bene_dict.get(name)
            master_dict['actual'] = reached_beneficiary
            master_dict['total'] = tot_beneficiary_
            master_dict['percentage'] = beneficiary_percentage
            master_dict['others'] = 0
            master_dict[
                'others_percentage'] = 0.0
            master_dict['others_backgroundColor'] = ''
            cd = chart_data.get('data')
            cd.append(master_dict)
            # Table View
            body_list = chart_data.get('table_data').get('bodylist')
            table_dict['Indicator'] = name
            table_dict['Total'] = tot_beneficiary_
            table_dict['Reached'] = reached_beneficiary
            table_dict['Others'] = 0
            body_list.append(table_dict)
            bm = beneficiary_data.get('data')
            loc_bm = list(set(beneficiary.get(bene_data).get('boundary_id')))
            parent_villages = []
            for hamlet in loc_bm:
                get_vill = get_levels_upper_data(hamlet, 6)
                if get_vill:
                    parent_villages.extend(get_vill)
            tot_assigned_beneficiary_bm = list(
                villages_set & set(parent_villages))
            reached_beneficiary_bm = len(
                list(set(tot_assigned_beneficiary_bm)))
            tot_beneficiary_bm = len(list(villages_set))
            beneficiary_percentage_bm = self.get_percentage_achieved(
                villages, parent_villages)
            bene_mast_loc['name'] = name
            bene_mast_loc['backgroundColor'] = master_bene_dict.get(name)
            bene_mast_loc['actual'] = reached_beneficiary_bm
            bene_mast_loc['total'] = tot_beneficiary_bm
            bene_mast_loc['percentage'] = beneficiary_percentage_bm
            bene_mast_loc['others'] = 0
            bene_mast_loc[
                'others_percentage'] = 0.0
            bene_mast_loc['others_backgroundColor'] = ''
            tot_others = list(set(parent_villages) - set(villages_set))
            beneficiary_percentage_bm_others = self.get_percentage_achieved(
                villages, tot_others)
            bene_mast_loc['others'] = len(tot_others)
            bene_mast_loc[
                'others_percentage'] = beneficiary_percentage_bm_others
            bene_mast_loc[
                'others_backgroundColor'] = '#7142f4'
            bm.append(bene_mast_loc)
            body_list_bm = beneficiary_data.get('table_data').get('bodylist')
            bene_mast_table['Beneficiary-Type'] = name
            bene_mast_table['Total'] = tot_beneficiary_bm
            bene_mast_table['Reached'] = reached_beneficiary_bm
            bene_mast_table['Others'] = len(tot_others)
            body_list_bm.append(bene_mast_table)
        # End Beneficiary Details
        master_facility = tot_facility
        for bene_data in facility.keys():
            get_bene = MasterLookUp.objects.get(id=bene_data)
            name = get_bene.name
            master_dict = {}
            table_dict = {}
            bene_mast_loc = {}
            bene_mast_table = {}
            mas = master_facility.get(bene_data).get('id')
            loc = facility.get(bene_data).get('id')
            tot_assigned_beneficiary = list(set(mas) & set(loc))
            reached_beneficiary = len(list(set(tot_assigned_beneficiary)))
            tot_beneficiary_ = len(list(set(mas)))
            color = 'blue'
            beneficiary_percentage = self.get_percentage_achieved(mas, loc)
            master_dict['name'] = name
            master_dict['backgroundColor'] = master_facili_dict.get(name)
            master_dict['actual'] = reached_beneficiary
            master_dict['total'] = tot_beneficiary_
            master_dict['percentage'] = beneficiary_percentage
            master_dict['others'] = 0
            master_dict[
                'others_percentage'] = 0.0
            master_dict['others_backgroundColor'] = ''
            cd = chart_data.get('data')
            cd.append(master_dict)
            # Table View
            body_list = chart_data.get('table_data').get('bodylist')
            table_dict['Indicator'] = name
            table_dict['Total'] = tot_beneficiary_
            table_dict['Reached'] = reached_beneficiary
            table_dict['Others'] = 0
            body_list.append(table_dict)
            bm = facility_data.get('data')
            loc_bm = list(set(facility.get(bene_data).get('boundary_id')))
            parent_villages = []
            for hamlet in loc_bm:
                get_vill = get_levels_upper_data(hamlet, 6)
                if get_vill:
                    parent_villages.extend(get_vill)
            tot_assigned_beneficiary_bm = list(
                villages_set & set(parent_villages))
            reached_beneficiary_bm = len(
                list(set(tot_assigned_beneficiary_bm)))
            tot_beneficiary_bm = len(list(villages_set))
            beneficiary_percentage_bm = self.get_percentage_achieved(
                villages, parent_villages)
            bene_mast_loc['name'] = name
            bene_mast_loc['backgroundColor'] = master_facili_dict.get(name)
            bene_mast_loc['actual'] = reached_beneficiary_bm
            bene_mast_loc['total'] = tot_beneficiary_bm
            bene_mast_loc['percentage'] = beneficiary_percentage_bm
            tot_others = list(set(parent_villages) - set(villages_set))
            beneficiary_percentage_bm_others = self.get_percentage_achieved(
                villages, tot_others)
            bene_mast_loc['others'] = len(tot_others)
            bene_mast_loc[
                'others_percentage'] = beneficiary_percentage_bm_others
            bene_mast_loc[
                'others_backgroundColor'] = '#f442d4'
            bm.append(bene_mast_loc)
            body_list_bm = facility_data.get('table_data').get('bodylist')
            bene_mast_table['Facility-Type'] = name
            bene_mast_table['Total'] = tot_beneficiary_bm
            bene_mast_table['Reached'] = reached_beneficiary_bm
            bene_mast_table['Others'] = len(tot_others)
            body_list_bm.append(bene_mast_table)
        # end of reach out
        feq = Frequence.objects.get(active=2, duration=frequence)
        dash_overall, created = DashBoardResponse.objects.get_or_create(
            schedule=feq, user_id=users, user_type=3)
        dash_overall.region_id = region
        dash_overall.partner_level = partner_level
        dash_overall.chartdata = chart_data
        dash_overall.facility = facility_data
        dash_overall.beneficiary = beneficiary_data
        dash_overall.user_summary = users_mod
        dash_overall.save()
        return dash_overall

    def get_current_week_data(self, orders, user_id, beneficiary, facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 1
        curr_week, year, order_ = self.freq.get_current_week_dates()
        gets_ans_new = []
        for w in curr_week:
            data = all_ans.filter(user__id=user_id, created__date=w)
            gets_ans_new.extend(list(data))
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, gets_ans_new,
                                     frequence)

    def get_current_month_data(self, orders, user_id, beneficiary, facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 2
        curr_month, year, order_ = self.freq.get_current_month()
        get_ans_new = all_ans.filter(user__id=user_id,
                                     created__month=curr_month,
                                     created__year=year)
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, get_ans_new,
                                     frequence)

    def get_quarter_data(self, orders, user_id, beneficiary, facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 3
        curr_quarter, year, order_ = self.freq.get_current_quarter()
        get_ans_new = all_ans.filter(user__id=user_id,
                                     created__month__in=curr_quarter,
                                     created__year=year)
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, get_ans_new,
                                     frequence)

    def get_half_year_data(self, orders, user_id, beneficiary, facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 4
        curr_half_year, year, order_ = self.freq.get_current_half_quarter()
        get_ans_new = all_ans.filter(user__id=user_id,
                                     created__month__in=curr_half_year,
                                     created__year=year)
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, get_ans_new,
                                     frequence)

    def get_yearly_data(self, orders, user_id, beneficiary, facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 5
        start_date, last_date, order_ = self.freq.get_current_year()
        get_ans_new = all_ans.filter(user__id=user_id,
                                     created__gte=start_date,
                                     created__lte=last_date)
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, get_ans_new,
                                     frequence)

    def get_fiscal_data(self, orders, user_id, beneficiary,
                        facility, villages_id, region, users, get_ans, frequence):
        all_ans = get_ans
        frequence = 6
        start_date_fiscal, end_date_fiscal, order_ = self.freq.get_financial_year()
        get_ans_new = all_ans.filter(user__id=user_id,
                                     created__gte=start_date_fiscal,
                                     created__lte=end_date_fiscal)
        data = self.get_overall_data(user_id, beneficiary, facility,
                                     villages_id, region, users, get_ans_new,
                                     frequence)

    def data_dump(self):
        users_partners = self.get_all_partners_of_user_bound()
        for user_id, partner_id in users_partners:
            get_ans = JsonAnswer.objects.filter(active=2)
            part, region = self.get_partner(partner_id)
            beneficiary = self.get_total_beneficiary_for_partner(part)
            facility = self.get_total_facility_for_partner(part)
            villages = list(self.partner_bound_villages(part))
            villages_id = self.get_others_villages_for_facility_beneficiary(
                beneficiary.get('all_villages', []), facility.get('all_villages', []), part)
            villages_id.extend(villages)
            users = self.get_all_users_partner_data(part)
            dash_overall = self.get_overall_data(
                user_id, beneficiary, facility, villages_id, region, users,
                get_ans.filter(user__id=user_id), 0)
            curr_week = self.get_current_week_data(
                1, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)
            curr_month = self.get_current_month_data(
                2, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)
            curr_quarter = self.get_quarter_data(
                3, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)
            curr_half_quater = self.get_half_year_data(
                4, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)
            curr_yearly = self.get_yearly_data(
                5, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)
            curr_fiscal = self.get_fiscal_data(
                6, user_id, beneficiary, facility, villages_id, region, users,
                get_ans, 0)


class RegionalHead(object):

    def __init__(self):
        self.headers = ['Username', 'Responses', 'Last-Data-Collected']
        self.reach_out_header = ['Indicator', 'Total', 'Reached', 'Others']
        self.beneficiary_header = [
            'Beneficiary-Type', 'Total', 'Reached', 'Others']
        self.facility_header = ['Facility-Type', 'Total', 'Reached', 'Others']
        self.freq = DurationFrequency()

    def get_region_user_id(self):
        roles = RoleTypes.objects.filter(
            slug__iexact='regional-coordinator').values_list('id', flat=True)
        users = UserRoles.objects.filter(
            active=2, user_type=1, role_type__id__in=roles,
            partner__isnull=True).values_list('user__id', flat=True)
        return users

    def get_percentage_achieved(self, a, b):
        try:
            per = (b / a) * 100
        except ZeroDivisionError as e:
            per = 0
        return per

    def date_comp(self, old_date, new_date):
        try:
            new_old = datetime.datetime.strptime(
                '%d/%m/%Y  %I:%M %p', old_date)
            new_ = datetime.datetime.strptime('%d/%m/%Y  %I:%M %p', new_date)
            if new_ > new_old:
                dates_ = new_date
            else:
                dates_ = old_date
        except:
            dates_ = 'N/A'
        return dates_

    def get_total_beneficiary_facility(self, queryset):
        total_data = {}
        for dash in queryset:
            chart_d = dash.chartdata.get('data')
            for mp_ in chart_d:
                if mp_.get('name') in total_data:
                    total_data[mp_.get('name')] += mp_.get('total', 0)
                else:
                    total_data[mp_.get('name')] = mp_.get('total', 0)
        return total_data

    def partners_data(self, region, frequence):
        master_region = MasterLookUp.objects.filter(
            active=2, parent__slug__iexact='region').values_list('id', flat=True)
        users_mod = {'name': 'User Summary', 'table_data': {
            "display_header": ['Username', 'Responses',
                               'Last-Data-Collected'],
            'headerlist': self.headers, 'bodylist': []}}
        partner_level = {'data': []}
        chart_data = {'name': 'Beneficiary / Facility / Villages', 'data': [],
                      'table_data': {
            "display_header":
            ['Indicator', 'Total', 'Reached', 'Others'],
            'headerlist': self.reach_out_header, 'bodylist': []}}
        beneficiary_data = {'name': 'Beneficiary against the Villages.', 'data': [], 'table_data': {
            "display_header": ['Indicator', 'Total', 'Reached', 'Others'],
            'headerlist': self.beneficiary_header,
            'bodylist': []}}
        facility_data = {'name': 'Facility against the Villages.', 'data': [], 'table_data': {
            "display_header": ['Indicator', 'Total', 'Reached', 'Others'],
            'headerlist':
            self.facility_header,
            'bodylist': []}}
        if region == 0:
            region = master_region
            get_dash_response = DashBoardResponse.objects.filter(
                active=2, schedule__duration=frequence, region_id__in=region, user_type=2)
        else:
            get_dash_response = DashBoardResponse.objects.filter(
                active=2, schedule__duration=frequence, region_id=region, user_type=3)
        total_data = self.get_total_beneficiary_facility(get_dash_response)
        final_list = partner_level.get('data')
        master_partner = {}
        master_data_chart = {}
        master_bodylist_table = {}
        master_beneficiary_data = {}
        master_beneficiary_bodylist_table = {}
        master_facility_data = {}
        master_facility_bodylist_table = {}
        master_user_bodylist_table = {}
        for dash in get_dash_response:
            k = dash.partner_level.get('data')
            for mp in k:
                if mp.get('name') in master_partner:
                    master_partner[mp.get('name')] += mp.get('value')
                else:
                    master_partner[mp.get('name')] = mp.get('value')
            chart_d = dash.chartdata.get('data')
            chart_tab = dash.chartdata.get('table_data').get('bodylist')
            for mp in chart_d:
                if mp.get('name') in master_data_chart:
                    loc_dict = master_data_chart[mp.get('name')]
                    loc_dict['actual'] += mp.get('actual', 0) or 0
                    loc_dict['others'] += mp.get('others', 0) or 0
                else:
                    master_data_chart[mp.get('name')] = {'actual': mp.get('actual'),
                                                         'backgroundColor': mp.get('backgroundColor'),
                                                         'name': mp.get('name'),
                                                         'percentage': mp.get('percentage'),
                                                         'others': mp.get('others', 0),
                                                         'others_percentage': mp.get('others_percentage', 0),
                                                         'others_backgroundColor': mp.get('others_backgroundColor'),
                                                         'total': total_data.get(mp.get('name'))}
            for tmp in chart_tab:
                if tmp.get('Indicator') in master_bodylist_table:
                    loc_dict = master_bodylist_table[tmp.get('Indicator')]
                    loc_dict['Reached'] += tmp.get('Reached', 0) or 0
                    loc_dict['Others'] += tmp.get('Others', 0)
                else:
                    master_bodylist_table[tmp.get('Indicator')] = {
                        'Indicator': tmp.get('Indicator'),
                        'Reached': tmp.get('Reached'),
                        'Others': tmp.get('Others', 0),
                        'Total': total_data.get(tmp.get('Indicator'))}
            chart_beneficiary = dash.beneficiary.get('data')
            chart_beneficiary_tab = dash.beneficiary.get(
                'table_data').get('bodylist')
            for bmp in chart_beneficiary:
                if bmp.get('name') in master_beneficiary_data:
                    loc_dict = master_beneficiary_data[bmp.get('name')]
                    loc_dict['actual'] += bmp.get('actual', 0) or 0
                    loc_dict['total'] += bmp.get('total', 0) or 0
                    loc_dict['others'] += mp.get('others', 0) or 0
                else:
                    master_beneficiary_data[bmp.get('name')] = {
                        'actual': bmp.get('actual'),
                        'backgroundColor': bmp.get('backgroundColor'),
                        'name': bmp.get('name'),
                        'percentage': bmp.get('percentage'),
                        'total': bmp.get('total'),
                        'others': bmp.get('others', 0),
                        'others_percentage': bmp.get('others_percentage', 0),
                        'others_backgroundColor': bmp.get('others_backgroundColor')}
            for btmp in chart_beneficiary_tab:
                if btmp.get('Beneficiary-Type') in master_beneficiary_bodylist_table:
                    loc_dict = master_beneficiary_bodylist_table[
                        btmp.get('Beneficiary-Type')]
                    loc_dict['Reached'] += btmp.get('Reached', 0) or 0
                    loc_dict['Total'] += btmp.get('Total', 0) or 0
                    loc_dict['Others'] += btmp.get('Others', 0)
                else:
                    master_beneficiary_bodylist_table[btmp.get('Beneficiary-Type')] = {
                        'Beneficiary-Type': btmp.get('Beneficiary-Type'),
                        'Reached': btmp.get('Reached'),
                        'Total': btmp.get('Total'), 'Others': btmp.get('Others', 0)}
            chart_facility = dash.facility.get('data')
            chart_facility_tab = dash.facility.get(
                'table_data').get('bodylist')
            for bmp in chart_facility:
                if bmp.get('name') in master_facility_data:
                    loc_dict = master_facility_data[bmp.get('name')]
                    loc_dict['actual'] += bmp.get('actual', 0) or 0
                    loc_dict['total'] += bmp.get('total', 0) or 0
                    loc_dict['others'] += bmp.get('others', 0) or 0
                else:
                    master_facility_data[bmp.get('name')] = {
                        'actual': bmp.get('actual'),
                        'backgroundColor': bmp.get('backgroundColor'),
                        'name': bmp.get('name'),
                        'percentage': bmp.get('percentage'),
                        'total': bmp.get('total'),
                        'others': bmp.get('others', 0),
                        'others_percentage': bmp.get('others_percentage', 0),
                        'others_backgroundColor': bmp.get('others_backgroundColor')}
            for btmp in chart_facility_tab:
                if btmp.get('Facility-Type') in master_facility_bodylist_table:
                    loc_dict = master_facility_bodylist_table[
                        btmp.get('Facility-Type')]
                    loc_dict['Reached'] += btmp.get('Reached', 0) or 0
                    loc_dict['Total'] += btmp.get('Total', 0) or 0
                    loc_dict['Others'] += btmp.get('Others', 0)
                else:
                    master_facility_bodylist_table[btmp.get('Facility-Type')] = {
                        'Facility-Type': btmp.get('Facility-Type'),
                        'Reached': btmp.get('Reached'),
                        'Total': btmp.get('Total'), 'Others': btmp.get('Others', 0)}
            chart_users_tab = dash.user_summary.get(
                'table_data').get('bodylist')
            for usrs in chart_users_tab:
                if usrs.get('Username') in master_user_bodylist_table:
                    loc_dict = master_user_bodylist_table[usrs.get('Username')]
                    loc_dict['Responses'] += usrs.get('Responses', 0) or 0
                    loc_dict['Last-Data-Collected'] = self.date_comp(
                        loc_dict['Last-Data-Collected'], usrs.get('Last-Data-Collected'))
                else:
                    master_user_bodylist_table[usrs.get('Username')] = {
                        'Username': usrs.get('Username'),
                        'Responses': usrs.get('Responses'),
                        'Last-Data-Collected': 'N/A' if usrs.get('Last-Data-Collected') == 'N/A' else usrs.get('Last-Data-Collected')}
        partner = namedtuple('partner', ['name', 'value'])
        for pa in master_partner.items():
            ptr = partner(*pa)
            final_list.append({'name': ptr.name, 'value': ptr.value})
        chartdata = chart_data.get('data')
        chart_table = chart_data.get('table_data').get('bodylist')
        for mdc in master_data_chart.keys():
            get_dict = master_data_chart[mdc]
            get_dict['percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['actual'])
            get_dict['others_percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['others'])
            chartdata.append(get_dict)
        for mbt in master_bodylist_table.keys():
            get_dict = master_bodylist_table[mbt]
            chart_table.append(get_dict)
        chart_beneficiary_data = beneficiary_data.get('data')
        chart_beneficiary_table = beneficiary_data.get(
            'table_data').get('bodylist')
        for bmdc in master_beneficiary_data.keys():
            get_dict = master_beneficiary_data[bmdc]
            get_dict['percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['actual'])
            get_dict['others_percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['others'])
            chart_beneficiary_data.append(get_dict)
        for bmbt in master_beneficiary_bodylist_table.keys():
            get_dict = master_beneficiary_bodylist_table[bmbt]
            chart_beneficiary_table.append(get_dict)
        chart_facility_data = facility_data.get('data')
        chart_facility_table = facility_data.get(
            'table_data').get('bodylist')
        for bmdc in master_facility_data.keys():
            get_dict = master_facility_data[bmdc]
            get_dict['percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['actual'])
            get_dict['others_percentage'] = self.get_percentage_achieved(
                get_dict['total'], get_dict['others'])
            chart_facility_data.append(get_dict)
        for bmbt in master_facility_bodylist_table.keys():
            get_dict = master_facility_bodylist_table[bmbt]
            chart_facility_table.append(get_dict)
        chart_user_table = users_mod.get(
            'table_data').get('bodylist')
        for usrt in master_user_bodylist_table:
            get_dict = master_user_bodylist_table[usrt]
            chart_user_table.append(get_dict)
        return partner_level, chart_data, facility_data, beneficiary_data, users_mod

    def get_dump_data(self):
        get_all_frequences = Frequence.objects.all().values_list('duration', flat=True)
        get_users = self.get_region_user_id()
        for user_id in get_users:
            get_region = EmploymentDetail.objects.filter(user__id=user_id)
            if get_region:
                actual_region = get_region[0].region.id
                for fq in get_all_frequences:
                    partner_level, chart_data, facility_data, beneficiary_data, users_mod = self.partners_data(
                        actual_region, fq)
                    feq = Frequence.objects.get(active=2, duration=fq)
                    dash_overall, created = DashBoardResponse.objects.get_or_create(
                        schedule=feq, user_id=user_id, user_type=2)
                    dash_overall.region_id = actual_region
                    dash_overall.partner_level = partner_level
                    dash_overall.chartdata = chart_data
                    dash_overall.facility = facility_data
                    dash_overall.beneficiary = beneficiary_data
                    dash_overall.user_summary = users_mod
                    dash_overall.save()


class NationalHead(object):

    def get_national_user_id(self):
        roles = RoleTypes.objects.filter(
            slug__iexact='ceo').values_list('id', flat=True)
        users = UserRoles.objects.filter(
            active=2, user_type=1, role_type__id__in=roles,
            partner__isnull=True).values_list('user__id', flat=True)
        return users

    def get_dump_data(self):
        rh = RegionalHead()
        get_all_frequences = Frequence.objects.all().values_list('duration', flat=True)
        get_users = self.get_national_user_id()
        get_national = MasterLookUp.objects.get(slug__iexact='national-ho')
        for user_id in get_users:
            for fq in get_all_frequences:
                partner_level, chart_data, facility_data, beneficiary_data, users_mod = rh.partners_data(
                    0, fq)
                feq = Frequence.objects.get(active=2, duration=fq)
                dash_overall, created = DashBoardResponse.objects.get_or_create(
                    schedule=feq, user_id=user_id, region_id=get_national.id, user_type=1)
                dash_overall.partner_level = partner_level
                dash_overall.chartdata = chart_data
                dash_overall.facility = facility_data
                dash_overall.beneficiary = beneficiary_data
                dash_overall.user_summary = users_mod
                dash_overall.save()
