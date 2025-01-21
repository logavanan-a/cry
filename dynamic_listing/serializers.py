from rest_framework import serializers
from .models import *

class DynamicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicListing
        fields = ('model_name','listing_fields')

class DynamicFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicFilter
        fields = ('model_name','filtering_fields')
