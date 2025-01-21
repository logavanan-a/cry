import re
from math import ceil
import calendar
from datetime import date
import datetime
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from .models import *
from .serializers import *
from django.db.models import Q
from survey.models import Survey,JsonAnswer
from masterdata.views import CustomPagination
from survey.views.survey_views import *
from survey.views.custom_dates import CustomDates
import sys

# Create your views here.
class DListing(APIView):
    def post(self,request):
        """
        DListing view.
        ---
        parameters:
        - name: model_name
          description: Pass model name
          required: true
          type: string
          paramType: string
        """
        try:
            model_class = ContentType.objects.get(model=request.data.get('model_name'))
            res = {}
            fields = DynamicListing.objects.get(model_name=model_class).listing_fields
            values_list = model_class.model_class().objects.filter(active=2).custom_values(fields)
            res['headers'] = fields
            res['display_headers'] = [ re.sub("[_-]"," ",i).title() for i in fields]
            res['data'] = values_list
        except Exception as e:
            res = {"error":e.message}
        return Response(res)

# this should support new changes
class DFiltering(APIView):
    def post(self,request):
        """
        DListing view.
        ---
        parameters:
        - name: filter_id
          description: Pass model name
          required: true
          type: string
          paramType: string
        """
        try:
            res = {}
            df = DynamicFilter.objects.get(id=request.data.get('filter_id'))
            model_class = df.model_name
            query_list = df.filtering_query
            fields = DynamicListing.objects.get(model_name__id=model_class.id).listing_fields
            conditional_query = []
            filter_query = {}
            for qry in query_list:
                if type(qry) == list:
                    conditional_query.append(eval(qry[0]))
                else:
                    filter_query.update(qry)
            values_list = model_class.model_class().objects.filter(*conditional_query,active=2,**filter_query).custom_values(fields)
            res['headers'] = fields
            res['display_headers'] = [ re.sub("[_-]"," ",i).title() for i in fields]
            res['data'] = values_list
        except Exception as e:
            res = {"error":e.message}
        return Response(res)

class DCreate(APIView):
    def post(self,request):
        """
        ---
        parameters:
        - name: model_name
          description: pass model name
          required: true
          type: string
          paramType: string
        - name : listing_fields
          description: pass listing
          required: true
          type : JSON
          paramType: JSON
        """

        return Response({"status":"success "})

class ModelFields(APIView):
    def post(self,request):
        """
        ---
        parameters:
        - name: model_name
          description: paas model_name to get fields
          required: true
          type: string
          paramType: string
        """

        fields = get_model_fields(request.data.get('model_name'))
        res = {}
        if fields.get("fields"):
            fields = [{"name":i,"label":re.sub("[_-]"," ",i).title()}for i in fields.get("fields")]
            res = {"data":fields}
        res = fields
        return Response(res)

class ModelFilterCreate(APIView):
    def post(self,request):
        """
        ---
        parameters:
        - name: model_name
          description: pass model name here
          required: true
          type: string
          paramType: string
        - name: querybuilder
          description: pass Json structure
          required: true
          type: JSON
          paramType: JSON
        - name: query_name
          description: name for query
          required: true
          type: string
          paramType: string
        """
        q_filter = create_query_dict(request.data.get('querybuilder'))
        return Response({"filter":q_filter})


def get_model_fields(model_name):
    try:
        model_class = ContentType.objects.get(model=model_name)
        return {"fields":model_class.model_class()._meta.get_all_field_names()}
    except:
        return {"error":"Model does'nt exist"}

def create_query_dict(js):
    raw_query = eval(js).get('rules')
    combinator = eval(js).get('combinator')
    q_list = []
    for i in raw_query:
        if not i.get('rules'):
            q_list.append("Q(**{'"+i.get('field')+"__"+i.get('operator')+"':'"+i.get('value')+"'})")
    if combinator == 'None':
        combinator = "|"
    query_string = q_list[0]+str(combinator)+q_list[1]
    return query_string

