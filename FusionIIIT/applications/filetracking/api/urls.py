from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
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
    ArchiveFileView,
    UnArchiveFile,
    AjaxDropdownView
)

urlpatterns = [
    path('file/', CreateFileView.as_view(), name='create_file'),
    path('file/<int:file_id>/', ViewFileView.as_view(), name='view_file'),
    path('inbox/', ViewInboxView.as_view(), name='view_inbox'),
    path('outbox/', ViewOutboxView.as_view(), name='view_outbox'),
    path('history/<int:file_id>/', ViewHistoryView.as_view(), name='view_history'),
    path('forwardfile/<int:file_id>/', ForwardFileView.as_view(), name='forward_file'),
    path('draft/', DraftFileView.as_view(), name='view_drafts'),
    path('createdraft/', CreateDraftFile.as_view(), name='create_draft'),
    path('createarchive/', CreateArchiveFile.as_view(), name='archive_file'),
    path('unarchive/', UnArchiveFile.as_view(), name='un_archive'),
    path('archive/', ArchiveFileView.as_view(), name='view_archived'),
    path('designations/<str:username>/', GetDesignationsView.as_view(), name='get_designations'),
    path('dropdown/', AjaxDropdownView.as_view(), name='get_dropdown'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)