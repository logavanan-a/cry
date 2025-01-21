import xlrd,xlwt
from xlutils.copy import copy as x1_copy

from masterdata.models import *
from partner.models import *
from survey.models import *


new_list = []
new_list_n = []  
list_cry_admin_id = []
count = 0

#function for updating the location data
def update_check_location_data():
    path = input("File Path ")
    book = xlrd.open_workbook(path)
    print(book.sheet_names())
    sheet = book.sheet_by_index(0)
    empty_list = []
    count_district = 0
    import ipdb ; ipdb.set_trace()
    flag = False
    count_gp = 0
    count_village = 0
    count_block = 0
    count_hamlet = 0
    
    for row in range(sheet.nrows):
        if row == 0:
            continue
        else:
            state_obj = None
            district_obj = None
            block_obj = None
            gp_obj = None
            hamlet_obj = None
            empty_list.append(sheet.row_values(row))
        current_list = empty_list[-1]
        try :
            if current_list[1]:
                state_obj = Boundary.objects.get_or_none(id = int(current_list[1]))
                child_district_boundary_name = list(Boundary.objects.filter(parent = state_obj , active = 2 , boundary_level = 3 ).values_list('name' , flat = True))
                if current_list[3]:
                    state_obj.cry_admin_id = int(current_list[3])
                    state_obj.save()
                if current_list[4]:
                    state_obj.name = str(current_list[4])
                    state_obj.save()
                if current_list[2] == 'Bihar':
                    import ipdb ; ipdb.set_trace()
                    
                    
                    
                    
                if current_list[6]:
                    district_obj = Boundary.objects.get(id = int(current_list[6]))
                    if current_list[8]:
                        district_obj.cry_admin_id = int(current_list[8])
                        district_obj.save()
                    if current_list[9]:
                        district_obj.name = str(current_list[9])
                        district_obj.save()
                if not current_list[6] and current_list[7]:
                    if current_list[7] in child_district_boundary_name:
                        try:
                            district_obj_list = list(Boundary.objects.filter(name = current_list[7] , parent = state_obj , active = 2 ))
                            list1 = district_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == state_obj and i.active == 2:
                                    district_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            district_obj = list2[0]
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("district_obj =============" , count_district )
                        print("district Already Created")
                    else:
                        district_obj = Boundary.objects.create(parent = state_obj , name = current_list[7] , boundary_level = 3  )
                        district_obj.cry_admin_id = district_obj.id
                        district_obj.save()
                child_block_boundary_name = list(Boundary.objects.filter(parent = district_obj , active = 2 , boundary_level = 4).values_list('name' , flat = True))
                        

                        
                if current_list[11]:
                    block_obj = Boundary.objects.get(id = int(current_list[11]))
                    if current_list[13]:
                        block_obj.cry_admin_id = int(current_list[13])
                        block_obj.save()
                    if current_list[14]:
                        block_obj.name = str(current_list[14])
                        block_obj.save()
                if not current_list[11] and current_list[12]:
                    if current_list[12] in child_block_boundary_name:
                        try:
                            block_obj_list = list(Boundary.objects.filter(name = current_list[12] , parent = district_obj , active = 2 ).filter(parent__parent = state_obj))
                            list1 = block_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == district_obj and i.parent.parent == state_obj and i.active == 2:
                                    block_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("block " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            block_obj = list2[0]
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print(" Block created ==============" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        block_obj = Boundary.objects.create(parent = district_obj , name = current_list[12] , boundary_level = 4 , content_type = content_obj , object_id = 17 )
                        block_obj.cry_admin_id = block_obj.id
                        block_obj.save()
                child_gp_boundary_name = list(Boundary.objects.filter(parent = block_obj, active = 2 , boundary_level = 5).values_list('name' , flat = True))
                
                
                
                
                
                if not current_list[16] == '' and current_list[16]:
                    gp_obj = Boundary.objects.get(id = int(current_list[16]))
                    if current_list[18]:
                        gp_obj.cry_admin_id = int(current_list[18])
                        gp_obj.save()
                    if current_list[19]:
                        gp_obj.name = str(current_list[19])
                        gp_obj.save()
                if not current_list[16] and current_list[17]:
                    if current_list[17] == 'RaipurBujurg':
                        import ipdb;ipdb.set_trace()
                    if current_list[17] in child_gp_boundary_name:
                        try:
                            gp_obj_list = list(Boundary.objects.filter(name = current_list[17] , parent = block_obj).filter(parent__parent = district_obj))
                            list1 = gp_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == block_obj and i.parent.parent == district_obj:
                                    gp_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("block " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            gp_obj = list2[0]
                            gp_obj.active = 2
                            gp_obj.save()
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("gp_created================" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        gp_obj = Boundary.objects.create(parent = block_obj , name = current_list[17] , boundary_level = 5 , content_type = content_obj , object_id = 17 )
                        gp_obj.cry_admin_id = gp_obj.id
                        gp_obj.save()
                child_village_boundary_name = list(Boundary.objects.filter(parent = gp_obj , active = 2 , boundary_level = 6).values_list('name' , flat = True))
                
                
                
                if not current_list[21] == '' or current_list[21]:
                    village_obj = Boundary.objects.get(id = int(current_list[21]))
                    if current_list[23]:
                        village_obj.cry_admin_id = int(current_list[23])
                        village_obj.save()
                    if current_list[24]:
                        village_obj.name = str(current_list[14])
                        village_obj.save()
                if not current_list[21] and current_list[22]:
                    if current_list[22] in child_village_boundary_name:
                        try:
                            village_obj_list = list(Boundary.objects.filter(name = current_list[22] , parent = gp_obj , active = 2 ).filter(parent__parent = block_obj))
                            list1 = village_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == gp_obj and i.parent.parent == block_obj :
                                    village_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("village " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            village_obj = list2[0]
                            village_obj.active = 2
                            village_obj.save()
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("village_obj already created ===================" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        village_obj = Boundary.objects.create(parent = gp_obj , name = current_list[22] , boundary_level = 6 , content_type = content_obj , object_id = 17 )
                        village_obj.cry_admin_id = village_obj.id
                        village_obj.save()
                child_hamlet_boundary_name = list(Boundary.objects.filter(parent = village_obj , active = 2 , boundary_level = 7).values_list('name' , flat = True))
                
                
                 
                if not current_list[26] == '' and current_list[26]:
                    hamlet_obj = Boundary.objects.get(id = int(current_list[26]))
                    
                    if current_list[28]:
                        hamlet_obj.cry_admin_id = int(current_list[28])
                        hamlet_obj.save()
                    if current_list[29]:
                        
                        hamlet_obj.name = str(current_list[29])
                        hamlet_obj.save()
                if not current_list[26] and current_list[27]:
                    if current_list[27] in child_hamlet_boundary_name:
                        try:
                            if current_list[27] == 'Angara':
                                import ipdb; ipdb.set_trace()
                            hamlet_obj_list = list(Boundary.objects.filter(name = current_list[27] , boundary_level = 7 ))
                            if current_list[27] == 'Pallapu Lanka':
                                import ipdb ; ipdb.set_trace()
                            list1 = hamlet_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == village_obj and i.parent.parent == gp_obj:
                                    hamlet_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print(" hamlet new place " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                                else:
                                    if i.parent.boundary_level == 5:
                                        i.delete()
                                    else:
                                        i.active = 0
                                        i.save()
                            hamlet_obj = list2[0]
                            hamlet_obj.active = 2
                            hamlet_obj.save()
                            if hamlet_obj.id == 5106:
                                print("am here")
                                import ipdb; ipdb.set_trace()
                                hamlet_obj.parent = village_obj
                                hamlet_obj.save()
                            
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            pass
                        count_district += 1
                        print("hamlet_obj already created " , count_district)
                        print("hamlet object id ===========" , hamlet_obj.id)
                        print("hamlet object name ===========" , hamlet_obj.name)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        hamlet_obj = Boundary.objects.create(parent = village_obj , name = current_list[27] , boundary_level = 7 ,content_type = content_obj , object_id = 17)
                        hamlet_obj.cry_admin_id = hamlet_obj.id
                        hamlet_obj.save()
            new_list_n = empty_list.pop()
        except:
            global count 
            count += 1
            print("count=======================" , count)
            new_list = empty_list.pop()











#state_validated
def check_and_count_state(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('state2_validated')
    database_data.write(0,0,'region code' )
    database_data.write(0,1  , 'region' )
    database_data.write(0,2  , 'State' )
    database_data.write(0,3, 'State Code')
    database_data.write(0,4, 'Sysytem Code')
    database_data.write(0,5,'flag')
    database_data.write(0,6,'missing and fixed')
    sheet = location_book.sheet_by_index(0)
    total_rows = sheet.nrows
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b = Boundary.objects.get(name__icontains = str(sheet.row_values(row)[2]) , boundary_level = 2)
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[3])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[3])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,6, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                database_data.write(row , 0 , b.region_id)
                database_data.write(row , 1 , b.region.name)
                database_data.write(row , 2 , b.name)
                database_data.write(row , 3 , int(b.cry_admin_id))
                database_data.write(row , 4 , b.id)
                database_data.write(row,5,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 0 , sheet.row_values(row)[0])
                database_data.write(row , 1 , str(sheet.row_values(row)[1]))
                database_data.write(row , 2 , str(sheet.row_values(row)[2]))
                database_data.write(row , 3 , sheet.row_values(row)[3])
                database_data.write(row , 5 , 0)
                database_data.write(row , 6 , e.message)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    wb.save('location.xlsx')











#district_validated
path = "location.xlsx"
count = 0
successcount = 0
def check_and_count_district(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('district5_validated')
    database_data.write(0,0,'State Code' )
    database_data.write(0,1  , 'District' )
    database_data.write(0,2  , 'District Code' )
    database_data.write(0,3, 'Sysytem Id')
    database_data.write(0,4,'flag')
    database_data.write(0,6,'missing and fixed')
    sheet = location_book.sheet_by_index(1)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b_filter = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(sheet.row_values(row)[0]) , boundary_level = 3)
                if b_filter:
                    for i in b_filter:
                        if str(i.name.lower()) == str(sheet.row_values(row)[1].lower()):
                            b = i
                            flag = 1
                        if flag == 0:
                            raise Exception
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[2])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[2])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,6, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                if int(float(b.parent.cry_admin_id)) != sheet.row_values(row)[0]:
                    pusuccesscount += 1
                    print("Incorrect parent saved continue")
                    print("pusuccesscount============== pusuccesscount" , pusuccesscount)
                    database_data.write(row , 7 ,'incorrect parent saved')
                    continue
                database_data.write(row , 0 , b.parent.cry_admin_id)
                database_data.write(row , 1 , b.name)
                database_data.write(row , 2 , b.cry_admin_id)
                database_data.write(row , 3 , b.id)
                database_data.write(row,4,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 1 , sheet.row_values(row)[0])
                database_data.write(row , 2 , str(sheet.row_values(row)[1]))
                database_data.write(row , 3 , sheet.row_values(row)[1])
                database_data.write(row , 4 , 0)
                database_data.write(row , 6 , e.message)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    wb.save('location.xlsx')
    


#block_validated
def check_and_count_block(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('block_validated')
    database_data.write(0,0,'District Code' )
    database_data.write(0,1  , 'Block' )
    database_data.write(0,2  , 'Block Code' )
    database_data.write(0,3, 'System Id')
    database_data.write(0,4,'flag')
    database_data.write(0,6,'missing and fixed')
    sheet = location_book.sheet_by_index(2)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b_filter = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(float(sheet.row_values(row)[0])) , object_id = 17  )
                for i in b_filter:
                    cai = int(filter(lambda x: x.isdigit(), str(i.cry_admin_id)))
                    if cai == int(sheet.row_values(row)[2]):
                        b = i
                        flag = 1
                    if flag == 0:
                        raise Exception
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[2])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[2])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,6, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                if int(float(b.parent.cry_admin_id)) != sheet.row_values(row)[0]:
                    pusuccesscount += 1
                    print("Incorrect parent saved continue")
                    print("pusuccesscount============== pusuccesscount" , pusuccesscount)
                    database_data.write(row , 7 ,'incorrect parent saved')
                    continue
                database_data.write(row , 0 , b.parent.cry_admin_id)
                database_data.write(row , 1 , b.name)
                database_data.write(row , 2 , b.cry_admin_id)
                database_data.write(row , 3 , b.id)
                database_data.write(row,4,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 0 , sheet.row_values(row)[0])
                database_data.write(row , 1 , str(sheet.row_values(row)[1]))
                database_data.write(row , 2 , sheet.row_values(row)[2])
                database_data.write(row , 4 , 0)
                database_data.write(row , 6 , e.message)
                b1 = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(sheet.row_values(row)[0]))
                for i in range(len(b1)):
                    try:
                        database_data.write(0 , 11+i*3 , 'Distrcit Code')
                        database_data.write(0 , 12+i*3 , 'Block')
                        database_data.write(0 , 13+i*3 , 'Block Code')
                    except:
                        pass
                    database_data.write(row , 11+i*3 , b1[i].parent.cry_admin_id)
                    database_data.write(row , 12+i*3 , b1[i].name)
                    database_data.write(row , 13+i*3 , b1[i].cry_admin_id)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    
    wb.save('location.xlsx')
    


#grampanchayat_validated
def check_and_count_grampanchayat(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('grampanchayat_validated')
    database_data.write(0,0,'District Code' )
    database_data.write(0,1  , 'Block Code' )
    database_data.write(0,2  , 'GramPanchayat' )
    database_data.write(0,3  , 'GramPanchayat Code' )
    database_data.write(0,4, 'System Id')
    database_data.write(0,5,'flag')
    database_data.write(0,7,'missing and fixed')
    sheet = location_book.sheet_by_index(3)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b_filter = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[2]) , parent__cry_admin_id = int(float(sheet.row_values(row)[1])) , object_id = 17 , parent__parent__cry_admin_id = int(float(sheet.row_values(row)[0])) )
                for i in b_filter:
                    cai = int(filter(lambda x: x.isdigit(), str(i.cry_admin_id)))
                    if cai == int(sheet.row_values(row)[3]):
                        b = i
                        flag = 1
                    if flag == 0:
                        raise Exception
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[3])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[3])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,7, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                if int(b.parent.cry_admin_id) != sheet.row_values(row)[1]:
                    pusuccesscount += 1
                    print("Incorrect parent saved continue")
                    print("pusuccesscount============== pusuccesscount" , pusuccesscount)
                    database_data.write(row , 7 ,'incorrect parent saved')
                    continue
                database_data.write(row , 0 , b.parent.parent.cry_admin_id)
                database_data.write(row , 1 , b.parent.cry_admin_id)
                database_data.write(row , 2 , b.name)
                database_data.write(row , 3 , b.cry_admin_id)
                database_data.write(row , 4 , b.id)
                database_data.write(row,5,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 0 , sheet.row_values(row)[0])
                database_data.write(row , 1 , sheet.row_values(row)[1])
                database_data.write(row , 2 , str(sheet.row_values(row)[2]))
                database_data.write(row , 3 , sheet.row_values(row)[2])
                database_data.write(row , 5 , 0)
                database_data.write(row , 7 , e.message)
                b1 = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(sheet.row_values(row)[0]))
                for i in range(len(b1)):
                    try:
                        database_data.write(0 , 11+i*3 , 'District Code')
                        database_data.write(0 , 12+i*3 , 'Block Code')
                        database_data.write(0 , 13+i*3 , 'GramPanchayat')
                        database_data.write(0 , 14+i*3 , 'GramPanchayat Code')
                    except:
                        pass
                    database_data.write(row , 11+i*3 , b1[i].parent.cry_admin_id)
                    database_data.write(row , 12+i*3 , b1[i].name)
                    database_data.write(row , 13+i*3 , b1[i].cry_admin_id)
                    database_data.write(0 , 14+i*3 , b1[i].cry_admin_id)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    
    wb.save('location.xlsx')
    

