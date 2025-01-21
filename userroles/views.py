from uuid import uuid4
import re
from math import ceil
from django.shortcuts import render
from django.apps import apps
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.template import loader
from django.core.mail import send_mail
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.utils.urls import replace_query_param
from rest_framework import generics as g
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination
from .models import (UserRoles,UserPartnerMapping)
from partner.models import Partner
from userroles.authentication import (
    ExpiringTokenAuthentication, MenuRoleTokenAuthentication)
from .serializers import (UserSerializer, LoginSerializer, UserDetailSerializer,
                          UserUpdateSerializer)
from ccd.settings import (HOST_URL, EMAIL_HOST_USER,
                          BASE_DIR, FRONT_URL, REST_FRAMEWORK)
from masterdata.models import (
    ResetActivation, Boundary, MasterLookUp, ContactDetail)
from userroles.models import (OrganizationUnit, EmergencyContactDetail,
                              EmploymentDetail, Address, ADTable)
from .ad_apis import update_ad
from ad_auth import *
from menu_decorators import *
from rest_framework import permissions
from django.db.models import Q

pg_size = REST_FRAMEWORK.get('PAGE_SIZE')


# Create your views here.
class UserLogin(APIView):

    def post(self, request, *args, **kwargs):
        """
        User Login.
        ---
        parameters:
        - name: username
          description: Username Login
          required: true
          type: string
          paramType: form
        - name: password
          description: Password for Login
          paramType: form
          required: true
          type: string
        """
        response = {}
        username = request.data['username'].lower()
        passwd = request.data['password']
        auth_ad = None
        cry_user = 0
        try:
            userobj = ADTable.objects.get(active=2,username__icontains=username)
            auth_ad = auth_ad_user(userobj, passwd)
        except:
            auth_ad = 0
        if auth_ad == 1:
            try:
                ad = ADTable.objects.get(username__icontains=username)
                response.update({'status': 1, 'admin': 1 if ad.user.is_superuser else 0, 'user_id': int(
                    ad.user.id), 'first_name': ad.user.first_name , 'cry_user' : 0})
                user_id = ad.user_id
                try:
                    userrole = UserRoles.objects.get(user_id = user_id)
                    user_type = userrole.user_type
                    usr = userrole.role_type.all()
                    if user_type == 1:
                        role_confs = RoleConfig.objects.filter(role = usr[0]).filter(menu__id__in = (13,14,15)).count()
                        if role_confs == 3:
                            cry_user = 1
                except:
                    user_type = 0
            except:
            	response.update({'status': 0, 'msg': "User not created"})
        elif auth_ad == 0:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = authenticate(username=request.data['username'], password=request.data['password'])
                if user is not None:
                    if user.is_active and user.is_superuser:
                        login(request, user)
                        response.update({'status': 1, 'admin': 1, 'user_id': int(
                            user.id), 'first_name': user.first_name , 'cry_user' : 0})
                    elif user.is_active:
                        try:
                            userrole = UserRoles.objects.get(user_id = user.id)
                            user_type = userrole.user_type
                            usr = userrole.role_type.all()
                            if user_type == 1:
                                role_confs = RoleConfig.objects.filter(role = usr[0]).filter(menu__id__in = (13,14,15)).count()
                                if role_confs == 3:
                                    cry_user = 1
                                else:
                                    cry_user = 0
                            else:
                                cry_user = 0
                        except:
                            user_type = 0
                        login(request , user)
                        response.update({'status': 1, 'admin': 0, 'user_id': int(user.id),
                                         'first_name': user.first_name , 'cry_user':cry_user,
                                         })
                    else:
                        response.update(
                            {'status': 0, 'msg': "User is inactive"})
                else:
                    response.update(
                        {'status': 0, 'msg': "Username/Password mismatch"})
            else:
                response.update({'status': 0, 'msg': "Invalid credentials"})
        return Response(response)


class UserLogout(APIView):

    @classmethod
    def post(cls, request):
        response = {}
        logout(request)
        response.update({'status': 1, 'msg': "user logged out successfully"})
        return Response()


