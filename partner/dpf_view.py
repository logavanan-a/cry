from ast import literal_eval
from copy import deepcopy
from datetime import (date, datetime)
from itertools import (groupby, chain)
from math import ceil
import re
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import User
from django.core.mail import send_mail
from django.db.models import Q
from django.template import loader
from rest_framework import (status, )
from rest_framework.views import APIView
from rest_framework.generics import (
    CreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView)
from rest_framework.response import Response
from rest_framework.pagination import (PageNumberPagination,)
import attr
from box import Box
from ccd.settings import(web_dict, REST_FRAMEWORK, HOST_URL,)
from masterdata.models import (MasterLookUp,)
from masterdata.views import (CustomPagination,)
from userroles.views import (stripmessage,)
from .models import (Partner, Donar, BudgetConfig, Project, ProjectLocation, BudgetYear, Funding, ConfigureThematic,
                     FundingRemark, FundingLogging)
from .serializers import (DonarSerializer, DonarDetailSerializer, BudgetConfigSerializer,
                          BudgetYearSerializer, DatetoYearSerializerThematic, DatetoYearSerializer, BudgetYearSerializer,
                          ItemSerializer,
                          BudgetConfigListingFilter, BudgetConfigEditSerializer, FundingSerializer, FundingDateSerializer,
                          ConfigureThematicSerializer, ConfigureThematicSerializerDetail, DFPProjectViewDetailSerializer)
from .views import (unpack_errors, get_ceo)
from datetime import datetime


pg_size = REST_FRAMEWORK.get('DPF_PAGE_SIZE')

EMAIL_HOST_USER = 'admin@meal.mahiti.org'


def convert_months_to_years(all_dates):
    final_dates = []
    for con in all_dates:
        alter_ = re.findall(r'\d+', con)
        if alter_:
            alter_.sort(key=int)
            final_dates.append(' - '.join(alter_))
    return final_dates


def get_months_along_years(free_years, all_years):
    final_years = []
    for con_id, con in enumerate(all_years):
        for don in free_years:
            alter_ = re.findall(r'\d+', con)
            if alter_:
                alter_ = map(int, alter_)
                alter_.sort()
            f_year = map(int, don.split(' - '))
            f_year.sort()
            if alter_[0] == f_year[0]:
                final_years.append(all_years[con_id])
    return final_years


def convert_months_to_years_individual(all_dates):
    final_dates = ''
    alter_ = re.findall(r'\d+', all_dates)
    if alter_:
        alter_.sort(key=int)
        final_dates = ' - '.join(alter_)
    return final_dates


class DonarCreate(CreateAPIView):
    queryset = Donar.objects.filter(active=2)
    serializer_class = DonarSerializer

    def send_ceo_to_donar_mail(self, donar):
        image = HOST_URL + '/static/logo-new.jpg'
        subject = 'Welcome Donar %s.' % donar.name
        message = ''
        from_email = EMAIL_HOST_USER
        to_list = [donar.email]
        html_message = loader.render_to_string(
            'ceo_to_donar.html',
            {
                'image': image,
                'dobj': donar,
                'website': web_dict.get('webiste')
            }
        )
        send_mail(subject, message, from_email, to_list,
                  fail_silently=True, html_message=html_message)

    def send_donar_to_ceo_mail(self, donar):
        image = HOST_URL + '/static/logo-new.jpg'
        subject = 'New Donar Created %s.' % donar.name
        message = ''
        from_email = EMAIL_HOST_USER
        to_list = list(get_ceo())
        html_message = loader.render_to_string(
            'donar_to_ceo.html',
            {
                'image': image,
                'dobj': donar,
                'website': web_dict.get('webiste'),
                'donar': web_dict.get('donar')
            }
        )
        send_mail(subject, message, from_email, to_list,
                  fail_silently=True, html_message=html_message)

    def perform_create(self, serializer):
        data = serializer.save()
        return data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            get_data = self.perform_create(serializer)
            data = serializer.data
            data.update(
                status=2, message='successfully created the donor.', donor_id=get_data.id)
            self.send_ceo_to_donar_mail(get_data)
            self.send_donar_to_ceo_mail(get_data)
        else:
            data = stripmessage(serializer.errors)
            data.update(status=0)
        return Response(data, status=status.HTTP_201_CREATED)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = pg_size
    page_size_query_param = 'page_size'
    max_page_size = 1000