#village_validated
def check_and_count_village(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('village_validated')
    database_data.write(0,0,'District Code' )
    database_data.write(0,1  , 'Block Code' )
    database_data.write(0,2  , 'GramPanchayat Code' )
    database_data.write(0,3  , 'Village' )
    database_data.write(0,4  , 'Village Code' )
    database_data.write(0,5, 'System Id')
    database_data.write(0,6,'flag')
    database_data.write(0,8,'missing and fixed')
    sheet = location_book.sheet_by_index(4)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b_filter = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[3]) , parent__cry_admin_id = int(float(sheet.row_values(row)[2])) , object_id = 17 , parent__parent__cry_admin_id = int(float(sheet.row_values(row)[1])) , parent__parent__parent__cry_admin_id = int(float(sheet.row_values(row)[0])) )
                for i in b_filter:
                    cai = int(filter(lambda x: x.isdigit(), str(i.cry_admin_id)))
                    if cai == int(sheet.row_values(row)[4]):
                        b = i
                        flag = 1
                    if flag == 0:
                        raise Exception
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[4])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[4])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,7, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                if int(b.parent.cry_admin_id) != sheet.row_values(row)[2]:
                    pusuccesscount += 1
                    print("Incorrect parent saved continue")
                    print("pusuccesscount============== pusuccesscount" , pusuccesscount)
                    database_data.write(row , 0 , sheet.row_values(row)[0])
                    database_data.write(row , 1 , sheet.row_values(row)[1])
                    database_data.write(row , 2 , sheet.row_values(row)[2])
                    database_data.write(row , 3 , str(sheet.row_values(row)[3]))
                    database_data.write(row , 4 , sheet.row_values(row)[4])
                    database_data.write(row , 6 , 0)
                    database_data.write(row , 7 ,'incorrect parent saved')
                    continue
                database_data.write(row , 0 , b.parent.parent.parent.cry_admin_id)
                database_data.write(row , 1 , b.parent.parent.cry_admin_id)
                database_data.write(row , 2 , b.parent.cry_admin_id)
                database_data.write(row , 3 , b.name)
                database_data.write(row , 4 , b.cry_admin_id)
                database_data.write(row , 5 , b.id)
                database_data.write(row,6,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 0 , sheet.row_values(row)[0])
                database_data.write(row , 1 , sheet.row_values(row)[1])
                database_data.write(row , 2 , sheet.row_values(row)[2])
                database_data.write(row , 3 , str(sheet.row_values(row)[3]))
                database_data.write(row , 4 , sheet.row_values(row)[4])
                database_data.write(row , 6 , 0)
                database_data.write(row , 7 , e.message)
                b1 = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(sheet.row_values(row)[0]))
                for i in range(len(b1)):
                    try:
                        database_data.write(0 , 11+i*3 , 'District Code')
                        database_data.write(0 , 12+i*3 , 'Block Code')
                        database_data.write(0 , 13+i*3 , 'GramPanchayat Code')
                        database_data.write(0 , 14+i*3 , 'village')
                        database_data.write(row , 15+i*3 , 'Village Code')
                    except:
                        pass
                    database_data.write(row , 11+i*3 , b1[i].parent.parent.parent.cry_admin_id)
                    database_data.write(row , 12+i*3 , b1[i].parent.parent.cry_admin_id)
                    database_data.write(row , 13+i*3 , b1[i].parent.cry_admin_id)
                    database_data.write(0 , 14+i*3 , b1[i].name)
                    database_data.write(0 , 15+i*3 , b1[i].cry_admin_id)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    
    wb.save('location.xlsx')
    




