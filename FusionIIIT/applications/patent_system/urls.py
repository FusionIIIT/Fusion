from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # Applicant-related paths
    path("applicant/applications/submit", views.submit_application, name="submit_application"),
    path("applicant/applications/", views.view_applications, name="view_applications"),
    path("applicant/applications/details/<int:application_id>/", views.view_application_details, name="view_application_details"),
    path("applicant/drafts", views.saved_drafts, name="saved_drafts"),
    path("applicant/notifications", views.applicant_notifications, name="applicant_notifications"),
    path("applicant/applications/submit/new", views.application_form, name="application_form"),
    path("applicant/applications/submitted", views.ip_filing_form, name="ip_filing_form"),
    path("applicant/applications/status-view", views.status_view, name="status_view"),

    # Director-related paths
    path("director", views.director_main_dashboard, name="director_main_dashboard"),
    path("director-dashboard", views.director_dashboard, name="director_dashboard"),
    path("director/accept_reject", views.director_accept_reject, name="director_accept_reject"),
    path("director/recents", views.recents_view, name="recents_view"),
    path("director/pending-reviews", views.pending_reviews, name="pending_reviews"),
    path("director/reviewedapplications", views.reviewed_applications, name="reviewed_applications"),
    path("director/active", views.active_applications, name="active_applications"),
    path("director/final-review/details", views.director_status_view, name="director_status_view"),
    path("director/notifications/", views.director_notifications, name="director_notifications"),
    path("director/submitted-applications", views.submitted_applications, name="submitted_applications"),

    # PCCAdmin-related paths
    path("pccAdmin/", views.pcc_admin_main_dashboard, name="pcc_admin_main_dashboard"),
    path("pccAdmin/dashboard", views.pcc_admin_dashboard, name="pcc_admin_dashboard"),
    path("pccAdmin/reviewed-applications", views.review_applications, name="review_applications"),
    path("pccAdmin/manageAttorney", views.manage_attorney, name="manage_attorney"),
    path("pccAdmin/notifyApplicant", views.notify_applicant, name="notify_applicant"),
    path("pccAdmin/downloads", views.downloads_page, name="downloads_page"),
    path("pccAdmin/insights", views.insights_page, name="insights_page"),
    path("pccAdmin/application/view-details", views.pcc_admin_status_view, name="pcc_admin_status_view"),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)