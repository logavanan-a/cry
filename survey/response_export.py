from survey.models import *
from SST.settings import BASE_DIR
import csv
from datetime import datetime

def response_csv():
    responses = Answer.objects.filter(active=2,user__id__in=[334,335,336,337,338,339]).distinct('app_answer_data')
    with open(BASE_DIR+'/logFiles/answer_list.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
       
        spamwriter.writerow(['Username','Survey name','Village name','District name','Response date', 'Response ID'])
        for r in responses:
            vil = Village.objects.get_or_none(id=r.object_id)
            if vil:
                spamwriter.writerow([r.user.first_name,r.question.block.survey.name,vil.name,vil.gramapanchayath.mandal.taluk.district.name,datetime.strftime(r.created, '%Y-%m-%d'),r.id])
        csvfile.close()
        
