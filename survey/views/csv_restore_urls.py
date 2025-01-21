from django.conf.urls import patterns, include, url
from .csv_restore import (DataRestore,)
urlpatterns = patterns(
    url(r'^data-upload/$', DataRestore, name="survey-data-restore"),
)
