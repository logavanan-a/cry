from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import *
from rest_framework.response import Response
from .serializers import ServiceSerializer
from .models import ServiceType, ServiceMonitor
from django.db import models
from masterdata.models import MasterLookUp

def model_field_exists(cls, field):
    try:
        cls._meta.get_field(field)
        return True
    except models.FieldDoesNotExist:
        return False

class ServiceTypeListing(CreateAPIView):

    def post(self, request):
        response = {}
        response = [{'id':i.id, 'name':i.name} 
            for i in MasterLookUp.objects.filter(parent__slug='service-type')]
        return Response(response)

class ServiceSubTypeListing(CreateAPIView):

    def post(self, request):
        """
        Listing for service subtype
        ---
            parameters:
            - name: id
              description: Enter service type Id
              type: Integer
              required: true
        """
        response = {}
        response = [{'id':i.id, 'name':i.name} for i in MasterLookUp.objects.filter(parent__id=request.data['id'])]
        return Response(response)
