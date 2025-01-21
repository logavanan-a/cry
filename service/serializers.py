from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator
from .models import Service

class ServiceSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    service_type_id = serializers.IntegerField(required=True)
    service_subtype_id = serializers.IntegerField(required=True)
    thematic_area_id = serializers.IntegerField(required=True)
    beneficiary_id = serializers.IntegerField(required=False)
    partner_id = serializers.IntegerField(required=False)
    parent_id = serializers.IntegerField(required=False)
    address1 = serializers.CharField(required=False)
    address2 = serializers.CharField(required=False)
    boundary_id = serializers.IntegerField(required=False)
    contact_no = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)


    def validate(self, data):


        service_names = [i.lower() for i in Service.objects.all().exclude(id=self.initial_data.get('id')).values_list('name', flat=True)]

        if data['name'].lower() in service_names:
            raise serializers.ValidationError('Service name must be unique.')
        return data

