from django.contrib.auth.models import User
from survey.models import *



def get_question_code(self):
    # Ans Type to feeds Enter case id and enter cluster code are 
    # Customer Id (6) Select villagename(3)
    # first two questions made as hardcoded if any spelling mistakes 
    # return default qtype code
    # For Text and Email 1 because email is also text
    # only for validation "M:R:Message"
    if self.meta_qtype == 3:
        app_qtype = 16
    elif self.meta_qtype == 1:
        app_qtype = 3
    elif self.meta_qtype == 2:
        app_qtype = 6
    else:
        app_qtype = {'T':1, 'S':10,'R':4, 'C':2,\
                     'D':5, 'G':11,'I':12,'V':13,\
                     'A':14, 'E':1}.get(self.qtype,1)
    return app_qtype


def question_check(self):
    if self.qtype in ['S','R','C']:
        access = Choice.objects.filter(question=self,active=2).exists()
    else:
        access = True
    return access


def get_cluster(self):
    # Cluster Code is combination of STATE CODE + DISTRICT CODE
    # For household and Plot level its not done
    res = []
    uid = self.user.user.id
    user_id = {1:str('00')+str(uid),2:str('0')+str(uid)}.get(len(str(uid)),str(uid))
    if self.survey.active == 2:
        if self.survey.data_entry_level == '1':
            res = [{'cluster_id':i.id,
                        'cluster_name': i.name,
                        #'cluster_code': i.code,
                        'cluster_code':str(i.country.code)+str(i.code),
                        'district_id': i.country.id,
                        'district': i.country.name,
                        't_id' : self.survey.id,
                        'key':'state'
                        } for i in self.state.active_items().order_by('name')]
        elif self.survey.data_entry_level == '2':
            res = [{'cluster_id':i.id,
                        'cluster_name': i.name,
                        #'cluster_code': i.code,
                        'cluster_code': str(i.state.code) + str(i.code),
                        'district_id': i.state.id,
                        'district': i.state.name,
                        't_id' : self.survey.id,
                        'key':'district'
                        } for i in self.district.active_items().order_by('name')]
        elif self.survey.data_entry_level == '3':
             res = [{'cluster_id':i.id,
                        'cluster_name': i.name,
                        #'cluster_code': i.code,
                        'cluster_code': str(i.district.state.code) + str(i.district.code),
                        'district_id': i.district.id,
                        'district': i.district.name,
                        't_id' : self.survey.id,
                        'key':'taluk'
                        } for i in self.taluk.active_items().order_by('name')]
        elif self.survey.data_entry_level == '4':
            # Here its wrong=====
            res = [{'cluster_id':i.id,
                        'cluster_name': i.name,
                        #'cluster_code': i.code,
                        'cluster_code': str(i.mandal.taluk.district.state.code) + str(i.mandal.taluk.district.code),
                        'district_id': i.mandal.id,
                        'district': i.mandal.name,
                        't_id' : self.survey.id,
                        'key':'gramapanchayath'
                        } for i in self.gramapanchayath.active_items().order_by('name')]
        elif self.survey.data_entry_level == '5':
             res = [{'cluster_id':i.id,
                        'cluster_name': i.name,
                        #'cluster_code': i.code,
                        'cluster_code': str(i.gramapanchayath.mandal.taluk.district.state.code) + \
                                            str(i.gramapanchayath.mandal.taluk.district.code),
                        'district_id': i.gramapanchayath.id,
                        'district': i.gramapanchayath.name,
                        't_id' : self.survey.id,
                        'key':'village'
                        } for i in self.village.active_items().order_by('name')]
        elif self.survey.data_entry_level == '7':
            res = [{'cluster_id':h.id,
                        'cluster_name': h.head_of_family,
                        'cluster_code': h.house_no,
                        'district_id': h.village.id,
                        'district': h.village.name,
                        't_id' : self.survey.id,
                        'key':'houseHold'
                        } for i in self.village.active_items().order_by('name') for h in i.household_set.active_items()]
        elif self.survey.data_entry_level == '8':
            res = [{'cluster_id':p.id,
                        'cluster_name': p.household.name,
                        #'cluster_code': p.household.house_no,
                        'cluster_code': p.household.house_no,
                        'district_id': p.household.village.id,
                        'district': p.household.village.name,
                        't_id' : self.survey.id,
                        'key':'Plot'
                        } for i in self.village.active_items().order_by('name') for h in i.household_set.active_items() for p in h.plot_set.active_items()]
    return res