class UserCreate(g.CreateAPIView):

    serializer_class = UserSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def post(cls, request, format=None):
        """
        API to Create New User
        ---
        parameters:
        - name: mobile_number
          description: Pass mobile_number
          required: true
          type: string
          paramType: form
        - name: organization_unit
          description: Pass organization_unit
          required: true
          type: string
          paramType: form
        - name: roles
          description: Pass roles
          required: true
          type: string
          paramType: form
        - name: ad_id
          description: Pass AD id
          required: false
          type: integer
          paramType: form
        """
        data = {}
        response_data = request.data
        serializer = UserSerializer(data=request.data)
        try:
            if serializer.is_valid():
                with transaction.atomic():
                    userobj = serializer.save()
                    userobj.set_password(response_data.get('mobile_number'))
                    userobj.save()

                    retrieve_params = {'user': userobj, 'organization_unit': OrganizationUnit.objects.get(id=int(
                        response_data.get('organization_unit'))), 'mobile_number': response_data.get('mobile_number')}
                    userrole = UserRoles.objects.create(**retrieve_params)
                    role_ids = map(int, response_data.get('roles').split(','))
                    userrole.role_type.add(*role_ids)
                    data.update({'userid': int(userobj.id), 'status': 2})
                    return Response(data)
            else:
                errors = serializer.errors
        except:
            errors = {'msg': 'Data is not valid', 'status': 0}
        return Response(errors)


class CustomPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data):
        result = {'count': self.page.paginator.count,
                  'next': self.get_next_link(data),
                  'previous': self.get_previous_link(data),
                  'objlist': data,
                  'pages': int(data[0]['pages'] if data else 0)
                  }
#        try:
#                result.update({'rfp_count':data[0]['rfp_count'],'program_count':data[0]['program_count']})
#                del result.get('objlist')[0]
#        except:
#            pass
        return Response(result)

    def get_next_link(self, data):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        return replace_query_param(HOST_URL + '/user/list/', self.page_query_param, page_number)

    def get_previous_link(self, data):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        return replace_query_param(HOST_URL + '/user/list/', self.page_query_param, page_number)


class Userlist(APIView):

    #    authentication_class = (ExpiringTokenAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def get(cls, request, format=None):
        
        try:
            userroles = UserRoles.objects.select_related('user__id' , 'user__first_name' , 'user__last_name' , 'user__email' , 'organization_unit__name' , 'organization_unit__organization_level').filter(active=2)
            if request.GET.get('name'):
                nm = request.GET.get('name')
                userroles = userroles.filter(Q(user__username__icontains=nm)|Q(user__first_name__icontains=nm)|Q(user__last_name__icontains=nm))
            if request.GET.get('roleid'):
                userroles = userroles.filter(role_type__id=request.GET.get('roleid'))
            
            response = [{'user_id': i.user.id,
                         'roles_id': i.id,
                         'first_name': i.user.first_name,
                         'last_name': i.user.last_name,
                         'email': i.user.email,
                         'mobile_number': i.mobile_number,
                         'organization_unit': i.organization_unit.name if i.organization_unit else '',
                         'roles': i.user_roles_names(),
                         'user_type': i.user_type,
                         'manage_location_status': i.managelocationstatus(),
                         'org_level': i.organization_unit.organization_level if i.organization_unit else 0,
                         'location_created': i.locationstagged(),
                         'pages': ceil(float(len(userroles)) / float(pg_size)) if userroles else 0,
                         }
                        for i in userroles]
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request)
            return paginator.get_paginated_response(result_page)
        except:
            response = [{'msg': 'Data is not valid', 'status': 0, 'pages': 1}]
        return Response(response)