#hamlet_validated
def check_and_count_hamlet(path):
    import ipdb ; ipdb.set_trace()
    count = 0
    successcount = 0
    pusuccesscount = 0
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('hamlet_validated')
    database_data.write(0,0,'District Code' )
    database_data.write(0,1  , 'Block Code' )
    database_data.write(0,2  , 'GramPanchayat Code' )
    database_data.write(0,3  , 'Village Code' )
    database_data.write(0, 4 , 'hamlet' )
    database_data.write(0,5  , 'hamlet Code')    
    database_data.write(0,6, 'System Id')
    database_data.write(0,7,'flag')
    database_data.write(0,10,'missing and fixed')
    sheet = location_book.sheet_by_index(5)
    total_rows = sheet.nrows
    flag = 0
    print("total_rows" , total_rows)
    for row in range(total_rows):
        print("row=====" , row)
        if row == 0:
            pass
        else:
            try:
                b_filter = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[4]) , parent__cry_admin_id = int(float(sheet.row_values(row)[3])) , object_id = 17 , parent__parent__cry_admin_id = int(float(sheet.row_values(row)[2])) , parent__parent__parent__cry_admin_id = int(float(sheet.row_values(row)[1])) , parent__parent__parent__parent__cry_admin_id = int(float(sheet.row_values(row)[0])) )
                for i in b_filter:
                    cai = int(filter(lambda x: x.isdigit(), str(i.cry_admin_id)))
                    if cai == int(sheet.row_values(row)[5]):
                        b = i
                        flag = 1
                    if flag == 0:
                        raise Exception
                successcount = successcount + 1
                if b.cry_admin_id:
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                    b.cry_admin_id = int(sheet.row_values(row)[5])
                    b.save()
                else:
                    b.cry_admin_id = int(sheet.row_values(row)[5])
                    print("{} row number has no saved cry_admin_id saved now")
                    b.save()
                    database_data.write(row,10, "saved")
                    print('row count {} and boundary name {}  and boundary cry admin {} '.format(row , b.name , b.cry_admin_id))
                if int(b.parent.cry_admin_id) != sheet.row_values(row)[3]:
                    pusuccesscount += 1
                    print("Incorrect parent saved continue")
                    print("pusuccesscount============== pusuccesscount" , pusuccesscount)
                    database_data.write(row , 0 , sheet.row_values(row)[0])
                    database_data.write(row , 1 , sheet.row_values(row)[1])
                    database_data.write(row , 2 , sheet.row_values(row)[2])
                    database_data.write(row , 3 , sheet.row_values(row)[3])
                    database_data.write(row , 4 , str(sheet.row_values(row)[4]))
                    database_data.write(row , 5, sheet.row_values(row)[5])
                    database_data.write(row , 7 , 0)
                    database_data.write(row , 10 ,'incorrect parent saved')
                    continue
                database_data.write(row , 0 , b.parent.parent.parent.parent.cry_admin_id)
                database_data.write(row , 1 , b.parent.parent.parent.cry_admin_id)
                database_data.write(row , 2 , b.parent.parent.cry_admin_id)
                database_data.write(row , 3 , b.parent.cry_admin_id)
                database_data.write(row , 4 , b.name)
                database_data.write(row , 5 , b.cry_admin_id)
                database_data.write(row , 6 , b.id)
                database_data.write(row,7,1)
                print("SucessCount========SuccessCount" , successcount)
            except Exception as e:
                print("Row throwing exception {}".format(e.message))
                database_data.write(row , 0 , sheet.row_values(row)[0])
                database_data.write(row , 1 , sheet.row_values(row)[1])
                database_data.write(row , 2 , sheet.row_values(row)[2])
                database_data.write(row , 3 , sheet.row_values(row)[3])
                database_data.write(row , 4 , str(sheet.row_values(row)[4]))
                database_data.write(row , 5, sheet.row_values(row)[5])
                database_data.write(row , 7 , 0)
                database_data.write(row , 10 , e.message)
                b1 = Boundary.objects.filter(name__icontains = str(sheet.row_values(row)[1]) , parent__cry_admin_id = int(sheet.row_values(row)[0]))
                for i in range(len(b1)):
                    try:
                        database_data.write(0 , 12+i*3 , 'District Code')
                        database_data.write(0 , 13+i*3 , 'Block Code')
                        database_data.write(0 , 14+i*3 , 'GramPanchayat Code')
                        database_data.write(0 , 15+i*3 , 'village Code')
                        database_data.write(row , 16+i*3 , 'Hamlet')
                        database_data.write(row , 17+i*3 , 'Hamlet Code')
                    except:
                        pass
                    database_data.write(row , 12+i*3 , b1[i].parent.parent.parent.parent.cry_admin_id)
                    database_data.write(row , 13+i*3 , b1[i].parent.parent.parent.cry_admin_id)
                    database_data.write(row , 14+i*3 , b1[i].parent.parent.cry_admin_id)
                    database_data.write(row , 15+i*3 , b1[i].parent.cry_admin_id)
                    database_data.write(0 , 16+i*3 , b1[i].name)
                    database_data.write(0 , 17+i*3 , b1[i].cry_admin_id)
                count = count + 1
                print("Count =========Count " , count)
    database_data.write(row + 4 , 0 , "Success")
    
    wb.save('location.xlsx')
    




