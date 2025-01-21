from reports.models import *
from beneficiary.views import *
from survey.views.survey_views_two import *
import operator
from dateutil.relativedelta import relativedelta
import requests
from django.conf import settings
import xlsxwriter


class ReportSurveyList(APIView):

    def post(self, request):
        '''function that returns the list of
        survey in the report'''
        response = {}
        survey_list = ReportSurvey.objects.filter(active=2)
        final_list = []
        for i in survey_list:
            final_list.append({'name':i.name, 'id':i.id})
        response.update({'data':final_list, 'message':'success'})
        return Response(response)


class PartnerWiseYearQuarter(APIView):

    def post(self, request):
        """fucntion that returns the year and
        quarter of the partners
        ---
        parameters:
        - name: partner_id
          description: Pass partner id
          required: true
          type: integer
          paramType: integer
        """
        response = {}
        partner_id = request.data.get('partner_id')
        years = PartnerReportYear.objects.filter(active=2, partner_id=partner_id)
        year_list = []
        for i in years:
            year_list.append({"id":i.id, "year":str(i.year)})
        response.update({'data':year_list, 'message':'success'})
        return Response(response)


class YearWiseQuarter(APIView):

    def post(self, request):
        """
        function that returns the
        quarter of the partners based on the year
        ---
        parameters:
        - name: year_id
          description: Pass year id
          required: true
          type: integer
          paramType: integer
        """
        response = {}
        year_id = request.data.get('year_id')
        year_obj = PartnerReportYear.objects.get(id=year_id)
        quarter_list = []
        for quarter in year_obj.get_quarters():
            quarter_list.append({"id":quarter.id, "quarter":str(quarter.get_quarter_display()), \
                "start_date":quarter.start_date, "end_date":quarter.end_date})
        response.update({'data':quarter_list, 'message':'success'})
        return Response(response)



def get_sdanded(quarter, number_of_quarters):
    '''function to get the start date and
    end date based on number of quarters
    number_of_months = (number_of_quarters-1) * 3'''
    start_date = quarter.partner_year.get_quarters().order_by('quarter')[0].start_date
    end_date = quarter.end_date
    return start_date, end_date


def get_lastyear(quarter):
    '''function to get the start date and
    end date based on number of quarters
    number_of_months = (number_of_quarters-1) * 3'''
    start_date1 = quarter.partner_year.get_quarters().order_by('quarter')[0].start_date
    start_date = start_date1 - relativedelta(months=12)
    end_date = start_date1 - relativedelta(days=1)
    return start_date, end_date


def get_question_dict(qdict, question, start_date, end_date, partner_id, prq):
    '''function to update questions which have subquestions'''
    name_list = []
    final_list = []
    max_count = []
    all_list = []
    for subquestion in question.get_sub_questions():
        subanswer_list = []
        name_list.append(str(subquestion.name))
        for question1 in subquestion.get_sub_questions():
            subanswer_list.append(get_answer_report(question1.answer_code, \
                start_date, end_date, partner_id, prq))
        final_list.append(subanswer_list)
    [max_count.append(len(i)) for i in final_list]
    for i in range(max(max_count)):
        ans_list = []
        for ans in final_list:
            try:
                ans_list.append(ans[i])
            except:
                ans_list.append('NA')
        all_list.append(ans_list)
    qdict.update({'answer':all_list, 'order':question.report_order, 'name':name_list})
    return None


