"""Defining Serializer for MasterData App."""
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.response import Response
from .models import (Boundary, MasterLookUp)


class BoundarySerializer(serializers.ModelSerializer):
    """Boundary to add Location."""
    boundary_level = serializers.IntegerField(required=True)

    def validate(self, data):
        """Check Validation."""
        location = data
        if data.get('parent'):
            act = Boundary.objects.filter(active=0, name__iexact=location.get('name').title(
            ), boundary_level=location.get('boundary_level'), object_id=location.get('object_id'))
            inact = Boundary.objects.filter(active=0, name__iexact=location.get('name').title(), boundary_level=location.get(
                'boundary_level'), parent=location.get('parent'), object_id=location.get('object_id'))
            if Boundary.objects.filter(active=2, name__iexact=location.get('name').title(), boundary_level=location.get('boundary_level'), parent=location.get('parent'), object_id=location.get('object_id')) and location.get('parent'):
                message = 'Given ' + \
                    location.get('name').title() + ' and ' + \
                    location.get('parent').name + ' are exists.'
                raise serializers.ValidationError(message)
            elif inact:
                inact[0].switch()
            elif Boundary.objects.filter(active=2, name__iexact=location.get('name').title(), boundary_level=location.get('boundary_level'), object_id=location.get('object_id')):
                message = 'Given ' + \
                    location.get('name').title() + \
                    ' are exists for Location Level.'
                raise serializers.ValidationError(message)
            elif act:
                act[0].switch()

        else:
            message = 'Parent location is mandatory.'
            raise serializers.ValidationError(message)
        return data

    def validate_name(self, value):
        """Converting the Name into Titlecase and striping the whitespaces."""
        return value.title().strip()

    class Meta:
        """Defining the Model."""

        model = Boundary
        fields = ['name', 'code', 'boundary_level', 'desc', 'slug', 'latitude',
                  'longitude', '_polypoints', 'parent', 'object_id']


class MasterLookUpSerializer(serializers.ModelSerializer):
    """Master Look up for Masterdata."""

    def validate(self, data):
        """Check Validation."""
        master = data
        inact_par = MasterLookUp.objects.filter(active=0, name__icontains=master.get(
            'name').strip().title(), parent=master.get('parent'))
        inact_mas = MasterLookUp.objects.filter(
            active=0, name__icontains=master.get('name').strip().title())
        if MasterLookUp.objects.filter(active=2, name__icontains=master.get('name').strip().title(), parent=master.get('parent')) and master.get('parent'):
            message = master.get('name') + ' and ' + \
                master.get('parent').name + ' already exists.'
            raise serializers.ValidationError(message)
        elif MasterLookUp.objects.filter(active=2, name__icontains=master.get('name').strip().title()):
            message = master.get('name') + ' already exists.'
            raise serializers.ValidationError(message)
        elif inact_par:
            inact_par[0].switch()
        elif inact_mas:
            inact_mas[0].switch()

        return data

    class Meta:
        """Defining the Model Fields."""
        model = MasterLookUp
        fields = ['name', 'parent', 'slug']


class BoundaryListingSerializer(serializers.Serializer):
    """Get Location Listing Based on the ID."""

    boundary_id = serializers.IntegerField(required=False)
    region_id = serializers.IntegerField(required=False)
    level = serializers.IntegerField(required=False)
    location_type = serializers.IntegerField(required=True)
    ward_type = serializers.IntegerField(required=False)
    key = serializers.ChoiceField(
        choices=[(i, i) for i in range(1, 8)], required=False)
    common_key = serializers.ChoiceField(
        choices=[(i, i) for i in range(2)], required=True)
    partner_id = serializers.IntegerField(required=False)


class BoundaryUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    ward_type = serializers.IntegerField(required=False)
    name = serializers.CharField(required=True)
    parent = serializers.CharField(required=False)
    boundary_level = serializers.IntegerField(required=True)
    latitude = serializers.CharField(required=False)
    pk = serializers.IntegerField(required=True)
    location_type = serializers.IntegerField(required=True)
    longitude = serializers.CharField(required=False)
    desc = serializers.CharField(required=False)
    common_key = serializers.ChoiceField(
        choices=[(i, i) for i in range(2)], required=True)


class SwitchSerializer(serializers.Serializer):
    """Activate and Deactivate the Objects."""

    object_id = serializers.IntegerField(required=True)
    model_name = serializers.CharField(required=True)

    def create(self, validated_data):
        """Get Model Successfully."""
        data = validated_data
        response = {'status': 0, 'message': 'Something went  wrong.'}
        try:
            ct = ContentType.objects.get(model=data.get('model_name').lower())
            model = ct.model_class()
            # Activate and Deactivate the Objects.
            get_object = model.objects.get(id=data.get('object_id'))
            get_object.switch()
            response = {'status': 2, 'data': {'id': get_object.active, 'name': get_object.get_active_display()},
                        'message': 'Successfully switched the object.'}
        except:
            pass
        return Response(response)


class SearchSerializer(serializers.Serializer):
    """Search the location."""

    location_type = serializers.IntegerField(required=True)
    ward_type = serializers.IntegerField(required=False)
    level = serializers.IntegerField(required=True)
    text = serializers.CharField(required=True)


class MasterLookupPartnerListing(serializers.Serializer):
    get_list = serializers.CharField(required=True)
    parent = serializers.IntegerField(required=True)


class MasterDataImport(serializers.Serializer):
    key = serializers.IntegerField(required=True)
    level = serializers.IntegerField(required=True)


class LocationDataReportSerializer(serializers.Serializer):
    loc_type = serializers.IntegerField(required=False)
    loc_level = serializers.IntegerField(required=False)
    loc_ids = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=True)