def urban_xlsx(path):
    b = Boundary.objects.filter(boundary_level = 7 , object_id = 18).exclude(cry_admin_id = None)
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('urban_mahiti_latest_data')
    database_data.write(0,0,'State cry_admin_id' )
    database_data.write(0,1  , 'State System ID' )
    database_data.write(0,2  , 'State Name' )
    database_data.write(0,3  , 'Change_state_cry_admin_id' )
    database_data.write(0, 4 , 'change_state_name' )
    database_data.write(0,5,'District cry_admin_id' )
    database_data.write(0,6  , 'District System ID' )
    database_data.write(0,7  , 'District Name' )
    database_data.write(0,8  , 'Change_District_cry_admin_id' )
    database_data.write(0, 9 , 'change_District_name' )
    database_data.write(0,10,'City cry_admin_id')
    database_data.write(0,11  , 'City System ID' )
    database_data.write(0,12  , 'City Name' )
    database_data.write(0,13  , 'Change_city_cry_admin_id' )
    database_data.write(0, 14 , 'change_city_name' )
    database_data.write(0,15,'Area cry_admin_id' )
    database_data.write(0,16  , 'Area System ID' )
    database_data.write(0,17  , 'Area Name' )
    database_data.write(0,18  , 'Change_area_cry_admin_id' )
    database_data.write(0, 19 , 'change_area_name' )
    database_data.write(0,20,'Ward cry_admin_id' )
    database_data.write(0,21  , 'Ward System ID' )
    database_data.write(0,22  , 'Ward Name' )
    database_data.write(0,23  , 'Change_ward_cry_admin_id' )
    database_data.write(0, 24 , 'change_ward_name' )
    database_data.write(0,25,'Slum cry_admin_id' )
    database_data.write(0,26  , 'Slum System ID' )
    database_data.write(0,27  , 'Slum Name' )
    database_data.write(0,28  , 'Change_slum_cry_admin_id' )
    database_data.write(0, 29 , 'change_slum_name' )
    for i in range(len(b)):
        database_data.write(i+1,0,b[i].parent.parent.parent.parent.parent.cry_admin_id )
        database_data.write(i+1,1  , b[i].parent.parent.parent.parent.parent.id)
        database_data.write(i+1,2  , b[i].parent.parent.parent.parent.parent.name )
        database_data.write(i+1,3  , '' )
        database_data.write(i+1, 4 , '' )
        
        database_data.write(i+1,5, b[i].parent.parent.parent.parent.cry_admin_id )
        database_data.write(i+1,6  , b[i].parent.parent.parent.parent.id)
        database_data.write(i+1,7  , b[i].parent.parent.parent.parent.name )
        database_data.write(i+1,8  , '' )
        database_data.write(i+1, 9 , '' )
        
        database_data.write(i+1,10, b[i].parent.parent.parent.cry_admin_id )
        database_data.write(i+1,11  ,  b[i].parent.parent.parent.id )
        database_data.write(i+1,12  , b[i].parent.parent.parent.name )
        database_data.write(i+1,13  , '')
        database_data.write(i+1, 14 , '' )
        
        database_data.write(i+1,15, b[i].parent.parent.cry_admin_id)
        database_data.write(i+1,16  ,  b[i].parent.parent.id)
        database_data.write(i+1,17 , b[i].parent.parent.name)
        database_data.write(i+1,18  , '')
        database_data.write(i+1, 19 , '' )
        
        database_data.write(i+1,20, b[i].parent.cry_admin_id )
        database_data.write(i+1,21  , b[i].parent.id )
        database_data.write(i+1,22 , b[i].parent.name )
        database_data.write(i+1,23 , '' )
        database_data.write(i+1, 24 , '' )
        
        database_data.write(i+1,25,b[i].cry_admin_id )
        database_data.write(i+1,26 , b[i].id )
        database_data.write(i+1,27 , b[i].name )
        database_data.write(i+1,28  , '' )
        database_data.write(i+1, 29 , '' )
    wb.save('urban_rural_latest_data.xlsx')
    
    
    
