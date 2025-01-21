from django.conf.urls import url
from .views import (WorkStateView, WorkStateViewEdit, WorkFlowView, WorkFlowViewEdit,
                    WorkFlowSurveyRelationView, WorkFlowSurveyRelationViewEdit, ListingData, GetStates,
                    WorkFlowCommentView, WorkFlowCommentEdit, WorkFlowBatchView, WorkFlowPrimaryComment,
                    WorkFlowCurrentDetail, WorkFlowBatchPrimary, WorkFlowBatchPlainDetail)


urlpatterns = [
    url(r'^state/$', WorkStateView.as_view()),
    url(r'^state/(?P<pk>[0-9]+)/$', WorkStateViewEdit.as_view()),
    url(r'^data/listing/$', ListingData.as_view()),
    url(r'^configure/$', WorkFlowView.as_view()),
    url(r'^configure/(?P<pk>[0-9]+)/$', WorkFlowViewEdit.as_view()),
    url(r'^configure/survey/$', WorkFlowSurveyRelationView.as_view()),
    url(r'^configure/survey/(?P<pk>[0-9]+)/$',
        WorkFlowSurveyRelationViewEdit.as_view()),
    url(r'^get-states/comment/$', GetStates.as_view()),
    url(r'^comment/$', WorkFlowCommentView.as_view()),
    url(r'^comment/(?P<pk>[0-9]+)/$', WorkFlowCommentEdit.as_view()),
    url(r'^batches/$', WorkFlowBatchView.as_view()),
    url(r'^comment/list/$', WorkFlowPrimaryComment.as_view()),
    url(r'^comment/detail/$', WorkFlowCurrentDetail.as_view()),
    url(r'^batch/detail/$', WorkFlowBatchPrimary.as_view()),
    url(r'^batch/plain/detail/$', WorkFlowBatchPlainDetail.as_view()),
]
