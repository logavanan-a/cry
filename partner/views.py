from __future__ import (print_function, unicode_literals)
from math import ceil
from ast import literal_eval
from itertools import chain
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import User
from django.core.mail import send_mail
from django.db import IntegrityError
from django.template import loader
from rest_framework.views import APIView
from rest_framework.generics import (CreateAPIView, ListAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView,
                                     UpdateAPIView)
from rest_framework.response import Response
from box import Box
from ccd.settings import(REST_FRAMEWORK, HOST_URL)
from masterdata.models import (
    MasterLookUp, DocumentCategory, Attachments, ContactDetail)
from masterdata.views import (CustomPagination,)
from userroles.models import(Address, UserRoles, RoleTypes)
from .models import (Partner, Project, ProjectuserDetail,
                     Registration, BankAccount, Program, ProjectLocation, PartnerUserInfo)
from .serializers import (PartnerNameSerializer, PartnerBasicDetailSerializer,
                          PartnerListingSlugSerializer,
                          ProjectCreateSerializer, ProjectHolderCreateSerializer,
                          AddressSerializer,
                          RegistrationSerializer, BankAccountSerializer,
                          PartnerDetailViewSerializer, RegistrationViewDetailSerializer,
                          BankViewDetailSerializer, AddressViewDetailSerializer,
                          ProjectSerializer,
                          ProgramSerializer, ProjectViewDetailSerializer,
                          GetPrioritySerializer, BankAccountEditSerializer,
                          PartnerNewEditSerializer,
                          ProjectLocationSerializer, AllModuleSerializer,
                          UserRolesSerializer, UserRolesDetailSerializer,PartnerUserInfoSerializer,
                          PartnerUserSerializer,)
from ccd.settings import STATIC_URL,HOST_URL
# Create your views here.

pg_size = REST_FRAMEWORK.get('PAGE_SIZE')

EMAIL_HOST_USER = 'admin@meal.mahiti.org'


def get_ceo():
    ceo_ids = RoleTypes.objects.filter(active=2,
                                       slug__iexact='ceo').values_list('id', flat=True)
    users_roles = UserRoles.objects.filter(
        active=2, role_type__id__in=ceo_ids).values_list('user__email', flat=True)
    return users_roles


def unpack_errors(errors):
    errors_ = errors
    for key, values in errors_.iteritems():
        errors_[key] = values[0]
    return errors_


