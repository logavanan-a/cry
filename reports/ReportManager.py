from beneficiary.models import *
from facilities.models import *
from partner.models import *
from masterdata.models import *
from userroles.models import *
from survey.models import *
from survey.views.custom_dates import CustomDates
from django.contrib.contenttypes.models import ContentType
from ccd.settings import FY_YEAR,BASE_DIR
from .models import AggregateReportConfig
from common_methods import *
import csv
import sys

class ReportManager():
    def get_basic_info(self, *args, **kwargs):
        try:
            kwarg = {'model': 'beneficiary',
             'model_filter_value':'4',
             'model_filter_field':'beneficiary_type_id',
             'required_fields':['boundary_id', 'partner',
                               'age', 'gender', 'name',
                                'id'],
             'boundary_levels':[3,4],
            'boundary_helper':{
                                  3: 'District',
                                  4: 'Block',
                                  7: 'Village'},
             'model_filter':{},
            }
            content_type = ContentType.objects.get(model=kwargs.get('model'))
            #Optimize the errors - from
            #filter_condition = {kwargs.get('model_filter_type'): kwargs.get('model_filter_value')}
            #filter_result = content_type.model_class().objects.filter(**filter_condition).custom_values(kwargs.get('required_fields'))
            ids = [((i.cluster[0].values())[0]).get('id') for i in JsonAnswer.objects.filter(active=2,survey_id__in=kwargs.get('surveyid'))] # optimize
            filter_result = content_type.model_class().objects.filter(id__in=ids).custom_values(kwargs.get('required_fields')) # optimize
            #Optimize the errors - to
            if kwargs.get('age'):
                filter_result = self.filter_json_age(**{'query_set':filter_result,
                                'min_age':kwargs.get('age').get('min_age'),
                                'max_age':kwargs.get('age').get('max_age')})
            #filter_result = [self.add_boundary_info(i) for i in filter_result]
            return filter_result
        except Exception as e:
            print "get_basic_info "+e.message
            return None

    def get_survey_info(self, *args, **kwargs):
        try:
            kwarg = {'survey_id': [48],
                      'cluster_type': 'beneficiary',
                      'cluster_id': '',
                      'question_filter':['249','254','255']}
            #print "cluster ",kwargs.get('cluster_id')
            if kwargs.get('survey_filter'):
                if not self.cluster_criteria_filter(**kwargs):
                    return {}
            responses = {}
            for i in kwargs.get('survey_id'):
                survey = Survey.objects.get(id=i)
                calling_methods = {'3': CustomDates().current_month_days(),
                                   '4': CustomDates().current_fy_quarter_dates(),
                                   '5': CustomDates().current_fy_half_year(),
                                   '6': CustomDates().fy_dates(int(FY_YEAR))}
                dates = calling_methods.get(survey.piriodicity)
                cluster_info = {"cluster__0__" + kwargs.get("cluster_type") + "__id": int(kwargs.get("cluster_id"))}

                if kwargs.get(i).get('question_filter'):
                    cluster_info.update({'response__contains':kwargs.get(i).get('question_filter')})

                response = JsonAnswer.objects.filter(active=2,survey=survey, created__gte=dates.get('start_date'),
                  created__lte=dates.get('end_date'), **cluster_info).custom_values(kwargs.get(i).get('question_list'))
                if response:
                    responses.update(response[0])
            return responses
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print " " + str(exc_tb.tb_lineno)
            print " get_survey_info "+e.message
            return None

    def cluster_criteria_filter(self,**kwargs):
        try:
            status = False
            for i in kwargs.get('survey_filter').keys():
                survey = Survey.objects.get(id=i.replace(" ",""))

                calling_methods = {'3': CustomDates().current_month_days(),
                                   '4': CustomDates().current_fy_quarter_dates(),
                                   '5': CustomDates().current_fy_half_year(),
                                   '6': CustomDates().fy_dates(int(kwargs.get('survey_filter').get('year')) if kwargs.get('survey_filter').get('year') else int(FY_YEAR))}
                dates = calling_methods.get(survey.piriodicity)
                cluster_info = {"cluster__0__" + kwargs.get("cluster_type") + "__id": int(kwargs.get("cluster_id"))}
                exclusion_filter = {}
                try:
                    exclusion_filter = kwargs.get('survey_filter').get(i).get('exclusion_filter')
                except:
                    exclusion_filter = {}
                if kwargs.get('survey_filter').get(i).get('question_filter'):
                    cluster_info.update({'response__contains':kwargs.get('survey_filter').get(i).get('question_filter')})
                response = None
                if exclusion_filter:
                    response = JsonAnswer.objects.filter(active=2,survey=survey, created__gte=dates.get('start_date'),created__lte=dates.get('end_date'), **cluster_info).exclude(**exclusion_filter)
                else:
                    response = JsonAnswer.objects.filter(active=2,survey=survey, created__gte=dates.get('start_date'),created__lte=dates.get('end_date'), **cluster_info)
                if response:
                    status = True
            return status
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print " "+str(exc_tb.tb_lineno)
            print "cluster_criteria "+e.message
            return False


    def info_combinor(self):
        try:
            report_id = raw_input("Enter the AggregateReportConfig id:")
            for report_config in AggregateReportConfig.objects.filter(id__in=[report_id]):
                model_config = report_config.model_config
                survey_configs = report_config.survey_config
                model_config['surveyid']=survey_configs.get('survey_id') ## added for filter beneficairy based on responses
                print " survey config ",survey_configs
                for i in self.get_basic_info(**model_config):
                    survey_configs['cluster_id']=i.get('id')
                    res = self.get_survey_info(**survey_configs)
                    if res:
                        i = self.add_boundary_info(i)
                        del i['address']
                        i['partner_id'] = i['partner_id'] #i['partner_id'][0]
                        i['beneficiary_id'] = i['id']
                        del i['id']
                        i['age'] = ReportManager.clean_age(i['age'])
                        i['gender'] = ReportManager.clean_gender(i['gender'])
                        i.update(res)
                        print i
                        if report_config.mutant_app_table:
                            obj,stat=report_config.mutant_app_table.model_class().objects.get_or_create(beneficiary_id=i['beneficiary_id'])
                            [setattr(obj,field,i.get(field)) for field in report_config.mutant_app_table.model_class()._meta.get_all_field_names() if field not in ['id','beneficiary_id']]
                            obj.save()
                            print obj
        except Exception as e:
            print e.message
            return None

    def filter_json_age(self, *args, **kwargs):
        child_query = kwargs.get('query_set')
        fil = filter(lambda x:self.age_checker(x,**kwargs),child_query)
        return fil

    @staticmethod
    def clean_gender(gender_value):
        if isinstance(gender_value,list):
            return ','.join(gender_value)
        else:
            return gender_value


    @staticmethod
    def clean_age(age_value):
        if isinstance(age_value,list):
            return float(age_value[0])
        else:
            return float(age_value)


    def age_checker(self,obje,**kwargs):
        try:
            min_age = float(kwargs.get('min_age'))
            max_age = float(kwargs.get('max_age'))
            if isinstance(obje.get('age'),list):
                if float(obje.get('age')[0].replace(' ','')) >= min_age and float(obje.get('age')[0].replace(' ','')) <= max_age:
                    return True
            elif float(obje.get('age').replace(' ','')) >= min_age and float(obje.get('age').replace(' ','')) <= max_age:
                return True
            return False
        except Exception as e:
            return False

    def gender_checker(self,obje,**kwargs):
        try:
            gender_value = kwargs.get('gender')
            if isinstance(obje.get('gender'),list):
                if obje.get('gender')[0] == gender_value:
                    return True
            elif obje.get('gender') == gender_value:
                return True
            return False
        except:
            return False

    def add_boundary_info(self,obje):
        try:
            #Optimize the errors - from
            benefic = Boundary.objects.get(id=int(obje.get('id')))
            address = Address.objects.filter(object_id=benefic.id,office=1).latest('id')
            parent_loc = Boundary.objects.get(id=address.boundary.id).get_parent_locations([])
            #boundary_id = eval(obje.get('address')[0]).get('address_0').get('boundary_id')
            #parent_loc = Boundary.objects.get(id=boundary_id).get_parent_locations([])
            #Optimize the errors - to
            parent_dic = {}
            [parent_dic.update(i) for i in parent_loc]
            obje['district']=Boundary.objects.get(id=parent_dic.get('level3_id')).name
            obje['block']=Boundary.objects.get(id=parent_dic.get('level4_id')).name
            return obje
        except Exception as e:
            print e.message
            obje['district']=''
            obje['block']=''
            return obje

    def display_report(self,report_id,partner_list,request):
        partner_list = [partner.id for partner in partner_list]
        aggregate_report = AggregateReportConfig.objects.get(id=report_id)
        mutant_class = aggregate_report.mutant_app_table.model_class()
        fields_dict = {}
        [fields_dict.update({field.name:field.verbose_name}) for field in mutant_class._meta.get_fields()]
        try:
            data = mutant_class.objects.filter(partner_id__in=partner_list).values(*fields_dict.keys())
        except:
            data = mutant_class.objects.all().values(*fields_dict.keys())
        if request.GET.get('pid') and request.GET.get('qid') and request.GET.get('yid'):
            qmnth = request.GET.get('qid')
            qyr = request.GET.get('yid')
