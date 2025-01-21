from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^report_views/$', GetViewReport.as_view()),
    ]