def get_updated_result(quarter, question, partner_id, qdict, block):
    '''inner function of reports
    returns an updated dictionay with all types of questions
    and its related answers
    quarter = request.data.get('quarter')
    this is for dynamic reports'''

    prq, start_date, end_date = None, None, None
    try:
        prq = PartnerReportQuarter.objects.get(id=quarter.id)
    except:
        pass
    if prq:
        start_date = prq.start_date
        end_date = prq.end_date
    question_name = question.name if question.name else \
                    question.question.text
    if question.get_sub_questions() and not block.dynamic_block:
        get_question_dict(qdict, question, start_date, end_date, partner_id, prq)
    elif question.location_level:
        boundary_id = Partner.objects.get(id=partner_id).state.id
        try:
            boundaries = eval(get_required_level_info(boundary_id, question.location_level).content)['locations']
            qdict.update({'answer':len(boundaries), 'order':question.report_order, 'name':question_name})
        except:
            qdict.update({'answer':1, 'order':question.report_order, 'name':question_name})
    elif question.answer_code:
        answers = get_answer_report(question.answer_code, start_date, end_date, partner_id, prq)
        qdict.update({'answer':answers, 'order':question.report_order, 'name':question_name})
        answers1 = 0
        if block.no_of_questions_in_a_row == 3:
            answers1 = 0
            if question.answer_code_two:
                answers1 = get_answer_report(question.answer_code_two, start_date, end_date, partner_id, prq)
            qdict.update({'answer2':answers1})
    return None


def get_tillquarter(quarter):
    '''function to get the start date and
    end date based on number of quarters
    number_of_months = (number_of_quarters-1) * 3'''
    start_date1 = quarter.start_date
    end_date = start_date1 - relativedelta(days=1)
    return start_date1, end_date


def get_answer_report(answer_code, start_date, end_date, partner_id, prq):
    '''function for get the answer of the question
    code whatever question may be passed'''
    answer_code_one = answer_code.split('split')[0]
    try:
        answer_code_two = answer_code.split('split')[1]
    except:
        answer_code_two = None
    answers = eval(answer_code_one)
    answers1 = answers
    slist = (set(map(str,answer_code.split('split'))) & set(['perc']))
    tillquarter = (set(map(str,answer_code.split('split'))) & set(['tillquarter']))
    lastyear = (set(map(str,answer_code.split('split'))) & set(['lastyear']))
    if answer_code_two and 'Q__' in answer_code_two:
        dates = get_sdanded(prq, int(answer_code_two.split("__")[1]))
        start_date = dates[0]
        end_date = dates[1]
    if lastyear:
        dates = get_lastyear(prq)
        start_date = dates[0]
        end_date = dates[1]
    if tillquarter:
        dates = get_tillquarter(prq)
        start_date = dates[1]
        answers = answers.filter(created__date__lt=start_date)
    if start_date and end_date and not tillquarter:
        answers = answers.filter(created__date__range=[start_date, end_date])
    if answers:
        if hasattr(answers[0], 'partner'):
            answers = answers.filter(partner_id=partner_id).count()
        elif hasattr(answers[0], 'get_partner'):
            ans_list = [i.id for i in answers if i.get_partner() if i.get_partner() == int(partner_id)]
            answers = answers.filter(id__in=ans_list).count()
        else:
            answers = answers.count()
    else:
        answers = 0
    try:
        if slist:
            survey_ids = list(set([i.survey_id for i in answers1 if i.get_partner() if i.get_partner() == int(partner_id)]))
            if start_date and end_date:
                answers = ((float(answers) / float(JsonAnswer.objects.filter(active=2,survey_id__in=survey_ids, created__date__range=[start_date, end_date]).count())) * 100)
            else:
                answers = ((float(answers) / float(JsonAnswer.objects.filter(active=2,survey_id__in=survey_ids).count())) * 100)
            answers = str(int(answers)) + "%"
    except:
        pass
    return answers


def get_dynamic_data(quarter, block, partner_id):
    '''function to get the dynamic data
    with headers, display headers and data to display
    quarter = request.data.get('quarter')
    this is for dynamic reports'''
    question_list = []
    display_headers = []
    prq, start_date, end_date = None, None, None
    try:
        prq = PartnerReportQuarter.objects.get(id=quarter.id)
    except:
        pass
    if prq:
        start_date = prq.start_date
        end_date = prq.end_date
    for question in block.get_report_block_question().order_by('report_order'):
        qdict = {}
        question_dict = {}
        if question.initial_code:
            display_headers = eval(question.initial_code)
        get_updated_result(quarter, question, partner_id, qdict, block)
        headers = ['c_'+x for x in map(str, range(len(display_headers)))]
        for counter, i in enumerate(question.get_sub_questions()):
            question_dict.update({'c_'+str(counter+2):get_answer_report(i.answer_code, start_date, end_date, partner_id, prq)})
        if not question.get_sub_questions():
            for counter, i in enumerate(headers):
                question_dict.update({'c_'+str(counter):'NA'})
        question_list.append(question_dict)
        question_dict.update({'c_0':qdict['name']})
        question_dict.update({'c_1':qdict['answer']})
    data_dict = {'display_headers':display_headers, 'headers':headers,
                'data':question_list}
    return data_dict


