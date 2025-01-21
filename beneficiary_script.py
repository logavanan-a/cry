import xlrd,xlwt
from xlutils.copy import copy as x1_copy
from partner.models import *
from facilities.models import *
from beneficiary.models import *
from masterdata.models import *

def partner_beneficiary_facility(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('data3')
    database_data.write(0,0,'Partner Name' )
    database_data.write(0,1  , 'Partner Id' )
    database_data.write(0,2  , 'Partner Region' )
    database_data.write(0,3  , 'UserName' )
    database_data.write(0,4, 'User Id')
    database_data.write(0,5,'Beneficiary Count')
    database_data.write(0,6,'Facility Aaganwadi Count')
    database_data.write(0,7,'Facility School Count')
    database_data.write(0,8,'Facility Health Center Count')
    database_data.write(0,9,'HH Count')
    database_data.write(0,10,'Child Count')
    database_data.write(0,11,'Mother Count')
    sheet = location_book.sheet_by_index(2)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    partner = Partner.objects.all()
    flag = 1
    for i in range(len(partner)):
        try:
            flag1 = 0
            database_data.write(flag , 0 , partner[i].name)
            database_data.write(flag , 1 , partner[i].id )
            database_data.write(flag , 2 , partner[i].region.name)
            database_data.write(flag , 3 , "All Users")
            u_userroles = UserRoles.objects.filter(partner_id = partner[i].id)
            flag1 = flag+1
            for j in range(len(u_userroles)):
                if u_userroles[j].role_type.filter(id = 1).exists():
                    database_data.write(flag1 , 3 , u_userroles[j].user.username)
                    database_data.write(flag1 , 4 , u_userroles[j].user.id)
                    flag1 += 1
            database_data.write(flag , 5 , Beneficiary.objects.filter(partner_id = partner[i]).count())
            database_data.write(flag , 6 , Facility.objects.filter(partner_id = partner[i] , facility_type_id = 262 , facility_subtype_id = 295).count())
            database_data.write(flag , 7 , Facility.objects.filter(partner_id = partner[i] , facility_type_id = 294 , facility_subtype_id = 266).count())
            database_data.write(flag , 8 , Facility.objects.filter(partner_id = partner[i] , facility_type_id = 286 , facility_subtype_id = 269).count())
            database_data.write(flag , 9 , Beneficiary.objects.filter(partner_id = partner[i] , beneficiary_type_id = 2).count())
            database_data.write(flag , 10 , Beneficiary.objects.filter(partner_id = partner[i] , beneficiary_type_id = 3).count())
            database_data.write(flag , 11 , Beneficiary.objects.filter(partner_id = partner[i] , beneficiary_type_id = 4).count()) 
            incre = flag1 - flag
            flag = flag + incre + 1                   
            
        except Exception as e:
            print (e)
            import ipdb ; ipdb.set_trace()
                    
    
    wb.save('partnergpdata.xlsx')





def partner_gpdata_mapping(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('partnergpdata_122')
    database_data.write(0,0  ,'Partner Name' )
    database_data.write(0,1  , 'Partner Id' )
    database_data.write(0,2  , 'Partner Region' )
    database_data.write(0,3  , 'Partner CRY ADMIN ID' )
    database_data.write(0,4  , 'Location Tagged')
    database_data.write(0,5  , 'Location ID')
    database_data.write(0,6  , 'ACTIVE')
    sheet = location_book.sheet_by_index(2)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    partner = Partner.objects.all()
    flag = 1
    for i in range(len(partner)):
        try:
            
            flag1 = 0
            database_data.write(flag , 0 , partner[i].name)
            database_data.write(flag , 1 , partner[i].id )
            database_data.write(flag , 2 , partner[i].region.name)
            database_data.write(flag , 3 , partner[i].partner_id)
            p = PartnerBoundaryMapping.objects.filter(partner = partner[i])
            if p:
                location_id_list = list(p.values_list('object_id' , flat = True))
                location_id = str(location_id_list).strip('[]')
                location_data_list = [str(Boundary.objects.get(id = i).name) for i in location_id_list]
                location_data = ','.join(location_data_list)
            else:
                location_data = ''
                location_id = ''
            database_data.write(flag , 4 , location_data)
            database_data.write(flag , 5 , location_id)
            database_data.write(flag , 5 , partner[i].active)
            flag = flag + 1            
        except Exception as e:
            print (e)
            import ipdb ; ipdb.set_trace()
    wb.save('partnergpdata.xlsx')

