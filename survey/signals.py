# Signals for survey
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save
from survey.models import *
from django.forms.models import model_to_dict
from django.core.cache import cache
from reports.models  import ProfileView


# Import prerequisites


#@receiver(post_save, sender=Survey)
#def surveypostsave(sender, **kwargs):

#    # Create block and question on creating survey

#    survey = kwargs["instance"]

#    if kwargs["created"]:

#        b = survey.block_set.create(name=survey.name)

#        if survey.piriodicity != '0':
#            b.question_set.create(
#                qtype='T', text='Date', order=-1, mandatory=True, hidden=1, meta_qtype=3,code=100)

#        b.question_set.create(
#            qtype='T', text='Village Name', order=-2, meta_qtype=1, code=97)

#        b.question_set.create(
#            qtype='T',text='Customer Id', order=-3, meta_qtype=2, code=99)

#        b.question_set.create(
#                qtype='R', text="Consent Status", order=-4,meta_qtype=4,code=98)

#        b.question_set.create(
#                qtype='T', text="Initial Question", order=-5,meta_qtype=5,code=101,active=0)

def update_version(survey_obj, survey_version_list=[], **kwargs):
    # Common method to update Survey
    # Survey, Question, Block, Choice any of the models objects is updated
    # Survey version gets updated (The default version is 1.0)
    content_type = ContentType.objects.get_for_model(kwargs['instance'])
    object_id = int(kwargs['instance'].id)
    if len(survey_version_list) >= 1:
        latest_survey_version = survey_version_list.latest('id')
        version_obj = Version.objects.create(survey = survey_obj,\
                                                content_type=content_type,\
                                                object_id=object_id)
        latest_vn = float(latest_survey_version.version_number)
        version_obj.version_number = str(latest_vn + 0.01)
        if kwargs['created']:
            version_obj.action = 'C'
        else:
            version_obj.action = 'U'
    else:
        # The default first version is 1.0
        version_obj = Version.objects.create(survey = survey_obj,\
                                                content_type=content_type,\
                                                object_id=object_id,\
                                                version_number = str('1.00'))
    version_obj.changes = kwargs['instance'].__class__.__name__ + " - " + str(kwargs['instance'].id)
    version_obj.save()
    if cache.get('version_diff'):
        user = cache.get('loguser')
        log_value = cache.get('version_diff')
        SurveyLog.objects.create(create_by = user, log_value=log_value, \
                                                    version=version_obj)
    return True


def listdiff(l1,l2):
    a,b = len(list(l1)),len(list(l2))
    if a < b:
        c = set(l2) - set(l1)
    else:
        c = set(l1) - set(l2)
    return list(c)

@receiver(post_save)
def make_version_update(sender, **kwargs):
    # This Signal runs for all models so to restict it from other models
    # models_list is used so that it looks only for these models
    # Survey version starts updating only when the is survey is published/active
    models_list = ['Survey','Question','Choice','Block']
    if kwargs['instance'].__class__.__name__ in models_list:
        survey_obj = get_survey_object(**kwargs)
        survey_version_list = Version.objects.filter(survey = survey_obj)
        if kwargs['instance'].__class__.__name__ == 'Survey':
            if len(survey_version_list) >= 1 or survey_obj.active == 2:
                update_version(survey_obj, survey_version_list, **kwargs)
        elif len(survey_version_list) >= 1:
            update_version(survey_obj, survey_version_list, **kwargs)


def get_survey_object(**kwargs):
    # Common method to fetch the survey object based on the instance
    # and returns the survey object to the calling function
    # object (Class) (name)
    survey_obj = None
    model_name = kwargs['instance'].__class__.__name__
    if model_name == 'Survey':
        survey_obj = kwargs['instance']
    elif model_name == 'Question':
        question_obj = kwargs['instance']
        survey_obj = question_obj.block.survey
    elif model_name == 'Choice':
        choice_obj = kwargs['instance']
        survey_obj = choice_obj.question.block.survey
    elif model_name == 'Block':
        block_obj = kwargs['instance']
        survey_obj = block_obj.survey
    return survey_obj


