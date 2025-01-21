from rest_framework import generics as g
from .serializers import (RoleTypesSerializer, ActivateSerializer, RoleConfigsSerializer,
                          RoleConfigsUpdateSerializer, UserMenuPermSerializer, OrgUnitSerializer,
                          ListingSerializer, UserLocationSerializer,)
from .models import RoleTypes, RoleConfig, UserRoles, Menus, OrganizationUnit, ADTable, OrganizationLocation
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps
from django.contrib.auth.models import User
from math import ceil
from rest_framework import authentication, permissions
from userroles.authentication import (ExpiringTokenAuthentication)
from django.contrib.contenttypes.models import ContentType
from ccd.settings import (HOST_URL, EMAIL_HOST_USER,
                          BASE_DIR, FRONT_URL, REST_FRAMEWORK)
from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import replace_query_param
from masterdata.models import (Boundary, MasterLookUp)
from .models import UserPartnerMapping
#from .user_decorators import menu_permissions

pg_size = REST_FRAMEWORK.get('PAGE_SIZE')


class CustomPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data, pages, level):
        result = {'count': self.page.paginator.count,
                  'next': self.get_next_link(data, level),
                  'previous': self.get_previous_link(data, level),
                  'objlist': data,
                  'pages': pages
                  }
        return Response(result)

    def get_next_link(self, data, level):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        get_next = {1: replace_query_param(HOST_URL + '/userroles/list/', self.page_query_param, page_number),
                    2: replace_query_param(HOST_URL + '/userroles/organization-unit/list/', self.page_query_param, page_number)}
        return get_next.get(level)

    def get_previous_link(self, data, level):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        get_previous = {1: replace_query_param(HOST_URL + '/userroles/list/', self.page_query_param, page_number),
                        2: replace_query_param(HOST_URL + '/userroles/organization-unit/list/', self.page_query_param, page_number)}
        return get_previous.get(level)


#@menu_permissions(user_id='',url_path='')
class RolesCreateAPI(g.CreateAPIView):
    """API to create Roles"""
    queryset = RoleTypes.objects.filter(active=2)
    serializer_class = RoleTypesSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)


class RolesListAPI(APIView):

    #    authentication_class = (ExpiringTokenAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def get(self, request, format=None):
        try:
            roles = RoleTypes.objects.filter(active=2)
            pages = ceil(float(len(roles)) / float(pg_size)) if roles else 0
            response = [{'id': i.id,
                         'name': i.name,
                         'code': i.code,
                         }
                        for i in roles]
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request, pages)
            if request.GET.get('key')=="all":
                response = [{'objlist':response,"pagex":"","previous":"","count":len(response),"next":""}]
                return Response(response)
            else:
                print pages
                return paginator.get_paginated_response(result_page, pages, 1)
        except Exception as e:
            response = [{'msg': e.message, 'status': 0, 'pages': 1}]
        return Response(response)


class RolesRetriveUpdateAPI(g.RetrieveUpdateAPIView):

    queryset = RoleTypes.objects.filter(active=2)
    serializer_class = RoleTypesSerializer
    lookup_field = 'pk'
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)


class ActivateAPI(g.CreateAPIView):

    serializer_class = ActivateSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """ API for activation or deactivating objects in userroles.
            obj_id : the id of the object whih has to be activated/deactivated,
            key : the name of the table """
        serializer = self.serializer_class(data=request.data)
        res = []
        if serializer.is_valid():
            try:
                data = request.data
                obj_id = data.get("obj_id")
                key = data.get("key")
                role_obj = apps.get_model(
                    'userroles', key).objects.get(id=obj_id)
                role_obj.switch()
                res = {'id': role_obj.id,
                       'status': role_obj.active, key: role_obj.name, }
            except:
                res = {'message': key + " does not exist"}
        else:
            res.append(dict(errors=serializer.errors))
        return Response(res)


class RoleConfigsAPI(g.CreateAPIView):
    serializer_class = RoleConfigsSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)
    """API to list the menu permissions for a particular role of a particular organization"""

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        res = []
        if serializer.is_valid():
            try:
                data = request.data
		role_id = int(data.get("role_id"))
                roles = RoleTypes.objects.get(id=role_id)
                role_confs = roles.get_role_config()
                for i in role_confs:
                    res.append({"id": i.id,
                                "role": role_id,
                                "menu": i.menu.name,
                                "menu_id": i.menu.id,
                                "parent_id": i.menu.parent.id if i.menu.parent else "",
                                "is_parent": "Yes" if not i.menu.parent else "No",
                                "add": i.add,
                                "edit": i.edit,
                                "view": i.view,
                                "delete": i.delete,
                                "search": i.search})
            except Exception as e:
                res = {"status": 0,
                       "message": e.message}
        else:
            res.append(dict(errors=serializer.errors))
        return Response(res)


