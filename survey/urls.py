from django.conf.urls import patterns, include, url
from survey.capture_tabinfo import *
from django.conf.urls import url, include
from .models import *
from .get_parent_levels import get_parent_levels, get_levels
from .views.survey_views import (SurveyList, BlockCreate, QuestionList,
QuestionCreate, AnswerValidator, SaveAnswer, SurveyResponses, SurveyList,
ResponseView, SurveyBlockList, GetSurveyQuestions, CreateQuestion,
GetBlockQuestions, GetQuestionDetail, GetQuestionOptions, UpdateAnswer,
CreateQuestionOptions, GetOption, DeoList, UserSurveyMap, GetUserSurveyMap,
GetFaciltyTypes, GetLocationTypes, CreateSurvey, GetDataEntryLevels,GetUserPartner,MasterChoiceSearch, ProfileViewWebApp , profileViewAndroidApp )

from .views.survey_views_two import (GetCluster,UpdateQuestion,
GetExtendedProfileDetails,GetBoundaryLevelData,GetQuestionValidation,
UpdateQuestionValidation,GetSkipQuestion,GetSurvey,UpdateSurvey,ConfigSkip,
PeriodicityValidate,GetResponse, GetBeneficiaryRelatedSurvey,GetFacilityRelatedSurvey,
GetAdditionalFacilityInfo,CheckUserPermission,GetPartnerExtensionParameters,
CreatePartnerExtension,PartnerExtensionDetail,PartnerExtensionUpdate,
SurveyPartnerExtensionListing,GetFilterRelatedSurvey,GetResponseDraftView,
GetRegionalStates,AutoQuestionCode,LanguageList,BatchPivotView,StatePartnerList,
FormExport,GetRegionalTranslations,RegionalTranslations,GetPreviousQuestions,
GetQuestionDependentValue,DeactivateChoice,MutantSurveyReportExport,DeactivateQuestion ,CreateEditBlock , EditUpdateBlock)

urlpatterns = patterns('',
                       url(r'^app-login/$', 'survey.api_views.applogin',
                           name='app_login'),
                       url(r'^app-cluster-list/$',
                           'survey.api_views.cluster_list', name='cluster_list'),
                       url(r'^add-survey-answers/$', 'survey.api_views.add_survey_answers',
                           name='add_survey_answers'),
                       url(r'^app-logout/$', 'survey.api_views.app_logout',
                           name='app_logout'),
                       url(r'^fetch-version-updates/$',
                           'survey.api_views.fetch_version_updates', name='fetch_version_updates'),
                       url(r'^feederrorlog/$', 'survey.api_views.feed_error_log',
                           name='feed_error_log'),
                       url(r'^logsentbyuser/$', 'survey.api_views.feed_error_log',
                           name='login_error_log'),
                       url(r'^get-language-labels/$', 'survey.api_views.get_language_app_label',
                           name="get_language_app_label"),
                       url(r'^check-network-connectivity/$',
                           'survey.api_views.check_network_connectivity', name="check_network_connectivity"),
                       url(r'^store-db/$', 'survey.api_views.dblog', name="dblog"),
                       )

urlpatterns += patterns('',
                        url(r'^survey-list/$',
                            'survey.api_views.surveylist', name="surveylist"),
                        url(r'^block-list/$', 'survey.new_apis.blocklist',
                            name="blocklist"),
                        url(r'^language-block-list/$',
                            'survey.new_apis.languageblocklist', name="languageblocklist"),
                        url(r'^language-question-list/$',
                            'survey.new_apis.languagequestionlist', name="languagequestionlist"),
                        url(r'^assessment-list/$',
                            'survey.new_apis.assessmentlist', name="assessmentlist"),
                        url(r'^language-assessment-list/$',
                            'survey.new_apis.languageassessmentlist', name="languageassessmentlist"),
                        url(r'^question-list/$',
                            'survey.new_apis.questionlist', name="questionlist"),
                        url(r'^choice-list/$',
                            'survey.new_apis.choicelist', name="choicelist"),
                        url(r'^updated-tables/$',
                            'survey.new_apis.updatedtables', name="updatedtables"),
                        url(r'^skip-mandatory/$',
                            'survey.new_apis.skipmandatory', name="skipmandatory"),
                        url(r'^alarm-frequency/$', 'survey.api_views.alarm_frequency',
                            name="alarm_frequency"),
                        #    url(r'^sub-questions/$', 'survey.new_apis.subquestion', name="subquestion"),
                        url(r'^language-label/$',
                            'survey.new_apis.languagelabel', name="languagelabel"),
                        url(r'^language-choice/$',
                            'survey.new_apis.languagechoice', name="languagechoice"),
                        url(r'^responses-list/$',
                            'survey.new_apis.responses_list', name="responses_list"),
                        url(r'^language-list/$', 'survey.new_apis.languagelist'),
                        url(r'^app-issue-tracker/$', 'survey.new_apis.appissuetracker', name="appissuetracker"),
                        url(r'^response-detail/$', 'survey.new_apis.response_details', name="response_details"),
                        )

