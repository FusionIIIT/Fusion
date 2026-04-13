"""
Patent Management System — API URL routing.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Applicant ──────────────────────────────────────────────────────────
    path("applicant/applications/submit/", views.submit_application, name="pms_submit"),
    path("applicant/applications/", views.view_applications, name="pms_applicant_list"),
    path("applicant/applications/details/<int:application_id>/", views.view_application_details_for_applicant, name="pms_applicant_detail"),
    path("applicant/applications/pending-consent/", views.view_pending_consent_applications, name="pms_pending_consent"),
    path("applicant/applications/resubmit/<int:application_id>/", views.resubmit_application, name="pms_resubmit"),
    path("applicant/applications/withdraw/<int:application_id>/", views.withdraw_application, name="pms_withdraw"),
    path("applicant/drafts/", views.saved_drafts, name="pms_drafts"),

    # Feature 1: Appeal endpoints (Applicant)
    path("applicant/applications/<int:application_id>/appeal/", views.lodge_appeal, name="pms_lodge_appeal"),

    # Feature 2: Consent endpoints (Applicant/Inventor)
    path("applicant/applications/<int:application_id>/consent/", views.give_inventor_consent, name="pms_give_consent"),
    path("applicant/applications/<int:application_id>/consent/revoke/", views.revoke_consent, name="pms_revoke_consent"),
    path("applicant/applications/<int:application_id>/consent/status/", views.get_consent_status, name="pms_consent_status"),

    # ── PCC Admin ──────────────────────────────────────────────────────────
    path("pccAdmin/applications/new/", views.new_applications, name="pms_pcc_new"),
    path("pccAdmin/applications/new/review/<int:application_id>/", views.review_application, name="pms_pcc_review"),
    path("pccAdmin/applications/new/forward/<int:application_id>/", views.forward_application, name="pms_pcc_forward"),
    path("pccAdmin/applications/new/requestModification/<int:application_id>/", views.request_application_modification, name="pms_pcc_modify"),
    path("pccAdmin/applications/ongoing/", views.ongoing_applications, name="pms_pcc_ongoing"),
    path("pccAdmin/applications/ongoing/changeStatus/<int:application_id>/", views.change_application_status, name="pms_pcc_change_status"),
    path("pccAdmin/applications/past/", views.past_applications, name="pms_pcc_past"),
    path("pccAdmin/applications/details/<int:application_id>/", views.view_application_details_for_pccAdmin, name="pms_pcc_detail"),

    # Feature 1: Appeal endpoints (PCC Admin)
    path("pccAdmin/applications/<int:application_id>/appeal/review/", views.pcc_review_appeal, name="pms_pcc_review_appeal"),

    # Communication logs (replaces attorney management)
    path("pccAdmin/applications/<int:application_id>/communications/", views.communication_logs, name="pms_comm_logs"),

    # Budget
    path("pccAdmin/applications/<int:application_id>/budget/", views.budget_view, name="pms_budget"),

    # Attorney Assignment (UC-006, BR-PMS-007 — PCC Admin assigns external attorney)
    path("pccAdmin/applications/<int:application_id>/attorney/", views.attorney_assignment_view, name="pms_attorney"),

    # Patentability Assessment (UC-007, BR-PMS-014 — PCC Admin records attorney opinion)
    path("pccAdmin/applications/<int:application_id>/assessment/", views.patentability_assessment_view, name="pms_assessment"),

    # Filing Record (UC-009, BR-PMS-017, WF-601 — PCC Admin logs filing with patent office)
    path("pccAdmin/applications/<int:application_id>/filing/", views.filing_record_view, name="pms_filing"),

    # Feature 5: Document version control
    path("pccAdmin/applications/<int:application_id>/documents/", views.application_documents, name="pms_documents_version"),

    # Audit
    path("pccAdmin/applications/<int:application_id>/audit/", views.audit_logs, name="pms_audit"),

    # Analytics
    path("pccAdmin/analytics/", views.analytics, name="pms_analytics"),
    path("pccAdmin/analytics/summary/", views.analytics_summary, name="pms_analytics_summary"),
    path("pccAdmin/departments/", views.get_departments, name="pms_departments"),

    # Feature 6: Search
    path("search/", views.search_applications, name="pms_search"),

    # ── Director ───────────────────────────────────────────────────────────
    path("director/applications/new/", views.director_new_applications, name="pms_dir_new"),
    path("director/application/accept", views.director_accept, name="pms_dir_accept"),
    path("director/application/reject", views.director_reject, name="pms_dir_reject"),
    path("director/reviewedapplications", views.director_reviewed_applications, name="pms_dir_reviewed"),
    path("director/active", views.active_applications, name="pms_dir_active"),
    path("director/application/details", views.director_application_view, name="pms_dir_detail"),
    path("director/notifications/", views.director_notifications, name="pms_dir_notif"),
    path("director/budget/<int:application_id>/decision/", views.director_budget_decision, name="pms_dir_budget"),

    # Feature 1: Appeal endpoints (Director)
    path("director/applications/<int:application_id>/appeal/decision/", views.director_appeal_decision, name="pms_dir_appeal_decision"),

    # ── Notifications (Feature 4) ─────────────────────────────────────────
    path("notifications/", views.get_notifications, name="pms_notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="pms_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="pms_notifications_read_all"),
    path("notifications/unread-count/", views.get_unread_count, name="pms_notifications_count"),

    # ── Documents (shared) ────────────────────────────────────────────────
    path("documents/", views.manage_documents, name="pms_documents"),
    path("pccAdmin/documents/<int:document_id>/delete/", views.delete_document, name="pms_doc_delete"),
]
