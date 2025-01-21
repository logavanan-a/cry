from django.db import models
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from userroles.models import ADTable
from ad_auth import get_ad_user

def update_ad(pk,userobj):
    ad_obj = ADTable.objects.get(id=pk)
    ad_obj.user = userobj
    ad_obj.save()
    return ad_obj

def is_ad_user(user_id):
    ad_user = ADTable.objects.filter(user__id=user_id).exists()
    return ad_user


class ADList(APIView):
    """API to get list of AD users"""
    def post(self,request):
        try:
            res = []
            new_list = []
            try:
                ad_list = get_ad_user()
                for i in ad_list:
                    username = i.get('user')
                    first_name = i.get('firstName')
                    email = i.get('email')
                    new_list.append(email)
                    ad_table,created = ADTable.objects.get_or_create(username=username,first_name=first_name,email=email)
            except:
                pass
            for i in ADTable.objects.filter(user=None,email__in = new_list):
                res.append({"username":i.username,"first_name":i.first_name if i.first_name else i.username,"email":i.email,"id":i.id})
        except Exception as e:
            res = {"status":0,"message":e.message}
        return Response(res)

