from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication, BaseAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status, generics as g
from django.http import HttpResponse
import requests
import datetime
import pytz
import json
from django.utils.timezone import utc
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
from ad_auth import *
from django.contrib.auth import login
from django.contrib.auth.models import *
from userroles.models import ADTable

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)

def get_userobj(username):
    try:
        userobj = ADTable.objects.get(username=username).email
    except:
        userobj = ''
    return userobj

class ObtainExpiringAuthToken(ObtainAuthToken):
    def post(self, request):
        """
        User Login.
        ---
        parameters:
        - name: username
          description: Enter username
          required: true
          type: string
          paramType: form
        - name: password
          description: Password for Login
          paramType: form
          required: true
          type: string
        """
        username = request.data['username']
        passwd = request.data['password']
        userobj = get_userobj(username)
        auth_ad = auth_ad_user(userobj,passwd)
        if auth_ad == 1:
            try:
                ad = ADTable.objects.get(username=username)


                response_data = {'status':1,
                                 'user_id':int(ad.id),
                                 'first_name':ad.user.first_name, 
                                 'last_name':ad.user.last_name, 
                                 'token': '',
                                 'ad_user':1
                                }
                return Response(response_data)
            except:
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid()
        elif auth_ad == 0:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                token, created =  Token.objects.get_or_create(user=serializer.validated_data['user'])

                utc_now = datetime.datetime.utcnow()
                utc_now = utc_now.replace(tzinfo=utc)
                if not created and token.created < utc_now - datetime.timedelta(minutes=10):
                    token.delete()
                    token = Token.objects.create(user=serializer.validated_data['user'])
                    token.created = datetime.datetime.now()
                    token.save()
                login(request, token.user)
                request.session['user'] = token.user.id

                response_data = {'token': token.key,
                                'first_name':token.user.first_name if token.user.first_name else '',
                                'last_name':token.user.last_name if token.user.last_name else '',
                                'user_id':int(token.user.id),
                                'ad_user':0}
                return Response(response_data)

        return HttpResponse(json.dumps(serializer.errors, cls=LazyEncoder))

obtain_expiring_auth_token = ObtainExpiringAuthToken.as_view()