class ForgetPasswordEmail(APIView):

    @classmethod
    def post(cls, request, format=None):
        """
        API to Change Password Request
        ---
        parameters:
        - name: email
          description: Enter a Registered Email ID
          required: true
          type: string
          paramType: form
        """
        status, message, response = '', '', {}
        get_email = request.data['email']
        url = FRONT_URL + "/#/resetpassword/"

        try:
            ad = ADTable.objects.get_or_none(user__email=get_email)
            if not ad:
                user = User.objects.get(email=get_email, is_active=2)
                if user and not ResetActivation.objects.filter(user=user, active=2).exists():
                    pswd_activation = ResetActivation.objects.create(
                        key=uuid4().hex, user=user)
                    html_message = loader.render_to_string(
                        BASE_DIR + '/userroles/templates/forgetpasswordlink.html',
                        {
                            'email': get_email,
                            'url': url,
                            'key': pswd_activation.key,
                        }
                    )
                    subject = 'Change Password Request'
                    message = ''
                    to_ = [get_email]
                    send_mail(subject, message, 'admin@meal.mahiti.org',
                              to_, fail_silently=True, html_message=html_message)
                    status = 0
                    message = 'Successfully Reset Mail has been sent'
                else:
                    status = 2
                    message = 'Invalid Mail-id/Request has already been sent'
            else:
                status = 0
                message = "Please contact AD-Adminstrator"
        except:
            status = 0
            message = 'Something went wrong'
        response = {'status': status, 'message': message}
        return Response(response)


class ResetPassword(APIView):

    def post(self, request, format=None):
        """
        API to Change Password Request
        ---
        parameters:
        - name: key
          description: Enter a Key
          required: true
          type: string
          paramType: form
        - name: password
          description: Enter a Password
          required: true
          type: string
          paramType: form
        - name: confirmpwd
          description: Enter a Confirm Passsword
          required: true
          type: string
          paramType: form
        """
        status, message = 2, 'Activation Key expires'
        passwd = request.data
        try:
            resetobj = ResetActivation.objects.get(key__exact=passwd['key'])
            user_mail = User.objects.get(email=resetobj.user.email)
            if resetobj and [False, True][str(passwd['password']) == str(passwd['confirmpwd'])]:
                user_mail.set_password(str(passwd['confirmpwd']))
                user_mail.save()
                status = 0
                message = "Password Successfully Reset"
                resetobj.delete()
            else:
                status = 2
                message = "Password and Comfirm Password didn't match"
        except:
            status, message
        response = {'status': status, 'message': message}
        return Response(response)


class ChangePasswordUser(APIView):
    #    api to change password of an admin or any user

    @classmethod
    def post(cls, request):
        """
        User Reset Password.
        ---
        parameters:
        - name: user_id
          description: pass user id
          required: true
          type: integer
          paramType: form
        - name: old_password
          description: User old password
          required: true
          type: string
          paramType: form
        - name: new_password
          description: user new password
          paramType: form
          required: true
          type: string
        - name: confirm_password
          description: confirm password
          paramType: form
          required: true
          type: string
        """
        data = request.data

        response = {}
        user_id = data["user_id"]
        old = data["old_password"]
        new = data["new_password"]
        conf = data["confirm_password"]
        try:
            userobj = User.objects.get(id=user_id)
            if userobj:
                if userobj != authenticate(username=userobj.username, password=old):
                    response.update(
                        {'status': 0, 'msg': " Current password is incorrect"})
                elif conf == old:
                    response.update(
                        {'status': 0, 'msg': " Current password and old password cannot be same"})
                elif conf != new:
                    response.update(
                        {'status': 0, 'msg': "Passwords doesn't match, please try again."})
                else:
                    userobj.set_password(new)
                    userobj.save()
#                    sendpasswordnotification(request,userobj)
                    response.update(
                        {'status': 1, 'success_msg': "Password updated successfully."})
        except:
            response.update({'status': 0, 'msg': "User Does not exist"})
        return Response(response)


def stripmessage(errors):
    for i, j in errors.items():
        errors[i] = j[0]
        expr = re.search(r'\w+:', errors[i])
        if expr:
            ik = expr.group().replace(':', '')
            errors[ik] = errors.pop(i)
            errors[ik] = re.sub(r'\w+:', '', errors[ik])
        return errors


