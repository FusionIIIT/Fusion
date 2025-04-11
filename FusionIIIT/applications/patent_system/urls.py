from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # Applicant-related paths
    path("applicant/applications/submit/", views.submit_application, name="submit_application"),
    path("applicant/applications/", views.view_applications, name="view_applications"),
    path("applicant/applications/details/<int:application_id>/", views.view_application_details_for_applicant, name="view_application_details"),
    path("applicant/drafts/", views.saved_drafts, name="saved_drafts"),

    # PCCAdmin-related paths
    path("pccAdmin/insights/yearly/", views.insights_by_year, name="insights_by_year"),
    path("pccAdmin/applications/new/", views.new_applications, name="new_applications"),
    path("pccAdmin/applications/review/", views.review_applications, name="review_applications"),
    path("pccAdmin/applications/forward/", views.forward_application, name="forward_applications"),
    path("pccAdmin/applications/status/", views.status_of_applications, name="status_of_applications"),
    path("pccAdmin/applications/status/details/<int:application_id>/", views.view_application_details_for_pccAdmin, name="view_application_details_for_pccAdmin"),
    path("pccAdmin/attorney/add/", views.add_attorney, name="add_attorney"),
    path("pccAdmin/attorney/remove/", views.remove_attorney, name="remove_attorney"),
    path("pccAdmin/attorneys/", views.view_attorney_list, name="view_attorney_list"),
    path("pccAdmin/attorneys/<int:attorney_id>/", views.view_attorney_details, name="view_attorney_details"),
    path("pccAdmin/attorneys/<int:attorney_id>/edit/", views.edit_attorney_details, name="edit_attorney_details"),

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

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