class DonarListing(ListAPIView):
    queryset = Donar.objects.filter(active=2).order_by('-id')
    serializer_class = DonarDetailSerializer
    pagination_class = StandardResultsSetPagination

    def get_data_donar(self, query):
        queryset = [{
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "location": d.location.name,
            "mobile_no": d.mobile_no,
            "active": d.active,
            "user": d.user.id if d.user else 0
        } for d in query]
        return queryset

    def list(self, request, *args, **kwargs):
        key = request.query_params.get('key')
        project_id = request.query_params.get('project_id', 0) or 0
        query = self.get_queryset()
        if key == '3':
            fund_donar = Funding.objects.filter(active=2, object_id=int(project_id)).values_list(
                'donar__id', flat=True).distinct()
            unique_donar = set(query.values_list(
                'id', flat=True)) - set(fund_donar)
            query = query.filter(id__in=list(unique_donar))
            queryset = self.get_data_donar(query)
        elif key == '1':
            queryset = self.get_data_donar(query)
        elif key == '2':
            queryset = self.get_data_donar(query)
            get_page = ceil(
                float(self.get_queryset().count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            return paginator.get_paginated_response(result_page, 2, 'Successfully Retreieved', 26, get_page)
        return Response(queryset)


class DonarDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Donar.objects.all()
    serializer_class = DonarDetailSerializer

    def update(self, request, *args, **kwargs):
        don = Donar.objects.filter(active=2)
        validated_data = unpack_errors(dict(request.data))
        mas = MasterLookUp.objects.filter(id=validated_data.get('location'))
        if mas:
            validated_data['location'] = mas[0]
        else:
            del validated_data['location']
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False)
        data = {}
        if serializer.is_valid():
            if instance.email != validated_data.get('email') and don.filter(email__iexact=validated_data.get('email')):

                data.update(
                        message="Already Donar by this mail-id exists.")
            if instance.mobile_no != validated_data.get('mobile_no') and don.filter(mobile_no__iexact=validated_data.get('mobile_no')):

                data.update(message="Already Donar by this mobile exists.")
            if not data:
                for attrs, value in validated_data.items():
                    try:
                        if attrs == 'user':
                            value = User.objects.get(id=value)
                    except:
                        value = value
                    setattr(instance, attrs, value)
                instance.save()
                data = serializer.data
                data.update(
                    status=2, message='successfully updated the donor details.')
        else:
            data.update(status=0, message='something went wrong.',
                        errors=unpack_errors(serializer.errors))
        return Response(data)

    def perform_destroy(self, instance):
        instance.switch()


@attr.s
class ConvertDateToYear(object):
    diff_year = attr.ib(default=7)
    start_year = attr.ib(default=1991)
    actual_start_date = attr.ib(default=1991)
    actual_end_date = attr.ib(default=1991)

    def convert_year(self):
        start_ = self.start_year
        end_ = self.start_year
        date_to_year = []
        if not self.diff_year:
            date_to_year.append('{0} - {1}'.format(self.actual_start_date.strftime(
                "%b %Y"), self.actual_end_date.strftime("%b %Y")))
        else:
            for i in iter(range(self.diff_year)):
                if i == 0:
                    end_ += 1
                    end_year = date(end_, 01, 01)
                    date_to_year.append(
                        '{0} - {1}'.format(self.actual_start_date.strftime("%b %Y"), end_year.strftime("%b %Y")))
                else:
                    start_ += 1
                    end_ += 1
                    start_year = date(start_, 01, 01)
                    end_year = date(end_, 01, 01)
                    if self.actual_end_date.year == end_:
                        end_year = self.actual_end_date
                    date_to_year.append(
                        '{0} - {1}'.format(start_year.strftime("%b %Y"), end_year.strftime("%b %Y")))
        return date_to_year


class GetDateToYear(APIView):

    def post(self, request):
        """
        To Convert Partner Support Since and Support to date into years.
        ---
        parameters:
        - name: proj_id
          description: Pass partner id
          required: true
          type: integer
          paramType: form
        - name: key
          description: Pass key as 1 or 2
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        serializer = DatetoYearSerializerThematic(data=data)
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        if serializer.is_valid():
            proj_id = int(data.get('proj_id'))
            proj = Project.objects.filter(active=2, id=proj_id)
            if proj:
                p = proj[0]
                start_year = p.program.partner.support_from
                end_year = p.program.partner.support_to if p.program.partner.support_to else datetime.datetime.now()
                if start_year and end_year:
                    diff_year = end_year.year - start_year.year
                    if request.data.get('key') == '2':
                        bc = BudgetConfig.objects.filter(
                            active=2, object_id=proj_id)
                        if bc:
                            get_date = ConvertDateToYear(
                                diff_year, start_year.year, start_year, end_year)
                            get_years = convert_months_to_years(
                                get_date.convert_year())
                            years_ = [b.get_years() for b in bc]
                            years_.sort(key=lambda x: x[0])
                            all_years_ = list(k for k, _ in groupby(years_))
                            [get_years.remove(
                                ' - '.join(map(str, list(b)))) for b in all_years_]
                            get_years = get_months_along_years(
                                get_years, get_date.convert_year())
                            if not get_years:
                                response = {
                                    'status': 0, 'message': 'all the years data is saved', 'data': get_years}
                            else:
                                response = {
                                    'status': 2, 'message': 'successfully retrieved years', 'data': get_years}
                        else:
                            get_date = ConvertDateToYear(
                                diff_year, start_year.year, start_year, end_year)
                            get_years = get_date.convert_year()
                            response = {
                                'status': 2, 'message': 'successfully retrieved years', 'data': get_years}
                    else:
                        get_date = ConvertDateToYear(
                            diff_year, start_year.year, start_year, end_year)
                        get_years = get_date.convert_year()
                        response = {
                            'status': 2, 'message': 'successfully retrieved years', 'data': get_years}
                else:
                    response.update(errros={
                                    'project': 'Project id %s doesn\'t contain support from date or support to date please check.' % proj_id})
            else:
                response.update(
                    errros={'project': 'Project does\'t exists for this id %d' % proj_id})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class GetThematic(CreateAPIView):
    serializer_class = DatetoYearSerializerThematic

    def post(self, request):
        data = request.data
        serializer = DatetoYearSerializerThematic(data=data)
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        if serializer.is_valid():
            proj_id = data.get('proj_id')
            proj_loc = ProjectLocation.objects.filter(
                active=2, project__id=proj_id).order_by('-id')
            if proj_loc:
                pro = proj_loc[0]
                get_thematic = pro.theme.filter(active=2)
                if get_thematic:
                    response = {
                        'status': 2, 'message': 'successfully retrieved the thematics'}
                    response.update(
                        data=[{'id': t.id, 'name': t.name} for t in get_thematic])
                else:
                    response.update(errors={
                                    'thematics': 'No thematics or inactive in backend for this project id %s' % proj_id})
            else:
                response.update(
                    errors={'thematics': 'No Object for this project id %s' % proj_id})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class ItemLineChecker(CreateAPIView):
    serializer_class = ItemSerializer

    def post(self, request):
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went wrong'}
        serializer = ItemSerializer(data=data.to_dict())
        if serializer.is_valid():
            budget_years = convert_months_to_years_individual(data.start_year)
            years = budget_years.split(' - ')
            years.sort(key=int)
            if years:
                if len(years) == 1:
                    bc = BudgetConfig.objects.filter(active=2, object_id=int(data.proj_id),
                                                     line_item__iexact=data.name,
                                                     theme_budget__id=int(
                                                         data.theme_budget),
                                                     year__start_year__year=int(years[0]), year__end_year__year=int(years[0]))
                else:
                    bc = BudgetConfig.objects.filter(active=2, object_id=int(data.proj_id), line_item__iexact=data.name,
                                                     theme_budget__id=int(
                                                         data.theme_budget),
                                                     year__start_year__year=int(years[0]), year__end_year__year=int(years[1]))
                if bc:
                    response.update(errors={'item_line': 'already %s line item exists for this project' % data.name.title(
                    )}, data=[{'id': b.id, 'name': b.line_item, 'amount': b.amount} for b in bc])
                else:
                    response = {'status': 2,
                                'message': 'thank god no data is there.'}
            else:
                response.update(message='Budget Year is required.')
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class BudgetConfigCreate(CreateAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = BudgetConfigSerializer

    @staticmethod
    def get_diff_year(get_year, start_, end_):
        if len(get_year) == 1:
            if start_.year == get_year[0] and end_.year == get_year[0]:
                budget_year, created = BudgetYear.objects.get_or_create(
                    start_year=start_, end_year=end_)
        else:
            if start_.year == get_year[0] and end_.year == get_year[1]:
                budget_year, created = BudgetYear.objects.get_or_create(
                    start_year=start_, end_year=end_)
            elif start_.year == get_year[0] and end_.year != get_year[1]:
                budget_year, created = BudgetYear.objects.get_or_create(
                    start_year=start_, end_year=date(get_year[1], 1, 1))
            elif start_.year != get_year[0] and end_.year == get_year[1]:
                budget_year, created = BudgetYear.objects.get_or_create(
                    start_year=date(get_year[0], 1, 1), end_year=end_)
            else:
                budget_year, created = BudgetYear.objects.get_or_create(
                    start_year=date(get_year[0], 1, 1), end_year=date(get_year[1], 1, 1))
        return budget_year

    @classmethod
    def get_budget_year(cls, get_year, start_, end_):
        if len(get_year) == 1:
            budget_year, created = BudgetYear.objects.get_or_create(
                start_year=start_, end_year=end_)
        else:
            budget_year = cls.get_diff_year(get_year, start_, end_)
        return budget_year

    def create(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            proj_id = data.get('proj_id')
            proj = Project.objects.filter(id=proj_id)
            if proj:
                p = proj[0]
                start_year = p.program.partner.support_from
                end_year = p.program.partner.support_to
                if start_year and end_year:
                    budget_years = convert_months_to_years_individual(
                        data.year)
                    get_bud_year = self.get_budget_year(map(int, map(
                        lambda x: x.strip(), re.split('-', budget_years))), start_year, end_year)
                    budget = literal_eval(data.budget_config)
                    get_theme_ = ProjectLocation.objects.filter(
                        active=2, project=p).order_by('-id')
                    if get_theme_:
                        get_theme = get_theme_[0].theme.filter(
                            active=2).values_list('id', flat=True)
                        for b in get_theme:
                            get_budget = budget.get(str(b))
                            for config in get_budget:
                                budget_dict = {
                                    'year': get_bud_year, 'theme_budget_id': b, 'user_id': int(data.user_id)}
                                budget_dict.update(config)
                                bc = BudgetConfig.objects.create(**budget_dict)
                                bc.content_type, bc.object_id = ContentType.objects.get_for_model(
                                    Project), int(request.data.get('proj_id'))
                                bc.save()
                        response = {
                            'status': 2, 'message': 'Successfully created the budget config', 'proj_id': proj_id}
                    else:
                        response.update(
                            errors={'project': 'Project doesn\'t have themantics'})
                else:
                    response.update(errros={
                                    'project': 'Project doesn\'t contain support from or to date please check.'})
            else:
                response.update(
                    errors={'project': 'No Object for this project id'})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class BudgetConfigListing(CreateAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = BudgetConfigListingFilter

    def post(self, request, *args, **kwargs):
        data = Box(request.data)
        proj_id = int(data.proj_id)
        query_ = self.get_queryset().filter(object_id=proj_id)
        response = {'status': 0,
                    'message': 'No data for this Project.', 'data': []}
        if data.key == '2':
            if request.data.get('year') and data.thematic_area != '0':
                budget_years = convert_months_to_years_individual(data.year)
                get_years = list(set(budget_years.split(' - ')))
                get_years.sort(key=int)
                if len(get_years) == 1:
                    query_ = query_.filter(theme_budget__id=int(
                        data.thematic_area), year__start_year__year=get_years[0], year__end_year__year=get_years[0])
                else:
                    query_ = query_.filter(theme_budget__id=int(
                        data.thematic_area), year__start_year__year=get_years[0], year__end_year__year=get_years[1])
            elif data.thematic_area != '0' and request.data.get('year') == '':
                query_ = query_.filter(
                    theme_budget__id=int(data.thematic_area))
            elif data.thematic_area == '0' and request.data.get('year') != '':
                budget_years = convert_months_to_years_individual(data.year)
                get_years = list(set(budget_years.split(' - ')))
                get_years.sort(key=int)
                if len(get_years) == 1:
                    query_ = query_.filter(year__start_year__year=get_years[
                                           0], year__end_year__year=get_years[0])
                else:
                    query_ = query_.filter(year__start_year__year=get_years[
                                           0], year__end_year__year=get_years[1])
        if query_:
            response = {'status': 2,
                        'message': 'Successfully retrieved the values'}
            get_budget_year = [{'id': bc.id, 'theme_budget': bc.theme_budget.name,
                                'line_item': bc.line_item, 'amount': bc.get_budget_amount(),
                                'raw_amount': bc.amount,
                                'year': ' - '.join(bc.new_get_years())}
                               for bc in query_.order_by('-id')]
            response.update(budget_config=get_budget_year)
            get_page = ceil(float(query_.count()) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(get_budget_year, request)
            return paginator.get_paginated_response(result_page, 2, 'Successfully Retreieved', 24, get_page)
        return Response(response)


class BudgetConfigEdit(RetrieveUpdateDestroyAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = BudgetConfigEditSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer = dict(serializer.data)
        serializer.update(year=' - '.join(instance.new_get_years()),
                          theme_budget_name=instance.theme_budget.name)
        return Response(serializer)

    def update(self, request, *args, **kwargs):
        don = self.get_queryset()
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went wrong'}
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=data.to_dict(), partial=False)
        if serializer.is_valid():
            proj_id = data.get('proj_id')
            proj = Project.objects.filter(id=proj_id)
            if proj:
                p = proj[0]
                start_year = p.program.partner.support_from
                end_year = p.program.partner.support_to
                if start_year and end_year:
                    data_ = {}
                    bgconfig = BudgetConfigCreate()
                    budget_years = convert_months_to_years_individual(
                        data.year)
                    get_budget_year = bgconfig.get_budget_year(map(int, map(
                        lambda x: x.strip(), re.split('-', budget_years))), start_year, end_year)
                    if instance.line_item != data.line_item and instance.theme_budget.id != data.theme_budget and instance.year != get_budget_year \
                        and don.filter(line_item__iexact=data.line_item, theme_budget__id=int(data.theme_budget), year=get_budget_year, object_id=proj_id):
                        data_.update(
                                message="Already theme budget and line item exists for this Project.")
                    if not data_:
                        obj = serializer.save()
                        obj.year = get_budget_year
                        obj.user_id = int(data.user)
                        obj.save()
                        budget_dict = {
                            'year': obj.year, 'theme_budget_id': obj.theme_budget.id, 'user_id': obj.user.id}
                        if request.data.get('edit_budget_config', 0):
                            dic_bud = literal_eval(data.edit_budget_config)
                            for key, value in dic_bud.items():
                                for v in value:
                                    budget_dict.update(v)
                                    bc = BudgetConfig.objects.create(
                                        **budget_dict)
                                    bc.content_type, bc.object_id = ContentType.objects.get_for_model(
                                        Project), int(request.data.get('proj_id'))
                                    bc.save()
                            response = {
                                'status': 2, 'message': 'Successfully updated the budget config.', 'budget': obj.id}
                    else:
                        response.update(data_)
            else:
                response.update(
                    message={'project': 'No Object for this project id'})
        else:
            response.update(message=unpack_errors(serializer.errors))
        return Response(response)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        all_active_id = list(set([bc.id for c in ConfigureThematic.objects.filter(
            active=2) for bc in c.thematic.filter(active=2)]))
        if instance.id in all_active_id:
            response = {
                'status': 0, 'message': 'This Line Item is already tagged to one of the Funding!!'}
        else:
            response = {
                'status': 2, 'message': 'Successfully Deleted the Item!!'}
            instance.switch()
        return Response(response)


class FundingThematicListing(CreateAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = DatetoYearSerializer

    def get_comb_next_years(self, list_, d):
        mast_ = 0
        for i, q in enumerate(list_):
            sy = map(int, q.split('-'))
            sy.sort()
            if sy[0] == d:
                mast_ = i
        final_years = map(int, list_[mast_].split(' - '))
        final_years.sort()
        return final_years

    def get_project_support_to(self, proj_id):
        start_year = end_year = ''
        proj = Project.objects.filter(active=2, id=int(proj_id))
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
        return start_year, end_year

    def entire_project(self, **kwargs):
        data = Box(kwargs)
        theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id),
                                           object_id=int(data.proj_id)).values_list('id', flat=True)
        return theme

    def get_years_(self, *args, **kwargs):
        data = Box(kwargs)
        budget_years = convert_months_to_years_individual(args[0])
        start_years = map(int, map(lambda x: x.strip(),
                                   re.split('-', budget_years)))
        start_years.sort(key=int)
        theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id), object_id=int(data.proj_id),
                                           year__start_year__year=start_years[0], year__end_year__year=start_years[1]).values_list('id', flat=True)
        return theme

    def get_custom_column_(self, *args, **kwargs):
        data = Box(kwargs)
        args = [a.strftime('%Y-%m-%d').split('-') for a in args if a]
        [ar.sort(key=int) for ar in args]
        years = list(set([int(a[2]) for a in args if a]))
        get_start_years, get_end_years = self.get_project_support_to(
            data.proj_id)
        diff_year = get_end_years.year - get_start_years.year
        get_date = ConvertDateToYear(
            diff_year, get_start_years.year, get_start_years, get_end_years)
        get_years = convert_months_to_years(get_date.convert_year())
        com_next = map(int, data.thematic_id.split(','))
        if len(years) == 1:
            get_next_years_ = self.get_comb_next_years(get_years, years[0])
            date(get_next_years_[1], 1, 1)
            theme = self.get_queryset().filter(theme_budget__id__in=com_next, object_id=int(data.proj_id),
                                               year__start_year__year__gte=get_next_years_[0], year__end_year__year__lte=get_next_years_[1]).values_list('id', flat=True)
        else:
            years.sort()
            theme = self.get_queryset().filter(theme_budget__id__in=com_next, object_id=int(data.proj_id),
                                               year__start_year__year__gte=years[0], year__end_year__year__lte=years[1]).values_list('id', flat=True)
        return theme

    def post(self, request, *args, **kwargs):
        get_budget_config = []
        data = Box(request.data)
        serializer = DatetoYearSerializer(data=data.to_dict())
        response = {
            'status': 0, 'message': 'Something went wrong, All the Item Line have been taken.', 'data': []}
        start_year_ = data.start_year
        end_year_ = data.end_year
        get_budget_year = []
        if data.thematic_id == '0' and data.fund_id != '0':
            fun = Funding.objects.filter(id=data.fund_id,
                                         active=2, object_id=int(data.proj_id))
            get_fun_theme = ConfigureThematic.objects.filter(active=2, funding__in=fun.values_list(
                'id', flat=True))
            if fun:
                fun_ = fun[0]
                all_theme = get_fun_theme.values_list(
                    'funding_theme__id', flat=True)
                years = [fun_.year.start_year.year, fun_.year.end_year.year]
                get_remain_theme = self.get_queryset().filter(theme_budget__id__in=all_theme, object_id=int(data.proj_id),
                                                              year__start_year__year__gte=years[0], year__end_year__year__lte=years[1]).values_list('id', flat=True)
                if get_fun_theme:
                    get_budget_config = [
                        gf.id for f in get_fun_theme for gf in f.thematic.filter(active=2)]
                    get_remain_theme = list(
                        set(list(get_budget_config) + list(get_remain_theme)))
            else:
                get_remain_theme = []
            get_thematic = map(lambda x: BudgetConfig.objects.get(
                id=int(x)), get_remain_theme)
        else:
            entire_start_years, entire_end_years = self.get_project_support_to(
                data.proj_id)
            tof = {'0': lambda: (entire_start_years.strftime('%Y-%m-%d'), entire_end_years.strftime('%Y-%m-%d')),
                   '1': lambda: (start_year_, end_year_),
                   '2': lambda: (datetime.strptime(start_year_, '%Y-%m'), datetime.strptime(end_year_, '%Y-%m'))}
            start_years, end_years = tof.get(data.type_funding)()
            get_years_thematics = {'0': lambda: self.entire_project(**data.to_dict()),
                                   '1': lambda: self.get_years_(start_year_, **data.to_dict()),
                                   '2': lambda: self.get_custom_column_(start_years, end_years, **data.to_dict())}
            if serializer.is_valid():
                get_remain_theme = get_years_thematics.get(data.type_funding)()
                all_theme = map(lambda x: BudgetConfig.objects.get(
                    id=int(x)), get_remain_theme)
                fund_tof = {'0': lambda: (entire_start_years.year, entire_end_years.year),
                            '1': lambda: map(int, convert_months_to_years_individual(start_years).split(' - ')),
                            '2': lambda: (datetime.strptime(start_year_, '%Y-%m').year, datetime.strptime(end_year_, '%Y-%m').year)}
                start_years_, end_years_ = fund_tof.get(data.type_funding)()
                fun = Funding.objects.filter(active=2, object_id=int(data.proj_id),
                                             year__start_year__year=start_years_, year__end_year__year=end_years_)
                if fun:
                    com_next = map(int, data.thematic_id.split(','))
                    get_fun_theme = ConfigureThematic.objects.filter(active=2, funding__in=fun.values_list(
                        'id', flat=True), funding_theme__id__in=com_next)
                    if get_fun_theme:
                        get_budget_config = [
                            gf.id for f in get_fun_theme for gf in f.thematic.filter(active=2)]
                        get_remain_theme = list(
                            set(get_remain_theme) - set(get_budget_config))
                get_thematic = map(lambda x: BudgetConfig.objects.get(
                    id=int(x)), get_remain_theme)
                if data.key_edit == '1':
                    funny = Funding.objects.get(id=data.fund_id)
                    if get_budget_config:
                        get_budget_config = []
                    all_theme_budget_theme = list(
                        set(list(get_remain_theme) + list(set(get_budget_config))))
                    all_theme_budget_theme_data = map(lambda x: BudgetConfig.objects.get(
                        id=int(x)), all_theme_budget_theme)
                    com_next = map(int, data.thematic_id.split(','))
                    finalize_line = funny.get_selected_line_items(com_next)
                    get_budget_year_ = [{'id': bc.id, 'theme_budget': bc.theme_budget.name,
                                         'theme_budget_id': bc.theme_budget.id,
                                         'line_item': bc.line_item, 'amount': bc.get_budget_amount(),
                                         'raw_amount': bc.amount,
                                         'year': ' - '.join(bc.new_get_years())}
                                        for bc in all_theme_budget_theme_data]
                    completed_data = finalize_line + get_budget_year_

                    response = {
                        'status': 2, 'message': 'Successfully retreieved the data'}
                    response['data'] = completed_data
            else:
                response.update(errors=unpack_errors(serializer.errors))
        if get_thematic and data.key_edit != '1':
            response = {'status': 2,
                        'message': 'Successfully retrieved the data'}
            get_budget_year = [{'id': bc.id, 'theme_budget': bc.theme_budget.name,
                                'theme_budget_id': bc.theme_budget.id,
                                'line_item': bc.line_item, 'amount': bc.get_budget_amount(),
                                'raw_amount': bc.amount,
                                'year': ' - '.join(bc.new_get_years())}
                               for bc in get_thematic]
            response['data'] = get_budget_year
        return Response(response)


class FundingYearListing(CreateAPIView):
    queryset = Funding.objects.filter(active=2)
    serializer_class = FundingDateSerializer

    @staticmethod
    def get_project_support_to(proj_id):
        start_year = end_year = ''
        proj = Project.objects.filter(active=2, id=proj_id)
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
        return start_year, end_year

    @staticmethod
    def get_comb_years(list_, d):
        for i, q in enumerate(list_):
            sy = map(int, q.split(' - '))
            sy.sort()
            if sy[0] == d:
                del list_[i]
        return list_

    @staticmethod
    def entire_project():
        return {'status': 2, 'message': 'successfully'}

    @staticmethod
    def specific_year(cls, query, proj_id):
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        start_year, end_year = cls.get_project_support_to(proj_id)
        if start_year and end_year:
            diff_year = end_year.year - start_year.year
            if not query:
                get_date = ConvertDateToYear(
                    diff_year, start_year.year, start_year, end_year)
                get_years = get_date.convert_year()
            else:
                start = start_year.year
                end = end_year.year
                get_date = ConvertDateToYear(
                    diff_year, start_year.year, start_year, end_year)
                get_years = convert_months_to_years(get_date.convert_year())
                all_date = get_years[::]
                get_years_mod = [b.get_years() for b in query]
                get_years_mod.sort(key=lambda x: x[0])
                get_years_ = list((k for k, _ in groupby(get_years_mod)))
                for d in get_years_:
                    d = list(set(d))
                    if len(d) == 1:
                        if d[0] == start:
                            get_years = cls.get_comb_years(get_years, d[0])
                        elif d[0] == end:
                            for j in get_years:
                                k = j.split(' - ')
                                k.sort(key=int)
                                if k[0] == str(d[0]):
                                    all_date.remove(' - '.join(k))
                            get_years = all_date
                    elif d[0] == start and d[1] == end:
                        get_years = []
                    elif d[0] == start and d[1] != end:
                        diff = d[1] - d[0]
                        get_date = ConvertDateToYear(
                            diff, d[0], start_year, end_year)
                        get_years_end = convert_months_to_years(
                            get_date.convert_year())
                        for gd in get_years_end:
                            if gd in get_years:
                                get_years.remove(gd)
                    elif d[0] != start and d[1] == end:
                        for a in get_years:
                            if str(d[1]) in a:
                                get_years.remove(a)
                        get_years = cls.get_comb_years(get_years, d[0])
                    elif d[0] != start and d[1] != end:
                        get_years = cls.get_comb_years(get_years, d[0])
            get_date_ = ConvertDateToYear(
                diff_year, start_year.year, start_year, end_year)
            get_years = get_months_along_years(
                get_years, get_date_.convert_year())
            response = {
                'status': 2, 'message': 'successfully retrieved years', 'data': get_years}
        else:
            response.update(errros={
                            'project': 'Project doesn\'t contain support from or to date please check.'})
        return response

    @staticmethod
    def specific_custom(cls, query, proj_id):
        get_dates_range = []
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        start_year, end_year = cls.get_project_support_to(proj_id)
        if query:
            get_dates_range = [q.get_dates() for q in query]
            get_groups = list((k for k, _ in groupby(get_dates_range)))
        response = {'status': 2, 'message': 'successfully retrieved years',
                    'data': {'start_date': start_year.strftime('%Y-%m'), 'end_date': end_year.strftime('%Y-%m'), 'date_range': get_groups}}
        return response

    def no_funding_year(self, proj_id):
        response = {'status': 0, 'message': "No Data for this project."}
        proj = Project.objects.filter(id=proj_id)
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
            if start_year and end_year:
                get_cust = list(set([start_year.year, end_year.year]))
                get_cust.sort()
                if len(get_cust) == 1:
                    start_ = start_year.strftime("%b %Y")
                    end_ = end_year.strftime("%b %Y")
                    get_years_end = [start_ + ' - ' + end_]
                else:
                    diff_year = end_year.year - start_year.year
                    get_date = ConvertDateToYear(
                        diff_year, get_cust[0], start_year, end_year)
                    get_years_end = get_date.convert_year()
                response = {
                    'status': 2, 'message': 'successfully retrieved years', 'data': get_years_end}
            else:
                response = {'status': 0, 'message': 'No data', 'data': []}
        return response

    def no_funding_specific_custom(self, proj_id):
        get_groups = []
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        proj = Project.objects.filter(id=proj_id)
        if proj:
            start_year, end_year = self.get_project_support_to(proj_id)
            response = {'status': 2, 'message': 'successfully retrieved years',
                        'data': {'start_date': start_year.strftime('%Y-%m'), 'end_date': end_year.strftime('%Y-%m'), 'date_range': get_groups}}
        return response

    def post(self, request):
        data = Box(request.data)
        class_ = self.get_serializer_class()
        serializer = class_(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            proj_id = int(data.to_dict().get('proj_id', 0))
            query = self.get_queryset().filter(object_id=proj_id)
            if data.key == '2':
                if query:
                    response = {'0': lambda: self.entire_project(),
                                '1': lambda: self.specific_year(self, query, proj_id),
                                '2': lambda: self.specific_custom(self, query, proj_id)}.get(data.type_funding)()
                else:
                    response = {'0': lambda: self.entire_project(),
                                '1': lambda: self.no_funding_year(proj_id),
                                '2': lambda: self.no_funding_specific_custom(proj_id)}.get(data.type_funding)()
            else:
                response = {'0': lambda: self.entire_project(),
                            '1': lambda: self.no_funding_year(proj_id),
                            '2': lambda: self.no_funding_specific_custom(proj_id)}.get(data.type_funding)()
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


def partner_year_check(query, data):
    response = {}
    proj_id = int(data.get('proj_id'))
    proj = Project.objects.filter(id=proj_id)
    fun = int(data.get('types_of_funding'))
    if proj:
        p = proj[0]
        start_year = p.program.partner.support_from
        end_year = p.program.partner.support_to
        label_start = start_year.strftime('%Y-%m-%d')
        label_end = end_year.strftime('%Y-%m-%d')
        if fun == 1:
            budget_years = convert_months_to_years_individual(
                data.get('start_year'))
            de_start_year = map(int, budget_years.split(' - '))
            de_start_year.sort()
            if len(de_start_year) == 1 and (start_year.year != de_start_year[0]):
                response.update(
                        errors_year={'funding_year': 'Year doesn\'t match to partner support since'})
            elif not (de_start_year[0] >= start_year.year and de_start_year[1] <= end_year.year):
                response.update(errors_year={
                                    'funding_year': 'Year doesn\'t match to partner support from or suppport to years', 'start': start_year.year, 'end': end_year.year})
        elif fun == 2:
            start_year_ = data.get('start_year')
            end_year_ = data.get('end_year')
            con_start_year = datetime.strptime(start_year_, '%Y-%m')
            con_end_year = datetime.strptime(end_year_, '%Y-%m')
            if start_year.year == con_start_year.year:
                con_start_year = start_year
            if end_year.year == con_end_year.year:
                con_end_year = end_year
            elif not (con_start_year >= start_year and con_end_year <= end_year):
                response.update(errors_year={
                                'funding_year': 'Dates doesn\'t come within the to partner support from and suppport to dates', 'start': label_start, 'end': label_end})
    else:
        response = {'status': 0, 'message': 'Something went wrong',
                    'project': 'No Project Exists'}
    return response


def check_fund_exists(query, data):
    response = {}
    fund_type = {0: 'Entire Project', 1: 'Specific Year', 2: 'Specific Custom'}

    fun = int(data.get('types_of_funding'))
    query_data = query.filter(object_id=int(
        data.get('proj_id')), types_of_funding=fun)
    if fun == 1:
        budget_years = convert_months_to_years_individual(
            data.get('start_year'))
        start_year = map(int, budget_years.split(' - '))
        if len(start_year) == 1:
            query_data = query_data.filter(year__start_year__year=start_year[
                                           0], year__end_year__year=start_year[0])
            if query_data:
                response.update(errors={'types_of_funding': 'Already %s funding type is exists for the year %s' % (
                    fund_type.get(fun), data.get('start_year'))})
        else:
            query_data = query_data.filter(year__start_year__year=start_year[
                                           0], year__end_year__year=start_year[1])
            if query_data:
                response.update(errors={'types_of_funding': 'Already %s funding type is exists for the year %s' % (
                    fund_type.get(fun), data.get('start_year'))})
    elif fun == 2:
        start_year = datetime.strptime(data.get('start_year'), '%Y-%m')
        end_year = datetime.strptime(data.get('end_year'), '%Y-%m')
        query_data = query_data.filter(
            year__start_year=start_year, year__end_year=end_year)
        if query_data:
            response.update(errors={'types_of_funding': 'Already %s funding type is exists for the dates from %s to %s' % (
                fund_type.get(fun), data.get('start_year'), data.get('end_year'))})
    elif fun == 0 and query_data:

        response.update(errors={
                            'types_of_funding': 'Already %s funding type is exists for this project' % (fund_type.get(fun))})
    return response


class FundingCreate(CreateAPIView):
    queryset = Funding.objects.filter(active=2)
    serializer_class = FundingSerializer

    def funding_ceo_to_donar_mail(self, proj, funding):
        image = HOST_URL + '/static/logo-new.jpg'
        subject = '%s have been Funded to this Partner %s.' % (
            funding.donar.name, proj.program.partner.name)
        message = ''
        from_email = EMAIL_HOST_USER
        to_list = [funding.donar.email]
        start_date = funding.get_dates()
        remarks, created_date, status, prob_stat = funding.individual_remarks()
        themes_list = funding.get_all_themes().split('\n')
        html_message = loader.render_to_string(
            'ceo_to_donar_funding.html',
            {
                'image': image,
                'dobj': funding,
                'website': web_dict.get('webiste'),
                'theme': themes_list,
                'start_date': start_date,
                'remarks': remarks,
                'status': status,
                'prob_stat': prob_stat,
                'proj': proj
            }
        )
        send_mail(subject, message, from_email, to_list,
                  fail_silently=True, html_message=html_message)

    def funding_donar_to_ceo_mail(self, proj, funding):
        image = HOST_URL + '/static/logo-new.jpg'
        subject = '%s Partner is Funded by %s.' % (
            proj.program.partner.name, funding.donar.name)
        message = ''
        from_email = EMAIL_HOST_USER
        to_list = list(get_ceo())
        start_date = funding.get_dates()
        remarks, created_date, status, prob_stat = funding.individual_remarks()
        themes_list = funding.get_all_themes().split('\n')
        html_message = loader.render_to_string(
            'donar_to_ceo_funding.html',
            {
                'image': image,
                'dobj': funding,
                'website': web_dict.get('webiste'),
                'theme': themes_list,
                'start_date': start_date,
                'remarks': remarks,
                'status': status,
                'prob_stat': prob_stat,
                'funding': web_dict.get('funding') + str(proj.id),
                'proj': proj
            }
        )
        send_mail(subject, message, from_email, to_list,
                  fail_silently=True, html_message=html_message)

    @staticmethod
    def create_custom_funding(budget_year, **kwargs):
        data = Box(kwargs)
        instance = data.instance
        proj_id = data.proj_id
        thematic_id = data.thematic_id
        instance.year = budget_year
        instance.content_type, instance.object_id = ContentType.objects.get_for_model(
            Project), proj_id
        instance.save()
        fun_remark = FundingRemark.objects.create(funding=instance, status=instance.status,
                                                  probability_status=instance.probability_status)
        proj_loc = thematic_id
        for key, value in proj_loc.items():
            if value:
                configfun = ConfigureThematic.objects.create(
                    funding=instance, funding_theme_id=int(key))
                configfun.thematic.add(*value)
                fun_log = FundingLogging.objects.create(
                    fund_remark=fun_remark, funding_theme_id=int(key))
                fun_log.funding_budget.add(*value)
        return instance

    @staticmethod
    def specific_year_funding(cls, pass_start_year, start_year, end_year, **kwargs):
        get_budget = BudgetConfigCreate()
        get_all_budget = get_budget.get_budget_year(
            pass_start_year, start_year, end_year)
        create_funding = cls.create_custom_funding(get_all_budget, **kwargs)
        return create_funding

    @staticmethod
    def custom_column_funding(cls, pass_start_year, pass_end_year, **kwargs):
        start_y = pass_start_year
        start_y.sort(reverse=True)
        start_ = '-'.join(map(str, start_y))
        budget_year, created = BudgetYear.objects.get_or_create(start_year=datetime.strptime(
            start_, '%Y-%m'), end_year=datetime.strptime(pass_end_year, '%Y-%m'))
        create_funding = cls.create_custom_funding(budget_year, **kwargs)
        return create_funding

    @staticmethod
    def get_line_theme_dict(line_item_id, thematic_id, proj_id):
        line_ = map(int, literal_eval(line_item_id))
        thematic_id = map(int, literal_eval(thematic_id))
        new_dict = {}
        for the_ in thematic_id:
            for lie_ in line_:
                bu = BudgetConfig.objects.filter(
                    id=lie_, theme_budget__id=the_)
                if bu:
                    if the_ in new_dict:
                        l_k1 = new_dict.get(str(the_))
                        l_k1.append(lie_)
                    else:
                        new_dict.setdefault(str(the_), [])
                        l_k1 = new_dict.get(str(the_))
                        l_k1.append(lie_)
        return new_dict

    def post(self, request, *args, **kwargs):
        """
        API to create Funding.
        ---
        parameters:
        - name: proj_id
          description: Pass project id
          required: true
          type: integer
          paramType: form
        - name: start_year
          description: Pass start_year value
          required: true
          type: string
          paramType: form
        - name: end_year
          description: Pass end_year value
          required: true
          type: string
          paramType: form
        - name: thematic_id
          description: Pass thematic_ids
          required: true
          type: string
          paramType: form
        - name: line_item_id
          description: Pass line items
          required: true
          type: string
          paramType: form
        """
        data = Box(request.data)
        serializer = FundingSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        proj_id = int(data.proj_id)
        proj = Project.objects.filter(active=2, id=proj_id)
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
        if serializer.is_valid():
            instance = serializer.save()
            if data.types_of_funding == '0':
                if start_year and end_year:
                    mast_status = MasterLookUp.objects.filter(
                        slug__iexact='fully-funded').order_by('-id')
                    get_status = mast_status[0].id if mast_status else 0
                    budget_year, created = BudgetYear.objects.get_or_create(
                        start_year=start_year, end_year=end_year)
                    instance.year = budget_year
                    instance.status_id = get_status
                    instance.content_type, instance.object_id = ContentType.objects.get_for_model(
                        Project), proj_id
                    instance.save()
                    proj_loc = ProjectLocation.objects.get(project=p).theme.filter(
                        active=2).values_list('id', flat=True)
                    for pro in proj_loc:
                        configfun = ConfigureThematic.objects.create(
                            funding=instance, funding_theme_id=pro)
                        get_bug_con = BudgetConfig.objects.filter(
                            theme_budget__id=pro, object_id=proj_id).values_list('id', flat=True)
                        configfun.thematic.add(*get_bug_con)
            else:
                budget_years = convert_months_to_years_individual(
                    data.start_year)
                pass_start_year = map(
                    int, map(lambda x: x.strip(), re.split('-', budget_years)))
                pass_end_year = data.end_year
                all_values_data = self.get_line_theme_dict(
                    data.line_item_id, data.thematic_id, proj_id)
                response_dict = {
                    'instance': instance, 'proj_id': proj_id, 'p': p, 'thematic_id': all_values_data}
                {
                    '1': lambda: self.specific_year_funding(self, pass_start_year, start_year, end_year, **response_dict),
                    '2': lambda: self.custom_column_funding(self, pass_start_year, pass_end_year, **response_dict)
                }.get(data.types_of_funding)()
            response = {'status': 2,
                        'message': 'successfully funding is created.'}
            proj = Project.objects.get(id=int(data.proj_id))
            self.funding_ceo_to_donar_mail(proj, instance)
            self.funding_donar_to_ceo_mail(proj, instance)
        else:
            response.update(errors=stripmessage(serializer.errors))
        return Response(response)


class FundingListing(CreateAPIView):
    queryset = Funding.objects.filter(active=2).order_by('-id')
    serializer_class = ConfigureThematicSerializer

    def post(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = ConfigureThematicSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong', 'data': []}
        if serializer.is_valid():
            proj_id = int(data.proj_id)
            years = request.data.get('years', '')
            funding_ = self.get_queryset().filter(object_id=proj_id).order_by('-id')
            if data.key == '2':
                if data.status != '0':
                    funding_ = funding_.filter(
                        status__id=data.status).order_by('-id')
                if data.renewl_status != '0':
                    funding_ = funding_.filter(
                        probability_status__id=data.renewl_status).order_by('-id')
                if years != '0':
                    budget_years = convert_months_to_years_individual(
                        data.years)
                    data_ = budget_years.split(' - ')
                    data_.sort(key=int)
                    if len(data_) == 1:
                        funding_ = funding_.filter(Q(year__start_year__year=int(
                            data_[0])) & Q(year__end_year__year=int(data_[0])))
                    else:
                        same_year_funding_ = list(funding_.filter(Q(year__start_year__year=int(
                            data_[0])) & Q(year__end_year__year=int(data_[0]))).order_by('-id'))
                        differ_year_funding_ = list(funding_.filter(Q(year__start_year__year=int(
                            data_[0])) & Q(year__end_year__year=int(data_[1]))).order_by('-id'))
                        funding_ = same_year_funding_ + differ_year_funding_
                        funding_.sort(
                            key=lambda x: x.id, reverse=True)
            queryset = [{
                'year': ' - '.join(map(str, f.get_years())),
                'donar': f.donar.name if f.donar else '',
                'from_to': f.get_months(),
                'amount': f.get_total_amount(),
                'status': f.status.name if f.status else '',
                'renewl_status': f.probability_status.name if f.probability_status else '',
                'id': f.id,
                'type_funding': f.types_of_funding
            }
                for f in funding_]
            get_page = ceil(float(len(funding_)) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(queryset, request)
            return paginator.get_paginated_response(result_page, 2, 'Successfully Retreieved', 25, get_page)
        else:
            response.update(errors=unpack_errors(serializer.errors))
            queryset = response
        return Response(queryset)


class FundingDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Funding.objects.filter(active=2).order_by('-id')
    serializer_class = FundingSerializer
    child_class = ConfigureThematic.objects.filter(active=2).order_by('-id')

    @classmethod
    def child_instance(cls, instance):
        child = ''
        child_ = cls.child_class.filter(funding=instance)
        if child_:
            child = child_
        return child

    def perform_destroy(self, instance):
        child = ''
        instance.switch()
        child_ = self.child_class.filter(funding=instance)
        if child_:
            for c in child_:
                c.switch()
                c.thematic.clear()
            child = 'super'
        return child

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        child_ = self.child_instance(instance)
        response = serializer.data
        get_thematic = {}
        get_child_query = []
        get_child_name = []
        if child_:
            child_main = self.child_class.filter(
                funding=instance)
            get_child_query = child_main.values_list(
                'funding_theme__id', flat=True)
            get_child_name = child_main.filter(
                funding=instance).values_list('funding_theme__name', flat=True)
            for gp in get_child_query:
                get_thematic_ids = self.child_class.filter(
                    funding=instance, funding_theme__id=gp)
                get_all_theme = [
                    j.id for tname in get_thematic_ids for j in tname.thematic.filter(active=2)]
                get_thematic[gp] = get_all_theme
        get_thematic_ = list(chain.from_iterable(get_thematic.values()))
        get_thematic_years = {0: lambda instance: (instance.year.start_year.strftime('%Y-%m-%d'), instance.year.end_year.strftime('%Y-%m-%d')),
                              1: lambda instance: (instance.year.start_year.strftime("%b %Y") + ' - ' + instance.year.end_year.strftime("%b %Y"), 0),
                              2: lambda instance: (instance.year.start_year.strftime('%Y-%m'), instance.year.end_year.strftime('%Y-%m'))}
        start, end = get_thematic_years.get(
            instance.types_of_funding)(instance)
        if get_thematic_:
            response['line_item_id'] = get_thematic_
            response['theme_id'] = get_child_query
            response['theme_name'] = get_child_name
            response['start_year'] = start
            response['end_year'] = end
            response['type_funding_name'] = instance.get_types_of_funding_display()
            response['remarks'] = instance.get_remarks()
        else:
            response['line_item_id'] = []
            response['theme_id'] = []
            response['theme_name'] = []
            response['start_year'] = start
            response['end_year'] = end
            response['type_funding_name'] = instance.get_types_of_funding_display()
            response['remarks'] = []
            response['probability_status'] = 0
            response['status'] = 0
        return Response(response)

    def put(self, request, *args, **kwargs):
        """
        API to Update the Funding.
        ---
        parameters:
        - name: thematic_id
          description: Pass thematic ids
          required: true
          type: string
          paramType: form
        - name: remarks
          description: Pass remarks
          required: true
          type: string
          paramType: form
        - name: line_item_id
          description: Pass line items
          required: true
          type: string
          paramType: form
        """
        data = Box(request.data)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            instance = serializer.save()
            fun_remark = FundingRemark.objects.create(funding=instance, status=instance.status,
                                                      probability_status=instance.probability_status, remarks=data.remarks)
            get_creat = FundingCreate()
            proj_loc = get_creat.get_line_theme_dict(
                data.line_item_id, data.thematic_id, fun_remark.funding.object_id)
            ConfigureThematic.objects.filter(funding=instance).delete()
            for key, value in proj_loc.items():
                if value:
                    configfun, created = ConfigureThematic.objects.get_or_create(active=2,
                                                                                 funding=instance, funding_theme_id=int(key))
                    configfun.thematic.clear()
                    configfun.thematic.add(*value)
                    fun_log = FundingLogging.objects.create(
                        fund_remark=fun_remark, funding_theme_id=int(key))
                    fun_log.funding_budget.add(*value)
            response = {'status': 2,
                        'message': 'Successfully Updated the data.'}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class DPFProjectViewDetail(CreateAPIView):
    queryset = Project.objects.filter(active=2)
    serializer_class = DFPProjectViewDetailSerializer

    def post(self, request):
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went wrong'}
        serializer = DFPProjectViewDetailSerializer(data=data.to_dict())
        if serializer.is_valid():

            proj = Project.objects.filter(id=data.proj_id)
            if proj:
                p = proj[0]
                p_id = p.program.partner
                if p_id:
                    part = Partner.objects.get(active=2, id=p_id.id)
                    response = {'status': 2,
                                'message': 'Successfully retrieved'}

                    part_region_name = part.region.name if part.region else ''

                    part_state_name = part.state.name if part.state else ''

                    part_nature_of_partner_name = part.nature_of_partner.name if part.nature_of_partner else ''

                    part_status_name = part.status.name if part.status else 'N/A'

                    response.update(partner_id=part.id,
                                    region_name=part_region_name,
                                    state_name=part_state_name,
                                    nature_of_partner_name=part_nature_of_partner_name,
                                    status_name=part_status_name,)
                else:
                    response.update(
                        error='No Partner Avaiable for this %(p_id)s' % request.data)
            else:
                response.update(
                    error='No Project Avaiable for this %(p_id)s' % request.data)
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class GetDateToYearPartner(CreateAPIView):
    serializer_class = DFPProjectViewDetailSerializer

    def post(self, request):
        """
        To Get Partner Support Since and Support to date and Name.
        """
        data = request.data
        serializer = DatetoYearSerializerThematic(data=data)
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            proj_id = int(data.get('proj_id'))
            proj = Project.objects.filter(id=proj_id)
            if proj:
                p = proj[0]
                start_year = p.program.partner.support_from
                end_year = p.program.partner.support_to
                if start_year and end_year:
                    response = {
                        'status': 2, 'message': 'Successfully retrieved the data.', 'fund_type': 0}
                    fund_ = list(set(Funding.objects.filter(
                        active=2, object_id=proj_id).values_list('types_of_funding', flat=True)))
                    if fund_ and 0 not in fund_:
                        
                        response['fund_type'] = 2
                    start, end = start_year.year, end_year.year
                    config = '{0}'.format(p.program.partner.name)
                    support = 'CRY Supports: From {0} to {1}'.format(
                        start, end)
                    response.update(support=support, config=config)
            else:
                response.update(errors='Project Doesn\'t Exists for this id')
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)
