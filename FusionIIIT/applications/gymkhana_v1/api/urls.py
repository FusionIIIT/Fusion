from django.urls import path

from . import views


urlpatterns = [
    path("auth/me/", views.me_view, name="gymkhana-v1-api-me"),
    path("auth/users/", views.user_search, name="gymkhana-v1-api-user-search"),
    path("auth/faculty/", views.faculty_search, name="gymkhana-v1-api-faculty-search"),
    path("dashboard/", views.dashboard, name="gymkhana-v1-api-dashboard"),
    path("venues/", views.venue_lookup, name="gymkhana-v1-api-venues"),
    path("clubs/", views.clubs_list, name="gymkhana-v1-clubs-list"),
    path("clubs/<int:pk>/", views.club_detail, name="gymkhana-v1-club-detail"),
    path("clubs/<int:pk>/approve/", views.club_approve, name="gymkhana-v1-club-approve"),
    path("clubs/<int:pk>/reject/", views.club_reject, name="gymkhana-v1-club-reject"),
    path("clubs/<int:pk>/calendar/", views.club_upload_calendar, name="gymkhana-v1-club-calendar"),
    path("members/", views.members_list, name="gymkhana-v1-members-list"),
    path("members/<int:pk>/", views.member_update, name="gymkhana-v1-member-update"),
    path("events/", views.events_list, name="gymkhana-v1-events-list"),
    path("events/<int:pk>/", views.event_detail, name="gymkhana-v1-event-detail"),
    path("events/<int:pk>/approve/", views.event_approve, name="gymkhana-v1-event-approve"),
    path("events/<int:pk>/reject/", views.event_reject, name="gymkhana-v1-event-reject"),
    path("budget/", views.budget_list, name="gymkhana-v1-budget-list"),
    path("budget/<int:pk>/", views.budget_detail, name="gymkhana-v1-budget-detail"),
    path("budget/<int:pk>/approve/", views.budget_approve, name="gymkhana-v1-budget-approve"),
    path("budget/<int:pk>/reject/", views.budget_reject, name="gymkhana-v1-budget-reject"),
    path("polls/", views.polls_list, name="gymkhana-v1-polls-list"),
    path("polls/<int:pk>/", views.poll_delete, name="gymkhana-v1-poll-delete"),
    path("polls/<int:poll_id>/vote/<int:option_id>/", views.cast_vote, name="gymkhana-v1-cast-vote"),
    path("gallery/", views.gallery_list, name="gymkhana-v1-gallery-list"),
    path("gallery/<int:pk>/", views.gallery_detail, name="gymkhana-v1-gallery-detail"),
]