class PartnerName(CreateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerNameSerializer

    def post(self, request):
        """
        To Create Program.
        ---
        parameters:
        - name: p_id
          description: Pass partner id
          required: false
          type: integer
          paramType: form
        """
        data = Box(request.data)
        serializer = PartnerNameSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            if serializer.is_valid():
                try:
                    pid = data.p_id
                except:
                    pid = 0
                if pid:
                    part = Partner.objects.get(id=pid)
                    part.name = data.name
                    part.save()
                    response = {'status': 2, 'message': 'Successfully updated',
                                'partner_id': part.id, 'unique_id': part.partner_id}
                else:
                    obj = serializer.save()
                    obj.partner_id = 'CRY-' + str(obj.id)
                    obj.save()
                    response = {'status': 2, 'message': 'Successfully created',
                                'partner_id': obj.id, 'unique_id': obj.partner_id}
            else:
                errors = serializer.errors
                if errors.keys()[0] == 'non_field_errors':
                    errors['name'] = errors.pop('non_field_errors')
                    errors['name'] = errors.get('name')[0]
                else:
                    errors['name'] = errors.get('name')[0]
                response.update(errors=errors)
        except IntegrityError:
            response.update(
                errors={'name': 'Partner with this name already exists'})
        return Response(response)


class PartnerDetailCreate(CreateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerBasicDetailSerializer

    def send_partner_mail(self, partner):
        image = HOST_URL + '/static/logo-new.jpg'
        subject = 'New Partner Created.'
        message = ''
        from_email = EMAIL_HOST_USER
        to_list = get_ceo()
        html_message = loader.render_to_string(
            'partner_create_to_ceo.html',
            {
                'image': image,
                'dobj': partner,
            }
        )
        send_mail(subject, message, from_email, to_list,
                  fail_silently=True, html_message=html_message)

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerBasicDetailSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}

        try:
            if serializer.is_valid():
                partner = Partner.objects.get(active=2, id=int(data.p_id))
                partner.region_id = int(data.region)
                partner.state_id = int(data.state)
                partner.nature_of_partner_id = int(data.nature_of_partner)

                partner.support_from = data.support_from

                if data.support_to:
                    partner.support_to = data.support_to

                partner.save()
                prog = Program.objects.create(
                    partner=partner, name=partner.name)
                proj = Project.objects.create(program=prog, name=partner.name)
                response = {'status': 2, 'message': 'Successfully created',
                            'partner_id': data.p_id, 'program_id': prog.id,
                            'project_id': proj.id}
                #self.send_partner_mail(partner)
            else:
                errors_ = {}
                
                errors = [errors_.update({k: serializer.errors.get(k)[0]})
                          for k in serializer.errors.keys()]
                response.update(errors=errors_)
        except:
            pass
        return Response(response)


class PartnerListingMasterLookUp(CreateAPIView):
    queryset = MasterLookUp.objects.filter(active=2)
    serializer_class = PartnerListingSlugSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerListingSlugSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            master = MasterLookUp.objects.filter(
                active=2, parent__slug__iexact=data.slug)
            response = [{'id': m.id, 'name': m.name,
                         'slug': m.slug or ''} for m in master]
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class ProjectDetailsCreate(CreateAPIView):
    queryset = ProjectLocation.objects.filter(active=2)
    serializer_class = ProjectCreateSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = ProjectCreateSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            if serializer.is_valid():
                proj = ProjectLocation.objects.create(project_id=data.project_id,
                                                      pre_funding_id=data.pre_funding,
                                                      fla_grm_team_id=data.fla_grm_team, remarks=data.remarks)
                proj.boundary.add(*data.boundary.split(','))
                proj.community.add(*data.community.split(','))
                proj.theme.add(*data.theme.split(','))
                proj.prominent_issues.add(*data.prominent_issues.split(','))
                proj.save()
                try:
                    if data.pre_funding_file:
                        doc, created = DocumentCategory.objects.get_or_create(name='Pre Funding Visit Done',
                                                                              slug='pre-funding-visit-done')
                        attach = Attachments.objects.create(
                            document_category=doc, attachment=data.pre_funding_file)
                        attach.content_type, attach.object_id = ContentType.objects.get_for_model(
                            proj), proj.id
                        attach.save()
                except:
                    pass
                try:
                    if data.team_file:
                        team_doc, created = DocumentCategory.objects.get_or_create(name='FLA cleared from GRM Team',
                                                                                   slug='fla-cleared-from-grm-team')
                        attach = Attachments.objects.create(
                            document_category=team_doc, attachment=data.team_file)
                        attach.content_type, attach.object_id = ContentType.objects.get_for_model(
                            proj), proj.id
                        attach.save()
                except:
                    pass
                response = {
                    'status': 2, 'message': 'successfully created', 'project_location_id': proj.id}
            else:
                response.update(errors=serializer.errors)
        except:
            pass
        return Response(response)


class ProjectHolderCreate(CreateAPIView):
    queryset = ProjectuserDetail.objects.filter(active=2)
    serializer_class = ProjectHolderCreateSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = ProjectHolderCreateSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            if serializer.is_valid():
                if not User.objects.filter(username=data.username.strip()):
                    user = User.objects.create_user(data.username, data.email)
                    proj_hold = ProjectuserDetail.objects.create(user_type=1, project_id=data.proj_id,
                                                                 name=data.name, holder_user=user)
                    contact = literal_eval(data.get_contact)
                    for con in contact:
                        con_data = Box(con)
                        con = ContactDetail.objects.create(priority=int(con_data.priority) if int(con_data.priority) <= 3 else 3,
                                                           contact_no=con_data.mobile, content_type=ContentType.objects.get_for_model(
                                                               proj_hold),
                                                           object_id=proj_hold.id)
                    response = {
                        'status': 2, 'message': 'successfully created', 'project_holder': proj_hold.id}
                else:
                    response.update(
                        errors={'username': 'Username already Exists.'})
            else:
                response.update(errors=serializer.errors)
        except:
            pass
        return Response(response)


class ProjectHolderDetailView(CreateAPIView):
    queryset = ProjectuserDetail.objects.filter(active=2)
    serializer_class = ProjectViewDetailSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = ProjectViewDetailSerializer(data=data.to_dict())
        project_holder = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            get_holder_contact = []
            proj_ = ProjectuserDetail.objects.filter(
                active=2, user_type=1, project__id=int(data.project_id)).order_by('-id')
            if proj_:
                proj_holder = proj_[0]
                proj_holder_name = proj_holder.name
                proj_contact_holder = ContactDetail.objects.filter(active=2, content_type=ContentType.objects.get_for_model(proj_holder),
                                                                   object_id=proj_holder.id).order_by('priority')
                if proj_contact_holder:
                    get_holder_contact = [{'id': ph.id, 'priority': ph.priority, 'contact_no': ph.contact_no}
                                          for ph in proj_contact_holder]
                project_holder = {'id': proj_holder.id, 'active': proj_holder.active, 'project_holder': proj_holder_name,
                                  'project_id': proj_holder.project.id if proj_holder.project else '',
                                  'project_name': proj_holder.project.name if proj_holder.project else '',
                                  'username': proj_holder.holder_user.username if proj_holder.holder_user else '',
                                  'email': proj_holder.holder_user.email if proj_holder.holder_user else '',
                                  'contacts': get_holder_contact}
            else:
                project_holder.update(
                    errors='No Data for %(project_id)s id' % data.to_dict())
        else:
            project_holder.update(errors=serializer.errors)
        return Response(project_holder)


class PartnerAddressCreate(CreateAPIView):
    queryset = Address.objects.filter(active=2)
    serializer_class = AddressSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = AddressSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            partner_ = Partner.objects.filter(active=2, id=int(data.p_id))
            if partner_:
                partner = partner_[0]
                get_previous_address = Address.objects.filter(active=2,
                                                              content_type=ContentType.objects.get_for_model(
                                                                  Partner),
                                                              object_id=int(data.p_id))
                if get_previous_address:
                    ofce = None
                else:
                    ofce = 1
                addr = serializer.save()
                addr.content_type, addr.object_id = ContentType.objects.get_for_model(
                    partner), partner.id
                addr.office = ofce
                addr.save()
                response = {'status': 2, 'message': 'successfully created',

                        'partner_id': partner.id, 'office_type': addr.office,
                        'address_type':addr.address_type.id if addr.address_type else 0}
            else:
                response.update(
                    errors='No Partner for this %(p_id)s' % data.to_dict())
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class RegistrationCreate(CreateAPIView):
    queryset = Registration.objects.filter(active=2)
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        """
        To Edit the Program.
        ---
        parameters:
        - name: attachment
          description: Pass attachment
          required: false
          type: file
          paramType: form
        - name: p_id
          description: Pass partner id
          required: false
          type: integer
          paramType: form
        """
        data = Box(request.data)
        serializer = RegistrationSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            partner_ = Partner.objects.filter(active=2, id=int(data.p_id))
            if partner_:
                partner = partner_[0]
                get_registration = Registration.objects.filter(active=2, reg_type_id=int(data.reg_type),
                                                               content_type=ContentType.objects.get_for_model(
                                                                   Partner),
                                                               object_id=int(data.p_id))
                if get_registration:
                    response.update(errors={'reg_type': get_registration[
                                    0].reg_type.name + ' already exists for this partner: %s' % partner.name})
                else:
                    reg = serializer.save()
                    if data.exp_date:
                        reg.exp_date = data.exp_date
                    if data.attachment:
                        reg.attachment = data.attachment
                    reg.content_type, reg.object_id = ContentType.objects.get_for_model(
                        partner), partner.id
                    reg.save()
                    response = {
                        'status': 2, 'message': 'successfully created', 'partner_id': partner.id}
            else:
                response.update(
                    errors='No Partner for this %(p_id)s' % data.to_dict())
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class BankAccountCreate(CreateAPIView):
    queryset = BankAccount.objects.filter(active=2)
    serializer_class = BankAccountSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = BankAccountSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            partner_ = Partner.objects.filter(active=2, id=int(data.p_id))
            if partner_:
                partner = partner_[0]
                if 1 == int(data.priority) and BankAccount.objects.filter(priority=1, content_type=ContentType.objects.get_for_model(Partner), object_id=int(data.p_id)):
                    response.update(errors={
                                    'priority': 'Primary Bank Account is already their for this partner: %s' % partner.name})
                else:
                    bank = serializer.save()
                    bank.content_type, bank.object_id = ContentType.objects.get_for_model(
                        partner), partner.id
                    bank.save()
                    response = {
                        'status': 2, 'message': 'successfully created', 'partner_id': partner.id}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class PartnerList(ListAPIView):
    queryset = Partner.objects.filter()
    serializer_class = PartnerBasicDetailSerializer

    @staticmethod
    def get_project(p_id):
        prog = Project.objects.filter(program__partner__id=p_id)
        if prog:
            id_ = prog[0].id
        else:
            id_ = ''
        return id_

    @staticmethod
    def get_program(p_id):
        pro = Program.objects.filter(partner__id=p_id)
        if pro:
            id_ = pro[0].id
        else:
            id_ = ''
        return id_

    def get(self, request):

        queryset = self.get_queryset().order_by('-id')
        if self.request.GET.get('name'):
            queryset = queryset.filter(active=2,name__icontains=self.request.GET.get('name'))
        if self.request.GET.get('cryadmin'):
            queryset = queryset.filter(active=2,partner_id__icontains=self.request.GET.get('cryadmin'))
        if self.request.GET.get('stateid'):
            queryset = queryset.filter(active=2,state_id=self.request.GET.get('stateid'))
        if self.request.GET.get('natureid'):
            queryset = queryset.filter(active=2,nature_of_partner_id=self.request.GET.get('natureid'))
            
        response = [{'id': part.id, 'name': part.name, 'partner_id': part.partner_id,
                     'active': part.active,
                     'program_id': self.get_program(part.id), 'project_id': self.get_project(part.id),
                     'project_name': part.get_project_name(),'state':part.state.name if part.state else '','nature':part.nature_of_partner.name if part.nature_of_partner else ''}
                    for part in queryset]
        get_page = ceil(float(len(response)) / float(pg_size))
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(response, request)
        return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 14, get_page)


