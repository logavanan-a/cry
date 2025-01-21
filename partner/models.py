from __future__ import unicode_literals
from collections import namedtuple
import decimal
import re
from django.db import models
from django.contrib.auth.admin import User
from django.db.models import (Sum,)
from userroles.models import UserRoles
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from masterdata.models import (BaseContent, MasterLookUp)
from constants import OPTIONAL
import datetime
# Create your models here.


def currency_in_indian_format(n):
    """ Convert a number (int / float) into indian formatting style """
    d = decimal.Decimal(str(n))
    if d.as_tuple().exponent < -2:
        s = str(n)
    else:
        s = '{0:.2f}'.format(n)
    l = len(s)
    i = l - 1
    res, flag, k = '', 0, 0
    while i >= 0:
        if flag == 0:
            res += s[i]
            if s[i] == '.':
                flag = 1
        elif flag == 1:
            k += 1
            res += s[i]
            if k == 3 and i - 1 >= 0:
                res += ','
                flag = 2
                k = 0
        else:
            k += 1
            res += s[i]
            if k == 2 and i - 1 >= 0:
                res += ','
                flag = 2
                k = 0
        i -= 1
    return res[::-1]


class Partner(BaseContent):
    name = models.CharField(max_length=1000, unique=True)
    partner_id = models.CharField(max_length=100, **OPTIONAL)
    region = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_region', **OPTIONAL)
    state = models.ForeignKey('masterdata.Boundary', **OPTIONAL)
    nature_of_partner = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_nature', **OPTIONAL)
    status = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_status', **OPTIONAL)
    support_from = models.DateField(**OPTIONAL)
    support_to = models.DateField(**OPTIONAL)
    cry_admin_id = models.CharField(max_length=15,blank=True,null=True)

    def __self__(self):
        return self.name or ''

    def get_project_name(self):
        prog = Project.objects.filter(program__partner=self).order_by('-id')
        if prog:
            project_ = prog[0].name
            if not project_:
                project_name = 'N/A' + '-' + self.name
            else:
                project_name = project_ + '-' + self.name
        else:
            project_name = 'N/A'
        return project_name

    def get_project_partner_id(self):
        actual_object = project_ = 0
        prog = Project.objects.filter(program__partner=self).order_by('-id')
        if prog:
            actual_object = prog[0]
            project_ = prog[0].id
        return project_, actual_object

    def deactivate_project_program(self):
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            response = {'status': 2, 'message': 'switched the objects.'}
            pro = Program.objects.filter(partner=self).order_by('-id')
            proj = Project.objects.filter(program=pro).order_by('-id')
            if pro and proj:
                pro[0].switch()
                proj[0].switch()
        except:
            pass
        return response

    def get_project_id(self):
        project = 0
        proj = ProjectLocation.objects.filter(
            active=2, project__program__partner=self).order_by('-id')
        if proj:
            project = proj[0]
        return project

    def get_support_date(self):
        from_ = self.support_from.strftime(
            '%b-%y') if self.support_from else 'N/A'
        to_ = 'N/A'
        if self.support_from:
            if self.support_to:
                to_ = self.support_to.strftime('%b-%y')
            else:
                to_ = datetime.datetime.now().strftime('%b-%y')
        else:
            to_ = 'N/A'
        return from_ + ' - ' + to_

    def get_project_information(self):
        mist_ = MasterLookUp.objects.filter(active=2,
                                            parent__slug__iexact='theme').order_by('id')
        mast = mist_.values_list('name', flat=True)
        reg_stat = cry_location = ds_remarks = 'N/A'
        project = self.get_project_id()
        theme_tuple = namedtuple('theme_tuple', mast)
        theme_tuple.__new__.__defaults__ = (
            'N',) * len(theme_tuple._fields)
        data = theme_tuple()
        d_dict = data._asdict()
        if project:
            pmast = project.theme.filter(
                active=2).values_list('name', flat=True)
            reg_stat = project.fla_grm_team.name if project.fla_grm_team else 'N/A'
            cry_location = ','.join(project.boundary.all().values_list(
                'name', flat=True)) if project.boundary.all() else 'N/A'
            ds_remarks = project.remarks or 'N/A'
            theme = {no: 'N' for no in set(pmast) ^ set(mast)}
            theme.update(
                {yes: 'Y' for yes in set(pmast) & set(mast)})
            for tpl in theme_tuple._fields:
                d_dict[tpl] = theme.get(tpl)
        return reg_stat, cry_location, ds_remarks, d_dict

    def get_dpf_data(self):
        final_theme = 'Not-Available'
        actual_data = 0
        project, actual_object = self.get_project_partner_id()
        if project:
            main_line_item = BudgetConfig.objects.filter(
                active=2, object_id=project).values_list('id', flat=True)
            theme = ConfigureThematic.objects.filter(
                active=2, funding__object_id=project)
            assigned_theme = list(set([
                sth for th in theme for sth in th.thematic.all().values_list('id', flat=True)]))
            final_theme = 'Available' if set(main_line_item) - \
                set(assigned_theme) else 'Not-Available'
            actual_data = actual_object.program.partner.id if actual_object else 0
        return final_theme, actual_data

    def get_partner_master_data(self):
        budget = 'No Grant'
        project, actual_object = self.get_project_partner_id()
        update = self.modified.strftime('%b-%y')
        region = self.region.name if self.region else 'N/A'
        state = self.state.name if self.state else 'N/A'
        name = self.name or 'N/A'

        nature = self.nature_of_partner.name if self.nature_of_partner else 'N/A'
        ongoing_cycle = self.get_support_date()
        bud_amt = BudgetConfig.objects.filter(
            active=2, object_id=project).aggregate(Sum('amount')).get('amount__sum', 0)
        if bud_amt:
            budget = currency_in_indian_format(
                bud_amt) if project else 'No Grant'
        support = self.get_support_date()
        booking, project_id = self.get_dpf_data()
        reg_stat, cry_location, ds_remarks, d_dict = self.get_project_information()
        id_ = project
        master_list = [
            id_,
            update,
            region,
            state,
            name,
            nature,
            ongoing_cycle,
            budget,
            reg_stat,
            cry_location,
            support,
            booking]
        master_list.extend([d_dict[x] for x in d_dict.keys()])
        master_list.append(ds_remarks)
        return master_list

    def get_partner_deo(self):
        return UserRoles.objects.filter(active=2,partner_id=self.id).values_list('user',flat=True)

    def get_deo(self):
        return UserRoles.objects.filter(active=2,partner_id=self.id,role_type__id=1).values_list('id',flat=True)