class GetFilteringFields(APIView):
    def post(self,request):
        """
        API to get the filtering fields
        ---
        parameters:
        - name: model_name
          description: pass model name to get the filtering fields
          required: true
          type: string
          paramType: string
        - name: object_id
          description: pass object id for getting the sub type
          required: true
          type: integer
          paramType: integer
        """
        try:
            model_class = ContentType.objects.get(model=request.data.get('model_name'))
            dynamic_field_obj = DynamicField.objects.get(model_name=model_class,object_id=request.data.get('object_id'))
            filtering_fields = dynamic_field_obj.model_fields
            conditions_list = [
                {'name': 'null', 'label': 'Is Null'},{'name': 'notNull', 'label': 'Is Not Null'},
                {'name': '__in', 'label': 'In'},{'name': 'notIn', 'label': 'Not In'},
                {'name': '__istartswith', 'label': 'Start With'},{'name': '__icontains', 'label': 'Contains'},
                {'name': '__iendwith', 'label': 'End With'},{'name': '', 'label': 'Equals To'},
                {'name': '!=', 'label': 'Not Equal'},{'name': '__lt', 'label': 'Lesser Than'},
                {'name': '__gte', 'label': 'Greather Than Equal'},{'name': '__lte', 'label': 'Less Than Equal'},
                {'name': '__gt', 'label': 'Greather Than'},
            ]
            query_list = [{'name':'','label':'None'}]

            return Response({'status':2,'filtering_fields':filtering_fields,\
            'conditions_list':conditions_list,'query_list':query_list,\
            'model_name':str(model_class),'sub_type':str(dynamic_field_obj.content_type.model) if dynamic_field_obj.content_type else "",'object_id':dynamic_field_obj.object_id})
        except Exception as e:
            return Response({'status':0,'message':e.message})

class CreateFilterQuery(APIView):
    def post(self,request):
        """
        API to create the filter criteria
        ---
        parameters:
        - name: model_name
          description: pass model name to create the criteria query
          required: true
          type: string
          paramType: string
        - name: object_id
          description: pass the model id for which the criteria belongs to
          required: true
          type: integer
          paramType: integer
        - name: query_name
          description: pass the name for the criteria query
          required: true
          type: string
          paramType: string
        - name: criteria_query
          description: pass the json query here
          required: true
          type: Json
          paramType: Json
        """
        try:
            model_class = ContentType.objects.get(model=request.data.get('model_name'))
            dynamic_query = []
            criteria_query = eval(request.data.get('criteria_query'))
            for query in criteria_query:
                if not query.get('rules'):
                    dynamic_query.append({query.get('field')+query.get('operator'):query.get('value')})
                else:
                    combination_query = query.get('rules')
                    combination_list = []
                    for cq in combination_query:
                        combination_list.append("Q(**{'"+cq.get('field')+cq.get('operator')+"':'"+cq.get('value')+"'})")
                    dynamic_query.append([query.get('combinator').join(combination_list)])
            DynamicFilter.objects.create(filter_name=request.data.get('query_name'),
            model_name=model_class,filtering_query=dynamic_query,object_id=int(request.data.get('object_id')))
            return Response({'status':2,'message':'Filter criteria created successfully'})
        except Exception as e:
            return Response({'status':0,'message':e.message})

class FiltersAvailable(APIView):
    def get(self,request,model_name,object_id):
        model_class = ContentType.objects.get(model=model_name)
        df_list = DynamicFilter.objects.filter(model_name=model_class,active=2,object_id=object_id).values("id","filter_name")
        return Response({"filter_list":df_list})


class ListingsAvailable(APIView):
    def get(self,request,model_name,object_id):
        model_class = ContentType.objects.get(model=model_name)
        df_list = DynamicListing.objects.filter(model_name=model_class,active=2,object_id=object_id).values("id","listing_name")
        return Response({"dynamic_list":df_list})

class ModelField(APIView):
    def get(self,request,model_name,object_id):
        model_class = ContentType.objects.get(model=model_name)
        df_list = DynamicField.objects.get(model_name=model_class,object_id=object_id).model_fields
        return Response({"model_class":df_list})

