from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^auth/login/', views.login, name='login-api'),
    re_path(r'^auth/logout/', views.logout, name='logout-api'),
    re_path(r'^auth/me', views.auth_view, name='auth-api'),

    # OTP-based password reset (no authentication required)
    re_path(r'^auth/password-reset/send-otp/',  views.password_reset_send_otp,   name='password-reset-send-otp'),
    re_path(r'^auth/password-reset/verify-otp/', views.password_reset_verify_otp, name='password-reset-verify-otp'),
    re_path(r'^auth/password-reset/reset/',     views.password_reset_reset,       name='password-reset-reset'),

    re_path(r'^update-role/', views.update_last_selected_role, name='update_last_selected_role'),

    # Profile endpoints
    re_path(r'^profile/(?P<username>.+)/', views.profile, name='profile-api'),
    re_path(r'^profile/', views.profile, name='profile-api'),
    re_path(r'^profile_update/', views.profile_update, name='update-profile-api'),
    re_path(r'^profile_delete/(?P<id>[0-9]+)/', views.profile_delete, name='delete-profile-api'),

    # Notification endpoints
    re_path(r'^notification/', views.notification, name='notification'),
    re_path(r'^notificationread', views.NotificationRead, name='notifications-read'),
    re_path(r'^notificationdelete', views.delete_notification, name='notifications-delete'),
    re_path(r'^notificationunread', views.NotificationUnread, name='notifications-unread'),

    # Course management proxy
    re_path(r'^admin_delete_course/(?P<course_id>\d+)/', views.admin_delete_course_proxy, name='admin_delete_course_proxy')
]