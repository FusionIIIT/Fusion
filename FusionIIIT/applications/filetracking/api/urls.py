from django.conf.urls import url
from .views import (
    CreateFileView,
    ViewFileView,
    ViewInboxView,
    ViewOutboxView,
    ViewHistoryView,
    ForwardFileView,
    DraftFileView,
    CreateDraftFile,
    GetDesignationsView,
    CreateArchiveFile, 
    ArchiveFileView
)

urlpatterns = [
    url(r'^file/$', CreateFileView.as_view(), name='create_file'),
    url(r'^file/(?P<file_id>\d+)/$', ViewFileView.as_view(), name='view_file'),
    url(r'^inbox/$', ViewInboxView.as_view(), name='view_inbox'),
    url(r'^outbox/$', ViewOutboxView.as_view(), name='view_outbox'),
    url(r'^history/(?P<file_id>\d+)/$', ViewHistoryView.as_view(), name='view_history'),
    url(r'^forwardfile/(?P<file_id>\d+)/$', ForwardFileView.as_view(), name='forward_file'),
    url(r'^draft/$', DraftFileView.as_view(), name='view_drafts'),
    url(r'^createdraft/$', CreateDraftFile.as_view(), name='create_draft'),
    url(r'^createarchive/$', CreateArchiveFile.as_view(), name='archive_file'),
    url(r'^archive/$', ArchiveFileView.as_view(), name='view_archived'),
    url(r'^designations/(?P<username>\w+)/$', GetDesignationsView.as_view(), name='get_designations'),
]