class ModelFilterResult(APIView):
    def post(self,request):
        """
        API to get the filter result
        ---
        parameters:
        - name: model_class
          description: pass the name for the criteria query
          required: true
          type: string
          paramType: string
        - name: object_id
          description: pass the sub type id
          required: true
          type: integer
          paramType: integer
        - name: filter_condition
          description: pass the filter condition here
          required: true
          type: json
          paramType: json
        - name: listing_condition
          description: pass the listing condition here
          required: true
          type: json
          paramType: json
        - name: survey_condition
          description: pass the list of survey ids
          required: true
          type: json
          paramType: json
        - name: sorting_condition
          description: pass sorting condition here
          required: true
          type: json
          paramType: json
        - name: user_id
          description: pass user id here
          required: true
          type: integer
          paramType: integer
        """
        try:
            model = ContentType.objects.get(model=request.data.get('model_class'))
            partners = ModelFilterResult.get_user_partner_list(request.data.get('user_id'))
            model_helper = {"facility":"facility_type__id","beneficiary":"beneficiary_type__id"}
            model_filter_helper = {}
            survey_condition = request.data.get('survey_condition')

            if model_helper.has_key(request.data.get('model_class')):
                model_filter_helper = {model_helper.get(request.data.get("model_class")):request.data.get("object_id")}
                model_filter_helper = {'partner__id__in':partners}
            conditional_query = []
            filter_query = {}
            order_condition = []
            filter_query.update(model_filter_helper)
            if eval(eval(request.data.get('filter_condition')).get('df_status')):
                #change here to filter the query dynamically
                #change the get functionality to convert the query
                #df = DynamicFilter.objects.get(id=eval(request.data.get('filter_condition')).get('filter_condition'))
                #query_list = df.filtering_query
                # call the functionality here
                query_list = ModelFilterResult.query_converted(eval(request.data.get('filter_condition')).get('filter_condition'))
                for qry in query_list:
                    if type(qry) == list:
                        conditional_query.append(eval(qry[0]))
                    else:
                        filter_query.update(qry)
            order_condition.append(eval(request.data.get('sorting_condition')).get('sorting_condition'))

            fields_list = DynamicListing.objects.get(id=eval(request.data.get('listing_condition')).get('listing_condition')).listing_fields  if eval(eval(request.data.get('listing_condition')).get('dl_status')) else eval(request.data.get('listing_condition')).get('listing_condition')
            if not 'id' in fields_list:
                fields_list.insert(0,'id')
            filter_criteria = {}
            res = []
            exclude_criteria = {}
            headers = fields_list
            display_headers = [re.sub("[_-]", " ", i).title() for i in fields_list]
            if eval(survey_condition).get('status'):
                filter_ids = get_filter_survey_response(eval(survey_condition).get('survey_list'),str(request.data.get('model_class')))
                filter_criteria['id__in']=filter_ids
            else:

                filter_ids = get_filter_survey_response(eval(survey_condition).get('survey_list'),
                                                        str(request.data.get('model_class')))
                exclude_criteria['id__in']=filter_ids
            if eval(eval(survey_condition).get('condition')):
                res = model.model_class().objects.filter(**filter_criteria).filter(*conditional_query,**filter_query).order_by(*order_condition).custom_values(fields_list)
            else:
                try:
                    res = model.model_class().objects.filter(*conditional_query,**filter_query).exclude(**exclude_criteria).order_by(*order_condition).custom_values(fields_list)
                except:
                    fields_dict = {}
                    [fields_dict.update({field.name: field.verbose_name}) for field in model.model_class()._meta.get_fields() if field.name in fields_list]
                    fields_dict = [field.name for field in model.model_class()._meta.get_fields() if field.name in fields_list]
                    res= model.model_class().objects.filter(*conditional_query,**filter_query).exclude(**exclude_criteria).order_by(*order_condition).values(*fields_list)
                    headers = fields_dict
            data = res
            get_page = ceil(float(len(data)) / float(10))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(data, request)
            data = paginator.get_paginated_response(result_page, 2,'retrieved successfully', 34,  get_page).data
            data['headers'] = headers
            data['display_headers'] = display_headers
            return Response(data)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return Response({'status':0,'error':exc_tb.tb_lineno,'message':e.message})

    @staticmethod
    def query_converted(query_exp):
        dynamic_query = []
        criteria_query = query_exp
        for query in criteria_query:
            if not query.get('rules'):
                dynamic_query.append({query.get('field')+query.get('operator'):query.get('value')})
            else:
                combination_query = query.get('rules')
                combination_list = []
                for cq in combination_query:
                    combination_list.append("Q(**{'"+cq.get('field')+cq.get('operator')+"':'"+cq.get('value')+"'})")
                dynamic_query.append([query.get('combinator').join(combination_list)])
        return dynamic_query

    @staticmethod
    def get_user_partner_list(u_id):
        partner = UserRoles.objects.get(user__id=u_id).partner
        if partner:
            return [partner.id]
        else:
            try:
                return UserPartnerMapping.objects.get(user__id=u_id).partner.filter(active=2).all().values_list('id',flat=True)
            except:
                return []