class ReportPartnerWise(APIView):

    def post(self, request):
        """
        function that returns the question and answer for the report
        ---
        parameters:
        - name: survey_id
          description: Pass survey id
          required: true
          type: integer
          paramType: integer
        - name: partner_id
          description: Pass partner id
          required: false
          type: integer
          paramType: integer
        - name: quarter
          description: Pass quarter id
          required: true
          type: integer
          paramType: integer
        """
        response = {}
        survey_id = request.data.get('survey_id')
        partner_id = request.data.get('partner_id')
        quarter = request.data.get('quarter')

        try:
            quarter_obj = PartnerReportQuarter.objects.get(id=quarter)
            report_obj = ReportData.objects.get(partner_id=partner_id, quarter=quarter_obj)
        except:
            response.update({'data':'error', 'message':'error'})
        try:
            response.update({'data':report_obj.response[str(survey_id)], 'message':'success'})
        except:
            response.update({'data':'error', 'message':'error'})
        return Response(response)


def get_updated_block_data(quarter, partner_id, block_list, survey_obj):
    '''function to update the block data
    while data is storing to the report data json'''
    for block in survey_obj.get_report_survey_blocks().order_by('report_order'):
        question_dict = {}
        question_list = []
        
        if block.dynamic_block:
            question_list = get_dynamic_data(quarter, block, partner_id)
        else:
            for question in block.get_report_block_question().order_by('report_order'):
                qdict = {}
                get_updated_result(quarter, question, partner_id, qdict, block)
                if question.initial_code:
                    question_list.insert(0, eval(question.initial_code))
                question_list.append(qdict)
        question_dict.update({'no_of_questions_in_a_row':block.no_of_questions_in_a_row,
            'no_of_rows_with_one_row':block.no_of_rows_with_one_row,
            'order':block.report_order, 'name':block.name,
            'dynamic_block':block.dynamic_block, 'questions':question_list})
        block_list.append(question_dict)
    return block_list


def savereportdata():
    '''function for updating the report data'''
    partners = [int(i.id) for i in Partner.objects.all()]
    survey_list = ReportSurvey.objects.all()
    for partner_id in partners:
        for quarter in PartnerReportQuarter.objects.filter(partner_year__partner_id=partner_id):
            survey_dict = {}
            for survey_obj in survey_list:
                block_list = []
                data_dict = {}
                block_list = get_updated_block_data(quarter, partner_id, \
                    block_list, survey_obj)
                data_dict.update({'blocks':block_list})
                survey_dict.update({str(survey_obj.id):data_dict})
            report_obj, created = ReportData.objects.get_or_create(partner_id=partner_id,
                quarter=quarter)
            report_obj.response = survey_dict
            report_obj.save()


