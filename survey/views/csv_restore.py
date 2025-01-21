"""Storing Data in JsonField."""
from rest_framework.generics import CreateAPIView
from survey.models import (SurveyRestore,)
from survey.serializers import (SurveyRestoreSerializer,)


class DataRestore(CreateAPIView):
    queryset = SurveyRestore.objects.filter(active=2)
    serializer_class = SurveyRestoreSerializer

    def create(self, request, *args, **kwargs):
        status = {'status': 0, 'message': 'Something went wrong.'}
        data = request.data
        get_file = data.get('get_docu')
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            create_file = SurveyRestore.objects.create(survey_user_id=data.get('user_id'),
                                                       name=data.get('name'), restore_file=get_file)
            with open(create_file.restore_file.url, 'rb+') as f:
                pass
        else:
            status.update(errors=serializer.errors)
        return Response(status)
