from django.conf.urls import url, include

from . import views
from .api import urls

app_name = 'filetracking'

urlpatterns = [

    url(r'^$', views.filetracking, name='filetracking'),
    url(r'^draftdesign/$', views.draft_design, name='draft_design'),
    url(r'^drafts/(?P<id>\d+)$', views.drafts_view, name='drafts_view'),
    url(r'^outbox/(?P<id>\d+)$', views.outbox_view, name='outbox_view'),
    url(r'^inbox/(?P<id>\d+)$', views.inbox_view, name='inbox_view'),
    url(r'^outward/$', views.outward, name='outward'),
    url(r'^inward/$', views.inward, name='inward'),
    url(r'^confirmdelete/(?P<id>\d+)$',
        views.confirmdelete, name='confirm_delete'),
    url(r'^archive/(?P<id>\d+)/$', views.archive_view, name='archive_view'),
    url(r'^finish/(?P<id>\d+)/$', views.finish, name='finish'),
    url(r'^forward/(?P<id>\d+)/$', views.forward, name='forward'),
    url(r'^ajax/$', views.AjaxDropdown1, name='ajax_dropdown1'),
    url(r'^ajax_dropdown/$', views.AjaxDropdown, name='ajax_dropdown'),
    url(r'^test/$', views.test, name='test'),
    url(r'^delete/(?P<id>\d+)$', views.delete, name='delete'),
    url(r'^forward_inward/(?P<id>\d+)/$',
        views.forward_inward, name='forward_inward'),

    # correction team 24
    url(r'^finish_design/$', views.finish_design, name='finish_design'),
    url(r'^finish_fileview/(?P<id>\d+)$',
        views.finish_fileview,
        name='finish_fileview'),
    url(r'^archive_design/$', views.archive_design, name='archive_design'),
    url(r'^archive_finish/(?P<id>\d+)/$',
        views.archive_finish, name='archive_finish'),

    # REST api urls
    url(r'^api/', include(urls))

]