class ReportExcel(APIView):

    def post(self, request):
        """
        function that returns the excel for the report
        ---
        parameters:
        - name: survey_id
          description: Pass survey id
          required: true
          type: integer
          paramType: integer
        - name: partner_id
          description: Pass partner id
          required: false
          type: integer
          paramType: integer
        - name: quarter
          description: Pass quarter id
          required: false
          type: integer
          paramType: integer
        """
        response = {}
        survey_id = request.data.get('survey_id')
        partner_id = request.data.get('partner_id')
        quarter = request.data.get('quarter')
        response1 = requests.post(settings.HOST_URL+'/reports/displaycontents/',
                data={'survey_id':survey_id,
                'partner_id':partner_id, 'quarter':quarter
                })
        data = response1.json()
        partner = Partner.objects.get(id=partner_id)
        quarter = PartnerReportQuarter.objects.get(id=quarter)
        workbook = xlsxwriter.Workbook(settings.BASE_DIR+\
                        '/static/excelfiles/'+str(slugify(partner.name))+'_'+\
                        str(quarter.partner_year.year)+'_'+\
                        str(quarter.get_quarter_display())+'.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column(0, 1, 30)

        ''' Some data we want to write to the worksheet.'''
        basecontent = (
            ['Partner', partner.name],
            ['Year',   quarter.partner_year.year],
            ['Quarter',  quarter.get_quarter_display()],
        )

        ''' Start from the first cell. Rows and columns are zero indexed.'''
        row = 0
        col = 0
        bold = workbook.add_format({'bold': 1, 'text_wrap':True, \
                'fg_color':'#fed803', 'border':1})

        ''' Iterate over the data and write it out row by row.'''
        for item, cost in (basecontent):
            worksheet.write(row, col,     item, bold)
            worksheet.write(row, col + 1, cost, bold)
            row += 1

        for block in data['data']['blocks']:
            row += 2
            worksheet.write(row, 0, block['name'], bold)
            row += 1
            ws = get_block_content(block, worksheet, row, workbook)
            worksheet = ws['worksheet']
            row = ws['row']
        workbook.close()
        file_path = settings.HOST_URL+\
                        '/static/excelfiles/'+str(slugify(partner.name))+'_'+\
                        str(quarter.partner_year.year)+'_'+\
                        str(quarter.get_quarter_display())+'.xlsx'
        response.update({'file_path':file_path, 'status':2})
        return Response(response)


def add_worksheet_row(worksheet, row, llist, workbook):
    bold = workbook.add_format({'bold': 1})
    for counter, value in enumerate(llist):
        worksheet.write(row, counter, value, bold)
    return {'worksheet':worksheet, 'row':row+1}


def get_block_content(block, worksheet, row, workbook):
    '''function to retrieve dynamic block data
    all the type if answer is a list of list or a string
    will be extracted to excel in this function'''
    data_list = []
    bold = workbook.add_format({'bold': 1})
    if block["dynamic_block"] == True:
        display_headers = block['questions']['display_headers']
        ws = add_worksheet_row(worksheet, row, display_headers, workbook)
        worksheet = ws['worksheet']
        row = ws['row']
        dynamic_data = block['questions']['data']
        headers = block['questions']['headers']
        for counter, value in enumerate(dynamic_data):
            data_list = []
            for counter1, header in enumerate(headers):
                data_list.append(value[header])
            ws = add_worksheet_row(worksheet, row, data_list, workbook)
            worksheet = ws['worksheet']
            row = ws['row']
    for counter, question in enumerate(block['questions']):
        try:
            question.pop('order', None)
            if counter == 0:
                keys = question.keys()[::-1]
            for counter1, key in enumerate(keys):
                ws = get_non_dynamic_block_data(worksheet, row, workbook, \
                        question, bold, key, counter1)
                worksheet = ws['worksheet']
                row = ws['row']
        except:
            pass
        row += 1
    return {'worksheet':worksheet, 'row':row}


def get_non_dynamic_block_data(worksheet, row, workbook, question, \
            bold, key, counter1):
    '''function to retrieve non dynamic block data
    all the type if answer is a list of list or a string
    will be extracted to excel in this function'''
    if not type(question[key]) == list:
        worksheet.write(row, counter1, question[key], bold)
    else:
        ws = get_list_type_question_data(workbook, worksheet, \
                question, key, row)
        worksheet = ws['worksheet']
        row = ws['row']
    return {'worksheet':worksheet, 'row':row}


def get_list_type_question_data(workbook, worksheet, question, key, row):
    '''function to retrieve list type data
    all the type if answer is a list of list
    will be extracted to excel in this function'''
    for value in question[key]:
        if type(value) is list:
            for inner_value in question[key]:
                ws = add_worksheet_row(worksheet, row, inner_value, \
                        workbook)
                worksheet = ws['worksheet']
                row = ws['row']
        else:
            ws = add_worksheet_row(worksheet, row, question[key], workbook)
            worksheet = ws['worksheet']
            row = ws['row']
            break
    return {'worksheet':worksheet, 'row':row}
