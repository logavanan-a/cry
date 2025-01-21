from __future__ import (print_function, unicode_literals)
import re
from rest_framework import serializers
from masterdata.models import (MasterLookUp,)
from userroles.models import(Address, UserRoles)
from .models import (Partner, Registration, BankAccount, Program, Project, ProjectLocation,
                     Donar, BudgetConfig, BudgetYear, Funding, ConfigureThematic, PartnerUserInfo)


class MultipartM2MField(serializers.Field):

    def to_representation(self, obj):
        return obj.values_list('id', flat=True).order_by('id')

    def to_internal_value(self, data):
        return data.split(',') if data else None


class PartnerNameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Partner
        fields = ('name',)

    def validate_name(self, value):
        return value.strip().title()

    def validate(self, data):
        if not len(data['name']) >= 3 and len(data['name']) <= 30:
            raise serializers.ValidationError(
                "Name length should be min 3 and max 30 characters.")
        if not re.match(r'[A-Za-z ]*$', data['name']):
            raise serializers.ValidationError(
                "Name contains numbers or special characters.")
        return data


class PartnerBasicDetailSerializer(serializers.Serializer):
    p_id = serializers.IntegerField(required=True)
    region = serializers.IntegerField(required=True)
    state = serializers.IntegerField(required=True)
    nature_of_partner = serializers.IntegerField(required=True)
    support_from = serializers.DateField(required=True)
    #support_to = serializers.DateField(required=False)



class PartnerListingSlugSerializer(serializers.Serializer):
    slug = serializers.CharField(required=True)
    key = serializers.IntegerField(required=False)


class AdminSerializer(serializers.Serializer):
    p_id = serializers.IntegerField(required=True)
    username = serializers.CharField(required=True, trim_whitespace=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, trim_whitespace=True)

    def validate_username(self, value):
        return value.strip().lower()

    def validate(self, data):
        if not re.match(r'[A-Za-z ]*$', data['username']):
            raise serializers.ValidationError(
                "Name contains numbers or special characters.")
        if re.search(r'\s', data['password']):
            raise serializers.ValidationError("No white spaces are allowed.")
        return data


class ProjectCreateSerializer(serializers.Serializer):
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.filter(active=2), required=True)
    pre_funding = serializers.PrimaryKeyRelatedField(
        queryset=MasterLookUp.objects.filter(active=2), required=True)
    fla_grm_team = serializers.PrimaryKeyRelatedField(
        queryset=MasterLookUp.objects.filter(active=2), required=True)
    boundary = serializers.CharField(required=True)
    community = serializers.CharField(required=True)
    theme = serializers.CharField(required=True)
    prominent_issues = serializers.CharField(required=True)


class ProjectHolderCreateSerializer(serializers.Serializer):
    proj_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.filter(active=2), required=True)
    name = serializers.CharField(required=True, trim_whitespace=True)
    username = serializers.CharField(required=True, trim_whitespace=True)
    email = serializers.CharField(required=True, trim_whitespace=True)
    get_contact = serializers.CharField(required=True, trim_whitespace=True)


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('address1', 'address2', 'boundary', 'pincode','address_type')


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registration
        fields = ('name', 'status', 'reg_type', 'date_of_registered')


class BankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('bank', 'priority', 'account_type', 'bank_name',
                  'account_number', 'branch_name', 'fund_type', 'ifsc_code','remarks')


class BankAccountEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('priority', 'account_type', 'fund_type',
                  'bank_name', 'branch_name', 'ifsc_code', 'bank','remarks')


class PartnerDetailViewSerializer(serializers.Serializer):
    p_id = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.filter(active=2), required=True)
    project_id = serializers.IntegerField(required=False)


class RegistrationViewDetailSerializer(serializers.Serializer):
    reg_id = serializers.IntegerField(required=True)


class BankViewDetailSerializer(serializers.Serializer):
    bank_id = serializers.IntegerField(required=True)


class ProjectViewDetailSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=False)


class AddressViewDetailSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)


class PartnerEditSerializer(serializers.Serializer):
    part_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True, trim_whitespace=True)
    region = serializers.IntegerField(required=True)
    state = serializers.IntegerField(required=True)
    nature_of_partner = serializers.IntegerField(required=True)
    status = serializers.IntegerField(required=True)
    support_since = serializers.DateField(required=True)
    user = serializers.CharField(required=True, trim_whitespace=True)
    project_name = serializers.CharField(required=True, trim_whitespace=True)
    other_legal_registration = serializers.BooleanField(default=False)
    disbursal = serializers.PrimaryKeyRelatedField(
        queryset=MasterLookUp.objects.filter(active=2), required=True)
    pre_funding = serializers.PrimaryKeyRelatedField(
        queryset=MasterLookUp.objects.filter(active=2), required=True)
    fla_grm_team = serializers.PrimaryKeyRelatedField(
        queryset=MasterLookUp.objects.filter(active=2), required=True)
    boundary = serializers.CharField(required=True)
    community = serializers.CharField(required=True)
    theme = serializers.CharField(required=True)
    prominent_issues = serializers.CharField(required=True)
    remarks = serializers.CharField(trim_whitespace=True)
    project_holder = serializers.CharField(required=True)
    project_manager = serializers.CharField(required=True)
    bank = serializers.CharField(required=True)
    registration = serializers.CharField(required=True)
    address = serializers.CharField(required=True)