@receiver(post_save, sender=Question)
def create_default_choice(sender,**kwargs):
    # Creates default Choice for Text and Date as "default"
    # for GPS [G] default options as Latitude and Longitude
    # Mainly code as 1 and 2 is most important for android
    if kwargs["created"]:
        question_obj = kwargs['instance']
        if question_obj.qtype in ['T','D','I','E','V']:
            Choice.objects.create(question=question_obj,text="",code=1)

        elif question_obj.qtype == 'G':
            Choice.objects.create(question=question_obj,text="Latitude",code=1)
            Choice.objects.create(question=question_obj,text="Longitude",code=2)
        elif question_obj.code == 98:
            Choice.objects.create(question=question_obj,text="Agreed",code=1)
            Choice.objects.create(question=question_obj,text="DisAgreed",code=2)



# @receiver(pre_save)
def create_survey_log(sender, **kwargs):
    models_list = ['Survey','Question','Choice','Block']
    if kwargs['instance'].__class__.__name__ in models_list:
        obj_id = kwargs['instance'].id
        model_name = kwargs['instance'].__class__.__name__
        if obj_id:
            obj = eval(model_name).objects.get(id=int(obj_id))
            fields=[field.name for field in obj._meta.fields]
            olddict = model_to_dict(obj, fields)
            newdict = model_to_dict(kwargs['instance'],fields)
            diff = get_difference(olddict, newdict)
            cache.set('version_diff', str(diff))
        else:
            d = {str(model_name):'Created'}
            cache.set('version_diff', str(d))


def get_difference(olddict, newdict):
    d1 = olddict
    d2 = newdict
    diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
    return dict(diffs)


@receiver(post_save, sender=QuestionValidation)
def make_question_update(sender, **kwargs):
    # This Signal runs for QuestionValidation
    # When the QuestionValidation is updated,the modified date of the question is also updated
        questval_obj = kwargs['instance']
        if not kwargs['created']:
            quest = Question.objects.get(id=questval_obj.question.id)
            quest.modified = questval_obj.modified
            quest.save()
            
            
@receiver(post_save , sender = JsonAnswer)
def profileview_update(sender , **kwargs):
    print(kwargs)
    json_object = kwargs['instance']
    beneficiary_surveys = SurveyDataEntryConfig.objects.get(survey_id = json_object.survey_id)
    object_id1 =  beneficiary_surveys.object_id1
    try :
        if object_id1 in (2,3,4):
            block = Block.objects.filter(survey_id = json_object.survey_id)
            question_is_profile = []
            for i in block:
                q = Question.objects.filter(block_id = i.id , is_profile = True)
                question_is_profile.extend(q)
            print(question_is_profile)
            ques = []
            for i in question_is_profile:
                ques.append(i.id)
                print("Ques" , i.id)
            print("ques" , ques)
            print json_object.response
            answerlist = []
            profile_dict = {}
            for i in range(len(ques)):
                ans = json_object.response.get(str(ques[i]))
                profile_dict[ques[i]] = ans.encode('utf-8') if ans  else None
                answerlist.append(ans.encode('utf-8') if ans  else None)
            cluster = json_object.cluster[0].get('beneficiary').get('id')
            print cluster
            beneficiary = Beneficiary.objects.get(id = cluster )
            dict1 = {}
            dict1 = profile_dict
            print profile_dict
            print beneficiary.name
            type_id = json_object.cluster[0].get('beneficiary').get('beneficiary_type_id')
            p = ProfileView.objects.filter(ben_fac_loc_id = cluster)
            print("p ," , p)
            if not p:
                print 'NEW OBJECT CREATED'
                ProfileView.objects.create(jsonid = json_object.id , uuid_lid = beneficiary.uuid , type_name = "BEN" , ben_fac_loc_id = cluster , profile_info = profile_dict , partner_id = beneficiary.partner_id , type_id = type_id , submission_date = json_object.submission_date)
            elif len(p)>1:
                for i in range(len(p)):
                    if i != 0:
                        p[i].delete()
            else:
                print 'Update the objects In the backend speed is very good!!!!!!!!!!!'
                print dict1
                p_n = p[0]
                p_n.profile_info = dict1
                p_n.type_id = type_id
                p_n.save()
                
        else:
            print("No Profiling")
    except:
        print("No Profiling")

