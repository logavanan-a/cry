from rest_framework import serializers
from userroles.serializers import MultipartM2MField
from .models import *


class SurveySerializer(serializers.ModelSerializer):

    class Meta:
        model = Survey
        fields = ('id', 'name', 'data_entry_level')


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = ('id', 'name', 'survey')


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ('id', 'name', 'qtype', 'block')


class ChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Choice
        fields = ('id', 'question', 'text', 'code', 'order')

    def validate(self, data):
        if data.get('question') == None:
            raise serializers.ValidationError(
                {"question": "Question id is needed ..!"})
        question = Question.objects.get(id=int(data.get('question').id))
        excl = {}
        if self.instance:
            excl['id'] = self.instance.id
        option_codes = Choice.objects.filter(question=question).exclude(
            **excl).values_list('code', flat=True)

        if data.get('code') in option_codes:
            raise serializers.ValidationError(
                {"code": "Code already exist ..!"})
        return data


class UserSurveyMapSerializer(serializers.ModelSerializer):
    user = MultipartM2MField()

    class Meta:
        model = DetailedUserSurveyMap
        fields = ('survey', 'user', 'level')


class SurveyRestoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurveyRestore
        fields = ('name', 'survey_user', 'level', 'object_id')


class UsersDashBoard(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)


class FrequenceUsersDashBoard(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    frequence = serializers.IntegerField(required=False)
    region = serializers.IntegerField(required=False)
    key = serializers.IntegerField(required=False)
    partner_id = serializers.IntegerField(required=False)