# Function to get the survey responses of the filter
def get_filter_survey_response(survey_list=None,cluster=None):

    surveys = Survey.objects.filter(id__in=survey_list)
    current_date = datetime.now()

    # calling_methods = {'3':month_range(current_date),
    #                    '4':get_quarter_dates(current_date),
    #                    '5':get_half_yearly_dates(current_date),
    #                    '6':get_yearly_months()
    #                    }

    calling_methods = {'3': CustomDates().previous_month_days(),
                       '4': CustomDates().get_fy_last_quarter(int(FY_YEAR)),
                       '5': CustomDates().current_fy_half_year(),
                       '6': CustomDates().fy_dates(int(FY_YEAR) - 1)}
    all_responses = []
    for srvy in surveys:
        dates = calling_methods.get(srvy.piriodicity)
        date_range = [dates.get('start_date').strftime('%Y-%m-%d'),dates.get('end_date').strftime('%Y-%m-%d')]
        response_ids = []
        responses = JsonAnswer.objects.filter(survey=srvy,created__range=date_range,active=2).custom_values([cluster])
        for i in responses:
            try:
                response_ids.append(i.get(cluster).get('id'))
            except:
                pass
        all_responses.append(response_ids)
    result = list_comprehension_intersection(all_responses)
    return result

def list_comprehension_intersection(list_comp=None):
    unique_set = []
    for one_list in list_comp:
        for one_element in one_list:
            if not one_element in unique_set:
                unique_set.append(one_element)
    return unique_set


# To get the quarter of the month
# Pass the date object to the function
def get_quarter(date):
    return (int(date.strftime('%m'))-1)//3+1


# function to get the last date and starting date of the month
def month_range(today_date):
    year = today_date.strftime('%Y')
    month = today_date.strftime('%m')
    _,_last = calendar.monthrange(int(year),int(month))
    first_date = date(int(year), int(month), 1)
    last_date = date(int(year), int(month), int(_last))
    return {"first_date":first_date,"last_date":last_date}

# function to get the quarter months based on the date object
def get_quarter_months(month):
    quarter_range = {1:[1,2,3],2:[4,5,6],3:[7,8,9],4:[10,11,12]}
    return quarter_range[get_quarter(month)]

def get_quarter_dates(month):
    months_range = get_quarter_months(month)
    first_month = date(int(datetime.now().strftime('%Y')),min(months_range),1)
    last_month = date(int(datetime.now().strftime('%Y')),max(months_range),1)
    return {"first_date":month_range(first_month).get('first_date'),
    "last_date":month_range(last_month).get('last_date')}

def get_half_yearly_dates(month):
    if int(month.strftime('%m'))<= 6:
        first_date = date(int(month.strftime('%Y')),1,1)
        last_date = date(int(month.strftime('%Y')),6,30)
        return {"first_date":first_date,"last_date":last_date}
    else:
        first_date = date(int(month.strftime('%Y')),7,1)
        last_date = date(int(month.strftime('%Y')),12,31)
        return {"first_date":first_date,"last_date":last_date}

def get_last_half_yearly_dates(month):
    if int(month.strftime('%m'))<= 6:
        first_date = date(int(month.strftime('%Y'))-1,7,1)
        last_date = date(int(month.strftime('%Y'))-1,12,31)
        return {"first_date":first_date,"last_date":last_date}
    else:
        first_date = date(int(month.strftime('%Y')),1,1)
        last_date = date(int(month.strftime('%Y')),6,30)
        return {"first_date":first_date,"last_date":last_date}

def get_yearly_months():
    return {"first_date":date(int(datetime.now().strftime('%Y')),1,1),
    "last_date":date(int(datetime.now().strftime('%Y')),12,31)}

def get_last_yearly_months():
    return {"first_date":date(int(datetime.now().strftime('%Y'))-1,1,1),
    "last_date":date(int(datetime.now().strftime('%Y'))-1,12,31)}

def get_last_month_date():
    current_year = int(datetime.now().strftime('%Y'))
    current_month = int(datetime.now().strftime('%m'))
    _,_last = calendar.monthrange(int(current_year),int(current_month))
    last_month_date = date(int(current_year), int(current_month), int(_last))
    return last_month_date

def get_last_quarter_months(last_month):
    quarter_range = {1:[1,2,3],2:[4,5,6],3:[7,8,9],4:[10,11,12]}
    if get_quarter(last_month) == 1:
        return quarter_range[4]
    return quarter_range[get_quarter(last_month)-1]

def get_last_quarter_dates(last_month):
    months_range = get_last_quarter_months(last_month)
    year = int(datetime.now().strftime('%Y'))
    if get_quarter(last_month) == 1:
        year = int(datetime.now().strftime('%Y')) - 1
    first_month = date(year,min(months_range),1)
    last_month = date(year,max(months_range),1)
    return {"first_date":month_range(first_month).get('first_date'),
    "last_date":month_range(last_month).get('last_date')}
