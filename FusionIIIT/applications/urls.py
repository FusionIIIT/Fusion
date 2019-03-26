from django.conf.urls import url

from . import views

app_name = 'filetracking'

urlpatterns = [

    url(r'^$', views.filetracking, name='filetracking'),
    url(r'^drafts/$', views.drafts, name='drafts'),
    url(r'^outward/$', views.outward, name='outward'),
    url(r'^inward/$', views.inward, name='inward'),
    url(r'^archive/$', views.archive, name='archive'),
    url(r'^finish/(?P<id>\d+)/$', views.finish, name='finish'),
    url(r'^forward/(?P<id>\d+)/$', views.forward, name='forward'),
]