def rural_xlsx(path):
    b = Boundary.objects.filter(boundary_level = 7 , object_id = 17 , active = 2).exclude(cry_admin_id = None).order_by('created')
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('rural_mahiti_latest_new_data')
    database_data.write(0,0,'State cry_admin_id' )
    database_data.write(0,1  , 'State System ID' )
    database_data.write(0,2  , 'State Name' )
    database_data.write(0,3  , 'Change_state_cry_admin_id' )
    database_data.write(0, 4 , 'change_state_name' )
    database_data.write(0,5,'District cry_admin_id' )
    database_data.write(0,6  , 'District System ID' )
    database_data.write(0,7  , 'District Name' )
    database_data.write(0,8  , 'Change_District_cry_admin_id' )
    database_data.write(0, 9 , 'change_District_name' )
    database_data.write(0,10,'Block cry_admin_id')
    database_data.write(0,11  , 'Block System ID' )
    database_data.write(0,12  , 'Block Name' )
    database_data.write(0,13  , 'Change_Block_cry_admin_id' )
    database_data.write(0, 14 , 'change_Block_name' )
    database_data.write(0,15,'Grampanchayat cry_admin_id' )
    database_data.write(0,16  , 'Grampanchayat System ID' )
    database_data.write(0,17  , 'Grampanchayat Name' )
    database_data.write(0,18  , 'Change_Grampanchayat_cry_admin_id' )
    database_data.write(0, 19 , 'change_Grampanchayat_name' )
    database_data.write(0,20,'village cry_admin_id' )
    database_data.write(0,21  , 'Village System ID' )
    database_data.write(0,22  , 'Village Name' )
    database_data.write(0,23  , 'Change_village_cry_admin_id' )
    database_data.write(0, 24 , 'change_village_name' )
    database_data.write(0,25,'hamlet cry_admin_id' )
    database_data.write(0,26  , 'hamlet System ID' )
    database_data.write(0,27  , 'hamlet Name' )
    database_data.write(0,28  , 'Change_hamlet_cry_admin_id' )
    database_data.write(0, 29 , 'change_hamlet_name' )
    for i in range(len(b)):
        print(b[i])
        print(b[i].id)
        database_data.write(i+1,0,b[i].parent.parent.parent.parent.parent.cry_admin_id )
        database_data.write(i+1,1  , b[i].parent.parent.parent.parent.parent.id)
        database_data.write(i+1,2  , b[i].parent.parent.parent.parent.parent.name )
        database_data.write(i+1,3  , '' )
        database_data.write(i+1, 4 , '' )
        database_data.write(i+1,5, b[i].parent.parent.parent.parent.cry_admin_id )
        database_data.write(i+1,6  , b[i].parent.parent.parent.parent.id)
        database_data.write(i+1,7  , b[i].parent.parent.parent.parent.name )
        database_data.write(i+1,8  , '' )
        database_data.write(i+1, 9 , '' )
        database_data.write(i+1,10, b[i].parent.parent.parent.cry_admin_id )
        database_data.write(i+1,11  ,  b[i].parent.parent.parent.id )
        database_data.write(i+1,12  , b[i].parent.parent.parent.name )
        database_data.write(i+1,13  , '')
        database_data.write(i+1, 14 , '' )
        database_data.write(i+1,15, b[i].parent.parent.cry_admin_id)
        database_data.write(i+1,16  ,  b[i].parent.parent.id)
        database_data.write(i+1,17 , b[i].parent.parent.name)
        database_data.write(i+1,18  , '')
        database_data.write(i+1, 19 , '' )
        database_data.write(i+1,20, b[i].parent.cry_admin_id )
        database_data.write(i+1,21  , b[i].parent.id )
        database_data.write(i+1,22 , b[i].parent.name )
        database_data.write(i+1,23 , '' )
        database_data.write(i+1, 24 , '' )
        database_data.write(i+1,25,b[i].cry_admin_id )
        database_data.write(i+1,26 , b[i].id )
        database_data.write(i+1,27 , b[i].name )
        database_data.write(i+1,28  , '' )
        database_data.write(i+1, 29 , '' )
    wb.save('new.xlsx')
    
    






