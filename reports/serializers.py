from rest_framework import serializers
from userroles.serializers import MultipartM2MField
from .models import *


class ProfileViewSerializer(serializers.ModelSerializer):

    modified = serializers.SerializerMethodField()
    class Meta:
        model = ProfileView
        fields = ('id' , 'modified' , 'jsonid', 'uuid_lid' , 'type_name' , 'type_id' , 'ben_fac_loc_id' , 'profile_info' , 'partner_id')
        
    def get_modified(self, obj):
        return obj.modified.strftime('%Y-%m-%d %H:%M:%S.%f')
        