class RoleConfigsUpdate(APIView):
    #    authentication_class = (ExpiringTokenAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)
    """API to update the permissions of menus for a particular role"""

    def post(self, request):
        """
        RoleConfigsUpdate view.
        ---
        parameters:
        - name: roles_list
          description: Pass roles_list
          required: true
          type: string
          paramType: form
        """
        roles_list = eval(request.data['roles_list'])
        res = []
        for i in roles_list:
            role_id = i.get('role')
            menu = i.get('menu_id')
            edit = eval(i.get('edit'))
            add = eval(i.get('add'))
            view = eval(i.get('view'))
            delete = eval(i.get('delete'))
            search = eval(i.get('search'))
            if(edit == True or add == True):
                view = True
            rc = {"add": add, "edit": edit, "view": view,
                  "delete": delete, "search": search}
            parent = Menus.objects.get(id=int(menu)).parent
            rc_obj = RoleConfig.objects.filter(
                role__id=role_id, menu__id=menu).update(**rc)
            childconfig = RoleConfig.objects.get(
                role__id=role_id, menu__id=menu , active = 2)
#            if parent!=None:
#                roleconf = RoleConfig.objects.get(menu=parent,role__id=int(role_id))
#                if childconfig.view == True:
#                    roleconf.view=True
#                else :
#                    roleconf.view=False
#                roleconf.save()
            res.append({"role": role_id,
                        "menu_id": menu,
                        "add": add,
                        "edit": edit,
                        "view": view,
                        "delete": delete,
                        'search': search, })

         # ** to give automatic permission for sub child menu whuch is also
         #  a parent menu based on sub child menus permissions **
        childroles = RoleConfig.objects.exclude(menu__parent=None)
        for i in childroles:
            subchilds = RoleConfig.objects.filter(
                menu__parent=i.menu, role__id=int(role_id), view=True)
            if subchilds:
                i.view = True
                i.save()
         # ** to give automatic permission for parent menu based on sub child
         #  menus permissions **
        parentmenu = RoleConfig.objects.filter(
            role__id=int(role_id), menu__parent=None)
        for i in parentmenu:
            if Menus.objects.filter(parent=i.menu, active=2):
                roles = RoleConfig.objects.filter(role__id=int(
                    role_id), menu__parent=i.menu, view=True)
                if roles:
                    i.view = True
                    i.save()
                else:
                    i.view = False
                    i.save()
            else:
                pass
        return Response(res)


class UserMenuPermissions(g.CreateAPIView):
    serializer_class = UserMenuPermSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """API to list menus for a particular user"""
        serializer = self.serializer_class(data=request.data)
        res = []
        if serializer.is_valid():
            try:
                user_id = int(request.data['user_id'])
                userobj = User.objects.get(id=user_id)
                if not userobj.is_superuser:
                    usr_role_obj = UserRoles.objects.get(user__id=user_id)
                    usr_role = usr_role_obj.role_type.ids()
    #                usr_org = OrganizationUnit.objects.get(id=usr_role_obj.organization_unit.id)
    #                usr_role = usr_org.roles.ids()
                    role_confs = RoleConfig.objects.filter(
                        role__id__in=usr_role, active=2, menu__parent=None).order_by("menu__menu_order")
                    for i in role_confs:
                        if i.view == True:
                            res.append({"menu_name": i.menu.name if i.menu.name else '',
                                        "user_id": user_id,
                                        "menu_id": i.menu.id,\
                                        #                                "organization_unit_id":i.menu.organization_unit.id,
                                        "icon": "/" + i.menu.icon if i.menu.icon else '',
                                        "front_end_url": i.menu.front_link if i.menu.front_link else '',
                                        "back_end_api": i.menu.backend_link if i.menu.backend_link else '',
                                        "child_menu": i.menu.get_submenu_list(i),
                                        "slug": i.menu.slug,
                                        "add": i.add,\
                                        "edit": i.edit,\
                                        "view": i.view,\
                                        "delete": i.delete,\
                                        'search': i.search, })
                else:
                    role_confs = Menus.objects.filter(
                        parent=None, active=2).order_by("menu_order")
                    for i in role_confs:
                        res.append({
                            "menu_name": i.name if i.name else '',
                            "user_id": user_id,
                            "menu_id": i.id,\
                            #                                "organization_unit_id":i.menu.organization_unit.id,
                            "icon": "/" + i.icon if i.icon else '',
                            "front_end_url": i.front_link if i.front_link else '',
                            "back_end_api": i.backend_link if i.backend_link else '',
                            "child_menu": i.get_adminsubmenu_list(),
                            "slug": i.slug,
                            "add": True,\
                            "edit": True,\
                            "view": True,\
                            "delete": True,\
                            'search': True,
                        })
            except Exception as e:
                if e.message == "UserRoles matching query does not exist.":
                    res.append({"message": "User does not exist"})
                else:
                    res.append({"message": e.message})
        else:
            res.append(dict(errors=serializer.errors))
        return Response(res)