class PartnerViewDetail(CreateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went wrong'}
        serializer = PartnerDetailViewSerializer(data=data.to_dict())
        if serializer.is_valid():
            part_ = Partner.objects.filter(active=2, id=data.p_id)
            if part_:
                response = {'status': 2, 'message': 'Successfully retrieved'}
                part = part_[0]
                part_name = part.name
                part_partner_id = part.partner_id
                part_region_id = part.region.id if part.region else 0
                part_region_name = part.region.name if part.region else ''
                part_state = part.state.id if part.state else 0
                part_state_name = part.state.name if part.state else ''
                part_nature_of_partner = part.nature_of_partner.id if part.nature_of_partner else 0
                part_nature_of_partner_name = part.nature_of_partner.name if part.nature_of_partner else ''
                part_status = part.status.id if part.status else 0
                part_status_name = part.status.name if part.status else ''
                part_support_from = part.support_from.strftime(
                    '%Y-%m-%d') if part.support_from else ''
                part_support_to = part.support_to.strftime(
                    '%Y-%m-%d') if part.support_to else ''
                response.update(partner_id=part.id, name=part_name, unique_id=part_partner_id, region=part_region_id,
                                state=part_state, nature_of_partner=part_nature_of_partner, status=part_status,
                                region_name=part_region_name,
                                state_name=part_state_name,
                                nature_of_partner_name=part_nature_of_partner_name,
                                status_name=part_status_name,
                                support_from=part_support_from, support_to=part_support_to)
            else:
                response.update(
                    error='No partner Avaiable for this %(p_id)s' % request.data)
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class RegistrationList(CreateAPIView):
    queryset = Registration.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = request.data
        reg = Registration.objects.filter(
            active=2, object_id=int(data.get('p_id')))
        response = [{'id': r.id, 'active': r.active, 'type': r.reg_type.name if r.reg_type else '', 'status': r.status.name if r.status else '',
                     'name': r.name, 'expiry': r.exp_date.strftime('%Y-%m-%d') if r.exp_date else '', 'date_reg': r.date_of_registered.strftime('%Y-%m-%d')}
                    for r in reg]
        get_page = ceil(float(len(response)) / float(pg_size))
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(response, request)
        return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 17, get_page)


