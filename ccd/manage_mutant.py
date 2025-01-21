from mutant.contrib.text.models import CharFieldDefinition
from mutant.contrib.numeric.models import BigIntegerFieldDefinition
from mutant.contrib.temporal.models import DateTimeFieldDefinition , DateFieldDefinition
from mutant.contrib.numeric.models import *
from mutant.models import ModelDefinition
from django.contrib.contenttypes.models import ContentType
from survey.models import *
from django.db.models import Q
from masterdata.models import *
from beneficiary.models import *
from facilities.models import *
from partner.models import Partner

class ManageMutantApp():

    def get_or_create(self,mdl, query):
        try:
            ct = ContentType.objects.get(model=str(mdl.__name__).lower())
            if mdl.__name__ not in ['ModelDefinition']:
                query['content_type_id'] = ct.id
            m,created = mdl.objects.get_or_create(**query)
            return m
        except Exception as e:
            if type(e).__name__ != 'OperationalError':
                raise

    def get_mutant_field_query(self,model_type):
        model_query = {'CharFieldDefinition':dict(max_length=250, blank=True, null=True),
                       'BigIntegerFieldDefinition':dict(blank=True, null=True),
                       'DateTimeFieldDefinition':dict(blank=True, null=True),
                       'FloatFieldDefinition':dict(blank=True,null=True),
                       }
        return model_query.get(str(model_type))

    def model_field_to_mutant_field(self,model_field_type):
        model_field_def = {'CharField':CharFieldDefinition,'PositiveIntegerField':BigIntegerFieldDefinition,
                           'IntegerField':BigIntegerFieldDefinition,'ForeignKey':BigIntegerFieldDefinition,
                           'AutoField':BigIntegerFieldDefinition,'DateField':DateFieldDefinition,
                           'DateTimeField':DateTimeFieldDefinition}
        return model_field_def.get(model_field_type)

    #specify the mutant app_label,verbose_name and model_name to be created
    def create_mutant_model(self,app_label,verbose_name,object_name):
        return self.get_or_create(ModelDefinition,dict(app_label=app_label,verbose_name=verbose_name,object_name=object_name))

    #specify the mutant_model name,from available model,and list of fields of model
    def create_pre_model_fields(self,for_model,from_model,fields_list):
        for fl in fields_list:
            try:
                internal_type = from_model._meta.get_field(fl).get_internal_type()
                converted_type = self.model_field_to_mutant_field(internal_type)
                query = self.get_mutant_field_query(converted_type.__name__)
                if fl == 'id':
                    fl = 'uid'
                query['model_def'] = for_model
                query['name'] = fl
                query['verbose_name'] = fl.replace('_',' ')
                self.get_or_create(converted_type,query)
            except Exception as e:
                print(e.message)
        print("Mutant fields created successfully..")

    #specify the mutant model name and fields info in fields_list
    #fields_list type be like [{'BigIntegerFieldDefinition':{'name':'field_name','verbose_name':'verbose name'}}]
    def create_custom_model_fields(self,for_model,fields_list):
        for fl in fields_list:
            try:
                for md in fl.keys():
                    query = fl.values()[0]
                    query.update(self.get_mutant_field_query(md.__name__))
                    query['model_def'] = for_model
                    self.get_or_create(md,query)
            except Exception as e:
                print(e.message)
        print("Custom mutant fields created successfully..")

    #specify the mutant model name and field list to delete from mutant model
    def delete_mutant_model_fields(self,for_model,fields_list):
        mutant_model_fields = FieldDefinition.objects.filter(model_def=for_model)
        for field in fields_list:
            mutant_model_fields.filter(name=field).delete()
        print("Fields deleted successfully..")

    #method to import data from django model fields..
    def import_data_to_mutant(self,from_model,to_model,from_model_fields):
        values = from_model.objects.filter(active=2).custom_values(*from_model_fields)
        #fields name replacer function
        from_model_fields = ManageMutantApp.list_fields_replacer(from_model_fields,[{'id':'uid'}])
        for value in values:
            fill_data_query = ManageMutantApp.convert_to_query_dict(zip(from_model_fields,value))
            to_model.model_class().objects.create(**fill_data_query)
        print("Data import successfully..")

    #method to update the data from django model fields..
    def import_new_data_to_mutant(self,from_model,to_model,from_model_fields):
        last_created = to_model.model_class().objects.latest('created')
        last_modified = to_model.model_class().objects.latest('modified')
        new_records = from_model.objects.filter(Q(created__gte=last_created)|
                        Q(modified__gte=last_modified),active=2)
        for i in new_records:
            fill_data_query = ManageMutantApp.list_fields_replacer(from_model_fields,[{'id':'uid'}])
            to_model.model_class().objects.create(**fill_data_query)
        print("Data imported successfully...")


    #replace_list should be a dict with key and value
    @staticmethod
    def list_fields_replacer(original_list,replace_list):
        for rf in replace_list:
            for i,v in enumerate(original_list):
                if rf.keys()[0] == v:
                    original_list[i] = rf.get(rf.keys()[0])
        return original_list

    @staticmethod
    def convert_to_query_dict(values):
        value_dict = {}
        for value in values:
            value_dict[value[0]]=value[1]
        return value_dict

    #create the mutant survey table
    def create_survey_models(self,survey_id):
        survey = Survey.objects.get(id=survey_id)
        mdl = self.get_or_create(ModelDefinition,
                     dict(app_label = "MutantApp",verbose_name = str(survey),
        object_name = '{}_{}'.format(str(survey).replace(' ','_'),str(survey.id))))
        questions = Question.objects.filter(block__survey=survey).order_by('code')
        self.create_pre_model_fields(mdl,JsonAnswer,['id','created','modified'])
        q_type_helper = {'T':CharFieldDefinition,
                         'S':BigIntegerFieldDefinition,
                         'C':BigIntegerFieldDefinition,
                         'R':BigIntegerFieldDefinition,
                         'D':DateTimeFieldDefinition,
                        }

        for question in questions:
            self.create_custom_model_fields(mdl,[{
                q_type_helper.get(str(question.qtype)):{'name':str(question.id),
                                'verbose_name':'q_{}'.format(question.text)}}])
        cluster_info = self.get_cluster_info(survey_id)
        cluster_info.remove('None')
        for cluster in cluster_info:
            self.create_custom_model_fields(mdl,[{CharFieldDefinition:{'name':str(cluster),
                                                   'verbose_name':str(cluster)}},
                         {CharFieldDefinition:{'name':str(cluster)+"_type_id",
           'verbose_name':str(cluster)+"_type_id"}}])


    def get_cluster_info(self,survey_id):
        survey_config = SurveyDataEntryConfig.objects.get(survey_id=survey_id)
        return [str(survey_config.content_type1),str(survey_config.content_type2)]



    #to import survey data into survey table
    def import_survey_data_to_mutant(self,survey_id):
        survey = Survey.objects.get(id=survey_id)
        mdl = ModelDefinition.objects.get(app_label = "MutantApp",verbose_name = str(survey),
        object_name = '{}_{}'.format(str(survey).replace(' ','_'),str(survey.id)))
        cluster_info = self.get_cluster_info(survey_id)
        cluster_info.remove('None')
        for answer in JsonAnswer.objects.filter(survey__id=survey_id,active=2):
            try:
                answer_object,created = mdl.model_class().objects.get_or_create(uid=answer.id)
                setattr(answer_object,'created',answer.created)
                setattr(answer_object,'modified',answer.modified)
                for question in Question.objects.filter(active=2,block__survey__id=survey_id).order_by('code'):
                    setattr(answer_object,str(question.id),answer.response.get(str(question.id)))
                for cluster in cluster_info:
                    setattr(answer_object,str(cluster),answer.cluster[0].get(cluster).get('id'))
                    setattr(answer_object,str(cluster)+"_type_id",
                    answer.cluster[0].get(cluster).get(str(cluster)+'_type_id'))
                answer_object.save()
		print ('Imported',answer_object.id)
            except Exception as e:
                print("Failed record: ",answer.id)

    #to fill the new entry records
    def import_survey_new_records(self,survey_id):
        survey = Survey.objects.get(id=survey_id)
        mdl = ModelDefinition.objects.get(app_label="MutantApp", verbose_name=str(survey),
                object_name='{}_{}'.format(str(survey).replace(' ', '_'), str(survey.id)))
        last_created = mdl.model_class().objects.exclude(created=None).latest('created').created
        last_modified = mdl.model_class().objects.exclude(modified=None).latest('modified').modified
        cluster_info = self.get_cluster_info(survey_id)
        cluster_info.remove('None')
        for answer in JsonAnswer.objects.filter(Q(created__gte=last_created)|Q(modified__gte=last_modified),
                                                survey__id=survey_id,active=2):
            try:
                answer_object,created = mdl.model_class().objects.get_or_create(uid=answer.id)
                setattr(answer_object,'created',answer.created)
                setattr(answer_object,'modified',answer.modified)
                self.set_question_values(answer_object,survey_id,answer)
                for cluster in cluster_info:
                    setattr(answer_object,str(cluster),answer_object.cluster[0].get(cluster).get('id'))
                    setattr(answer_object,str(cluster)+"_type_id",
                    answer_object.cluster[0].get(cluster).get(str(cluster)+'_type_id'))
                answer_object.save()
            except Exception as e:
                print("Failed record: ",answer.id)

    def set_question_values(self,answer_object,survey_id,answer):
        for question in Question.objects.filter(active=2, block__survey__id=survey_id).order_by('code'):
            try:
                setattr(answer_object, str(question.id), answer.response.get(str(question.id)))
            except Exception as e:
                print(e.message)
