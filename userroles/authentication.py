import datetime
from django.utils.timezone import utc
from django.contrib.auth.models import User
from rest_framework.authentication import (BasicAuthentication,
                                    TokenAuthentication,get_authorization_header)
from rest_framework import exceptions
from userroles.models import UserRoles, RoleConfig



class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            token = self.get_model().objects.get(key=key)
        except self.get_model().DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')
        # This is required for the time comparison
        utc_now = datetime.datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=utc)

        if token.created < utc_now - datetime.timedelta(minutes=10):
            raise exceptions.AuthenticationFailed('Token has expired')

#        user = User.objects.get(id=int(token.user.id))
#        if user.is_authenticated():
#            if not user.is_superuser:
#                path = request.path
#                role = UserRoles.objects.filter(user=user).values_list('role_type__id',flat=True)
#                menu_links = RoleConfig.objects.filter(role__id__in=role,active=2,view=2).values_list('menu__link',flat=True)
#                if path in menu_links:
#                    return (token.user, token)
#                else:
#                    msg = "Permission Denined"
#                    raise exceptions.AuthenticationFailed('Permission Denined')
        return (token.user, token)


class MenuRoleTokenAuthentication(TokenAuthentication):

    def authenticate(self,request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'token':
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = self.get_model().objects.get(key=token)
        except self.get_model().DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        # This is required for the time comparison
        utc_now = datetime.datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=utc)

        if token.created < utc_now - datetime.timedelta(minutes=10):
            raise exceptions.AuthenticationFailed('Token has expired')

        token = self.get_model().objects.get(key=token)
        user = User.objects.get(id=int(token.user.id))
        if not user.is_superuser:
            path = request.path
            role = UserRoles.objects.filter(user=user).values_list('role_type__id',flat=True)
            menu_links = RoleConfig.objects.filter(role__id__in=role,active=2,view=2).values_list('menu__link',flat=True)
            if path in menu_links:
                return (token.user, token)
            else:
                msg = "Permission Denined"
                raise exceptions.AuthenticationFailed('Permission Denined')

        return (token.user, token)


