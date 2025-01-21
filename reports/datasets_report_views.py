from django.shortcuts import render,HttpResponse,HttpResponseRedirect
from survey.models import Survey,Block,Question,Choice,JsonAnswer
from userroles.models import UserRoles
from beneficiary.models import Beneficiary,BeneficiaryType
from facilities.models import Facility
from masterdata.models import Boundary
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.response import Response
from survey.views.survey_views import  get_user_partner_list
from masterdata.views import CustomPagination
from common_methods import *
import psycopg2
from django.http import JsonResponse
from django.db import connection
from django.utils.encoding import smart_str
from ccd.settings import DATABASES
from ccd.settings import FY_YEAR,BASE_DIR,HOST_URL
from datetime import datetime 
from .models import AggregateReportConfig
import unicodecsv as csv
from io import BytesIO








def famly_info(sql):
    conn = psycopg2.connect(database=DATABASES.get('default').get('NAME'),user=DATABASES.get('default').get('USER'),password=DATABASES.get('default').get('PASSWORD'),host=DATABASES.get('default').get('HOST'))#ccd_demo29oct
    cursor = conn.cursor()
    cursor.execute(sql)
    nofam = cursor.fetchall()
    conn.close()
    return nofam


class ExportReportDataSets(APIView):
    def get(self,request,id,uid):
        #import ipdb; ipdb.set_trace()
        report_id = id
        user_id = uid
        
        res = export_report(report_id,user_id,request)
        return Response(res)
        
        


def export_report(report_id,partner_list,request):
    dd = datetime.today()
    aggregate = AggregateReportConfig.objects.get(id = report_id)
    sql = eval(aggregate.report_name)['sql_query']
    report_name =  eval(aggregate.report_name)['report_name']
    export_data = {'data': sql , 'report_name' : report_name}
    headers = aggregate.custom_sqlquery_config.get('header')
    if request.GET.get('pid') and request.GET.get('qid') and request.GET.get('yid'):
        pid = eval(request.GET.get('pid'))
        sql = sql + ' where partner_id in (' + ','.join(map(str, pid)) + ')'
    #export_file = open(BASE_DIR+"/static/response_csv/"+export_data.get('report_name')+'_Report_'+ str(dd.strftime('%d-%m-%Y-%I:%M:%p'))+'.csv','w')
    main_file = "/static/response_csv/"+export_data.get('report_name')+'_Report_'+ str(dd.strftime('%d-%m-%Y-%I:%M:%p'))+'.csv'
    file_path = BASE_DIR+main_file
    download_path = HOST_URL+main_file
    with open(file_path, 'w+') as f:
        sqldata = famly_info(sql)
        #response = HttpResponse(content_type='text/csv')
        #response['Content-Disposition'] = 'attachment; filename='+file_name
        export_writer = csv.writer(f , encoding='utf-8')
        #res_keys = export_data.get('headers').keys()
        #head_values = [export_data.get('headers').get(ke) for ke in res_keys]
        #import ipdb; ipdb.set_trace()
        #export_writer.writerow(head_values)
        export_writer.writerow(headers)
        for i in sqldata:
			lisj = list(i)
			lisj.pop(0)
			export_writer.writerow(lisj)
        #file_name = str(export_file.name).split('/')[-1]
    return {'status':2,'download':download_path}


    

#        
        
             
        
#        
#try:
#            data = mutant_class.objects.filter(partner_id__in=partner_list).values(*fields_dict.keys())
#        except:
#            data = mutant_class.objects.all().values(*fields_dict.keys())
#        if request.GET.get('pid') and request.GET.get('qid') and request.GET.get('yid'):
#            qmnth = request.GET.get('qid')
#            qyr = request.GET.get('yid')
#            fcn_yr = get_fincal_yr(qmnth,qyr)
#            data = data.filter(partner_id__in=eval(request.GET.get('pid')),financial_month_year=fcn_yr)
#            data = data.filter(partner_id__in=eval(request.GET.get('pid')))

#    
#return {'status':2,'data':data,'headers':fields_dict,'report_name':aggregate_report.report_name,'dl_name':aggregate_report.mutant_app_table.model}

    
            
        
        
        
        
#partner_list = [partner.id for partner in partner_list]
#        aggregate_report = AggregateReportConfig.objects.get(id=report_id)
#        mutant_class = aggregate_report.mutant_app_table.model_class()
#        fields_dict = {}
        