class RegistrationViewDetail(CreateAPIView):
    queryset = Registration.objects.filter(active=2)
    serializer_class = RegistrationViewDetailSerializer

    def post(self, request):
        data = request.data
        response = {'status': 0, 'message': 'Something went wrong'}
        reg = Registration.objects.filter(active=2, id=int(data.get('reg_id')))
        if reg:
            r = reg[0]
            response = {'status': 2, 'message': 'successfully retrieved',
                        'id': r.id, 'type': r.reg_type.name if r.reg_type else '',
                        'type_id': r.reg_type.id if r.reg_type else '',
                        'reg_status': r.status.name if r.status else '',
                        'reg_status_id': r.status.id if r.status else '',
                        'name': r.name,
                        'attachment': HOST_URL + '/' + r.attachment.url if r.attachment else '',
                        'expiry': r.exp_date.strftime('%Y-%m-%d') if r.exp_date else '',
                        'date_reg': r.date_of_registered.strftime('%Y-%m-%d')}
        else:
            response.update(
                error='No registration Avaiable for this %(reg_id)s id' % request.data)
        return Response(response)


class BankAccountList(CreateAPIView):
    queryset = BankAccount.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = request.data
        get_bank = BankAccount.objects.filter(
            active=2, object_id=int(data.get('p_id'))).order_by('priority')
        response = [{'account_number': bn.account_number,
                     'account_type': bn.account_type.name,
                     'bank_name': bn.bank.name if bn.bank else '',
                     'branch_name': bn.branch_name,
                     'ifsc_code': bn.ifsc_code,
                     'active': bn.active,
                     'fund_type': bn.fund_type.id if bn.fund_type else 0,
                     'fund_type_name': bn.fund_type.name if bn.fund_type else '',
                     'priority': bn.priority, 'id': bn.id} for bn in get_bank]
        get_page = ceil(float(len(response)) / float(pg_size))
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(response, request)
        return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 18, get_page)


class BankViewDetail(CreateAPIView):
    queryset = BankAccount.objects.filter(active=2)
    serializer_class = BankViewDetailSerializer

    def post(self, request):
        data = request.data
        response = {'status': 0, 'message': 'Something went wrong'}
        bank = BankAccount.objects.filter(id=int(data.get('bank_id')))
        if bank:
            bn = bank[0]
            response = {'account_number': bn.account_number,
                        'account_type_id': bn.account_type.id if bn.account_type else '',
                        'account_type_name': bn.account_type.name if bn.account_type else '',
                        'bank_name': bn.bank_name,
                        'branch_name': bn.branch_name,
                        'fund_type': bn.fund_type.id if bn.fund_type else 0,
                        'fund_type_name': bn.fund_type.name if bn.fund_type else '',
                        'ifsc_code': bn.ifsc_code,
                        'priority': bn.priority, 'id': bn.id,
                        'remarks':bn.remarks}
        else:
            response.update(
                error='No Bank object Avaiable for this %(bank_id)s id' % request.data)
        return Response(response)


class AddressListing(CreateAPIView):
    queryset = Address.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = request.data
        get_addr = Address.objects.filter(active=2, object_id=int(data.get(
            'p_id')), content_type=ContentType.objects.get(app_label="partner", model="partner"))
        response = [{'address1': gd.address1, 'address2': gd.address2,
                     'active': gd.active,
                     'boundary': gd.boundary.id if gd.boundary else '',
                     'pincode': gd.pincode, 'id': gd.id, 'address_type': gd.address_type.id if gd.address_type else 0} for gd in get_addr]
        get_page = ceil(float(len(response)) / float(pg_size))
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(response, request)
        return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 19, get_page)