class Program(BaseContent):
    partner = models.ForeignKey(Partner, **OPTIONAL)
    name = models.CharField(max_length=300, **OPTIONAL)
    start_date = models.DateField(**OPTIONAL)
    end_date = models.DateField(**OPTIONAL)

    def __unicode__(self):
        return self.name or ''


class Project(BaseContent):
    program = models.ForeignKey(Program, **OPTIONAL)
    name = models.CharField(max_length=300, **OPTIONAL)
    start_date = models.DateField(**OPTIONAL)
    end_date = models.DateField(**OPTIONAL)

    def __unicode__(self):
        return self.program.partner.name or ''

    def get_partner_name(self):
        prog = self.program
        partner_name = 'N/A'
        if prog:
            prog_part = prog.partner
            if prog_part:
                if not self.name:
                    partner_name = prog.partner.name
                else:
                    partner_name = self.name
        return partner_name


class ProjectLocation(BaseContent):
    project = models.ForeignKey(Project, **OPTIONAL)
    other_legal_registration = models.BooleanField(default=False)
    legal_name = models.CharField(max_length=200, **OPTIONAL)
    legal_number = models.CharField(max_length=200, **OPTIONAL)
    disbursal = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_disbursal', **OPTIONAL)
    pre_funding = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_funding', **OPTIONAL)
    fla_grm_team = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_fla_grm_team', **OPTIONAL)
    boundary = models.ManyToManyField(
        'masterdata.Boundary', blank=True)
    community = models.ManyToManyField(
        'masterdata.MasterLookup', related_name='masterlookup_community', **OPTIONAL)
    theme = models.ManyToManyField(
        'masterdata.MasterLookup', related_name='masterlookup_theme', **OPTIONAL)
    prominent_issues = models.ManyToManyField(
        'masterdata.MasterLookup', related_name='masterlookup_issue', **OPTIONAL)
    remarks = models.TextField(**OPTIONAL)

    def __unicode__(self):
        return self.project.program.partner.name or ''


