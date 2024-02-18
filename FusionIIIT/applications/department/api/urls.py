from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'announcements/$', views.ListCreateAnnouncementView.as_view(),
        name='announcements'),
]