class UserDetailCreate(g.CreateAPIView):

    serializer_class = UserDetailSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def post(cls, request, format=None):
        """
        API to Create New User
        """
        data = {}
        response_data = request.data
        serializer1 = UserDetailSerializer(data=request.data)
        serializer = UserSerializer(data=request.data)
        url = FRONT_URL + "/#/activateuser/"
        try:
            if serializer1.is_valid():
                if serializer.is_valid():
                    userobj = serializer.save()
                    userobj.set_password(response_data.get('mobile_number'))
                    userobj.is_active = 0
                    userobj.save()
                    activation = ResetActivation.objects.create(
                        key=uuid4().hex, user=userobj)
                    try:
                        ad_id = response_data.get('ad_id')
                        if ad_id:
                            update_ad(ad_id, userobj)
                    except:
                        pass
                    try:
                        retrieve_params = {'user': userobj,
                                           'organization_unit': OrganizationUnit.objects.get(id=int(response_data.get('organization_unit'))),
                                           'mobile_number': response_data.get('mobile_number'),
                                           'title': response_data.get('title'),
                                           'middle_name': response_data.get('middle_name'),
                                           'dob': response_data.get('dob') if response_data.get('dob') else None,
                                           'adhar_no': response_data.get('adhar_no'),
                                           'pan_no': response_data.get('pan_no'),
                                           'user_type': response_data.get('user_type'),
                                           'partner': Partner.objects.get(id=int(response_data.get('partner'))) if response_data.get('partner') else None}
                        userrole = UserRoles.objects.create(**retrieve_params)
                        role_ids = map(
                            int, response_data.get('roles').split(','))
                        userrole.role_type.add(*role_ids)
                    except:
                        pass
                    try:
                        adetail = eval(response_data.get('address'))
                        object_id = int(userobj.id)
                        content_type = ContentType.objects.get_for_model(
                            userobj)
                        user_address = Address.objects.create(**adetail)
                        user_address.object_id = object_id
                        user_address.content_type = content_type
                        user_address.save()
                    except:
                        pass
                    try:
                        edetail = {'company_name': response_data.get('company_name'),
                                   'designation_id': response_data.get('designation'),
                                   'region_id': response_data.get('region'),
                                   'reporting_to_id': response_data.get('reporting_to'),
                                   'user': userobj
                                   }
                        EmploymentDetail.objects.create(**edetail)
                    except:
                        pass
                    try:
                        demergency = {
                            'name': response_data.get('emergency_name'),
                            'relationship': response_data.get('relationship'),
                            'object_id': int(userobj.id),
                            'content_type': ContentType.objects.get_for_model(userobj)
                        }
                        emergency_detail = EmergencyContactDetail.objects.create(
                            **demergency)
                        emergency_address = eval(
                            response_data.get('emergency_address'))
                        emergency_address.update(object_id=int(emergency_detail.id),
                                                 content_type=ContentType.objects.get_for_model(emergency_detail))
                        Address.objects.create(
                            **emergency_address)
                        get_contact = eval(response_data.get('get_contact'))
                        for i in get_contact:
                            ContactDetail.objects.create(priority=i["priority"], contact_no=i[
                                                                          "mobile"], content_type=ContentType.objects.get_for_model(emergency_detail), object_id=int(emergency_detail.id))
                        data.update({'userid': int(userobj.id), 'status': 2})
                    except:
                        data.update({'userid': int(userobj.id), 'status': 2})
                    html_message = loader.render_to_string(
                        BASE_DIR + '/userroles/templates/useractivationlink.html',
                        {
                            'email': userobj.username,
                            'url': url,
                            'key': activation.key,
                            'first_name': userobj.first_name,
                            'password': userrole.mobile_number
                        }
                    )
                    subject = 'User Activation Request'
                    message = ''
                    to_ = [userobj.email]
                    send_mail(subject, message, 'admin@meal.mahiti.org',
                              to_, fail_silently=True, html_message=html_message)
                    return Response(data)
                else:
                    errors = serializer.errors
                    errors = stripmessage(errors)
                return Response(errors)
            else:
                errors = serializer1.errors
                errors = stripmessage(errors)
                return Response(errors)
        except:
            errors = {'msg': 'Data is not valid', 'status': 0}
        return Response(errors)


class UserActivation(APIView):

    def post(self, request, format=None):
        """
        API to Change Password Request
        ---
        parameters:
        - name: key
          description: Enter a Key
          required: true
          type: string
          paramType: form
        """
        status, message = 2, 'Activation Key mismatch'
        data = request.data
        try:
            resetobj = ResetActivation.objects.get_or_none(
                key__exact=data['key'])
            if resetobj:
                userobj = User.objects.get(email=resetobj.user.email)
                userobj.is_active = 2
                userobj.save()
                status = 0
                message = "Activated Successfully"
                resetobj.delete()
            else:
                status = 2
                message = "Activation Key mismatch"
        except:
            status, message
        response = {'status': status, 'message': message}
        return Response(response)