class AddressViewDetail(CreateAPIView):
    queryset = Address.objects.filter(active=2)
    serializer_class = AddressViewDetailSerializer

    def post(self, request):
        data = request.data
        response = {'status': 0, 'message': 'Something went wrong'}
        add = Address.objects.filter(id=int(data.get('address_id')))
        if add:
            master, object_id = '', 0
            gd = add[0]
            levels_listing = {2: 0,
                              3: 0,
                              4: 1,
                              5: 1,
                              6: 1,
                              7: 1}
            if gd.boundary.object_id:
                master = MasterLookUp.objects.get(
                    id=gd.boundary.object_id).slug
                object_id = gd.boundary.object_id
            response = {'address1': gd.address1, 'address2': gd.address2,
                        'location_type_id': object_id,
                        'location_type_slug': master,
                        'common_key': levels_listing.get(gd.boundary.boundary_level),
                        'boundary': gd.boundary.id if gd.boundary else '',
                        'pincode': gd.pincode, 'id': gd.id, 'office_type': gd.office,
                        'address_type':gd.address_type_id if gd.address_type else 0 }
        else:
            response.update(
                error='No Address object Avaiable for this %(bank_id)s id' % request.data)
        return Response(response)


class ProjectLocationDetail(CreateAPIView):
    queryset = ProjectLocation.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = request.data
        try:
            proj_ = ProjectLocation.objects.filter(
                active=2, project__id=int(data.get('project_id'))).order_by('-id')
            proj = proj_[0]

            proj_pre_funding = proj.pre_funding.name if proj.pre_funding else ''
            proj_fla_grm_team = proj.fla_grm_team.name if proj.fla_grm_team else ''
            proj_boundary = ','.join(
                [b.name for b in proj.boundary.all()]) if proj.boundary.all() else ''
            proj_community = ','.join(
                [c.name for c in proj.community.all()]) if proj.community.all() else ''
            proj_theme = ','.join(
                [t.name for t in proj.theme.all()]) if proj.theme.all() else ''
            proj_prominent_issues = ','.join(
                [po.name for po in proj.prominent_issues.all()]) if proj.prominent_issues.all() else ''
            proj_remarks = proj.remarks if proj.remarks else ''
            try:
                doc = DocumentCategory.objects.get(
                    slug='pre-funding-visit-done')
                attach = Attachments.objects.get(
                    document_category=doc, object_id=proj.id)
                proj_attach = attach.attachment.url if attach.attachment else ''
            except:
                proj_attach = ''
            try:
                team_doc = DocumentCategory.objects.get(
                    slug='fla-cleared-from-grm-team')
                team_attach = Attachments.objects.get(
                    document_category=team_doc, object_id=proj.id)
                proj_team = team_attach.attachment.url if team_attach.attachment else ''
            except:
                proj_team = ''
            get_part_project = {'proj_boundary': proj_boundary,
                                'proj_community': proj_community,
                                'proj_fla_grm_team': proj_fla_grm_team,
                                'proj_fla_grm_team_file': proj_team,
                                'proj_pre_funding': proj_pre_funding,
                                'proj_pre_funding_file': proj_attach,
                                'proj_prominent_issues': proj_prominent_issues,
                                'proj_remarks': proj_remarks,
                                'proj_theme': proj_theme,
                                'active': proj.active,
                                'proj_id': proj.id, 'status': 2, 'message': 'successfully retrieved.'}
        except:
            get_part_project = {'status': 0, 'message': 'something went wrong', 'errors': {
                'message': 'something went wrong.'}}
        return Response(get_part_project)


class ProjectLocationListing(CreateAPIView):
    queryset = ProjectLocation.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = request.data
        try:
            proj_ = ProjectLocation.objects.filter(
                active=2, project__id=int(data.get('project_id'))).order_by('-id')
            proj = proj_[0]

            proj_pre_funding = proj.pre_funding.id if proj.pre_funding else ''
            proj_fla_grm_team = proj.fla_grm_team.id if proj.fla_grm_team else ''
            proj_boundary = [
                int(b.id) for b in proj.boundary.all()] if proj.boundary.all() else ''
            proj_community = [
                int(c.id) for c in proj.community.all()] if proj.community.all() else ''
            proj_theme = [int(t.id) for t in proj.theme.all()
                          ] if proj.theme.all() else ''
            proj_prominent_issues = [int(po.id) for po in proj.prominent_issues.all(
            )] if proj.prominent_issues.all() else ''
            proj_remarks = proj.remarks if proj.remarks else ''
            try:
                doc = DocumentCategory.objects.get(
                    slug='pre-funding-visit-done')
                attach = Attachments.objects.get(
                    document_category=doc, object_id=proj.id)
                proj_attach = attach.attachment.url if attach.attachment else ''
            except:
                proj_attach = ''
            try:
                team_doc = DocumentCategory.objects.get(
                    slug='fla-cleared-from-grm-team')
                team_attach = Attachments.objects.get(
                    document_category=team_doc, object_id=proj.id)
                proj_team = team_attach.attachment.url if team_attach.attachment else ''
            except:
                proj_team = ''
            get_part_project = {'proj_boundary': proj_boundary,
                                'proj_community': proj_community,
                                'proj_fla_grm_team': proj_fla_grm_team,
                                'proj_fla_grm_team_file': proj_team,
                                'proj_pre_funding': proj_pre_funding,
                                'proj_pre_funding_file': proj_attach,
                                'proj_prominent_issues': proj_prominent_issues,
                                'proj_remarks': proj_remarks,
                                'proj_theme': proj_theme,
                                'active': proj.active,
                                'proj_id': proj.id, 'status': 2, 'message': 'successfully retrieved.'}
        except:
            get_part_project = {'status': 0, 'message': 'something went wrong', 'errors': {
                'message': 'something went wrong.'}}
        return Response(get_part_project)


