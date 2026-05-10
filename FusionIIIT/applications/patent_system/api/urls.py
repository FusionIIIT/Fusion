from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # Applicant-related paths
    path("applicant/applications/submit/", views.submit_application, name="submit_application"),
    path("applicant/applications/", views.view_applications, name="view_applications"),
    path("applicant/applications/details/<int:application_id>/", views.view_application_details_for_applicant, name="view_application_details"),
    path("applicant/drafts/", views.saved_drafts, name="saved_drafts"),
    path("applicant/applications/<int:app_id>/withdraw/", views.withdraw_application, name="withdraw_application"),
    path("applicant/applications/<int:app_id>/resubmit/", views.resubmit_application, name="resubmit_application"),
    path("applicant/applications/<int:app_id>/appeals/", views.submit_appeal, name="submit_appeal"),
    path("applicant/insights/", views.get_applicant_insights, name="get_applicant_insights"),

    # PCCAdmin-related paths
    path("pccAdmin/applications/new/", views.new_applications, name="new_applications"),
    path("pccAdmin/applications/new/review/<int:application_id>/", views.review_application, name="review_applications"),
    path("pccAdmin/applications/new/forward/<int:application_id>/", views.forward_application, name="forward_application"),
    path("pccAdmin/applications/new/requestModification/<int:application_id>/", views.request_application_modification, name="request_application_modification"),
    path("pccAdmin/applications/ongoing/", views.ongoing_applications, name="ongoing_applications"),
    path("pccAdmin/applications/ongoing/changeStatus/<int:application_id>/", views.change_application_status, name="change_application_status"),
    path("pccAdmin/applications/past/", views.past_applications, name="past_applications"),
    path("pccAdmin/applications/details/<int:application_id>/", views.view_application_details_for_pccAdmin, name="view_application_details_for_pccAdmin"),
    path("pccAdmin/applications/<int:application_id>/communication-logs/", views.communication_logs, name="communication_logs"),
    path("pccAdmin/applications/<int:app_id>/declare-conflict/", views.declare_conflict, name="declare_conflict"),
    path("pccAdmin/applications/<int:app_id>/legal-assessment/", views.legal_assessment_api, name="legal_assessment_api"),
    path("pccAdmin/applications/<int:app_id>/legal-memos/", views.legal_memos_api, name="legal_memos_api"),
    path("pccAdmin/applications/<int:app_id>/budget/", views.budget_api, name="budget_api"),
    path("pccAdmin/budget/<int:budget_id>/decision/", views.budget_decision_by_id, name="budget_decision_by_id"),
    path("pccAdmin/applications/<int:app_id>/external-filing/", views.external_filing_api, name="external_filing_api"),
    path("pccAdmin/applications/<int:app_id>/office-actions/", views.office_actions_api, name="office_actions_api"),
    path("pccAdmin/office-actions/<int:office_action_id>/respond/", views.respond_office_action, name="respond_office_action"),
    path("pccAdmin/applications/<int:app_id>/prior-art/", views.prior_art_api, name="prior_art_api"),
    path("pccAdmin/applications/<int:app_id>/appeals/", views.appeals_api, name="appeals_api"),
    path("pccAdmin/applications/<int:app_id>/licensing/", views.licensing_api, name="licensing_api"),
    path("pccAdmin/applications/<int:app_id>/inventor-consents/", views.inventor_consents_api, name="inventor_consents_api"),
    path("pccAdmin/applications/<int:app_id>/maintenance/", views.maintenance_api, name="maintenance_api"),
    path("pccAdmin/maintenance/<int:schedule_id>/mark-paid/", views.mark_maintenance_paid, name="mark_maintenance_paid"),
    path("pccAdmin/reviewer-queue/", views.reviewer_queue, name="reviewer_queue"),
    path("pccAdmin/queue/prioritized/", views.queue_prioritized, name="queue_prioritized"),
    path("pccAdmin/notifications/", views.get_notifications, name="get_notifications"),
    path("pccAdmin/notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("pccAdmin/audit-logs/", views.get_audit_logs, name="get_audit_logs"),
    path("pccAdmin/insights/", views.pcc_insights, name="pcc_insights"),
    path("pccAdmin/applications/new/resubmit/<int:app_id>/", views.pcc_resubmit_application, name="pcc_resubmit_application"),

    # Director-related paths
    path("director/applications/new/", views.director_new_applications, name="director_new_applications"), 
    path("director/application/reject", views.director_reject, name="director_reject"),
    path("director/application/accept", views.director_accept, name="director_accept"),
    path("director/reviewedapplications", views.director_reviewed_applications, name="director_reviewed_applications"),
    path("director/active", views.active_applications, name="active_applications"),
    path("director/application/details", views.director_application_view, name="director_application_view"),
    path("director/notifications/", views.director_notifications, name="director_notifications"),
    path("director/applications/<int:app_id>/budget/decision/", views.director_decide_budget, name="director_decide_budget"),
    path("director/insights/", views.director_insights, name="director_insights"),
    path("attorney/applications/", views.attorney_applications, name="attorney_applications"),
    path("attorney/applications/<int:app_id>/forward/", views.attorney_forward_to_director, name="attorney_forward_to_director"),

    # Attorney management URLs
    path("pccAdmin/attorneys/", views.get_attorney_list, name="get_attorney_list"),
    path("pccAdmin/directors/", views.get_director_list, name="get_director_list"),
    path("pccAdmin/attorneys/add/", views.add_attorney, name="add_attorney"),
    path("pccAdmin/attorneys/<int:attorney_id>/remove/", views.remove_attorney, name="remove_attorney"),
    path("pccAdmin/attorneys/<int:attorney_id>/applications/", views.get_attorney_applications, name="get_attorney_applications"),
    path("pccAdmin/attorneys/<int:attorney_id>/update/", views.update_attorney_details, name="update_attorney_details"),

    # Document Management URLs
    path('documents/', views.manage_documents, name='manage_documents'),
    path('pccAdmin/documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    path('pccAdmin/documents/<int:document_id>/versions/upload/', views.upload_document_version, name='upload_document_version'),
    path('pccAdmin/documents/<int:document_id>/lock/', views.lock_document, name='lock_document'),
    path('documents/<int:document_id>/versions/upload/', views.upload_document_version, name='upload_document_version_alias'),
    path('documents/<int:document_id>/versions/', views.document_versions_api, name='document_versions_api'),
    path('documents/<int:document_id>/lock/', views.lock_document, name='lock_document_alias'),

    # Global aliases used by imported frontend services
    path('notifications/', views.notifications_root, name='notifications_root'),
    path('audit-logs/', views.audit_logs_root, name='audit_logs_root'),
    path('audit-logs/<int:application_id>/', views.audit_logs_by_application, name='audit_logs_by_application'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