urlpatterns += patterns('', url(r'^level/(?P<level>.+)/$', 'survey.get_parent_levels.get_levels'),
                        #    url(r'^level1-list/$', 'survey.capture_sur_levels.levellist', {'key':'country'}),
                        #    url(r'^level2-list/$', 'survey.capture_sur_levels.levellist', {'key':'state'}),
                        #    url(r'^level3-list/$', 'survey.capture_sur_levels.levellist', PartnerExtensionUpdate{'key':'village'}),
                        ##    url(r'^level8-list/$', 'survey.capture_sur_levels.level8list', name='level8_list'),
                        #    url(r'^parent-child/$', 'survey.capture_sur_levels.parent_child_info', name='parent_child_info'),
                        )

# urlpatterns += patterns('',
#    url(r'^api-dynamic-data-report/$', 'survey.report_view.api_data_report', name="api_dynamic_data_report"),
#    url(r'^api-data-report/kill-response/$','survey.report_view.api_data_report_kill', name="api_data_report_kill"),
#    url(r'^download-answer-data/$','survey.report_view.download_answer_data', name="download_answer_data"),
#    url(r'^get-survey-users-languages/$','survey.report_view.get_survey_users_languages', name="get_survey_users_languages"),
#    url(r'^get-user-villages/$','survey.report_view.get_user_villages', name="get_user_villages"),
#)

# urlpatterns += patterns('',
#    url(r'^sms-data/$','survey.sms_view.save_sms_data', name="save_sms_data"),
#    url(r'^check-customer/$','survey.sms_view.validate_customerid', name="validate_customerid"),
#    url(r'^get-rb-mobile-number/$','sskip_choicesey.sms_view.rba_based_service', name="rba_based_service"),
#)

# urlpatterns += patterns('',
#    url(r'^view-orders/$','survey.assistme.view_orders', name="view_orders"),
#    url(r'^update-order-status/(?P<oid>\d+)/$','survey.assistme.update_order_status', name="update_order_status"),
#    url(r'^assistme-auth/$','survey.assistme.assistme_authenticate', name="assistme_authenticate"),
#    url(r'^update-token/$','survey.assistme.update_token', name="update_token"),
#    url(r'^view-services/$','survey.assistme.view_services', name="view_services"),
#    url(r'^add-assistme-service/$','survey.assistme.add_assistme_service', name="add_assistme_service"),
#    url(r'^edit-service/(?P<sid>\d+)/$','survey.assistme.edit_service', name="edit_service"),
#    url(r'^view-categories/$','survey.assistme.view_categories', name="view_categories"),
#    url(r'^add-assistme-category/$','survey.assistme.add_assistme_category', name="add_assistme_category"),
#    url(r'^edit-category/(?P<cid>\d+)/$','survey.assistme.edit_category', name="edit_category"),
#    url(r'^list-rba-service-mapping/$','survey.assistme.list_rba_service_mapping', name="list_rba_service_mapping"),
#    url(r'^add-rba-service-mapping/$','survey.assistme.add_rba_service_mapping', name="add_rba_service_mapping"),
#    url(r'^view-mobile-logs/$','survey.assistme.view_mobile_logs', name="view_mobile_logs"),
#)

urlpatterns += patterns('',
                        url(r'^capture-tab-info/$',
                            CaptureTabInfo.as_view(), name="capture_tabinfo"),
                        url(r'^view-users-on-map/$',
                            UserMapView.as_view(), name="capture_tabinfo"),
                        )