def rural_new_xlsx(path):
    b = Boundary.objects.filter(boundary_level = 7 , object_id = 17 , active = 2).exclude(cry_admin_id = None).order_by('-created')
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('rural_latest_data')
    database_data.write(0,0  , 'State Name' )
    database_data.write(0,1  , 'District Name' )
    database_data.write(0,2  , 'Block Name' )
    database_data.write(0,3,'Grampanchayat cry_admin_id' )
    database_data.write(0,4  , 'Grampanchayat System ID' )
    database_data.write(0,5  , 'Grampanchayat Name' )
    for i in range(len(b)):
        print(b[i])
        print(b[i].id)
        database_data.write(i+1,0  , b[i].parent.parent.parent.parent.parent.name )
        database_data.write(i+1,1  , b[i].parent.parent.parent.parent.name )
        database_data.write(i+1,2  , b[i].parent.parent.parent.name )
        database_data.write(i+1,3  , b[i].parent.parent.cry_admin_id)
        database_data.write(i+1,16 , b[i].parent.parent.id)
        database_data.write(i+1,17 , b[i].parent.parent.name)
    wb.save('new.xlsx')


def partner_new_xlsx(path):
    p = Partner.objects.filter(active = 2).order_by('-created')
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('partner_latest_new_data')
    database_data.write(0,0  , 'Partner Name' )
    database_data.write(0,1  , 'Partner Cry_admin_id' )
    database_data.write(0,2  , 'Partner System_id' )
    database_data.write(0,3  , 'Partner Region' )
    database_data.write(0,4  , 'Partner State Id' )
    database_data.write(0,5  , 'Partner State Cry_admin_id' )
    database_data.write(0,6  , 'Partner State Name' )
    for i in range(len(p)):
        print(p[i])
        print(p[i].id)
        database_data.write(i+1,0  , p[i].name )
        database_data.write(i+1,1  , p[i].cry_admin_id )
        database_data.write(i+1,2  , p[i].id )
        database_data.write(i+1,3  , p[i].region.name)
        database_data.write(i+1,4  , p[i].state.id)
        database_data.write(i+1,5  , p[i].state.cry_admin_id)
        database_data.write(i+1,6  , p[i].state.name )
    wb.save('new.xlsx')