class PartnerActions(APIView):
    """Partner Activate and Deactive."""

    def post(self, request):
        """
        API to Switch Active and Deactive.
        ---
        parameters:
        - name: part_id
          description: pass partner id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 0, 'message': 'Something went  wrong.',
                    'error': 'Object Doesn\'t exists'}
        try:
            # Activate and Deactivate the Objects.
            get_object = Partner.objects.get(id=data.get('part_id'))
            get_object.switch()
            status = {0: False, 2: True}
            user_ids = UserRoles.objects.filter(
                partner__id=data.get('part_id')).values_list('user', flat=True)
            User.objects.filter(id__in=user_ids).update(
                is_active=status.get(get_object.active))
            get_object.deactivate_project_program()
            response = {'data': {'active_id': get_object.active, 'name': get_object.get_active_display()},
                        'message': 'Successfully switched the object.'}
        except:
            pass
        return Response(response)


class CustomProjectListing(CreateAPIView):
    queryset = Project.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerDetailViewSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            proj = Project.objects.filter(
                active=2, program__partner__id=int(data.p_id))
            if proj:
                response = {'status': 2, 'message': 'Successfully retrieved'}
                response.update(
                    data=[{'id': p.id, 'name': p.name, 'active': p.active} for p in proj])
            else:
                response.update(
                    errors='No objects for this %(p_id)s id' % request.data)
        else:
            response.update(errors=serializer.errors)
        return Response(response)


class ProjectList(ListCreateAPIView):
    queryset = Project.objects.filter(
        active=2, program__partner__active=2).order_by('-program__partner__id')
    serializer_class = ProjectSerializer

    def list(self, request, *args, **kwargs):
        response = [{'id': pc.id, 'name': pc.get_partner_name()}
                    for pc in self.get_queryset()]
        get_page = ceil(float(len(response)) / float(pg_size))
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(response, request)
        return paginator.get_paginated_response(result_page, '200', 'Successfully Retreieved', 23, get_page)


class ProgramList(ListCreateAPIView):
    queryset = Program.objects.filter(active=2)
    serializer_class = ProgramSerializer


class ProjectViewDetail(RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.filter(active=2)
    serializer_class = ProjectSerializer


class ProgramViewDetail(RetrieveUpdateDestroyAPIView):
    queryset = Program.objects.filter(active=2)
    serializer_class = ProgramSerializer


class GetPriority(CreateAPIView):
    serializer_class = GetPrioritySerializer

    def post(self, request):
        data = Box(request.data)
        get_mod = {'1': Registration, '2': BankAccount}
        priority_list = {1: {1: 'Primary'}, 2: {
            2: 'Secondary'}, 3: {3: 'Others'}}
        get_objects = list(set(get_mod.get(data.model_name).objects.filter(active=2,
                                                                           object_id=int(data.object_id)).values_list('priority', flat=True)))
        get_priority_list = set(priority_list.keys()) - set(get_objects)
        if get_priority_list:
            get_priority_list.add(3)
            response = chain.from_iterable([[{'id': k, 'name': v} for k, v in priority_list.get(
                i).items()] for i in get_priority_list])
        else:
            response = [{'id': k, 'name': v}
                        for k, v in priority_list.get(3).items()]
        return Response(response)


class AddressEdit(UpdateAPIView):
    queryset = Address.objects.filter(active=2)
    serializer_class = AddressSerializer

    def update(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = AddressSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=data.to_dict(), partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            response = {
                'status': 2, 'message': 'Successfully updated for the address id: %(pk)s' % self.kwargs}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class RegistrationEdit(UpdateAPIView):
    queryset = Registration.objects.filter(active=2)
    serializer_class = RegistrationSerializer

    def update(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = RegistrationSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=data.to_dict(), partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if data.exp_date:
                instance.exp_date = data.exp_date
            if data.attachment:
                instance.attachment = data.attachment
            instance.save()
            response = {
                'status': 2, 'message': 'Successfully updated for the registration id: %(pk)s' % self.kwargs}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class BankAccountEdit(UpdateAPIView):
    queryset = BankAccount.objects.filter(active=2)
    serializer_class = BankAccountEditSerializer

    def update(self, request, *args, **kwargs):
        """
        API to Account Type.
        ---
        parameters:
        - name: account_number
          description: pass account number
          required: true
          type: string
          paramType: form
        """
        data = Box(request.data)
        serializer = BankAccountEditSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        try:
            if serializer.is_valid():
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=data.to_dict(), partial=False)
                serializer.is_valid(raise_exception=True)
                instance.account_number = data.account_number
                instance.save()
                self.perform_update(serializer)
                response = {
                    'status': 2, 'message': 'Successfully updated for the bank detail-id: %(pk)s' % self.kwargs}
            else:
                response.update(errors=unpack_errors(serializer.errors))
        except:
            response.update(
                errors={'account_number': 'Account Number already Exists.'})
        return Response(response)


class PartnerNewEdit(UpdateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerNewEditSerializer

    def update(self, request, *args, **kwargs):
        response = {}
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            response.update(serializer.data)
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class PartnerProjectLocationEdit(CreateAPIView):
    queryset = ProjectLocation.objects.filter(active=2)
    serializer_class = ProjectLocationSerializer

    def post(self, request):
        """
        API to Program Location Edit.
        ---
        parameters:
        - name: project_id
          description: pass project id
          required: true
          type: integer
          paramType: form
        """
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went  wrong.'}
        proj = ProjectLocation.objects.filter(
            active=2, project__id=int(data.project_id))
        if proj:
            response = {'status': 2, 'message': 'Updated Successfully.'}
            pro = proj[0]
            pro.pre_funding_id = data.pre_funding
            pro.fla_grm_team_id = data.fla_grm_team
            pro.boundary.clear()
            pro.boundary.add(*data.boundary.split(','))
            pro.community.clear()
            pro.community.add(*data.community.split(','))
            pro.theme.clear()
            pro.theme.add(*data.theme.split(','))
            pro.prominent_issues.clear()
            pro.prominent_issues.add(*data.prominent_issues.split(','))
            pro.remarks = data.remarks
            pro.save()
            try:
                if data.pre_funding_file:
                    doc, created = DocumentCategory.objects.get_or_create(name='Pre Funding Visit Done',
                                                                          slug='pre-funding-visit-done')
                    attach, created = Attachments.objects.get_or_create(
                        document_category=doc, content_type=ContentType.objects.get_for_model(pro), object_id=pro.id)
                    attach.attachment = data.pre_funding_file
                    attach.save()
            except:
                pass
            try:
                if data.team_file:
                    team_doc, created = DocumentCategory.objects.get_or_create(name='FLA cleared from GRM Team',
                                                                               slug='fla-cleared-from-grm-team')
                    attach, created = Attachments.objects.get_or_create(
                        document_category=team_doc, content_type=ContentType.objects.get_for_model(pro), object_id=pro.id)
                    attach.attachment = data.team_file
                    attach.save()
            except:
                pass
        else:
            response.update(errors={'project': 'Does not Exist'})
        return Response(response)


class ProjectHolderEdit(CreateAPIView):
    queryset = ProjectuserDetail.objects.filter(active=2)
    serializer_class = ProjectHolderCreateSerializer

    def post(self, request):
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went  wrong.'}
        proj_holder = ProjectuserDetail.objects.filter(
            active=2, user_type=1, project__id=int(data.proj_id)).order_by('-id')
        if proj_holder:
            response = {'status': 2, 'message': 'Updated Successfully.'}
            proj_hold = proj_holder[0]
            proj_hold.name = data.name
            proj_hold.holder_user.username = data.username
            proj_hold.holder_user.email = data.email
            proj_hold.holder_user.save()
            proj_hold.save()
            ContactDetail.objects.filter(
                active=2, object_id=proj_hold.id).order_by('priority').delete()
            for con in literal_eval(data.get_contact):
                con_data = Box(con)
                con = ContactDetail.objects.create(priority=int(con_data.priority) if int(con_data.priority) <= 3 else 3,
                                                   contact_no=con_data.mobile, content_type=ContentType.objects.get_for_model(proj_hold), object_id=proj_hold.id)
        else:
            response.update(
                errors={'projectholder': 'Project Does not Exists.'})
        return Response(response)


class AllModuleActions(CreateAPIView):
    """All Modules Activate and Deactive."""
    serializer_class = AllModuleSerializer

    def post(self, request):
        """
        API to Switch Active and Deactive.
        ---
        parameters:
        - name: object_id
          description: pass object id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        serializer = AllModuleSerializer(data=data)
        response = {'status': 0, 'message': 'Something went  wrong.',
                    'error': 'Object Doesn\'t exists'}
        if serializer.is_valid():
            try:
                models_act = {'1': Address,
                              '2': Registration,
                              '3': BankAccount,
                              '4': ProjectLocation,
                              '5': ProjectuserDetail,
                              '6': UserRoles}.get(data.get('key'))
                # Activate and Deactivate the Objects.
                get_object = models_act.objects.get(id=data.get('object_id'))
                get_object.switch()
                response = {'data': {'active_id': get_object.active, 'name': get_object.get_active_display()},
                            'message': 'Successfully switched the object.'}
            except:
                pass
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class PartnerEmployee(CreateAPIView):
    queryset = UserRoles.objects.filter(active=2)
    serializer_class = UserRolesSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = UserRolesSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        pe_roles = self.queryset().filter(active=2, role_type__code='707',
                                          partner__id=int(data.partner))
        if not pe_roles:
            if serializer.is_valid():
                pe = serializer.save()
                user = User.objects.create_user(
                    data.username, data.email, data.password)
                user.first_name = data.first_name
                user.last_name = data.last_name
                user.save()
                pe.role_type.add(*data.role_type)
                pe.user = user
                pe.user_type = 2
                pe.save()
            else:
                response.update(errors=unpack_errors(serializer.errors))
        else:
            response.update(errors={'role_type': 'Already Partner DEO role exists for the {}'.format(
                pe_roles[0].user.username)})
        return Response(response)