class OrgUnitCreate(g.CreateAPIView):
    """API to create Organization unit"""
    queryset = OrganizationUnit.objects.filter(active=2)
    serializer_class = OrgUnitSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)


class OrgUnitList(g.ListAPIView):
    """API to list organization unit"""
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def get(self, request, format=None):
        try:
            org_unit = OrganizationUnit.objects.filter(active=2)
            pages = ceil(float(len(org_unit)) /
                         float(pg_size)) if org_unit else 0
            response = [{'id': i.id,
                         'name': i.name,
                         'organization_type': i.organization_type,
                         'organization_level': i.organization_level,
                         'parent': i.parent.name if i.parent else "",
                         'order': i.order,
                         'roles': i.roles.ids(),
                         }
                        for i in org_unit]
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request, pages)
            return paginator.get_paginated_response(result_page, pages, 2)
        except Exception as e:
            response = [{'msg': e.message, 'status': 0, 'pages': 1}]
        return Response(response)


class OrgUnitUpdate(g.RetrieveUpdateAPIView):
    """API to update Roles"""
    queryset = OrganizationUnit.objects.filter(active=2)
    serializer_class = OrgUnitSerializer
    lookup_field = 'pk'
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)


class Locationllevels(APIView):
    """API to get all the location levels"""

    def get(self, request):
        response = []
        response.append({"id": 1, "name": "Country"})
        response.append({"id": 2, "name": "State"})
        response.append({"id": 3, "name": "District"})
        response.append({"id": 4, "name": "Taluk"})
        response.append({"id": 5, "name": "Mandal"})
        response.append({"id": 6, "name": "GramaPanchayath"})
        response.append({"id": 7, "name": "Village"})
        return Response(response)


class ListingAPI(g.CreateAPIView):

    serializer_class = ListingSerializer