def update_check_urban_location_data():
    path = input("File Path ")
    book = xlrd.open_workbook(path)
    print(book.sheet_names())
    sheet = book.sheet_by_index(1)
    empty_list = []
    count_district = 0
    import ipdb ; ipdb.set_trace()
    flag = False
    count_gp = 0
    count_village = 0
    count_block = 0
    count_hamlet = 0
    
    for row in range(sheet.nrows):
        if row == 0:
            continue
        else:
            state_obj = None
            district_obj = None
            block_obj = None
            gp_obj = None
            hamlet_obj = None
            empty_list.append(sheet.row_values(row))
        current_list = empty_list[-1]
        try :
            if current_list[1]:
                state_obj = Boundary.objects.get_or_none(id = int(current_list[1]))
                child_district_boundary_name = list(Boundary.objects.filter(parent = state_obj , active = 2 , boundary_level = 3 ).values_list('name' , flat = True))
                if current_list[3]:
                    state_obj.cry_admin_id = int(current_list[3])
                    state_obj.save()
                if current_list[4]:
                    state_obj.name = str(current_list[4])
                    state_obj.save()
                if current_list[2] == 'Bihar':
                    import ipdb ; ipdb.set_trace()
                    
                    
                    
                    
                if current_list[6]:
                    district_obj = Boundary.objects.get(id = int(current_list[6]))
                    if current_list[8]:
                        district_obj.cry_admin_id = int(current_list[8])
                        district_obj.save()
                    if current_list[9]:
                        district_obj.name = str(current_list[9])
                        district_obj.save()
                if not current_list[6] and current_list[7]:
                    if current_list[7] in child_district_boundary_name:
                        try:
                            district_obj_list = list(Boundary.objects.filter(name = current_list[7] , parent = state_obj , active = 2 ))
                            list1 = district_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == state_obj and i.active == 2:
                                    district_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            district_obj = list2[0]
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("district_obj =============" , count_district )
                        print("district Already Created")
                    else:
                        district_obj = Boundary.objects.create(parent = state_obj , name = current_list[7] , boundary_level = 3  )
                        district_obj.cry_admin_id = district_obj.id
                        district_obj.save()
                child_block_boundary_name = list(Boundary.objects.filter(parent = district_obj , active = 2 , boundary_level = 4).values_list('name' , flat = True))
                        

                        
                if current_list[11]:
                    block_obj = Boundary.objects.get(id = int(current_list[11]))
                    if current_list[13]:
                        block_obj.cry_admin_id = int(current_list[13])
                        block_obj.save()
                    if current_list[14]:
                        block_obj.name = str(current_list[14])
                        block_obj.save()
                if not current_list[11] and current_list[12]:
                    if current_list[12] in child_block_boundary_name:
                        try:
                            block_obj_list = list(Boundary.objects.filter(name = current_list[12] , parent = district_obj , active = 2 ).filter(parent__parent = state_obj))
                            list1 = block_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == district_obj and i.parent.parent == state_obj and i.active == 2:
                                    block_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("block " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            block_obj = list2[0]
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print(" Block created ==============" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        block_obj = Boundary.objects.create(parent = district_obj , name = current_list[12] , boundary_level = 4 , content_type = content_obj , object_id = 18 )
                        block_obj.cry_admin_id = block_obj.id
                        block_obj.save()
                child_gp_boundary_name = list(Boundary.objects.filter(parent = block_obj, active = 2 , boundary_level = 5).values_list('name' , flat = True))
                
                
                
                
                
                if not current_list[16] == '' and current_list[16]:
                    gp_obj = Boundary.objects.get(id = int(current_list[16]))
                    if current_list[18]:
                        gp_obj.cry_admin_id = int(current_list[18])
                        gp_obj.save()
                    if current_list[19]:
                        gp_obj.name = str(current_list[19])
                        gp_obj.save()
                if not current_list[16] and current_list[17]:
                    if current_list[17] == 'RaipurBujurg':
                        import ipdb;ipdb.set_trace()
                    if current_list[17] in child_gp_boundary_name:
                        try:
                            gp_obj_list = list(Boundary.objects.filter(name = current_list[17] , parent = block_obj).filter(parent__parent = district_obj))
                            list1 = gp_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == block_obj and i.parent.parent == district_obj:
                                    gp_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("block " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            gp_obj = list2[0]
                            gp_obj.active = 2
                            gp_obj.save()
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("gp_created================" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        gp_obj = Boundary.objects.create(parent = block_obj , name = current_list[17] , boundary_level = 5 , content_type = content_obj , object_id = 18 )
                        gp_obj.cry_admin_id = gp_obj.id
                        gp_obj.save()
                child_village_boundary_name = list(Boundary.objects.filter(parent = gp_obj , active = 2 , boundary_level = 6).values_list('name' , flat = True))
                
                
                
                if not current_list[21] == '' or current_list[21]:
                    village_obj = Boundary.objects.get(id = int(current_list[21]))
                    if current_list[23]:
                        village_obj.cry_admin_id = int(current_list[23])
                        village_obj.save()
                    if current_list[24]:
                        village_obj.name = str(current_list[14])
                        village_obj.save()
                if not current_list[21] and current_list[22]:
                    if current_list[22] in child_village_boundary_name:
                        try:
                            village_obj_list = list(Boundary.objects.filter(name = current_list[22] , parent = gp_obj , active = 2 ).filter(parent__parent = block_obj))
                            list1 = village_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == gp_obj and i.parent.parent == block_obj :
                                    village_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print("village " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                            village_obj = list2[0]
                            village_obj.active = 2
                            village_obj.save()
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            
                            pass
                        count_district += 1
                        print("village_obj already created ===================" , count_district)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        village_obj = Boundary.objects.create(parent = gp_obj , name = current_list[22] , boundary_level = 6 , content_type = content_obj , object_id = 18 )
                        village_obj.cry_admin_id = village_obj.id
                        village_obj.save()
                child_hamlet_boundary_name = list(Boundary.objects.filter(parent = village_obj , active = 2 , boundary_level = 7).values_list('name' , flat = True))
                
                
                 
                if not current_list[26] == '' and current_list[26]:
                    hamlet_obj = Boundary.objects.get(id = int(current_list[26]))
                    
                    if current_list[28]:
                        hamlet_obj.cry_admin_id = int(current_list[28])
                        hamlet_obj.save()
                    if current_list[29]:
                        
                        hamlet_obj.name = str(current_list[29])
                        hamlet_obj.save()
                if not current_list[26] and current_list[27]:
                    if current_list[27] in child_hamlet_boundary_name:
                        try:
                            if current_list[27] == 'Angara':
                                import ipdb; ipdb.set_trace()
                            hamlet_obj_list = list(Boundary.objects.filter(name = current_list[27] , boundary_level = 7 ))
                            if current_list[27] == 'Pallapu Lanka':
                                import ipdb ; ipdb.set_trace()
                            list1 = hamlet_obj_list
                            list2 = []
                            for i in list1:
                                if i.parent == village_obj and i.parent.parent == gp_obj:
                                    hamlet_obj_list.remove(i)
                                    if not list2:
                                        list2.append(i)
                                        print(" hamlet new place " , list2)
                                    else:
                                        i.active = 0
                                        if i.cry_admin_id:
                                            list_cry_admin_id.append(i.cry_admin_id)
                                        i.save()
                                else:
                                    if i.parent.boundary_level == 5:
                                        i.delete()
                                    else:
                                        i.active = 0
                                        i.save()
                            hamlet_obj = list2[0]
                            hamlet_obj.active = 2
                            hamlet_obj.save()
                            if hamlet_obj.id == 5106:
                                print("am here")
                                import ipdb; ipdb.set_trace()
                                hamlet_obj.parent = village_obj
                                hamlet_obj.save()
                            
                        except:
                            import ipdb; ipdb.set_trace()
                            print("======================================================Failed===================================")
                            pass
                        count_district += 1
                        print("hamlet_obj already created " , count_district)
                        print("hamlet object id ===========" , hamlet_obj.id)
                        print("hamlet object name ===========" , hamlet_obj.name)
                        print("Already Created")
                    else:
                        content_obj = ContentType.objects.get(model =  'masterlookup')
                        hamlet_obj = Boundary.objects.create(parent = village_obj , name = current_list[27] , boundary_level = 7 ,content_type = content_obj , object_id = 18)
                        hamlet_obj.cry_admin_id = hamlet_obj.id
                        hamlet_obj.save()
            new_list_n = empty_list.pop()
        except:
            global count 
            count += 1
            print("count=======================" , count)
            new_list = empty_list.pop()




dup_row = []
obj = []
sheet_list = []
sheet_header = []
created_obj = []
created_row = []
def partner_gp_data():
    path = "partnerareadata.xlsx"
    book = xlrd.open_workbook(path)
    print(book.sheet_names())
    sheet = book.sheet_by_index(0)
    empty_list = []
    issue_list = []
    flag = 0
    count = 0
    import ipdb ; ipdb.set_trace()
    for row in range(sheet.nrows):
        if row == 0:
            sheet_header.extend(sheet.row_values(row))
            continue
        else:
            pass
        new_list = sheet.row_values(row)
        print(new_list)
        print("row ===============================" , row)
        try:
            if not new_list[4]:
                if new_list[3] and new_list[2] and new_list[1]:
                    gp_id = int(new_list[1])
                    gp_obj = Boundary.objects.get_or_none(id = gp_id)
                    partner_obj = Partner.objects.get_or_none(partner_id = new_list[3])
                    
                    p = PartnerBoundaryMapping.objects.get_or_none(object_id = gp_id)
                if gp_obj and partner_obj and not p:
                    content_obj = ContentType.objects.get(model =  'boundary')
                    object_id = gp_id
                    p , created = PartnerBoundaryMapping.objects.get_or_create(partner = partner_obj , content_type = content_obj , object_id = object_id)
                    print(p)
                    print("===========created=====================" , created)
                    flag = 1
                    print("================ Success =========================")
                    if created == False:
                        dup_row.append(row)
                        obj.append(p.id)
                        sheet_list.append(new_list)
                    else:
                        created_obj.append(new_list)
                        created_row.append(row)
                else:
                    print("Already Gp Added to partner")
                    count = count+1
        except:
            import ipdb ; ipdb.set_trace()    
        if flag == 0:
            issue_list.append(row)
            print(issue_list)
        if flag == 1:
            flag = 0 



def partner_gp_data_export(path):
    import ipdb ; ipdb.set_trace()
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    sheet_header.append("Duplicated")
    sheet_header.append("Duplicated row")
    sheet_header.append("row created")
    
    database_data = wb.add_sheet('partner_gp_duplicates')
    for j in range(len(sheet_header)):
        database_data.write(0,j  , sheet_header[j] )
    try:
        for i in range(len(dup_row)):
            new_list = []
            new_list.extend(sheet_list[i])
            new_list.append("Duplicated")
            new_list.append(dup_row[i])
            for l in range(len(created_obj)):
                if sheet_list[i] == created_obj[l]:
                    print("found =================")
                    new_list.append(created_row[l])
                    break
            for m in range(len(new_list)):
                print("printing")
                database_data.write(i+1 , m , new_list[m])
    except:
        import ipdb;ipdb.set_trace()
           
    wb.save('partnergpdata.xlsx')

from collections import defaultdict
gp_list = []
dict1 = defaultdict()
duplicated_gp_id = []
def gp_partner():
    path = "partnergpdata.xlsx"
    book = xlrd.open_workbook(path)
    print(book.sheet_names())
    sheet = book.sheet_by_index(0)
    import ipdb ; ipdb.set_trace()
    for row in range(sheet.nrows):
        if row == 0:
            continue
        else:
            gp_id = int(sheet.row_values(row)[3])
            
            if gp_id in gp_list:
                dict1[gp_id] += 1
            else:
                dict1[gp_id] = 1
            gp_list.append(gp_id)
    for k,v in dict1.items():
        if v>1:
            duplicated_gp_id.append(k)
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('partner_gp_duplicates_1')
    database_data.write(0, 1  , 'Partner Name' )
    database_data.write(0, 2  , 'Partner ID' )
    database_data.write(0, 3  , 'Partner CRY ADMIN ID' )
    database_data.write(0, 4  , 'Partner Region' )
    database_data.write(0, 5  , 'GramPanchayat Name' )
    database_data.write(0, 6  , 'GramPanchayat ID')
    database_data.write(0, 7  , 'GramPanchayat CRY ADMIN ID' )
    flag = 0
    for row in range(sheet.nrows):
        if row==0:
            continue
        gp_id_row = int(sheet.row_values(row)[3])
        sheet_list_row = sheet.row_values(row)
        current_partner = sheet_list_row[1]
        for gps in duplicated_gp_id:    
            if gps == gp_id_row:
                print("==============gps=============" , gps)
                flag += 1
                partner_id = int(sheet_list_row[1])
                gp_id = int(sheet_list_row[3])
                p = Partner.objects.get(id = partner_id)
                b = Boundary.objects.get(id = gp_id)
                database_data.write(flag, 1  , p.name )
                database_data.write(flag, 2  , p.id )
                database_data.write(flag, 3  , sheet_list_row[0] )
                database_data.write(flag, 4  , p.region.name )
                database_data.write(flag, 5  , b.name )
                database_data.write(flag, 6  , b.id)
                database_data.write(flag, 7  , sheet_list_row[2])
    wb.save("partnergpdata.xlsx")                
     
     
     
     
def form_question():
    path = "formquestion.xlsx"
    location_book = xlrd.open_workbook(path)
    total_sheets = location_book.nsheets
    wb = x1_copy(location_book)
    database_data = wb.add_sheet('form active questions ')
    database_data.write(0, 1  , "Form Name" )
    database_data.write(0, 2  , "Form ID" )
    database_data.write(0, 3  , "Question Text" )
    database_data.write(0, 4  , "Question ID" )
    survey_ids = [49 , 57 , 70 , 1 , 3 , 2]
    survey_list = Survey.objects.filter(id__in = survey_ids)
    flag = 0
    try:
        for survey in survey_list:
            questions = Question.objects.filter(block__survey = survey , active = 2)
            for question in questions:
                flag += 1
                database_data.write( flag , 1 , survey.name)
                database_data.write( flag , 2 , survey.id)
                database_data.write( flag , 3 , question.id)
                database_data.write( flag , 4 , question.text)
    except:
        import ipdb;ipdb.set_trace()
           
    wb.save('formquestion.xlsx')




def partner_gp_data_check():
    p = PartnerBoundaryMapping.objects.filter().order_by('created')
    path = "partnergpdata.xlsx"
    book = xlrd.open_workbook(path)
    print(book.sheet_names())
    sheet = book.sheet_by_index(0)
    import ipdb ; ipdb.set_trace()
    wb = x1_copy(book)
    database_data = wb.add_sheet('partner_gp_verification')
    database_data.write(0, 1  , 'PARTNER CRY ADMIN ID')
    database_data.write(0, 2  , 'PARTNER ID')
    database_data.write(0, 3  , 'PARTNER Name')
    database_data.write(0, 4  , 'GRAMPANCHAYAT CRY ADMIN ID')
    database_data.write(0, 5  , 'GRAMPANCHAYAT ID')
    database_data.write(0, 6  , 'GRAMPANCHAYAT NAME')
    database_data.write(0, 9  , 'Remarks')
    list_of_gps = []
    for row in range(1,sheet.nrows):
        sheet_list_row = sheet.row_values(row)
        if sheet_list_row[4]:
            database_data.write(row,  9 , 'Mapping Doesnt Exist')
        else:
            try:
                if sheet_list_row[3] in list_of_gps:
                    database_data.write(row,  9 , 'Duplicate GPs')
                else:
                    pbm = p.get(object_id = int(sheet_list_row[3]))
                    database_data.write(row,  9 , 'Created')
            except:
                import ipdb ; ipdb.set_trace()
    wb.save('partnergpdata.xlsx')
