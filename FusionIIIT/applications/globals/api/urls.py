from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^auth/login/', views.login, name='login-api'),
    url(r'^auth/logout/', views.logout, name='logout-api'),
    url(r'^auth/me', views.auth_view, name='auth-api'),
    url(r'^update-role/', views.update_last_selected_role, name='update_last_selected_role'),
    
    # Profile endpoints
    url(r'^profile/(?P<username>.+)/', views.profile, name='profile-api'),
    url(r'^profile/', views.profile, name='profile-api'),
    url(r'^profile_update/', views.profile_update, name='update-profile-api'),
    url(r'^profile_delete/(?P<id>[0-9]+)/', views.profile_delete, name='delete-profile-api'),

    # Notification endpoints
    url(r'^notification/',views.notification,name='notification'),
    url(r'^notificationread',views.NotificationRead,name='notifications-read'),
    url(r'^notificationdelete',views.delete_notification,name='notifications-delete'),
    url(r'^notificationunread',views.NotificationUnread,name='notifications-unread'),

    # Database dashboard APIs
    url(r'^db/issues/$', views.db_issues, name='db-issues'),
    url(r'^db/issues/(?P<issue_id>\d+)/$', views.db_issue_update, name='db-issue-update'),
    url(r'^db/issues/(?P<issue_id>\d+)/support/$', views.db_issue_support_toggle, name='db-issue-support'),
    url(r'^db/feedback/$', views.db_feedback, name='db-feedback'),
    url(r'^db/search/$', views.db_user_search, name='db-user-search'),
    
    # Course management proxy
    url(r'^admin_delete_course/(?P<course_id>\d+)/', views.admin_delete_course_proxy, name='admin_delete_course_proxy')
]