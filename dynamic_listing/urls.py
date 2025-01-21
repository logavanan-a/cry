from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import (DListing,DCreate,ModelFields,ModelFilterCreate,
DFiltering,GetFilteringFields,CreateFilterQuery,FiltersAvailable,ListingsAvailable,
ModelField,ModelFilterResult,)

urlpatterns = [
    url(r'^listing/$', DListing.as_view()),
    url(r'^create/$',DCreate.as_view()),
    url(r'^model_field/$',ModelFields.as_view()),
    url(r'^create_model_filter/$',ModelFilterCreate.as_view()),
    url(r'^filtering/$', DFiltering.as_view()),
    url(r'^filtering_fields_list/$',GetFilteringFields.as_view()),
    url(r'^create_filter_criteria/$',CreateFilterQuery.as_view()),
    url(r'^filters_available/(?P<model_name>.+)/(?P<object_id>.+)/$',FiltersAvailable.as_view()),
    url(r'^listing-available/(?P<model_name>.+)/(?P<object_id>.+)/$',ListingsAvailable.as_view()),
    url(r'^model-fields/(?P<model_name>.+)/(?P<object_id>.+)/$',ModelField.as_view()),
    url(r'^filter-listing/$',ModelFilterResult.as_view()),
    ]
