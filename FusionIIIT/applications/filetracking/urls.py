from django.conf.urls import url

from . import views

app_name = 'filetracking'

urlpatterns = [

    url(r'^$', views.filetracking, name='filetracking'),
    url(r'^drafts/$', views.drafts, name='drafts'),
    url(r'^fileview/(?P<id>\d+)$', views.fileview, name='fileview'),
    url(r'^fileview1/(?P<id>\d+)$', views.fileview1, name='fileview1'),
    url(r'^fileview2/(?P<id>\d+)$', views.fileview2, name='fileview2'),
    url(r'^outward/$', views.outward, name='outward'),
    url(r'^inward/$', views.inward, name='inward'),
    url(r'^confirmdelete/(?P<id>\d+)$', views.confirmdelete, name='confirm_delete'),
    url(r'^archive/(?P<id>\d+)/$', views.archive, name='archive'),
    url(r'^finish/(?P<id>\d+)/$', views.finish, name='finish'),
    url(r'^forward/(?P<id>\d+)/$', views.forward, name='forward'),
    url(r'^ajax/$', views.AjaxDropdown1, name='ajax_dropdown1'),
    url(r'^ajax_dropdown/$', views.AjaxDropdown, name='ajax_dropdown'),
    url(r'^test/$',views.test, name='test'),
    url(r'^delete/(?P<id>\d+)$',views.delete, name='delete'),
    url(r'^forward_inward/(?P<id>\d+)/$', views.forward_inward, name='forward_inward'),

    ## correction team 24
    url(r'^finish_design/$', views.finish_design, name='finish_design'),
    url(r'^finish_fileview/(?P<id>\d+)$', views.finish_fileview, name='finish_fileview'),
    url(r'^archive_design/$', views.archive_design, name='archive_design'),
    url(r'^archive_finish/(?P<id>\d+)/$', views.archive_finish, name='archive_finish'),
]