USER_TYPE = ((1, 'CEO/HOLDER'), (2, 'CO-ORDINATOR'))


class ProjectuserDetail(BaseContent):
    user_type = models.IntegerField(choices=USER_TYPE, **OPTIONAL)
    holder_user = models.ForeignKey('auth.User', **OPTIONAL)
    project = models.ForeignKey(Project, **OPTIONAL)
    name = models.CharField(max_length=200, **OPTIONAL)
    contact_address = models.BooleanField(
        'Do the Contact address is same as Project holder/organization chief executive?', default=False)

    def __unicode__(self):
        return self.name or ''


REGISTRATION_STATUS = ((1, 'OPEN'), (2, 'CLOSED'))
PRIORITY = ((1, 'Primary'), (2, 'Secondary'), (3, 'Others'))


class Registration(BaseContent):
    name = models.CharField(max_length=100, **OPTIONAL)
    reg_type = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_reg_type', **OPTIONAL)
    date_of_registered = models.DateField(**OPTIONAL)
    status = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_reg_status', **OPTIONAL)
    priority = models.IntegerField(choices=PRIORITY, **OPTIONAL)
    exp_date = models.DateField(**OPTIONAL)
    attachment = models.FileField(upload_to='static/%Y/%m/%d', **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name or ''


class BankAccount(BaseContent):
    priority = models.IntegerField(choices=PRIORITY, **OPTIONAL)
    account_type = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_account_type', **OPTIONAL)
    fund_type = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_fund_type', **OPTIONAL)
    bank = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_bank', **OPTIONAL)
    bank_name = models.CharField(max_length=100, **OPTIONAL)
    account_number = models.CharField(max_length=100, unique=True, **OPTIONAL)
    branch_name = models.CharField(max_length=100, **OPTIONAL)
    ifsc_code = models.CharField(max_length=15, **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')
    remarks = models.CharField(max_length=200, **OPTIONAL)

    def __unicode__(self):
        return self.bank_name or ''


class Donar(BaseContent):
    user = models.ForeignKey('auth.User', **OPTIONAL)
    name = models.CharField(max_length=100, **OPTIONAL)
    email = models.EmailField(max_length=254, **OPTIONAL)
    location = models.ForeignKey(MasterLookUp, **OPTIONAL)
    mobile_no = models.CharField(max_length=15, **OPTIONAL)
    contact_person = models.CharField(max_length=100, **OPTIONAL)

    def __unicode__(self):
        return self.name


class BudgetYear(BaseContent):
    start_year = models.DateField(**OPTIONAL)
    end_year = models.DateField(**OPTIONAL)

    def __unicode__(self):
        return '{0} to {1}'.format(self.start_year.strftime('%Y-%m-%d'), self.end_year.strftime('%Y-%m-%d'))


class BudgetConfig(BaseContent):
    user = models.ForeignKey('auth.User', **OPTIONAL)
    year = models.ForeignKey(BudgetYear, **OPTIONAL)
    theme_budget = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_budget_theme', **OPTIONAL)
    line_item = models.CharField(max_length=200, **OPTIONAL)
    amount = models.PositiveIntegerField(default=0)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return "{}|{}".format(self.year, self.line_item)

    def get_years(self):
        final_ = []
        if self.year:
            start_ = self.year.start_year.year or ''
            end_ = self.year.end_year.year or ''
            final_ = [start_, end_]
        return final_

    def new_get_years(self):
        final_ = []
        if self.year:
            start_ = self.year.start_year.strftime("%b %Y") or ''
            end_ = self.year.end_year.strftime("%b %Y") or ''
            final_ = [start_, end_]
        return final_

    def get_budget_amount(self):
        sum_theme = '0' + '/-'
        sum_curr = re.search(r'\.\d+', currency_in_indian_format(self.amount))
        if sum_curr and not int(sum_curr.group().replace('.', '')):

            sum_theme = re.sub(
                    r'\.\d+', '', currency_in_indian_format(self.amount)) + '/-'
        return sum_theme


type_funding = ((0, 'Entire Project'), (1, 'Specific Year'),
                (2, 'Specific Custom'))


class Funding(BaseContent):
    user = models.ForeignKey('auth.User', **OPTIONAL)
    types_of_funding = models.IntegerField(choices=type_funding, **OPTIONAL)
    year = models.ForeignKey(BudgetYear, **OPTIONAL)
    donar = models.ForeignKey(Donar, **OPTIONAL)
    status = models.ForeignKey(
        MasterLookUp, related_name='masterlookup_funding_status', **OPTIONAL)
    probability_status = models.ForeignKey(
        MasterLookUp, related_name='masterlookup_probability_status', **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return "{0} | {1}".format(self.donar or '', self.status or '')

    def get_years(self):
        start_, end_ = "", ""
        years = []
        if self.active == 2 and self.year:

            start_ = self.year.start_year.year or ''
            end_ = self.year.end_year.year or ''
            years = [start_, end_]
            years.sort()
        return years

    def get_dates(self):
        start_, end_ = "", ""
        if self.year:
            start_ = self.year.start_year
            end_ = self.year.end_year
        return start_.strftime("%Y-%m") + ',' + end_.strftime("%Y-%m")

    def get_months(self):
        start_, end_ = "", ""
        if self.year:
            start_ = self.year.start_year
            end_ = self.year.end_year
        return start_.strftime('%b %d') + ' - ' + end_.strftime('%b %d')

    def get_remarks(self):
        remarks = []
        if self.active == 2:
            remarks = [{'remarks': rmk.remarks, 'created_date': rmk.created.strftime("%Y-%m-%d"),
                        'status': rmk.status.name if rmk.status else '', 'prob_stat': rmk.probability_status.name if rmk.probability_status else ''}
                       for rmk in FundingRemark.objects.filter(active=2, funding=self).order_by('-id')]
        return remarks

    def individual_remarks(self):
        remarks = created_date = status = prob_stat = ''
        if self.active == 2:
            fun_rmk = FundingRemark.objects.filter(active=2, funding=self)
            if fun_rmk:
                rmk = fun_rmk[0]
                remarks = rmk.remarks
                created_date = rmk.created.strftime("%Y-%m-%d"),
                status = rmk.status.name if rmk.status else ''
                prob_stat = rmk.probability_status.name if rmk.probability_status else ''
        return remarks, created_date, status, prob_stat

    def get_total_amount(self):
        sum_theme = '0' + '/-'
        theme = ConfigureThematic.objects.filter(active=2, funding__id=self.id)
        if theme:
            try:
                sum_ = sum([k.thematic.filter(active=2).aggregate(Sum('amount')).get(
                    'amount__sum', 0) for k in theme])
                sum_curr = re.search(r'\.\d+', currency_in_indian_format(sum_))
                if sum_curr and not int(sum_curr.group().replace('.', '')):

                    sum_theme = re.sub(
                            r'\.\d+', '', currency_in_indian_format(sum_)) + '/-'
            except:
                pass
        return sum_theme

    def get_selected_line_items(self, com_next):
        fund_items = ConfigureThematic.objects.filter(
            active=2, funding_theme__id__in=com_next, funding=self)
        all_theme_budget_theme = [
            ct.id for cf in fund_items for ct in cf.thematic.filter(active=2)]
        all_theme_budget_theme_data = map(lambda x: BudgetConfig.objects.get(
            id=int(x)), all_theme_budget_theme)
        get_budget_year_ = [{'id': bc.id, 'theme_budget': bc.theme_budget.name,
                             'theme_budget_id': bc.theme_budget.id,
                             'line_item': bc.line_item, 'amount': bc.get_budget_amount(),
                             'raw_amount': bc.amount,
                             'year': ' - '.join(bc.new_get_years())}
                            for bc in all_theme_budget_theme_data]
        return get_budget_year_

    def get_all_themes(self):
        theme = ''
        total_ = 0.0
        fund_theme = ConfigureThematic.objects.filter(
            active=2, funding=self)
        get_theme_id = fund_theme.values_list('funding_theme__id', flat=True)
        for th in get_theme_id:
            tot = fund_theme.filter(funding_theme__id=th)
            if tot:
                fund_name = tot[0]
                get_tot = sum(
                    [kill.amount for kill in fund_name.thematic.all()])
                data = "{0}: {1}\n".format(
                    fund_name.funding_theme.name, get_tot)
                theme += data
                total_ += get_tot
        if theme:
            theme += '%s: %d' % ('Total', total_)
        return theme


class ConfigureThematic(BaseContent):
    funding = models.ForeignKey(Funding, **OPTIONAL)
    funding_theme = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_funding_theme', **OPTIONAL)
    thematic = models.ManyToManyField(BudgetConfig, **OPTIONAL)

    def __unicode__(self):
        return self.funding.get_types_of_funding_display()


class FundingRemark(BaseContent):
    funding = models.ForeignKey(
        Funding, related_name='funding_remark', **OPTIONAL)
    status = models.ForeignKey(
        MasterLookUp, related_name='masterlookup_funding_remark_status', **OPTIONAL)
    probability_status = models.ForeignKey(
        MasterLookUp, related_name='masterlookup_funding_remark_probability_status', **OPTIONAL)
    remarks = models.TextField(**OPTIONAL)

    def __unicode__(self):
        return '{0}|{1}|{2}'.format(self.funding.get_types_of_funding_display(), self.funding.donar.name, self.status.name)


class FundingLogging(BaseContent):
    fund_remark = models.ForeignKey(FundingRemark, **OPTIONAL)
    funding_theme = models.ForeignKey(
        'masterdata.MasterLookup', related_name='funding_theme_name', **OPTIONAL)
    funding_budget = models.ManyToManyField(
        BudgetConfig, related_name='funding_theme_remark', **OPTIONAL)

    def __unicode__(self):
        return '{0}|{1}'.format(self.fund_remark.remarks, self.funding_theme.name)


class PartnerReportFile(BaseContent):
    name = models.TextField()
    user = models.ForeignKey('auth.User', **OPTIONAL)
    report = models.FileField(upload_to='static/%Y/%m/%d', **OPTIONAL)

    def __unicode__(self):
        return self.name

class PartnerUserInfo(BaseContent):
    name = models.CharField(max_length=250,**OPTIONAL)
    designation = models.CharField(max_length=250,**OPTIONAL)
    department = models.CharField(max_length=250,**OPTIONAL)
    partner = models.ForeignKey(Partner)
    email = models.CharField(max_length=250,**OPTIONAL)
    mobile = models.CharField(max_length=12,**OPTIONAL)
    address = models.TextField(max_length=500,**OPTIONAL)
    pan = models.CharField(max_length=10,**OPTIONAL)
    adhar = models.CharField(max_length=20,**OPTIONAL)
    remarks = models.TextField(max_length=500,**OPTIONAL)
    def __unicode__(self):
        return  self.name
        
        

class PartnerBoundaryMapping(BaseContent):
    partner = models.ForeignKey(Partner)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    def __str__(self):
        return self.partner.name
