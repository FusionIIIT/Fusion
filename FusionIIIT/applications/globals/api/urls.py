from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^auth/login/', views.login, name='login-api'),
    url(r'^auth/logout/', views.logout, name='logout-api'),
    url(r'^auth/me', views.auth_view, name='auth-api'),
    url(r'^update-role/', views.update_last_selected_role, name='update_last_selected_role'),
    # generic profile endpoint
    #code of corresponding view is modifiedtemporary because of mismatched designations
    url(r'^profile/(?P<username>.+)/', views.profile, name='profile-api'),
    # current user profile
    url(r'^profile/', views.profile, name='profile-api'),
    url(r'^profile_update/', views.profile_update, name='update-profile-api'),
    url(r'^profile_delete/(?P<id>[0-9]+)/', views.profile_delete, name='delete-profile-api'),

    url(r'^notification/',views.notification,name='notification'),
    url(r'^notificationread',views.NotificationRead,name='notifications-read'),
    url(r'^notificationdelete',views.delete_notification,name='notifications-delete'),
    url(r'^notificationunread',views.NotificationUnread,name='notifications-unread')
]
