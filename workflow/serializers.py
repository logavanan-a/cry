from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import serializers
from box import Box
from .models import (WorkState, WorkStateUserRelation,
                     WorkFlow, WorkFlowSurveyRelation, WorkFlowComment, WorkFlowBatch, Comment)


class WorkStateSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkState
        fields = ('name', 'order')

    def validate(self, data):
        """
        Check that the Unique State Name.
        """
        data = Box(data)
        ws = WorkState.objects.filter(active=2)
        if ws.filter(name__iexact=data['name'], order=data['order']):
            raise serializers.ValidationError(
                "name:already workstate contain name {name} by this order {order}.".format(**data))
        elif ws.filter(Q(name__iexact=data['name']) | Q(order=data['order'])):
            raise serializers.ValidationError(
                "name:already workstate contain name or order.".format(**data))
        return data


class WorkStateSerializerEdit(serializers.ModelSerializer):

    class Meta:
        model = WorkState
        fields = ('name', 'order')


class WorkFlowSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlow
        fields = ('name', 'created_by')

    def validate(self, data):
        from .views import (BasicOperation,)
        BasicOperation()
        data = Box(data)
        wtf = WorkFlow.objects.filter(active=2)
        if wtf.filter(name__iexact=data.name):
            raise serializers.ValidationError(
                "name:already workflow contain this name {name}.".format(**data))
        return data


class WorkFlowSerializerEdit(serializers.ModelSerializer):

    class Meta:
        model = WorkFlow
        fields = ('name', 'created_by')


class WorkFlowSurveyRelationSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowSurveyRelation
        fields = ('workflow', 'survey', 'start_date', 'end_date')

    def validate(self, data):
        data = Box(data)
        wfsr = WorkFlowSurveyRelation.objects.filter(active=2)
        if wfsr.filter(workflow=data.workflow, survey=data.survey):
            raise serializers.ValidationError(
                "name:already workflow configured for this survey.")
        return data


class WorkFlowSurveyRelationSerializerEdit(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowSurveyRelation
        fields = ('workflow', 'survey', 'start_date', 'end_date')


class WorkFlowCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowComment
        fields = ('batch', 'status', 'curr_state',)


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('status', 'types', 'comment', 'curr_user', 'curr_state')


class WorkFlowBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowBatch
        fields = ('name', 'current_status', 'no_of_response', 'partner', )


class WorkFlowGetStates(serializers.Serializer):
    batch_id = serializers.IntegerField(min_value=1, required=True)
    survey_id = serializers.IntegerField(min_value=1, required=True)
    user_id = serializers.IntegerField(min_value=1, required=True)


class WorkFlowDetailSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField(min_value=1, required=True)
    user_id = serializers.IntegerField(min_value=1, required=True)


class WorkFlowPrimarySerializer(serializers.Serializer):
    batch_id = serializers.IntegerField(min_value=1, required=True)
    curr_user = serializers.IntegerField(required=True)
    previous_user = serializers.IntegerField(required=True)
    curr_state_id = serializers.IntegerField(required=True)
    previour_state = serializers.IntegerField(required=True)
    next_user = serializers.IntegerField(required=True)
    next_state = serializers.IntegerField(required=True)


class WorkFlowDetailBatchSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField(min_value=1, required=True)
    user_id = serializers.IntegerField(min_value=1, required=False)
    survey_id = serializers.IntegerField(min_value=1, required=True)
