from notifications.urls import urlpatterns
from applications.notifications_extension.views import mark_as_read_and_redirect
from django.urls import re_path as pattern
from django.urls import include, re_path as url
from . import views
from . import api_views

app_name = 'notifications'

urlpatterns = [
        pattern(r'^mark-as-read-and-redirect/(?P<slug>\d+)/$', views.mark_as_read_and_redirect, name='mark_as_read_and_redirect'),
        pattern(r'^api/announcements/$', api_views.system_announcements_api, name='system_announcements_api'),
        pattern(r'^api/announcements/(?P<pk>\d+)/archive/$', api_views.archive_announcement_api, name='archive_announcement_api'),
    ] + urlpatterns

