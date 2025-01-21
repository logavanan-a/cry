"""UserRoles Urls."""
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .manage_roles import (RolesCreateAPI, RolesListAPI, RolesRetriveUpdateAPI,
                           ActivateAPI, RoleConfigsAPI, RoleConfigsUpdate,
                           UserMenuPermissions, OrgUnitCreate, OrgUnitList, OrgUnitUpdate,
                           Locationllevels, ListingAPI, ADdetail, UserLocationCreate, UserLocationEdit,
                           UserLocationList, UserLevelList, )
from .ad_apis import ADList
from .views import (UserCreate,UserPartnerMappingManagement,GetUserRegionalPartners,)


urlpatterns = [
    url(r'^create/$', RolesCreateAPI.as_view()),
    url(r'^list/$', RolesListAPI.as_view()),
    url(r'^update/retrieve/(?P<pk>\d+)/$', RolesRetriveUpdateAPI.as_view()),
    url(r'^activate/$', ActivateAPI.as_view()),
    url(r'^menu-permissions/$', RoleConfigsAPI.as_view()),
    url(r'^menu-permissions/update/$', RoleConfigsUpdate.as_view()),
    url(r'^user/menu-permissions/$', UserMenuPermissions.as_view()),
    url(r'^organization-unit/$', OrgUnitCreate.as_view()),
    url(r'^organization-unit/list/$', OrgUnitList.as_view()),
    url(r'^organization-unit/update/retrieve/(?P<pk>\d+)/$', OrgUnitUpdate.as_view()),
    url(r'^location/levels/$', Locationllevels.as_view()),
    url(r'^listing/$', ListingAPI.as_view()),
    url(r'^ad-list/$', ADList.as_view()),
    url(r'^ad-user-detail/$', ADdetail.as_view()),
    url(r'^user/location/$', UserLocationCreate.as_view()),
    url(r'^user-location/update/(?P<pk>\d+)/$', UserLocationEdit.as_view()),
    url(r'^user-location/list/$', UserLocationList.as_view()),
    url(r'^user-location/oragnization/list/$', UserLevelList.as_view()),
    url(r'^user-partner-mapping/$',UserPartnerMappingManagement.as_view()),
    url(r'^get-user-partner-mapping/$',UserPartnerMappingManagement.as_view()),
    url(r'^user-region-partners/(?P<user_id>\d+)/$',GetUserRegionalPartners.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
