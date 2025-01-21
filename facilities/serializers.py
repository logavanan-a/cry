from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from django.contrib.auth import authenticate
from .models import Facility, FacilityCentre
from masterdata.models import MasterLookUp
from beneficiary.models import Beneficiary_choices

class FacilityModelSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    facility_type_id = serializers.IntegerField(required=True)
    facility_subtype_id = serializers.IntegerField(required=True)
    thematic_area = serializers.CharField(required=True)
    btype = serializers.ChoiceField(choices=Beneficiary_choices, required=False)
    partner_id = serializers.IntegerField(required=False)
    parent_id = serializers.IntegerField(required=False)
    services = serializers.CharField(required=False)
    address1 = serializers.CharField(required=False)
    address2 = serializers.CharField(required=False)
    boundary_id = serializers.IntegerField(required=False)
    contact_no = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)

class FacilityCentreSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    facilities = serializers.CharField(required=False)
    centre_id = serializers.IntegerField(required=True)
    parent_id = serializers.IntegerField(required=False)
    address1 = serializers.CharField(required=False)
    address2 = serializers.CharField(required=False)
    boundary_id = serializers.IntegerField(required=False)
    contact_no = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)
