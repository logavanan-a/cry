from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from facilities.views import FacilityAdd, FacilityUpdate, FacilityDetail, FacilityWtPaginationListing, FacilityListing
from .views import ServiceTypeListing, ServiceSubTypeListing

urlpatterns = [
#    url(r'^servicetypelisting/$', ServiceTypeListing.as_view()),
#    url(r'^servicemonitoradd/$', ServiceMonitorAdd.as_view()),
#    url(r'^servicemonitordetail/$', ServiceMonitorDetail.as_view()),
#    url(r'^servicemonitorupdate/$', ServiceMonitorUpdate.as_view()),
    url(r'^serviceadd/$', FacilityAdd.as_view(), {'key':'service'}),
    url(r'^serviceupdate/$', FacilityUpdate.as_view(), {'key':'service'}),
    url(r'^servicetypelisting/$', ServiceTypeListing.as_view()),
    url(r'^servicesubtypelisting/$', ServiceSubTypeListing.as_view()),
    url(r'^servicedetail/$', FacilityDetail.as_view(), {'key':'service'}),
    url(r'^servicelisting/$', FacilityWtPaginationListing.as_view(), {'key':'service'}),
    url(r'^servicelistingwithpagination/$', FacilityListing.as_view(), {'key':'service'}),
    url(r'^servicedatewiselisting/$', FacilityWtPaginationListing.as_view(), {'key':'service'}),
]