class PartnerEmployeeListing(CreateAPIView):
    queryset = UserRoles.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    @staticmethod
    def employee_list(get_pe):
        for p in get_pe:
            yield {'first_name': p.user.first_name, 'last_name': p.user.last_name,
                   'username': p.user.username,
                   'email': p.user.email, 'middle_name': p.middle_name, 'mobile_no': p.mobile_number,
                   'designation': ','.join([rp.name for rp in p.role_type.all()])}

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerDetailViewSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            get_pe = self.get_queryset().filter(partner__id=data.p_id)
            response = list(self.employee_list(get_pe))
            get_page = ceil(float(len(response)) / float(pg_size))
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request)
            return paginator.get_paginated_response(result_page, '200', 'Successfully Retrieved', 22, get_page)
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class PartnerEmployeeDetail(CreateAPIView):
    queryset = UserRoles.objects.filter(active=2)
    serializer_class = UserRolesDetailSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = UserRolesDetailSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong.'}
        if serializer.is_valid():
            get_pe = self.queryset().filter(partner__id=data.p_id)
            response = {'status': 2,
                        'message': 'Successfully Retrieved Detail.'}
            if get_pe:
                p = get_pe[0]
                pe_dict = {'first_name': p.user.first_name, 'last_name': p.user.last_name,
                           'email': p.user.email, 'middle_name': p.middle_name,
                           'role_type': ''.join(p.role_type.all())}
                response['data'] = pe_dict
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)

