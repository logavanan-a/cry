from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import (RoleTypes, UserRoles,
                     OrganizationUnit, OrganizationLocation)
from partner.models import (Partner,)
from userroles.models import UserRoles


class MultipartM2MField(serializers.Field):

    def to_representation(self, obj):
        return obj.values_list('id', flat=True).order_by('id')

    def to_internal_value(self, data):
        return data.split(',') if data else None


class UserSerializer(serializers.ModelSerializer):
    #---------to create user---------------------------------------------#

    class Meta:
        model = User
        fields = ('first_name', 'username', 'last_name', 'email')

    def validate(self, attrs):
        if self.instance:
            if (self.Meta.model).objects.exclude(id=self.instance.id).filter(email=attrs['email']).exists():
                raise serializers.ValidationError(
                    'email:Email-id is already exists')
            if (self.Meta.model).objects.exclude(id=self.instance.id).filter(username=attrs['username']).exists():
                raise serializers.ValidationError(
                    'username:Username is already exists')
        else:
            if (self.Meta.model).objects.filter(email=attrs['email']).exists():
                raise serializers.ValidationError(
                    'email:Email-id is already exists')
            if (self.Meta.model).objects.filter(username__iexact=attrs['username']).exists():
                raise serializers.ValidationError(
                    'username:Username is already exists')
        return attrs

    def create(self, validated_data):
        user = User(email=validated_data['email'],
                    username=validated_data['username'],
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                    is_active=True)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True, allow_blank=False, max_length=100)
    password = serializers.CharField(
        required=True, allow_blank=False, max_length=100)

    def validate(self, data):
        user = authenticate(
            username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_superuser:
            user_partner = UserRoles.objects.get(user__username = data['username'])
            if user_partner:
                if user_partner.partner.active != 2:
                    raise serializers.ValidationError("Partner is deactivated")
        return data


class RoleTypesSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=True, validators=[
                                 UniqueValidator(queryset=RoleTypes.objects.filter(active=2))])

    class Meta:
        model = RoleTypes
        fields = ('id', 'name', 'code',)

    def validate(self, data):
        if data.get('code').isalnum() == False:
            raise serializers.ValidationError('Code should be Aplanumeric')
        return data


class RoleConfigsSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=True)


class ActivateSerializer(serializers.Serializer):
    obj_id = serializers.IntegerField(required=True)
    key = serializers.CharField(required=True)


class RoleConfigsUpdateSerializer(serializers.Serializer):
    roles_list = serializers.ListField(required=True)


class UserMenuPermSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)


class OrgUnitSerializer(serializers.ModelSerializer):
    roles = MultipartM2MField()

    class Meta:
        model = OrganizationUnit
        fields = ('id', 'name', 'organization_type',
                  'organization_level', 'parent', 'order', 'roles',)

    def validate(self, data):
        if data.get('organization_type') == 2 and not data.get('organization_level'):
            self.fields.get('organization_level').required = True
            raise serializers.ValidationError(
                'Please select organization level')
        elif data.get('organization_type') == 1 and data.get('organization_level'):
            raise serializers.ValidationError(
                'Please dont select organization level if type is non location')
        if self.instance:
            if (self.Meta.model).objects.exclude(id=self.instance.id).filter(name=data['name']).exists():
                raise serializers.ValidationError(
                    'Organization name already exists')
        else:
            if OrganizationUnit.objects.filter(name=data.get('name'), parent=data.get('parent')).exists():
                raise serializers.ValidationError(
                    'Organization name already exists')
        return data


class ListingSerializer(serializers.Serializer):
    key = serializers.CharField(required=True)
    field = serializers.CharField(required=True)


class OrganizationUnitSerializer(serializers.Serializer):
    user_type = serializers.IntegerField(required=True)


class UserDetailSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    last_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    username = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    email = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    organization_unit = serializers.IntegerField(required=False)
    roles = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    title = serializers.IntegerField(required=False)
    middle_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    adhar_no = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    pan_no = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    dob = serializers.DateField(required=False)
    designation = serializers.IntegerField(required=False)
    reporting_to = serializers.IntegerField(required=False)
    address = serializers.CharField(required=False)
    relationship = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    region = serializers.IntegerField(required=False)
    mobile_number = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    emergency_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    company_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    emergency_address = serializers.CharField(required=True, allow_blank=True)
    company_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    ad_id = serializers.IntegerField(required=False)
    user_type = serializers.IntegerField(required=False)
    partner = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['user_type'] == 2:
            role_ids = map(int, attrs['roles'].split(','))
            role_data = RoleTypes.objects.filter(active=2, id=role_ids[0])[0]
            partnerobj = Partner.objects.get_or_none(id=attrs['partner'])
            if partnerobj and self.instance and role_data.slug != 'data-entry-operator' and UserRoles.objects.exclude(id=self.instance.id).filter(role_type__in=role_ids, partner=attrs['partner']).exists():
                raise serializers.ValidationError(
                    'role:Role is already already exists for this partner')
            elif partnerobj and role_data.slug != 'data-entry-operator' and UserRoles.objects.filter(role_type__in=role_ids, partner=attrs['partner']).exists() :
                raise serializers.ValidationError(
                    'role:Role is already exists for this partner')
        return attrs


class UserUpdateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    organization_unit = serializers.IntegerField(required=False)
    roles = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    title = serializers.IntegerField(required=False)
    middle_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    dob = serializers.CharField(required=False)
    adhar_no = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    pan_no = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    company_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    mobile_number = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    designation = serializers.IntegerField(required=False)
    region = serializers.IntegerField(required=False)
    reporting_to = serializers.IntegerField(required=False)
    address = serializers.CharField(required=False)
    emergency_name = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    relationship = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    emergency_address = serializers.CharField(required=True, allow_blank=True)


class UserLocationSerializer(serializers.ModelSerializer):
    location = MultipartM2MField()

    class Meta:
        model = OrganizationLocation
        fields = ('user', 'organization_level', 'location',)

    def validate(self, attrs):
        if self.instance:
            if (self.Meta.model).objects.exclude(id=self.instance.id).filter(user=attrs['user']).exists():
                raise serializers.ValidationError('User already exists')
        else:
            if (self.Meta.model).objects.filter(user=attrs['user']).exists():
                raise serializers.ValidationError('User already exists')
        return attrs


class LoggedinUserPartnerDetailSerializer(serializers.Serializer):
    user = serializers.IntegerField(required=True)