#    authentication_class = (ExpiringTokenAuthentication,)
#    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """ API for listing all the values in a table
            key : the name of the table """
        response = {'status': 0,
                    'message': 'Something went wrong.', 'data': []}
        serializer = self.serializer_class(data=request.data)
        res = []
        if serializer.is_valid():
            try:
                data = request.data
                key = data.get("key")
                field = data.get("field")
                user_id = data.get("uId")
                if user_id:
                    user_id = int(user_id)
                cont_type = ContentType.objects.get(model=str(key))
		if user_id != 1 and user_id != None:
			user = UserPartnerMapping.objects.filter(active = 2 , user__id = int(user_id))[0]
			values = user.partner.all()
		elif user_id == 1 or user_id is None:
			values = cont_type.model_class().objects.filter(active=2)
                response = {'status': 2,
                            'message': 'Successfully retrieved the data.'}
                if str(cont_type.model) == "userroles":
                    for i in values:
                        res.append(
                            {'id': i.user.id, 'field': i.user.first_name, })
                else:
                    for i in values:
                        res.append({'id': i.id, 'field': getattr(i, field), })
            except:
                response['message'] = key + " does not exist"
        else:
            response.append(dict(errors=serializer.errors))
        response['data'] = res
        return Response(response)


class ADdetail(APIView):
    """API to get details of a AD user"""

    def post(self, request):
        """
        ADdetail view.
        ---
        parameters:
        - name: ad_id
          description: Pass AD id
          required: true
          type: integer
          paramType: form
        """
        try:
            ad_id = request.data.get('ad_id')
            ad_obj = ADTable.objects.get(id=ad_id)
            res = {'ad_id': ad_obj.id, 'username': ad_obj.username,
                   'first_name': ad_obj.first_name if ad_obj.first_name else ad_obj.username, 'email': ad_obj.email, }
        except Exception as e:
            res = {'status': 0, 'message': e.message}
        return Response(res)


class UserLocationCreate(g.CreateAPIView):
    """API to create user locations"""
    queryset = OrganizationLocation.objects.filter(active=2)
    serializer_class = UserLocationSerializer

    def post(self, request, format=None):
        """
        User Location Tagging and updating.
        ---
        parameters:
        - name: key
          description: Pass "add" or "edit" key
          required: true
          type: integer
          paramType: form
        """
        serializer = self.serializer_class(data=request.data)
        res = []
        data = request.data
        if data.get("key") == "add":
            if serializer.is_valid():
                userlocationobj = serializer.save()
                response = {'status': 2,
                            'message': 'successfully tagged locations'}
            else:
                response = dict(errors=serializer.errors)
        else:
            user = data.get('user')
            organization_level = data.get('organization_level')
            location = data.get('location')
            userlocationobj, created = OrganizationLocation.objects.get_or_create(
                user=UserRoles.objects.get(id=int(user)), organization_level=organization_level)
            location = data.get('location').split(',') or data.get('location')
            location = map(int, location)
            userlocationobj.location.clear()
            userlocationobj.location.add(*location)
            response = {'status': 2, 'message': 'Updated Successfully'}
        return Response(response)


class UserLocationEdit(g.RetrieveUpdateAPIView):
    """API to edit user locations"""
    queryset = OrganizationLocation.objects.filter(active=2)
    serializer_class = UserLocationSerializer
    lookup_field = 'pk'


class UserLocationList(APIView):
    """API to list User Location"""
    @classmethod
    def post(self, request, format=None):
        try:
            org_loc = OrganizationLocation.objects.filter(active=2)
            pages = ceil(float(len(org_loc)) /
                         float(pg_size)) if org_loc else 0
            response = [{
                        'user': i.user.user.first_name,
                        'organization_unit': i.user.organization_unit.name,
                        'organization_level': i.organization_level,
                        'location': i.location.ids(),
                        }
                        for i in org_loc]
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(response, request, pages)
            return paginator.get_paginated_response(result_page, pages, 3)
        except Exception as e:
            response = [{'msg': e.message, 'status': 0, 'pages': 1}]
        return Response(response)


# class ContentTypeListing(APIView):
#    def post(self,request):
#        try:
#            response = []
#            cont_type = ContentType.objects.filter().exclude(model__in=['logentry','permission','group','user','contenttype','session', 'resetactivation','jsonanswer','codeconfig','dynamiclisting','usmcrontracker', 'surveylanguagetranslation','userlanguage','userimeiinfo', 'questionlanguagetranslation','choicelanguagetranslation','blocklanguagetranslation','blocklanguagetranslation','surveylog','version', 'surveylanguagetranslation','skipmandatory','usercluster','surveyskip','questionvalidation','validations','choicevalidation','corsmodel', 'adtable','documentcategory','attachments','menus'])
#            for i in cont_type:
#                response.append({'model_name':i.model,
#                                'fields':apps.get_model(i.app_label,i.model)._meta.get_all_field_names(),})
#        except Exception as e:
#            response = [{'message':e.message,'status':0}]
#        return Response(response)

class UserLevelList(APIView):

    def post(self, request, format=None):
        """
        To get Organization unit level name and list view.
        ---
        parameters:
        - name: level
          description: Pass level id
          required: true
          type: integer
          paramType: form
        - name: user_id
          description: Pass user_id
          required: true
          type: integer
          paramType: form
        """
        try:
            data = request.data
            boundarylist = Boundary.objects.filter(active=2,
                                                   boundary_level=data.get('level'))
            userobj = UserRoles.objects.get(id=int(data.get('user_id')))
            
            boundary_list = [
                {'name': i.name, 'id': int(i.id)}for i in boundarylist]

            boundary_name = userobj.organization_unit.get_organization_level_display()
            boundary_level = userobj.organization_unit.organization_level
            userlocationobj = OrganizationLocation.objects.get_or_none(
                user=userobj, organization_level=data.get('level'))
            if userlocationobj:
                created_location = [int(i.id)
                                    for i in userlocationobj.location.all()]
            else:
                created_location = []
            response = [{'boundary_name': boundary_name,
                         'boundary_level': boundary_level,
                         'boundary_list': boundary_list,
                         'created_location': created_location}]
        except:
            response = [{'boundary_name': ''}, {'boundary_list': []}]
        return Response(response)