#            fcn_yr = get_fincal_yr(qmnth,qyr)
            #data = data.filter(partner_id__in=eval(request.GET.get('pid')),financial_month_year=fcn_yr)
            data = data.filter(partner_id__in=eval(request.GET.get('pid')))

    
        for d in data:
            for k in d.keys():
                try:
                    if int(k) and Question.objects.filter(id=k,qtype__in=['R','S','C']).exists():
                        choice = Choice.objects.get_or_none(id=d.get(k))
                        if choice:
                            d[k]=choice.text
                except Exception as e:
                    pass
        return {'status':2,'data':data,'headers':fields_dict,'report_name':aggregate_report.report_name,'dl_name':aggregate_report.mutant_app_table.model}


    def export_report(self,report_id,partner_list,request):
        export_data = ReportManager().display_report(report_id,partner_list,request)
        export_file = open(BASE_DIR+"/static/response_csv/"+export_data.get('report_name')+".csv", 'w')
        export_writer = csv.writer(export_file)
        res_keys = export_data.get('headers').keys()
        head_values = [export_data.get('headers').get(ke) for ke in res_keys]
        export_writer.writerow(head_values)
        for d in export_data.get('data'):
            one_resp = []
            for k in res_keys:
                try:
                    if int(k) and Question.objects.get(id=k,qtype__in=['R','S','C']).exists():
                        choice = Choice.objects.get_or_none(id=d.get(k))
                        if choice:
                            d[k]=choice.text
                except Exception as e:
                    pass
                one_resp.append(str(d[k]))
            export_writer.writerow(one_resp)
        file_name = str(export_file.name).split('/')[-1]
        return {'status':2,'download':HOST_URL+'/static/response_csv/'+file_name}