# Mallik survey urls
urlpatterns += patterns(
    url(r'^surveylist/$', SurveyList.as_view()),
    url(r'^block_create/$', BlockCreate.as_view()),
    url(r'^questionlist/(?P<sid>.+)/(?P<block_id>.+)/(?P<skip>.+)/(?P<choice>.+)/(?P<lid>.+)/(?P<c_info>.+)/$',
        QuestionList.as_view()),
    url(r'^questioncreate/$', QuestionCreate.as_view()),
    url(r'^question_update/$', UpdateQuestion.as_view()),
    url(r'^answerValidator/$', AnswerValidator.as_view()),
    url(r'^saveAnswer/$', SaveAnswer.as_view()),
    url(r'^survey_responses/$', SurveyResponses.as_view()),
    url(r'^survey_list/(?P<user_id>.+)/$', SurveyList.as_view()),
    url(r'^response/$', ResponseView.as_view()),
    url(r'^survey_block_list/$', SurveyBlockList.as_view()),
    url(r'^survey_questions_list/$', GetSurveyQuestions.as_view()),
    url(r'^create_question/$', CreateQuestion.as_view()),
    url(r'^block_questions/$', GetBlockQuestions.as_view()),
    url(r'^get_question_details/(?P<question_id>.+)/$',
        GetQuestionDetail.as_view()),
    url(r'^get_question_options/(?P<question_id>.+)/$',
        GetQuestionOptions.as_view()),
    url(r'^update_response/$', UpdateAnswer.as_view()),
    url(r'^create_options/$', CreateQuestionOptions.as_view()),
    url(r'^get_option/(?P<id>.+)/$', GetOption.as_view()),
    url(r'^get_deo_list/$', DeoList.as_view()),
    url(r'^survey_user_config/$', UserSurveyMap.as_view()),
    url(r'^get_survey_user_config/(?P<survey_id>.+)/$', GetUserSurveyMap.as_view()),
    url(r'^get_facility_types/$', GetFaciltyTypes.as_view()),
    url(r'^get_location_types/$', GetLocationTypes.as_view()),
    url(r'^get_data_entry_levels/$', GetDataEntryLevels.as_view()),
    url(r'^create_survey/$', CreateSurvey.as_view()),
    url(r'^get_cluster/(?P<survey_id>.+)/(?P<user_id>.+)/$', GetCluster.as_view()),
    url(r'^get_skip_questions/(?P<qid>.+)/(?P<sid>.+)/$', GetSkipQuestion.as_view()),
    url(r'^config_skip/$', ConfigSkip.as_view()),
    url(r'^get_survey_details/(?P<sid>.+)/$', GetSurvey.as_view()),
    url(r'^survey_update/$', UpdateSurvey.as_view()),
    url(r'^periodicity_validate/(?P<sid>.+)/(?P<cluster>.+)/$',
        PeriodicityValidate.as_view()),
    url(r'^get_workflow_response/(?P<bid>.+)/$', GetResponse.as_view()),
    url(r'^get_beneficiary_related_survey/(?P<bid>.+)/$',
        GetBeneficiaryRelatedSurvey.as_view()),
    url(r'^get_facility_related_survey/(?P<fid>.+)/$',
        GetFacilityRelatedSurvey.as_view()),
    url(r'^get_user_permission/(?P<sid>.+)/(?P<uid>.+)/$',
        CheckUserPermission.as_view()),
    url(r'^get_additional_facility/(?P<uid>.+)/(?P<sid>.+)/$',
        GetAdditionalFacilityInfo.as_view()),
    url(r'^get_partner_extension_parameters/(?P<spid>.+)/$',
        GetPartnerExtensionParameters.as_view()),
    url(r'^create_partner_extension/$', CreatePartnerExtension.as_view()),
    url(r'^partner_extension_detail/(?P<spid>.+)/$',
        PartnerExtensionDetail.as_view()),
    url(r'^partner_extension_update/$', PartnerExtensionUpdate.as_view()),
    url(r'^partner_extension_listing/$', SurveyPartnerExtensionListing.as_view()),
    url(r'^get-boundary-level-data/(?P<bid>.+)/(?P<lid>.+)/$',GetBoundaryLevelData.as_view()),
    url(r'^get-filter-related-survey/(?P<model_name>.+)/(?P<object_id>.+)/$',GetFilterRelatedSurvey.as_view()),
    url(r'^get_question_validation/(?P<qid>.+)/$',GetQuestionValidation.as_view()),
    url(r'^update_question_validation/$',UpdateQuestionValidation.as_view()),
    url(r'^get_related_extended_profile/(?P<related_type>.+)/(?P<object_id>.+)/$',GetExtendedProfileDetails.as_view()),
    url(r'^get-response-draft-view/(?P<response_id>.+)/$',GetResponseDraftView.as_view()),
    url(r'^get_user_partner/(?P<user_id>.+)/$',GetUserPartner.as_view()),
    url(r'^get-regional-states/(?P<region>.+)/$',GetRegionalStates.as_view()),
    url(r'^get-auto-question-code/(?P<form_id>.+)/$',AutoQuestionCode.as_view()),
    url(r'^get_languages/$',LanguageList.as_view()),
    url(r'^get_pivot_view/(?P<batch_id>.+)/$',BatchPivotView.as_view()),
    url(r'^get-state-partner-list/$',StatePartnerList.as_view()),
    url(r'^export-form-responses/(?P<form_id>.+)/(?P<user_id>.+)/$',FormExport.as_view()),
    url(r'^get-regional-translations/(?P<model_name>.+)/(?P<object_id>.+)/$',GetRegionalTranslations.as_view()),
    url(r'^regional-translation/$',RegionalTranslations.as_view()),
    url(r'^get-previous-questions/(?P<qcode>.+)/(?P<sid>.+)/$',GetPreviousQuestions.as_view()),
    url(r'^question-dependent-value/(?P<qid>.+)/(?P<cid>.+)/$',GetQuestionDependentValue.as_view()),
    url(r'^deactivate-choice/(?P<cid>.+)/$',DeactivateChoice.as_view()),
    url(r'^deactivate-question/(?P<qid>.+)/$',DeactivateQuestion.as_view()),
    url(r'^master-choice/$',MasterChoiceSearch.as_view()),
    url(r'^export-mutant-form-responses/(?P<form_id>.+)/(?P<user_id>.+)/(?P<table>.+)/$',MutantSurveyReportExport.as_view()),
    url(r'^submitted_response_list/(?P<cluster>.+)/$' , ProfileViewWebApp.as_view()),
    url(r'^submitted_response_list_android/$' , profileViewAndroidApp.as_view()),
	url(r'^create_block/$' , CreateEditBlock.as_view()),
	url(r'^edit_block/$' , EditUpdateBlock.as_view()),
	url(r'^update_block/$',EditUpdateBlock.as_view()),
)
