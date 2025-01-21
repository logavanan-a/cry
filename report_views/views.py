from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
import re

# Create your views here.
class GetViewReport(APIView):
    def post(self,request):
        """
        Report Views Api
        ---
        parameters:
        - name: view_name
          description: Pass the view class name
          required: true
          type: character
          paramType: form
        - name: user_details
          description : Pass the logged in user id
          required: true
          type: integer
          paramType: integer
        """
        try:
            res = {}
            model_name = eval(request.POST.get('view_name'))()
            model_fields =  model_name._meta.get_all_field_names()
            view_response = eval(request.POST.get('view_name')).objects.all().values(*model_fields)
            res['headers'] = model_fields
            res['display_headers'] = [re.sub("[_-]", " ", i).title() for i in model_fields]
            res['data'] = view_response
            return Response({'status':2,'data':res})
        except:
            return Response({'status':0,'message':'Something went wrong'})