class UserDetailView(APIView):

    def post(self, request):
        """
        Ngo Credibility form view.
        ---
        parameters:
        - name: user_id
          description: Pass created_by
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            userobj = UserRoles.objects.get_or_none(user__id=user_id)
            empdetail = EmploymentDetail.objects.get_or_none(user__id=user_id)
            emergency_detail = EmergencyContactDetail.objects.get_or_none(object_id=str(user_id),
                                                                          content_type=ContentType.objects.get_for_model(user))
            main_address = {'address1': '', 'address2': '', 'boundary_id': '', 'pincode': '', 'contact_no': '',
                            'master_level': '', 'parent_id': '', 'parent_boundary_level': ''}
            response = {
                'id': int(userobj.id),
                'title': userobj.title,
                'user_type': userobj.user_type,
                'middle_name': userobj.middle_name if userobj.middle_name else '',
                'dob': userobj.dob if userobj.dob else '',
                'adhar_no': userobj.adhar_no if userobj.adhar_no else '',
                'pan_no': userobj.pan_no if userobj.pan_no else '',
                'organization_unit': int(userobj.organization_unit.id) if userobj else '',
                'roles': [int(j.id) for j in userobj.role_type.all()] if userobj else [],
                'mobile_number': userobj.mobile_number if userobj else '',
                'company_name': empdetail.company_name if empdetail and empdetail.company_name else '',
                'designation': int(empdetail.designation.id) if empdetail and empdetail.designation else '',
                'region': int(empdetail.region.id) if empdetail and empdetail.region else '',
                'reporting_to': int(empdetail.reporting_to.id) if empdetail and empdetail.reporting_to else '',
                'address': userobj.get_address() if userobj else {},
                'emergency_name': emergency_detail.name if emergency_detail else '',
                'relationship': emergency_detail.relationship if emergency_detail else '',
                'emergency_address': emergency_detail.get_emergency_address() if emergency_detail else main_address,
                'contacts': emergency_detail.get_contact_details() if emergency_detail else '' }
        except Exception as e:
            response = {'key': 0, 'msg': "Not Registered",
                        'pages': '1', 'error_msg': e.message}
        return Response(response)


class UserDetailUpdate(g.CreateAPIView):

    queryset = UserRoles.objects.filter(active=2)
    serializer_class = UserUpdateSerializer

    def post(self, request):
        """
        To Edit the User Basic Details.
        """
        status = ''
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid():
            data = request.data
            user_id = int(data.get('user_id'))
            user = User.objects.get(id=user_id)
            try:
                userobj = UserRoles.objects.get(user__id=user_id)
            except:
                pass
            try:
                userobj.title = data.get('title')
                userobj.middle_name = data.get('middle_name')
                userobj.dob = data.get('dob') if data.get('dob') else None
                userobj.adhar_no = data.get('adhar_no')
                userobj.pan_no = data.get('pan_no')
                userobj.organization_unit = OrganizationUnit.objects.get(
                    id=int(data.get('organization_unit')))
                userobj.mobile_number = data.get('mobile_number')
                userobj.save()
                roles = data.get('roles').split(',') or data.get('roles')
                roles = map(int, roles)
                userobj.role_type.clear()
                userobj.role_type.add(*roles)
                status = {'status': 2, 'message': 'Updated Successfully'}
            except:
                pass
            try:
                newaddress = eval(data.get('address'))
                address, created = Address.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(user), object_id=str(user_id))
                address.address1 = newaddress.get('address1')
                address.address2 = newaddress.get('address2')
                address.boundary = Boundary.objects.get_or_none(id=int(
                    newaddress.get('boundary_id'))) if newaddress.get('boundary_id') else None
                address.pincode = newaddress.get('pincode')
                address.save()
            except:
                pass
            try:
                empdetail, created = EmploymentDetail.objects.get_or_create(
                    user__id=user_id)
                empdetail.company_name = data.get('company_name')
                empdetail.designation = MasterLookUp.objects.get(
                    id=int(data.get('designation')))
                empdetail.region = MasterLookUp.objects.get(
                    id=int(data.get('region')))
                empdetail.reporting_to = User.objects.get(
                    id=int(data.get('reporting_to')))
                empdetail.save()
            except:
                pass
            try:
                emergency_detail, created = EmergencyContactDetail.objects.get_or_create(object_id=str(user_id),
                                                                                         content_type=ContentType.objects.get_for_model(user))
                emergency_detail.name = data.get('emergency_name')
                emergency_detail.relationship = data.get('relationship')
                emergency_detail.save()
            except:
                pass
            try:
                newaddress = eval(data.get('emergency_address'))
                address, created = Address.objects.get_or_create(content_type=ContentType.objects.get_for_model(
                    emergency_detail), object_id=str(emergency_detail.id))
                address.address1 = newaddress.get('address1')
                address.address2 = newaddress.get('address2')
                address.boundary = Boundary.objects.get(
                    id=int(newaddress.get('boundary_id')))
                address.pincode = newaddress.get('pincode')
                address.contact_no = newaddress.get('contact_no')
                address.save()
            except:
                pass


            ContactDetail.objects.filter(content_type=ContentType.objects.get_for_model(
                emergency_detail), object_id=str(emergency_detail.id)).delete()
            get_contact = eval(data.get('get_contact'))
            for i in get_contact:
                ContactDetail.objects.create(priority=i["priority"], contact_no=i[
                                                              "mobile"], content_type=ContentType.objects.get_for_model(emergency_detail), object_id=str(emergency_detail.id))

        else:
            status = {'status': 0, 'message': 'something went wrong',
                      'errors': serializer.errors}
        return Response(status)

#@has_menu_permission


class UserlistMenu(APIView):

    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)
#    authentication_class = (MenuRoleTokenAuthentication)

    @classmethod
    def get(cls, request, format=None):
        try:
            userroles = UserRoles.objects.filter(active=2)
            response = [{'user_id': i.user.id,
                         'roles_id': i.id,
                         'first_name': i.user.first_name,
                         'last_name': i.user.last_name,
                         'email': i.user.email,
                         'mobile_number': i.mobile_number,
                         'organization_unit': i.organization_unit.name if i.organization_unit else '',
                         'roles': i.user_roles_names(),
                         'pages': ceil(float(len(userroles)) / float(pg_size)) if userroles else 0,
                         }
                        for i in userroles]
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request)
            return paginator.get_paginated_response(result_page)
        except:
            response = [{'msg': 'Data is not valid', 'status': 0, 'pages': 1}]
        return Response(response)

class UserPartnerMappingManagement(APIView):
    def post(self,request):
        """
        user partner mapping api
        ---
        parameters:
        - name: user_id
          description: user id to tag the partner
          required: true
          type: integer
          paramType: integer
        - name: partner_ids
          description : Pass the partner ids here
          required: true
          type: integer
          paramType: integer
        """
        user_id = request.data.get('user_id')
        partner_list = eval(request.data.get('partner_ids'))
        upm,upms = UserPartnerMapping.objects.get_or_create(user_id=user_id)
        if not upms:
            upm.partner.clear()
        upm.partner.add(*partner_list)
        upm.save()
        return Response({'status':2,'message':'Partners Mapped Successfully'})


class GetUserRegionalPartners(APIView):
    def get(self,request,user_id):
        partner_list = []
        tagged_partners = []
        try: 
            UserRoles.objects.get(user_id=user_id)
            edr = EmploymentDetail.objects.get(user_id=user_id).region
            if edr.slug == 'national-ho':
                partner_list = list(Partner.objects.filter(active=2,state__id__in=eval(request.GET.get('sid'))).values('id','name'))
            else:
                boundary = Boundary.objects.filter(region__slug=edr.slug).values_list('id',flat=True)
                partner_list = list(Partner.objects.filter(state__id__in=boundary).values('id','name'))
            for i,v in enumerate(partner_list):
                partner_list[i] = {'value':v.get('id'),'label':v.get('name')}
            upm = UserPartnerMapping.objects.get_or_none(user_id=user_id)
            if upm:
                tagged_partners = upm.partner.ids()
            return Response({'status':2,'message':'Success','partners_list':partner_list,'tagged_partners':tagged_partners})
        except Exception as e:
            return Response({'status':0,'message':e.message,
            'partners_list':partner_list})
