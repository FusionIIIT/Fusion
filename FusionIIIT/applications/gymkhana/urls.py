from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.urlpatterns import format_suffix_patterns

from applications.gymkhana.api.views import (
    # Clubs
    ListClubsAPIView,
    CreateClubAPIView,
    ClubDetailAPIView,
    ClubMembersAPIView,
    ApproveMembersAPIView,
    UpdateClubNameAPIView,
    ClubApproveAPIView,
    ClubRejectAPIView,
    DeleteClubAPIView,
    ChangeClubHeadAPIView,
    ActivityCalendarAPIView,
    # Members
    MembershipRequestAPIView,
    ApproveMembershipAPIView,
    RejectMembershipAPIView,
    CancelMembershipAPIView,
    DeleteMemberFormAPIView,
    DeleteMemberAPIView,
    # Events
    ListEventsAPIView,
    CreateEventAPIView,
    EventDetailAPIView,
    NewEventAPIView,
    EditEventAPIView,
    ApproveEventsAPIView,
    DeleteEventsAPIView,
    DateEventsAPIView,
    EventReportAPIView,
    # Sessions
    ListSessionsAPIView,
    CreateSessionAPIView,
    BulkDeleteSessionsAPIView,
    NewSessionAPIView,
    EditSessionAPIView,
    DeleteSessionsAPIView,
    DateSessionsAPIView,
    # Budget
    ClubBudgetAPIView,
    FestBudgetAPIView,
    BudgetApproveAPIView,
    BudgetRejectAPIView,
    UpdateBudgetAmountAPIView,
    # Reports
    ClubReportAPIView,
    # Registration
    RegistrationFormAPIView,
    FormAvailAPIView,
    DeleteRequestsAPIView,
    # Data / Lookup
    FacultyDataAPIView,
    StudentsDataAPIView,
    GetVenueAPIView,
    # Voting
    VotingPollAPIView,
    VoteAPIView,
    DeletePollAPIView,
)

app_name = 'gymkhana'

urlpatterns = [
    # Auth
    path('api/login/', obtain_auth_token, name='api-login'),

    # --- Clubs ---
    path('api/clubs/', ListClubsAPIView.as_view(), name='api-list-clubs'),
    path('api/clubs/create/', CreateClubAPIView.as_view(), name='api-create-club'),
    path('api/clubs/approve/', ClubApproveAPIView.as_view(), name='api-approve-clubs'),
    path('api/clubs/reject/', ClubRejectAPIView.as_view(), name='api-reject-clubs'),
    path('api/clubs/delete/', DeleteClubAPIView.as_view(), name='api-delete-clubs'),
    path('api/clubs/update-name/', UpdateClubNameAPIView.as_view(), name='api-update-club-name'),
    path('api/clubs/change-head/', ChangeClubHeadAPIView.as_view(), name='api-change-head'),
    path('api/clubs/activity-calendar/', ActivityCalendarAPIView.as_view(), name='api-activity-calendar'),
    path('api/clubs/<str:club_name>/', ClubDetailAPIView.as_view(), name='api-club-detail'),
    path('api/clubs/<str:club_name>/members/', ClubMembersAPIView.as_view(), name='api-club-members'),
    path('api/clubs/<str:club_name>/members/approve/', ApproveMembersAPIView.as_view(), name='api-approve-members'),

    # --- Members ---
    path('api/members/join/', MembershipRequestAPIView.as_view(), name='api-join-club'),
    path('api/members/approve/', ApproveMembershipAPIView.as_view(), name='api-approve-membership'),
    path('api/members/reject/', RejectMembershipAPIView.as_view(), name='api-reject-membership'),
    path('api/members/cancel/', CancelMembershipAPIView.as_view(), name='api-cancel-membership'),
    path('api/members/delete-form/', DeleteMemberFormAPIView.as_view(), name='api-delete-member-form'),
    path('api/members/del-mem/', DeleteMemberAPIView.as_view(), name='api-del-mem'),

    # --- Events ---
    path('api/events/', ListEventsAPIView.as_view(), name='api-list-events'),
    path('api/events/create/', CreateEventAPIView.as_view(), name='api-create-event'),
    path('api/events/new/', NewEventAPIView.as_view(), name='api-new-event'),
    path('api/events/approve/', ApproveEventsAPIView.as_view(), name='api-approve-events'),
    path('api/events/delete/', DeleteEventsAPIView.as_view(), name='api-delete-events'),
    path('api/events/by-date/', DateEventsAPIView.as_view(), name='api-date-events'),
    path('api/events/report/', EventReportAPIView.as_view(), name='api-event-report'),
    path('api/events/<int:event_id>/', EventDetailAPIView.as_view(), name='api-event-detail'),
    path('api/events/<int:event_id>/edit/', EditEventAPIView.as_view(), name='api-edit-event'),

    # --- Sessions ---
    path('api/sessions/', ListSessionsAPIView.as_view(), name='api-list-sessions'),
    path('api/sessions/create/', CreateSessionAPIView.as_view(), name='api-create-session'),
    path('api/sessions/new/', NewSessionAPIView.as_view(), name='api-new-session'),
    path('api/sessions/bulk-delete/', BulkDeleteSessionsAPIView.as_view(), name='api-bulk-delete-sessions'),
    path('api/sessions/delete/', DeleteSessionsAPIView.as_view(), name='api-delete-sessions'),
    path('api/sessions/by-date/', DateSessionsAPIView.as_view(), name='api-date-sessions'),
    path('api/sessions/<int:session_id>/edit/', EditSessionAPIView.as_view(), name='api-edit-session'),

    # --- Budget ---
    path('api/budget/club/', ClubBudgetAPIView.as_view(), name='api-club-budget'),
    path('api/budget/fest/', FestBudgetAPIView.as_view(), name='api-fest-budget'),
    path('api/budget/approve/', BudgetApproveAPIView.as_view(), name='api-budget-approve'),
    path('api/budget/reject/', BudgetRejectAPIView.as_view(), name='api-budget-reject'),
    path('api/budget/update-amount/', UpdateBudgetAmountAPIView.as_view(), name='api-update-budget'),

    # --- Reports ---
    path('api/reports/club/', ClubReportAPIView.as_view(), name='api-club-report'),

    # --- Registration ---
    path('api/registration/', RegistrationFormAPIView.as_view(), name='api-registration'),
    path('api/registration/form-availability/', FormAvailAPIView.as_view(), name='api-form-avail'),
    path('api/registration/delete-requests/', DeleteRequestsAPIView.as_view(), name='api-delete-requests'),

    # --- Data / Lookup ---
    path('api/data/faculty/', FacultyDataAPIView.as_view(), name='api-faculty-data'),
    path('api/data/students/', StudentsDataAPIView.as_view(), name='api-students-data'),
    path('api/data/venues/', GetVenueAPIView.as_view(), name='api-get-venue'),

    # --- Voting ---
    path('api/voting/polls/', VotingPollAPIView.as_view(), name='api-voting-poll'),
    path('api/voting/polls/<int:poll_id>/vote/', VoteAPIView.as_view(), name='api-vote'),
    path('api/voting/polls/<int:poll_id>/', DeletePollAPIView.as_view(), name='api-delete-poll'),
]

urlpatterns = format_suffix_patterns(urlpatterns)