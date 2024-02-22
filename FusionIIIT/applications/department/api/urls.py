from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'announcements/$', views.ListCreateAnnouncementView.as_view(),name='announcements'),
    url(r'dep-main/$', views.DepMainAPIView.as_view(), name='depmain'),
    url(r'fac-view/$', views.FacAPIView.as_view(), name='facapi'),
    url(r'staff-view/$',views.StaffAPIView.as_view(),name='staffapi'),
    
]