class ProgramSerializer(serializers.ModelSerializer):

    class Meta:
        model = Program
        fields = ('id', 'partner', 'name', 'start_date', 'end_date')


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('id', 'program', 'name', 'start_date', 'end_date')


class GetPrioritySerializer(serializers.Serializer):
    model_name = serializers.ChoiceField(
        choices=[(i, i) for i in range(1, 3)], required=True)
    object_id = serializers.IntegerField(required=True)


class PartnerNewEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Partner
        fields = ('name', 'partner_id', 'region', 'state',
                  'nature_of_partner', 'status', 'support_from', 'support_to', )


class ProjectLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectLocation
        fields = ('pre_funding', 'fla_grm_team', 'boundary',
                  'community', 'theme', 'prominent_issues', 'remarks', )

model_key_name = ['Address', 'Registration',
                  'BankAccount', 'ProjectLocation', 'Project Holder']


class AllModuleSerializer(serializers.Serializer):
    key = serializers.ChoiceField(
        choices=[(i, j) for i, j in zip(range(1, 7), model_key_name)], required=True)
    object_id = serializers.IntegerField(required=True)


class UserRolesSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserRoles
        fields = ('middle_name', 'mobile_number', 'partner')


class UserRolesDetailSerializer(serializers.Serializer):
    ur_id = serializers.IntegerField(required=True)


class DonarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Donar
        fields = ('user', 'name', 'email', 'location', 'mobile_no', )

    def validate(self, data):
        donar_email = Donar.objects.filter(email__iexact=data['email'])
        donar_mob = Donar.objects.filter(mobile_no__iexact=data['mobile_no'])
        if donar_email and donar_mob:
            raise serializers.ValidationError(
                "message:Already Donor by this mail-id and mobile number exists.")
        elif donar_email:
            raise serializers.ValidationError(
                "message:Already Donor by this mail-id exists.")
        elif donar_mob:
            raise serializers.ValidationError(
                "message:Already Donor by this mobile exists.")
        return data


class DatetoYearSerializerThematic(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 3)], required=False)
    thematic_id = serializers.IntegerField(required=False)
    key_edit = serializers.IntegerField(required=False)


class DatetoYearSerializer(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)
    type_funding = serializers.ChoiceField(
        choices=[i for i in range(3)], required=True)
    thematic_id = serializers.CharField(required=False, trim_whitespace=True)
    start_year = serializers.CharField(required=False, trim_whitespace=True)
    end_year = serializers.CharField(required=False, trim_whitespace=True)


class DonarDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Donar
        fields = ('pk', 'name', 'email', 'location',
                  'mobile_no', 'active', 'user','contact_person')


class BudgetYearSerializer(serializers.ModelSerializer):

    class Meta:
        model = BudgetYear
        fields = ('start_year', 'end_year', )


class BudgetConfigSerializer(serializers.Serializer):
    year = serializers.CharField(required=True, trim_whitespace=True)
    proj_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)
    budget_config = serializers.CharField(required=True, trim_whitespace=True)


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, trim_whitespace=True)
    proj_id = serializers.IntegerField(required=True)
    theme_budget = serializers.IntegerField(required=True)
    start_year = serializers.CharField(required=True, trim_whitespace=True)


class BudgetConfigEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = BudgetConfig
        fields = ('theme_budget', 'line_item', 'amount')


class BudgetConfigListingFilter(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 3)], required=True)
    year = serializers.CharField(required=False, trim_whitespace=True)
    thematic_area = serializers.IntegerField(required=True)


class FundingDateSerializer(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 3)], required=True)
    type_funding = serializers.ChoiceField(
        choices=[i for i in range(3)], required=True)


class FundingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Funding
        fields = ('user', 'types_of_funding', 'donar',
                  'status', 'probability_status')


class ConfigureThematicSerializer(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 3)], required=True)
    status = serializers.IntegerField(required=False)
    renewl_status = serializers.IntegerField(required=False)
    years = serializers.CharField(required=False, trim_whitespace=True)


class ConfigureThematicSerializerDetail(serializers.ModelSerializer):

    class Meta:
        model = ConfigureThematic
        fields = ('funding', 'funding_theme', 'thematic', )


class DFPProjectViewDetailSerializer(serializers.Serializer):
    proj_id = serializers.IntegerField(required=True)


class FilterDataSerializer(serializers.Serializer):
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 6)], required=True)
    region_id = serializers.CharField(required=False, trim_whitespace=True)


class PartnerReportTableSerializer(serializers.Serializer):
    key = serializers.ChoiceField(
        choices=[i for i in range(1, 3)], required=True)
    region_id = serializers.CharField(required=False, trim_whitespace=True)
    state = serializers.CharField(required=False, trim_whitespace=True)
    theme = serializers.CharField(required=False, trim_whitespace=True)
    nature = serializers.CharField(required=False, trim_whitespace=True)
    booking = serializers.CharField(required=False, trim_whitespace=True)

class PartnerUserInfoSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    partner = serializers.IntegerField(required=True)
    email = serializers.EmailField(allow_blank=False)
    mobile = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    pan = serializers.CharField(required=True)
    adhar = serializers.CharField(required=True)
    remarks = serializers.CharField(required=False)

class PartnerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerUserInfo
        exclude = ('created','modified','active')
