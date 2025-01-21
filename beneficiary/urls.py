from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *
from facilities.views import FacilityAdd, FacilityUpdate, FacilityDetail, FacilityListing
from .config_views import *
from .views1 import *

urlpatterns = [
    url(r'^addhousehold/$', BeneficiaryAdd.as_view()),
    url(r'^gethouseholds/$', HouseholdLisitng.as_view()),
    url(r'^householddetail/$', HouseholdDetail.as_view()),
    url(r'^householdupdate/$', HouseholdUpdate.as_view()),
    url(r'^activedeactive/$', ActiveDeactiveActions.as_view()),
    url(r'^gethouseholdparent/$', RetreiveMother.as_view()),
    url(r'^schooltype/listing/$', GenericListing.as_view(), {'slug':'school-type'}),
    url(r'^menulisting/$', BeneficiaryMenuListing.as_view()),
    url(r'^typewiselisting/$', BeneficiaryTypeWiseListing.as_view()),
    url(r'^typewiseparentlisting/$', RetreiveBtypeParentsListing.as_view()),
    url(r'^addressupdate/(?P<pk>[0-9]+)/$', BeneficiaryAddress.as_view()),
    url(r'^address/create/$', BeneficiaryAddressCreate.as_view(), {'key':'beneficiary'}),
    url(r'^address/update/$', BeneficiaryAddressUpdate.as_view()),
    url(r'^relation/add/$', BeneficiaryRelationCreate.as_view()),
    url(r'^relation/list/$', BeneficiaryRealtionListing.as_view()),
    url(r'^relation/update/$', BeneficiaryRelationUpdate.as_view()),
    url(r'^relation/detail/$', BeneficiaryRealtionDetail.as_view()),
    url(r'^retreivetypes/$', RetreiveBeneficiaryTypes.as_view()),
    url(r'^retreivepartnerbased/$', RetreivePartnerBasedBeneficiary.as_view()),
    url(r'^relation/masterlisting/$', GenericListing.as_view(), {'slug':'relation'}),
    url(r'^btype/add/$', BeneficiaryTypeCreate.as_view(), {'model':'beneficiarytype'}),
    url(r'^btype/update/$', BeneficiaryTypeUpdate.as_view(), {'model':'beneficiarytype'}),
    url(r'^btype/listing/$', FacilityListing.as_view(), {'key':'beneficiarytype'}),
    url(r'^btype/listing/withoutpagination/$', BeneficiarySubTypeListing.as_view()),
    url(r'^btype/detail/$', FacilityDetail.as_view(), {'key':'beneficiarytype'}),
    url(r'^updateaddresstype/$', UpdateAddressType.as_view(), {'model':'beneficiary'}),
    url(r'^partnerupdateaddresstype/$', UpdateAddressType.as_view(), {'model':'partner'}),
    url(r'^codeconfig/add/$', CodeConfigCreate.as_view()),
    url(r'^codeconfig/update/$', CodeConfigUpdate.as_view()),
    url(r'^codeconfig/listing/$', CodeConfigListing.as_view()),
    url(r'^codeconfig/detail/$', CodeConfigDetail.as_view()),
    url(r'^retrieve/contenttypes/$', RetrieveContentType.as_view()),
    url(r'^datewiselisting/$', BeneficiaryListingDateWise.as_view()),
    url(r'^btypedetails/$', HouseholdTypeDetail.as_view()),
    url(r'^livesearchbeneficiary/$', RetreiveLiveParentsListing.as_view()),
    url(r'^addressproof/masterlisting/$', GenericListing.as_view(), {'slug':'addressproof'}),
    url(r'^mother-list/$', HouseholdMotherListing.as_view()),

]