class StateRelatedPartner(ListAPIView):
    queryset = Partner.objects.filter(active=2)

    def get(self,request,state_list):
        partner_list = self.queryset.filter(state__id__in=eval(state_list)).values('id','name')
        return Response({'status':2,'partner_list':partner_list})

class CreatePartnerUserInfo(APIView):

    def post(self,request):
        """
        API to create the partner user info
        ---
        parameters:
        - name: name
          description: name of the user
          required: true
          type: string
          paramType: form
        - name: designation
          description: designation
          required: true
          type: string
          paramType: form
        - name: department
          description: department
          required: true
          type: string
          paramType: form
        - name: mobile
          description: mobile
          required: true
          type: string
          paramType: form
        - name: email
          description: email of the user
          required: true
          type: string
          paramType: form
        - name: pan
          description: pan
          required: true
          type: string
          paramType: form
        - name: adhar
          description: adhar of the user
          required: true
          type: string
          paramType: form
        - name: address
          description: designation
          required: true
          type: string
          paramType: form
        - name: remarks
          description: remarks
          required: false
          type: string
          paramType: form
        - name: partner_id
          description: partner id
          required: true
          type: integer
          paramType: form
        - name: id
          description: info id
          required: true
          type: integer
          paramType: form
        """
        data = Box(request.data)
        response = {'status': 0, 'message': 'Something went wrong.'}
        try:
            if int(request.data.get('id')) > 0:
                PartnerUserInfo.objects.filter(id=int(request.data.get('id'))).update(**data)
            else:
                data.pop('id')
                PartnerUserInfo.objects.create(**data)
            return Response({'status':2,'message':"User Info added successfully..."})
        except Exception as e:
            response['message']=e.message
            return Response(response)


class PartnerUserInfoDetail(APIView):
    """
    Retrieve, update or delete a user instance.
    """

    def get_object(self, pk):
        try:
            return PartnerUserInfo.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        user = PartnerUserSerializer(user)
        return Response(user.data)


class PartnerUserInfoList(APIView):
    def get(self,request,pk):
        p_users = PartnerUserInfo.objects.filter(partner_id=pk).values('id','name','mobile','address','pan','adhar','designation','department','email')
        return Response({'status':2,'users':p_users})

#class PartnerDatabase(APIView):
#    def post(self,request):
#        user = UserRoles.objects.get(user_id=request.POST.get('user_id')).partner.id
#        path_file = HOST_URL+STATIC_URL+"partner_database/"+str(user)+'.zip'
#        return Response({'status':2,'zipfile':path_file})


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
@csrf_exempt
def PartnerDatabase(request):
    if request.method == "POST":
        user = UserRoles.objects.get(user_id=request.POST.get('user_id')).partner.id
        path_file = HOST_URL+STATIC_URL+"partner_database/"+str(user)+'.zip'
        status = 2
    else:
        status = 0
        path_file = ""
    return JsonResponse({'status':2,'zipfile':path_file})



class NatureOfPartnerList(APIView):
    """
    Retrieve, nature_of_partner list.
    """

    def get(self, request):
        natur = list(set(Partner.objects.all().values_list('nature_of_partner_id',flat=True)))
        obj = MasterLookUp.objects.filter(id__in=natur).values('id','name')
        return Response({'status':2,'data':obj})



        
