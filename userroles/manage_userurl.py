"""UserRoles Urls."""
from django.conf.urls import url,include,patterns
from rest_framework.urlpatterns import format_suffix_patterns
from .views import (UserCreate,Userlist,UserLogin,UserLogout,ChangePasswordUser,
                    ForgetPasswordEmail,ResetPassword,UserDetailCreate,UserDetailUpdate,
                    UserDetailView,UserActivation,UserlistMenu)
from .common_api import (OrganizationUnitRolesApi,DesignationList,RegionList,
                        PartnerList,LoggedinUserPartnerDetail)


urlpatterns = [

    url(r'^login/$',UserLogin.as_view()),
    url(r'^logout/$',UserLogout.as_view()),
    url(r'^list/$',Userlist.as_view()),
    url(r'^create/$',UserDetailCreate.as_view()),
    url(r'^activation/$',UserActivation.as_view()),
    url(r'^detail/view/$',UserDetailView.as_view()),
    url(r'^detail/edit/$',UserDetailUpdate.as_view()),
    url(r'^change_password/$',ChangePasswordUser.as_view()),
    url(r'^forget-password-request/$',ForgetPasswordEmail.as_view()),
    url(r'^forget-password/$',ResetPassword.as_view()),
    url(r'^manage/organization-meet/$',OrganizationUnitRolesApi.as_view()),
    url(r'^manage/designation/list/$',DesignationList.as_view()),
    url(r'^manage/region/list/$',RegionList.as_view()),
    url(r'^manage/menu/list/$',UserlistMenu.as_view()),
    url(r'^manage/partner/list/$',PartnerList.as_view()),
    url(r'^manage/partner/detail/$',LoggedinUserPartnerDetail.as_view()),
    ]

urlpatterns += patterns('',
url(r'^login1/', 'userroles.tokenauth.obtain_expiring_auth_token', name="expiry_token_auth"),
)

urlpatterns = format_suffix_patterns(urlpatterns)

