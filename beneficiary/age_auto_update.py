from .models import  Beneficiary
from survey.views.custom_dates import CustomDates
from django.db.models import Q
from datetime import datetime
import threading

class BeneficiaryAgeUpdate():
    def get_beneficiary_dob(self):
        present_month,present_day = datetime.now().month,datetime.now().day
        for yr in range(2015,2020):
            date_format = CustomDates().req_year_req_format(str(yr)+'-'+str(present_month)+'-'+str(present_day),'%Y-%m-%d','%d-%m-%Y')
            update_age = BeneficiaryAgeUpdate().get_calculate_age(yr)
            beneficiaries = list(Beneficiary.objects.filter(jsondata__date_of_birth__0=str(date_format)))
            created_benef = list(Beneficiary.objects.filter(created__gte=str(yr)+'-'+str(present_month)+'-'+str(present_day)+' 00:00:00.00001',
                    created__lte=str(yr)+'-'+str(present_month)+'-'+str(present_day)+' 23:59:59.0001'))
            beneficiaries.extend(created_benef)
            for beneficiary in beneficiaries:
                #BeneficiaryAgeUpdate().update_json_data(beneficiary,update_age)
                threading.Thread(target=BeneficiaryAgeUpdate().update_json_data(beneficiary,update_age)).start()

    def get_calculate_age(self,for_year):
        return datetime.now().year-int(for_year)


    def update_json_data(self,beneficiary,age):
        json_data = beneficiary.jsondata
        json_data['age']=age
        beneficiary.jsondata = json_data
        beneficiary.save()
