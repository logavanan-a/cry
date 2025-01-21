"""API for DashBoard."""
from operator import add
from django.contrib.auth.models import (User,)
from rest_framework.generics import (CreateAPIView)
from rest_framework.views import APIView
from rest_framework.response import Response
from box import Box
from masterdata.models import (MasterLookUp,Boundary,)
from partner.models import (Partner,)
from beneficiary.models import (Beneficiary,)
from facilities.models import (Facility,)
from userroles.models import (RoleTypes, UserRoles,UserPartnerMapping,)
from .models import (DashBoardResponse, Frequence)
from .serializers import (UsersDashBoard, FrequenceUsersDashBoard)
from .views.survey_views import get_user_partner
from userroles.views import GetUserRegionalPartners
from copy import copy
import numpy as np

class GetDashboardData(APIView):

    def post(self,request):
        """
        DashBoard api
        ---
        parameters:
        - name: user_id
          description: user id to tag the partner
          required: true
          type: integer
          paramType: integer
        - name: partners
          description: pass partner ids in list
          required: false
          type: list
          paramType: list
        - name: frequency
          description: pass frequency here
          required: false
          type: integer
          paramType: integer
        """
        user_id = request.data.get('user_id')
        partner_set = Partner.objects.filter(active=2)
        partner = partner_set.filter(id__in = eval(request.data.get('partners'))) or self.get_partners(user_id)
        frequency = request.data.get('frequency') or 2
        freq = [ {'id':i.id,'duration':str(i)} for i in Frequence.objects.filter(active=2)]
        dbr = DashBoardResponse.objects.filter(partner__in=partner , periodicity = frequency)
        if dbr.count() == 1:
            dbr = dbr[0]
            resp = {'status':2,'req_data':request.data,'freq':freq,'regional':[],
                    'state':[],
                    'data':{'partner_level':dbr.partner_level,'chart_graph': [
                {'chartdata': dbr.chartdata},],
            'user_summary': dbr.user_summary}}
            return Response(resp)

        partner_level = self.get_processed(dbr,**{'data':"one_dbr.partner_level.get('data')",'key':'name','remove_keys':[]})

        chart_data_bodylist = self.get_processed(dbr,**{'data':"one_dbr.chartdata.get('table_data')['bodylist']",'key':'Indicator','remove_keys':[]})
        chart_data_data = self.get_processed(dbr,**{'data':"one_dbr.chartdata.get('data')",'key':'name','remove_keys':['others_backgroundColor','backgroundColor']})
        chart_data_data = self.calculate_percentage(**{'data':chart_data_data,'data1':'actual','data2':'total','replacer':'percentage'})

        facility_bodylist = self.get_processed(dbr,**{'data':"one_dbr.facility.get('table_data')['bodylist']",'key':'Indicator','remove_keys':[]})
        facility_data = self.get_processed(dbr,**{'data':"one_dbr.facility.get('data')",'key':'name','remove_keys':['others_backgroundColor','backgroundColor']})
        facility_data = self.calculate_percentage(**{'data':facility_data,'data1':'actual','data2':'total','replacer':'percentage'})

        beneficiary_bodylist = self.get_processed(dbr,**{'data':"one_dbr.beneficiary.get('table_data')['bodylist']",'key':'Indicator','remove_keys':[]})
        beneficiary_data = self.get_processed(dbr,**{'data':"one_dbr.beneficiary.get('data')",'key':'name','remove_keys':['others_backgroundColor','backgroundColor']})
        beneficiary_data = self.calculate_percentage(**{'data':beneficiary_data,'data1':'actual','data2':'total','replacer':'percentage'})

        user_summary = []
        for i in dbr:
            user_summary.extend(i.user_summary.get('table_data').get('bodylist'))

        dbr = dbr[0]
        dbr.partner_level['data'] = partner_level

        dbr.chartdata.get('table_data')['bodylist'] = chart_data_bodylist
        dbr.chartdata['data'] = chart_data_data

        dbr.facility.get('table_data')['bodylist'] = facility_bodylist
        dbr.facility['data'] = facility_data

        dbr.beneficiary.get('table_data')['bodylist'] = beneficiary_bodylist
        dbr.beneficiary['data'] = beneficiary_data

        dbr.user_summary.get('table_data')['bodylist'] = user_summary
        resp = {'status':2,'req_data':request.data,'freq':freq,'regional':[],
                'partner':partner.values('id','name','state'),
                'states':Boundary.objects.filter(active=2,id__in=partner.values_list('state',flat=True)).values('id','name'),
                'data':{'partner_level':dbr.partner_level,'chart_graph': [
            {'chartdata': dbr.chartdata},],
        'user_summary': dbr.user_summary}}
        return Response(resp)

    def get_partners(self,user_id):
        user_role = UserRoles.objects.get(user__id=user_id)
        if user_role.user_type == 2:
            return [user_role.partner]
        elif user_role.user_type == 1:
            return Partner.objects.filter(active = 2)
        else:
            return UserPartnerMapping.objects.get(user_id=user_id).partner.all()

    def add_columns(self,*args,**kwargs):
        data = kwargs.get('data')
        if len(data) > 0:
            keys = sorted(data[0].keys())
            if kwargs.get('remove_keys'):
                for i in kwargs.get('remove_keys'):
                    keys.remove(i)
            sorted_keys = copy(keys)
            array_values = {}
            array_keys = []
            keys.remove(kwargs.get('key'))
            for d in data:
                one_record = []
                one_indicator = d[kwargs.get('key')]
                array_keys.append(one_indicator)
                for k in keys:
                    one_record.append(d[k])
                array_values[one_indicator]=one_record
        return array_values,sorted_keys,sorted(array_keys)

    def arrange_in_matrix(self,*args,**kwargs):
        data = kwargs.get('data')
        key_order = kwargs.get('keys')
        order = [data[i] for i in key_order]
        return order

    def send_in_order(self,data):
        if len(data) == 1:
            return data
        elif len(data) == 2:
            return self.add_two_matrix(**{'array1':data[0],'array2':data[1]})
        else:
            count = 2
            first_set = self.add_two_matrix(**{'array1':data[0],'array2':data[1]})
            while count < len(data):
                first_set = self.add_two_matrix(**{'array1':first_set,'array2':data[count]})
                count = count +1
            return first_set

    def add_two_matrix(self,*args,**kwargs):
        return (np.array(kwargs.get('array1'))+np.array(kwargs.get('array2'))).tolist()

    def get_processed(self,dbr,*args,**kwargs):
        sum_list = []
        sorted_keys = {}
        query = copy(kwargs)
        a=b=c=None
        for one_dbr in dbr:
            query['data']=eval(kwargs.get('data'))
            resolver = kwargs.get('key')
            a,b,c = self.add_columns(**query)
            sorted_keys[resolver] = c
            arranged_matrix = self.arrange_in_matrix(**{'data':a,'keys':c})
            sum_list.append(arranged_matrix)
        processed = self.send_in_order(sum_list)

        for i,j in enumerate(processed):
            processed[i].insert(b.index(resolver),c[i])
            proc_dic = {}
            if kwargs.get('remove_keys'):
                proc_dic['backgroundColor']='#ffdd55'
                proc_dic['others_backgroundColor']=''
            for k,l in enumerate(b):
                proc_dic[l]=processed[i][k]
            processed[i] = proc_dic
        return processed

    def calculate_percentage(self,*args,**kwargs):
        data = kwargs.get('data')
        for i,j in enumerate(data):
            try:
                data[i][kwargs.get('replacer')] = (data[i][kwargs.get('data1')])*100/data[i][kwargs.get('data2')]
            except:
                data[i][kwargs.get('replacer')] = 0
        return data
