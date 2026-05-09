from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^designations/(?P<username>[\w.@+-]+)/$', views.designations_api, name='designations_api'),
    url(r'^dropdown/$', views.dropdown_api, name='dropdown_api'),
    url(r'^createdraft/$', views.create_draft_api, name='create_draft_api'),
    url(r'^draft/$', views.draft_api, name='draft_api'),
    url(r'^file/$', views.file_api, name='file_api'),
    url(r'^file/(?P<file_id>\d+)/$', views.file_detail_api, name='file_detail_api'),
    url(r'^inbox/$', views.inbox_api, name='inbox_api'),
    url(r'^outbox/$', views.outbox_api, name='outbox_api'),
    url(r'^archive/$', views.archive_list_api, name='archive_list_api'),
    url(r'^createarchive/$', views.create_archive_api, name='create_archive_api'),
    url(r'^unarchive/$', views.unarchive_api, name='unarchive_api'),
    url(r'^history/(?P<file_id>\d+)/$', views.history_api, name='history_api'),
    url(r'^forwardfile/(?P<file_id>\d+)/$', views.forward_file_api, name='forward_file_api'),

    # New comprehensive FTS endpoints
    url(r'^new/files/$', views.new_files_api, name='new_files_api'),
    url(r'^new/files/(?P<file_id>\d+)/$', views.new_file_detail_api, name='new_file_detail_api'),
    url(r'^new/files/(?P<file_id>\d+)/send/$', views.new_send_file_api, name='new_send_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/forward/$', views.new_forward_file_api, name='new_forward_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/approve/$', views.new_approve_file_api, name='new_approve_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/reject/$', views.new_reject_file_api, name='new_reject_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/close/$', views.new_close_file_api, name='new_close_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/archive/$', views.new_archive_file_api, name='new_archive_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/return/$', views.new_return_file_api, name='new_return_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/amend/$', views.new_amend_file_api, name='new_amend_file_api'),
    url(r'^new/files/(?P<file_id>\d+)/history/$', views.new_file_history_api, name='new_file_history_api'),
    url(r'^new/inbox/$', views.new_inbox_api, name='new_inbox_api'),
    url(r'^new/outbox/$', views.new_outbox_api, name='new_outbox_api'),
    url(r'^new/pending/$', views.new_pending_api, name='new_pending_api'),
    url(r'^new/archive/$', views.new_archive_list_api, name='new_archive_list_api'),
    url(r'^new/drafts/$', views.new_drafts_api, name='new_drafts_api'),
    url(r'^new/drafts/(?P<draft_id>\d+)/$', views.new_delete_draft_api, name='new_delete_draft_api'),
    url(r'^new/files/(?P<file_id>\d+)/unarchive/$', views.new_unarchive_file_api, name='new_unarchive_file_api'),
    url(r'^new/file-types/$', views.new_file_types_api, name='new_file_types_api'),
    url(r'^new/designations/$', views.new_designations_api, name='new_designations_api'),

    # FT admin user and role management
    url(r'^new/admin/users/$', views.new_admin_users_api, name='new_admin_users_api'),
    url(r'^new/admin/users/(?P<user_id>\d+)/$', views.new_admin_user_detail_api, name='new_admin_user_detail_api'),
    url(r'^new/admin/policies/$', views.new_admin_policies_api, name='new_admin_policies_api'),
    url(r'^new/admin/audit-logs/$', views.new_admin_audit_logs_api, name='new_admin_audit_logs_api'),
]