def get_question_validation(self):
    # Question Validation Make Sure each question has only one validation
    qv = None
    try:
        qv_obj = QuestionValidation.objects.filter(active=2).get_or_none(question=self)
    except:
        qv_obj = None
    if self.id in [484,498,512,526]:
        qv = "R:CE:^(0[4-9][0-9]|[4-9][0-9]|1[0-7][0-9]|180)\/(0[4-9][0-9]|[4-9][0-9]|1[0-1][0-9]|120)$:7:" \
             "Enter in range between 40/40 and 180/120"
    elif self.qtype in ['T', 'D'] and qv_obj:
        if self.validation == 0:
            qv = str(qv_obj.validation_type)+":D:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 1 or self.validation == 11:
            qv = str(qv_obj.validation_type)+":N:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 2:
            qv = str(qv_obj.validation_type)+":A:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 3:
            qv = str(qv_obj.validation_type)+":AN:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 6:
            qv = str(qv_obj.validation_type)+":M:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 7:
            qv = str(qv_obj.validation_type)+":LN:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 8 and qv_obj.validation_condition not in ['past','current','future','any']:
            qv = str(qv_obj.validation_type)+":D:dd/mm/yyyy:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 8 and qv_obj.validation_condition == 'past':
            qv = "R"+":D:dd/mm/yyyy:"+"01011900"+":"+"00000000"+":"+qv_obj.message
        elif self.validation == 8 and qv_obj.validation_condition == 'current':
            qv = "R"+":D:dd/mm/yyyy:"+"00000000"+":"+"00000000"+":"+qv_obj.message
        elif self.validation == 8 and qv_obj.validation_condition == 'future':
            qv = "R"+":D:dd/mm/yyyy:"+"00000000"+":"+"31122030"+":"+qv_obj.message
        elif self.validation == 9:
            qv = str(qv_obj.validation_type)+":T:ISO:HH-mm-ss:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
    elif self.qtype in ['E'] and qv_obj:
        qv = "M:"+str(qv_obj.validation_type)+":"+qv_obj.message
    return qv


def get_validations(self):
    # Question Validation Make Sure each question has only one validation
    qv = None
    try:
        qv_obj = Validations.objects.filter(active=2).get_or_none(object_id=self.id)
    except:
        qv_obj = None
    if self.qtype in ['T', 'D'] and qv_obj:
        if self.validation == 0:
            qv = str(qv_obj.validation_type)+":D:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 1:
            qv = str(qv_obj.validation_type)+":N:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 2:
            qv = str(qv_obj.validation_type)+":A:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 3:
            qv = str(qv_obj.validation_type)+":AN:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.messages
        elif self.validation == 6:
            qv = str(qv_obj.validation_type)+":M:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 7:
            qv = str(qv_obj.validation_type)+":LN:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 8:
            qv = str(qv_obj.validation_type)+":D:dd/mm/yyyy:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
        elif self.validation == 9:
            qv = str(qv_obj.validation_type)+":T:ISO:HH-mm-ss:"+str(qv_obj.min_value)+":"+str(qv_obj.max_value)+":"+qv_obj.message
    elif self.qtype in ['E'] and qv_obj:
        qv = "M:"+str(qv_obj.validation_type)+":"+qv_obj.message
    return qv



def get_choice_skip_code(self):
    # -1 in Choice table Indicates no skip code 
    # The Choice code will the skip code of any question
    # 1 and 2 for consent status 
    skip_code = None
    if self.code != -1 and self.code and self.code not in [1,2]:
        try:
            skip_code = str(self.code)
        except:
            skip_code = None
    elif self.code == -1 and self.skip_question == None:
        skip_code = self.code
    return skip_code


def get_question_status(self):
    # This method returns the number 2 or 3 or n
    # based on different conditions for android feeds
    # Send both active status and """ mandatory or non mandatory """
    status_code = 0
    if self.active == 2 and self.mandatory:
        status_code = 2
    elif self.active == 2 and not self.mandatory:
        status_code = 3
    elif (self.active == 0 and self.mandatory) or (self.active == 0 and not self.mandatory):
        status_code = 0
    return status_code



def get_answer_flag(self):
    # Answer Flag returns 1 for feeds T, D, CI, SV, G
    # For Radio and Select with Choice code 9999 will returns 1
    # For radio button with "other text" pop up then "9999" should be given 
    aflag = None
    if self.question.qtype in ['T','D','G','E'] or self.question.meta_qtype in ['CI','SV']:
        aflag = 1
    elif self.question.qtype in ['R','S'] and self.code == 9999:
        aflag = 1
    return aflag


def get_language_answer(self):
    res = None
    appanswerid = self.app_answer_data
    appans_obj = AppAnswerData.objects.get_or_none(id=int(appanswerid))
    if appans_obj:
        language_id = appans_obj.language_id
        try:
            lang_obj = Language.objects.get_or_none(id=int(language_id))
        except:
            lang_obj = None
        if lang_obj and lang_obj.name.lower() != "english":
            clt_obj = ChoiceLanguageTranslation.objects.get_or_none(choice = self.choice)
            if clt_obj:
                res = clt_obj.text
        else:
            res = self.choice.text
    return res


def get_piriodicity_status(self):
    piriodicity = int(self.piriodicity)
    res = 2
    if piriodicity != 0 or piriodicity != '0':
        res = 3
    return res


def get_answer_code(self):
    if self.code == -1:
        code = self.id
    else:
        code = self.code
    return code


#UserSurveyMap.add_to_class('get_cluster', get_cluster)
Question.add_to_class('get_question_code', get_question_code)
Question.add_to_class('question_check', question_check)
Question.add_to_class('get_question_validation', get_question_validation)
Choice.add_to_class('get_choice_skip_code', get_choice_skip_code)
Question.add_to_class('get_question_status', get_question_status)
Choice.add_to_class('get_answer_flag', get_answer_flag)
Answer.add_to_class('get_language_answer', get_language_answer)
Survey.add_to_class('get_piriodicity_status',get_piriodicity_status)
Choice.add_to_class('get_answer_code', get_answer_code)
#MetricsQuestionConfiguration.add_to_class('get_validations',get_validations)

