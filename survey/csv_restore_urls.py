from django.conf.urls import patterns, include, url
from survey.csv_restore import (
    DataRestore, DataRestoreListing, DataRestoreDetails)

urlpatterns = [
    url(r'^survey-data-upload/$', DataRestore.as_view(), name="survey-data-restore"),
    url(r'^survey-data-listing/$', DataRestoreListing.as_view(),
        name="survey-data-listing"),
    url(r'^survey-data-retrieve/(?P<pk>[0-9]+)/$',
        DataRestoreDetails.as_view()),
]
