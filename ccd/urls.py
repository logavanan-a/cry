"""ccd URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^masterdata/', include('masterdata.urls')),
    url(r'^userroles/', include('userroles.urls')),
    url(r'^user/', include('userroles.manage_userurl')),
    url(r'^beneficiary/', include('beneficiary.urls')),
    url(r'^facilities/', include('facilities.urls')),
    url(r'^partner/', include('partner.urls')),
    url(r'^service/', include('service.urls')),
    url(r'^api/', include('survey.urls')),
    #    url(r'^content-type/listing/$',ContentTypeListing.as_view()),
    url(r'^dynamic_listing/', include('dynamic_listing.urls')),
    url(r'^survey/', include('survey.urls')),
    url(r'^workflow/', include('workflow.urls')),
    url(r'^survey-file/', include('survey.csv_restore_urls')),
    url(r'^dashboard/', include('survey.dashboard_urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^report_views/',include('report_views.urls')),
    url(r'^silk/', include('silk.urls', namespace='silk'))

]
