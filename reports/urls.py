from django.conf.urls import url, include
from django.contrib import admin

from reports.report_views import *
from .views import *
from .datasets_report_views import *

urlpatterns = [
    url(r'^partnerwiseyear/$', PartnerWiseYearQuarter.as_view()),
    url(r'^yearwisequarter/$', YearWiseQuarter.as_view()),
    url(r'^displaycontents/$', ReportPartnerWise.as_view()),
    url(r'^survey-list/$', ReportSurveyList.as_view()),
    url(r'^export-excel/$', ReportExcel.as_view()),
    url(r'^reports-configured/$',GetReportConfigured.as_view()),
    url(r'^annual-reports/(?P<id>.+)/(?P<uid>.+)/$',GetReportDisplay.as_view()),
#    url(r'export-reports/(?P<id>.+)/(?P<uid>.+)/$',ExportReport.as_view()),
    url(r'export-reports/(?P<id>.+)/(?P<uid>.+)/$',ExportReportDataSets.as_view()),
    url(r'^export-custom-reports/$','reports.views.export_custom_reports'),
    url(r'^customreports-listing/$', 'reports.views.custom_reports_listing'),
#    url(r'^customreports-listing/$', MutantReportView.as_view()),
    url(r'^migrated-region-filters/(?P<uid>.+)/$', MutantReportFilterView.as_view()),
    url(r'^migrated-state-filters/(?P<uid>.+)/(?P<rgid>.+)/$', RegoinStateView.as_view()),
    url(r'^migrated-partner-filters/(?P<uid>.+)/(?P<pid>.+)/$', StatePartnerView.as_view()),
    ]
