from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework import status, generics as g
from django.contrib.auth import authenticate
from userroles.authentication import (ExpiringTokenAuthentication)
from userroles.models import (OrganizationUnit, UserRoles)
from partner.models import (Partner,)
from masterdata.models import (MasterLookUp,)
from serializers import (OrganizationUnitSerializer,
                         LoggedinUserPartnerDetailSerializer)


class OrganizationUnitRolesApi(g.CreateAPIView):
    #    API to send Orgaanization List
    #    authentication_class = (ExpiringTokenAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)

    queryset = OrganizationUnit.objects.filter(active=2)
    serializer_class = OrganizationUnitSerializer

    @classmethod
    def post(cls, request, *args, **kwargs):
        """
        API to send Organization List
        """
        response, response_list = {}, []
        data = request.data
        user_type = data.get('user_type')
        if int(user_type) == 2:
            organization_list = OrganizationUnit.objects.filter(
                active=2, slug="partner-unit").order_by("id")
        else:
            organization_list = OrganizationUnit.objects.exclude(
                slug="partner-unit").filter(active=2).order_by("id")
        for i in organization_list:
            roles_list = []
            for j in i.roles.all():
                roles_list.append({'role_name': j.name, 'id': int(j.id)})
            response_list.append({'organization_meet': [{"name": str(
                i.name), "id": int(i.id)}], 'roles_list': roles_list})
        return Response(response_list)


class DesignationList(APIView):

    def get(cls, request, *args, **kwargs):
        """
        API to list designation
        """
        try:
            response = [{'id': i.id, 'name': i.name}
                        for i in MasterLookUp.objects.filter(parent__slug="designation")]
        except:
            response = []
        return Response(response)


class RegionList(APIView):

    def get(cls, request, *args, **kwargs):
        """
        API to list designation
        """
        try:
            response = [{'id': i.id, 'name': i.name}
                        for i in MasterLookUp.objects.filter(parent__slug="region")]
        except:
            response = []
        return Response(response)


class PartnerList(APIView):

    def get(cls, request, *args, **kwargs):
        """
        API to list designation
        """
        try:
            response = [{'id': i.id, 'name': i.name}
                        for i in Partner.objects.filter(active=2)]
        except:
            response = []
        return Response(response)


class LoggedinUserPartnerDetail(g.CreateAPIView):
    #    API to get logged-in partner user details.
    #    authentication_class = (ExpiringTokenAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)

    queryset = Partner.objects.filter(active=2)
    serializer_class = LoggedinUserPartnerDetailSerializer

    @classmethod
    def post(cls, request, *args, **kwargs):
        data = request.data
        response = {'msg': "partner is not tagged to the user",
                    'partner_name': '', 'partner_id': ''}
        user_id = data.get('user')
        userroleobj = UserRoles.objects.get_or_none(user__id=user_id)
        if userroleobj:
            response = {
                'partner_name': userroleobj.partner.name if userroleobj.partner else '',
                'partner_id': int(userroleobj.partner.id) if userroleobj.partner else '',
                'msg': "Partner exists"
            }
        return Response(response)
