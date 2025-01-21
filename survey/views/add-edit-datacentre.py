from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from survey.forms import *
from survey.models import *
from partner.models import *
from profiles.models import *
from masterdata.models import State

def datacentre_list(request):
    partners = Partner.objects.filter( active = 2 )
    datacentres = DataCentre.objects.all()
    program = Program.objects.filter(active=2)
    projects = Project.objects.filter(active=2)
    if request.GET.get('project') and request.GET.get('program') and request.GET.get('partner') :
        program_id = int(request.GET.get('program'))
        partner_id = int(request.GET.get('partner'))
        project_id = int(request.GET.get('project'))
        datacentres = datacentres.filter(project__id = project_id)
    elif request.GET.get('program'):
        programid = request.GET.get('program')
        datacentres = DataCentre.objects.filter(project__program__id= programid)
    elif request.GET.get('partner'):
        partnerid = request.GET.get('partner')
        datacentres = DataCentre.objects.filter(project__program__partner__id = partnerid)
#    if sub_domain() != 'hufpartners':
##        partners = partners.filter(code=sub_domain())
#        partners = Partner.objects.get_or_none(code=sub_domain())
#        partner_lock = sub_domain() != 'hufpartners'
#        userobj = UserProfile.objects.get(user=request.user)
#        if request.GET.get('project') and request.GET.get('program') :
#            program_id = int(request.GET.get('program'))
#            partner_id = partners.id
#            partnerid = request.GET.get('partner')
#            project_id = int(request.GET.get('project'))
#            if userobj.designation.code == 2:
#                p_ids = datacentres.filter(cordinator__user__id=request.user.id).values_list("project_id",flat=True)
#                projects = projects.filter(id__in=p_ids)
#                program = list(set(program.filter(project__id__in=p_ids)))
#                datacentres = datacentres.filter(project__id = project_id,cordinator__user__id=request.user.id)
#            elif userobj.designation.code == 4:
#                program = program.filter(program_officer__id=userobj.id)
#                projects = projects.filter(program__in=program)
#                datacentres = datacentres.filter(project__id = project_id)
#            elif userobj.designation.code == 3:
#                projects = projects.filter(project_manager__id = userobj.id)
#                program = list(set(program.filter(project__in=projects)))
#                datacentres = datacentres.filter(project__id = project_id)
#        else:
#            if userobj.designation.code == 2:
#                datacentres = datacentres.filter(cordinator__user__id=request.user.id)
#                p_ids = datacentres.filter(cordinator__user__id=request.user.id).values_list("project_id",flat=True)
#                projects = projects.filter(id__in=p_ids)
#                program = list(set(program.filter(project__id__in=p_ids)))
#            elif userobj.designation.code == 4:
#                program = program.filter(program_officer__id=userobj.id)
#                projects = projects.filter(program__in=program)
#                if not projects != '' or projects != None:
#                    datacentres = datacentres.filter(project__in=projects)
#            elif userobj.designation.code == 3:
#                projects = projects.filter(project_manager__id = userobj.id)
#                program = list(set(program.filter(project__in=projects)))
#                datacentres = datacentres.filter(project__in=projects)
#            else:
#                    datacentres = []
#                    projects = []
#                    program = []

#    else:

    return render(request,"survey/datacentrelist.html",locals())

def data_centre(request):
    form = DataCentreForm()
#    form1 = DataCentreLocationForm()
    state_list = State.objects.filter(active=2)
    if request.method != "POST":
        return render(request,"survey/add-edit-datacentre.html",locals())
    form = DataCentreForm(request.POST)
#    form1 = DataCentreLocationForm(request.POST)
    if form.is_valid():
        form = DataCentreForm(request.POST)
#        form1 = DataCentreLocationForm(request.POST)
        f1 = form.save(commit=False)
        f1.save()
        form.save_m2m()
#        f2 = form1.save(commit=False)
#        f2.datacentre = f1
#        f2.save()
        return HttpResponseRedirect('/close/')
    return render(request,"survey/add-edit-datacentre.html",locals())
    
def state(request, pid=''):
    # --------------------------------------------------------------------#
    # this is called when we want filter district based on state 
    # ajax function to filter district on click of state in addressform
    # using json response
    #----------------------------------------------------------------------#
    import json;
    district_obj = ''
    results ={}
    if request.is_ajax():
        district_obj = District.objects.filter(state__id=pid,active=2).values('id','name')
        results['res']=list(district_obj)
        return HttpResponse(
                json.dumps(results), content_type='application/json'
     )
     
def edit_datacentre(request,pid=''):
    edit = True
    id_edit = pid or request.POST.get('id_edit')
    state_list = State.objects.filter(active=2)
    dcobject = DataCentre.objects.get(id=int(pid))
    dlobject = dcobject.get_datacentrelocation()
    form = DataCentreForm(instance = dcobject)
#    form1 =DataCentreLocationForm(instance = dlobject)
    if request.POST:
        form = DataCentreForm(request.POST,request.FILES,instance = dcobject)
#        form1 = DataCentreLocationForm(request.POST,request.FILES,instance = dlobject)
        if form.is_valid():
            f1 = form.save(commit=False)
            f1.save()
            form.save_m2m() 
#            f2 = form1.save(commit=False)
#            f2.datacentre = f1
#            f2.save()
            return HttpResponseRedirect('/close/')
    return render(request,"survey/add-edit-datacentre.html",locals())
    
