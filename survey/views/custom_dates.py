import datetime
import calendar
from datetime import date,timedelta
from ccd.settings import FY_YEAR

class CustomDates():
    def __init__(self):
        self.__current_date = datetime.datetime.now()

    def identify_callendar_quarter(self):
        return (int(self.__current_date.strftime('%m'))-1)//3+1

    def identify_financial_year_quarter(self):
        if int(self.__current_date.strftime('%m')) in range(1,4):
            return {'current_quarter':4}
        elif int(self.__current_date.strftime('%m')) in range(4,7):
            return {'current_quarter':1}
        elif int(self.__current_date.strftime('%m')) in range(7,10):
            return {'current_quarter':2}
        elif int(self.__current_date.strftime('%m')) in range(10,13):
            return {'current_quarter':3}

    def get_fy_last_quarter(self,year):
        last_quarters_helper = {1:self.fy_q4_dates(int(year)-1),2:self.fy_q1_dates(year),
                                3:self.fy_q2_dates(year),4:self.fy_q3_dates(year)}
        last_quarter = last_quarters_helper.get(self.identify_financial_year_quarter().get('current_quarter'))
        return last_quarter

    def fy_q1_dates(self,year):
        start_date = datetime.datetime.strptime(str(year)+'-04-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f')
        end_date = datetime.datetime.strptime(str(year)+'-06-30 23:59:59.0001','%Y-%m-%d %H:%M:%S.%f')
        return {'start_date':start_date,'end_date':end_date}

    def fy_q2_dates(self,year):
        start_date = datetime.datetime.strptime(str(year)+'-07-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f')
        end_date = datetime.datetime.strptime(str(year)+'-09-30 23:59:59.0001','%Y-%m-%d %H:%M:%S.%f')
        return {'start_date':start_date,'end_date':end_date}

    def fy_q3_dates(self,year):
        start_date = datetime.datetime.strptime(str(year)+'-10-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f')
        end_date = datetime.datetime.strptime(str(year)+'-12-31 23:59:59.0001','%Y-%m-%d %H:%M:%S.%f')
        return {'start_date':start_date,'end_date':end_date}

    def fy_q4_dates(self,year):
        year = str(int(year)+1)
        start_date = datetime.datetime.strptime(year+'-01-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f')
        end_date = datetime.datetime.strptime(year+'-03-31 23:59:59.0001','%Y-%m-%d %H:%M:%S.%f')
        return {'start_date':start_date,'end_date':end_date}

    def fy_first_half_dates(self,year):
        return {'start_date':self.fy_q1_dates(year).get('start_date'),
                'end_date':self.fy_q2_dates(year).get('end_date')}

    def fy_second_half_dates(self,year):
        return {'start_date':self.fy_q3_dates(year).get('start_date'),
                'end_date':self.fy_q4_dates(year).get('end_date')}

    def fy_dates(self,year):
        return {'start_date':self.fy_q1_dates(year).get('start_date'),
                'end_date':self.fy_q4_dates(year).get('end_date')}

    def current_year_dates(self,year):
        return {'start_date':datetime.datetime.strptime(year+'-01-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f'),
                'end_date':datetime.datetime.strptime(year+'-12-31 23:59:59.1000','%Y-%m-%d %H:%M:%S.%f')}

    def current_week_days(self):
        current_date = datetime.datetime.strptime(self.__current_date.strftime('%Y-%m-%d'),'%Y-%m-%d')
        return {'start_date':current_date - timedelta(days=current_date.weekday()),
                'end_date':(current_date - timedelta(days=current_date.weekday()))+timedelta(days=6)}

    def current_month_days(self):
        current_year,current_month = self.__current_date.strftime('%Y'),self.__current_date.strftime('%m')
        end_date = calendar.monthrange(int(current_year),int(current_month))[1]
        return {'start_date':datetime.datetime.strptime(current_year+'-'+current_month+'-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f'),
                'end_date':datetime.datetime.strptime(current_year+'-'+current_month+'-'+str(end_date)+' 23:59:59.1000','%Y-%m-%d %H:%M:%S.%f')}

    def previous_month_days(self):
        current_year,current_month = self.__current_date.strftime('%Y'),self.__current_date.strftime('%m')
        if int(current_month) == 1:
            current_month = str(13)
            current_year = str(int(current_year)-1)
        end_date = calendar.monthrange(int(current_year),int(current_month)-1)[1]
        return {'start_date':datetime.datetime.strptime(current_year+'-'+str(int(current_month)-1)+'-01 00:00:00.0001','%Y-%m-%d %H:%M:%S.%f'),
                'end_date':datetime.datetime.strptime(current_year+'-'+str(int(current_month)-1)+'-'+str(end_date)+' 23:59:59.1000','%Y-%m-%d %H:%M:%S.%f')}

    def current_fy_quarter_dates(self):
        quarter = {1:self.fy_q1_dates(FY_YEAR),2:self.fy_q2_dates(FY_YEAR),
                   3:self.fy_q3_dates(FY_YEAR),4:self.fy_q4_dates(FY_YEAR)}
        return quarter.get(self.identify_financial_year_quarter().get('current_quarter'))

    def current_fy_half_year(self):
        current_month = self.__current_date.strftime('%m')
        current_year = self.__current_date.strftime('%Y')
        if int(current_month) in range(4,10):
            return self.fy_first_half_dates(current_year)
        elif int(current_month) in range(10,13):
            return self.fy_second_half_dates(current_year)
        return self.fy_second_half_dates(str(int(current_year)-1))

    def current_half_year(self):
        current_month = self.__current_date.strftime('%m')
        current_year = self.__current_date.strftime('%Y')
        if int(current_month) in range(1,7):
            return {'start_date':datetime.datetime.strptime(current_year+'-01-01 00:00:00.0001'),
                    'end_date':datetime.datetime.strptime(current_year+'-06-30 00:00:00.0001')}
        return {'start_date':datetime.datetime.strptime(current_year+'-07-01 00:00:00.0001'),
                    'end_date':datetime.datetime.strptime(current_year+'-12-31 23:59:59.1000')}

    def year_req_format(self,way_format):
        return self.__current_date.strftime(way_format)

    @staticmethod
    def req_year_req_format(req_year,passing_format,req_format):
        return datetime.datetime.strptime(req_year,passing_format).strftime(req_format)
