from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from userroles.models import UserRoles, RoleConfig
from rest_framework.authentication import BasicAuthentication,TokenAuthentication
from rest_framework.permissions import BasePermission
import urllib


def menu_permissions(object,user_id='',url_path=''):
    def haspermission(function):
        def is_auth(request, *args ,**kwargs):
            user = User.objects.get(id=user_id)
            if user.is_authenticated():
                if not user.is_superuser:
                    path = url_path
                    role = UserRoles.objects.filter(user=user).values_list('role_type__id',flat=True)
                    menu_links = RoleConfig.objects.filter(role__id__in=role,active=2,view=2).values_list('menu__link',flat=True)
                    if path in menu_links:
                        return function(request, *args, **kwargs)
            else:
                return HttpResponseRedirect("/admin")
            return function(request, *args, **kwargs)
        return is_auth
    object.dispatch = method_decorator(haspermission)(object.dispatch)
    return object
    
    
class MenuPermission(TokenAuthentication):
    def authenticate_header(self, request):
        return "Token"

class IsAuthenticated1(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):

        return request.user and request.user.is_authenticated()

class MenuAuntenticateCredentials(BasicAuthentication):

    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'basic':
            return None

        if len(auth) == 1:
            msg = _('Invalid basic header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid basic header. Credentials string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
        except (TypeError, UnicodeDecodeError):
            msg = _('Invalid basic header. Credentials not correctly base64 encoded.')
            raise exceptions.AuthenticationFailed(msg)

        userid, password = auth_parts[0], auth_parts[2]
        return userid,password
