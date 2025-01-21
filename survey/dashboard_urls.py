"""Dashboard Urls."""
from django.conf.urls import url
from survey.dashboard_api import (GetDashboardData)

urlpatterns = [
    #url(r'^filter-overall-data/$', GetUserDashboardData.as_view(),
    #    name="data-filter"),
    url(r'^filter-overall-data/$',GetDashboardData.as_view()),
    #url(r'^frequence-data/$', FrequenceDashBoard.as_view(),
    #        name="data-fequence"),
]
