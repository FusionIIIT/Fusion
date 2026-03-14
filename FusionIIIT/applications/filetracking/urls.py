from django.conf.urls import url, include

from . import views
from .api import urls

app_name = 'filetracking'

urlpatterns = [

    url(r'^$', views.filetracking, name='filetracking'),
    url(r'^draftdesign/$', views.draft_design, name='draft_design'),
    url(r'^drafts/(?P<id>\d+)$', views.drafts_view, name='drafts_view'),
    url(r'^outbox/(?P<id>\d+)$', views.outbox_view, name='outbox_view'),
    url(r'^inbox/$', views.inbox_view, name='inbox_view'),
    url(r'^outward/$', views.outbox_view, name='outward'),
    url(r'^inward/$', views.inbox_view, name='inward'),
    url(r'^confirmdelete/(?P<id>\d+)$',
        views.confirmdelete, name='confirm_delete'),
    url(r'^archive/(?P<id>\d+)/$', views.archive_view, name='archive_view'),
    url(r'^finish/(?P<id>\d+)/$', views.archive_file, name='finish_file'),
    url(r'^viewfile/(?P<id>\d+)/$', views.view_file, name='view_file_view'),
    url(r'^forward/(?P<id>\d+)/$', views.forward, name='forward'),
    url(r'^ajax/$', views.AjaxDropdown1, name='ajax_dropdown1'),
    url(r'^ajax_dropdown/$', views.AjaxDropdown, name='ajax_dropdown'),
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
    url(r'unarchive/(?P<id>\d+)/$', 
        views.unarchive_file, name='unarchive'),
    url(r'^getdesignations/(?P<username>\w+)/$', views.get_designations_view, name="get_user_designations"),
    url(r'^editdraft/(?P<id>\w+)/$', views.edit_draft_view, name="edit_draft"),
    url(r'^download_file/(?P<id>\w+)/$', views.download_file, name="download_file"),

    # REST api urls
    url(r'^api/', include(urls))

]
