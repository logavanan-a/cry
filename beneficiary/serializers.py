from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from django.contrib.auth import authenticate
from .models import Beneficiary, Beneficiary_choices
from userroles.models import Address
from facilities.models import *

class BeneficiarySerializer(serializers.Serializer):

    btype = serializers.ChoiceField(choices=Beneficiary_choices)

class BeneficiaryModelSerializer(serializers.Serializer):

    class Meta:
        model = Beneficiary
        fields = ['id', 'name', 'parent', 'btype']

class BeneficiaryAddSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    btype = serializers.ChoiceField(choices=Beneficiary_choices, required=False)
    parent_id = serializers.IntegerField(required=False)
    beneficiary_type_id = serializers.IntegerField(required=False)
    partner_id = serializers.IntegerField(required=False)
    mother_id = serializers.IntegerField(required=False)
    address1 = serializers.CharField(required=False)
    address2 = serializers.CharField(required=False)
    age = serializers.FloatField(required=False)
    boundary_id = serializers.IntegerField(required=False)
    contact_no = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)
    mother_name = serializers.CharField(required=False)
    father_name = serializers.CharField(required=False)
    guardian_name = serializers.CharField(required=False)

class BeneficiaryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['pk', 'address1', 'address2', 'boundary', 'contact_no','pincode']

class BeneficiaryAddressSerializerCustom(serializers.Serializer):
    address1 = serializers.CharField(required=False)
    address2 = serializers.CharField(required=False)
    contact_no = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)
    boundary_id = serializers.IntegerField(required=True)

class BeneficiaryRelationSerializer(serializers.Serializer):

    partner_id = serializers.IntegerField(required=False)
    primary_beneficiary_id = serializers.IntegerField(required=True)
    secondary_beneficiary_id = serializers.IntegerField(required=True)
    relation_id = serializers.IntegerField(required=True)

class BeneficiaryTypeSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    order = serializers.IntegerField(required=True)
    parent_id = serializers.IntegerField(required=False)

class CodeConfigSerializer(serializers.Serializer):
    content_type_id = serializers.IntegerField(required=False)
    separator = serializers.CharField(required=True)
    start_number = serializers.IntegerField(required=True)
    padlength = serializers.IntegerField(required=True)
    prefix_type = serializers.ChoiceField(choices=PREFIX_TYPES, required=True)
    prefix = serializers.CharField(required=True)
    ctype_id = serializers.IntegerField(required=False)
    object_id = serializers.IntegerField(required=False)
    sequence = serializers.BooleanField(initial=False)
