from django.conf.urls import url

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.dep_main, name='dep'),
    url(r'^facView/$', views.faculty_view, name='faculty_view'),
    url(r'^staffView/$', views.staff_view, name='staff_view'),
    url(r'^All_Students/(?P<bid>[0-9]+)/$', views.all_students,name='all_students'),
    url(r'^approved/$', views.approved, name='approved'),
    url(r'^deny/$', views.deny, name='deny'),

    #api routes
    url(r'^fetchAnnouncements/$', views.AnnouncementAPI.as_view(http_method_names=['get']), name='fetchAnnouncements'),
    url(r'^addNewAnnouncement/$', views.AnnouncementAPI.as_view(http_method_names=['post']), name='addNewAnnouncement'),
    url(r'^fetchRequest/$', views.SpecialRequestAPI.as_view(http_method_names=['get']), name='fetchRequest'),
    url(r'^addNewRequest/$', views.SpecialRequestAPI.as_view(http_method_names=['post']), name='addNewRequest'),
]
               