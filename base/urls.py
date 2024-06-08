from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.homePage, name='home_page'),
    path('login/', views.loginPage, name='login_page'),
    path('register/', views.registerPage, name='register_page'),
    path('logout/', views.logoutUser, name='logout'),
    path('kyc/', views.kycForm, name='kyc_form'),
    path('kyc/batch_list', views.kycHomePage, name='kyc_home_page'),
    path('kyc/<str:pk>', views.kycStudentDetails, name='kyc_details'),
    path('spf/', views.spfForm, name='spf_form'),
    path('spf/batch_list', views.spfHomePage, name='spf_home_page'),
    path('spf/<str:pk>', views.spfStudentDetails, name='spf_details'),
    path('create_drive/', views.createDrive, name='create_drive'),
    path('create_chat', views.createChatRoom, name='create_chat'),
    path('chat/<str:pk>', views.room, name='chat_room'),
    path('tyl/<str:name>', views.tylHomePage, name='tyl_home_page'),
    path('tyl/create_test/<str:name>', views.createTest, name='tyl_create_test'),
    path('tyl/create_assigment/<str:pk>', views.createSubTest, name='tyl_create_sub_test'),
    path('tyl/test_details/<str:pk>', views.tylTestPage, name='tyl_trainer_test_details'),
    path('tyl/upload_marks/<str:pk>', views.uploadTestMarks, name='upload_marks'),
    path('message/delete/<str:pk>', views.deleteMessage, name='delete_message'),
    path('dashboard/spf_kyc/<str:pk>', views.spfKycDashboard, name='spf_kyc_dashboard'),
    path('spad/<str:batch>', views.spadDetails, name='spad_details'),
    path('user_profile/<str:pk>', views.user_profile, name='user_profile'),
    path('user_profile_update', views.user_profile_update, name='user_update'),
    path('dashboard/assignments/batch/<int:batch_id>/test/<int:test_id>/', views.subTestDashboard, name='sub_test_dashboard'),
    path('delete/<str:pk>/', views.delete_room, name='delete_room'),
    path('delete/<str:pk>', views.delete_message, name='delete_message'),
    # path('edit/<str:pk>', views.edit_room, name='edit_room'),
]   
