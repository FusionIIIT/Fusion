from django.conf.urls import url, include
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from applications.gymkhana.api.views import (
    # New API Views (from refactoring)
    ListClubsAPIView,
    CreateClubAPIView,
    ClubDetailAPIView,
    ClubMembersAPIView,
    ApproveMembersAPIView,
    ListEventsAPIView,
    CreateEventAPIView,
    EventDetailAPIView,
    ListSessionsAPIView,
    CreateSessionAPIView,
    BulkDeleteSessionsAPIView,
    # Existing API Views
    Voting_Polls,
    clubname,
    Club_Details,
    club_events,
    club_budgetinfo,
    Fest_Budget,
    club_report,
    Registraion_form,
    session_details,
)
from . import views
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'gymkhana'

# API URL patterns (new structure from refactoring)
api_urlpatterns = [
    # Club endpoints
    path('clubs/', ListClubsAPIView.as_view(), name='api-list-clubs'),
    path('clubs/create/', CreateClubAPIView.as_view(), name='api-create-club'),
    path('clubs/<str:club_name>/', ClubDetailAPIView.as_view(), name='api-club-detail'),
    path('clubs/<str:club_name>/members/', ClubMembersAPIView.as_view(), name='api-club-members'),
    path('clubs/<str:club_name>/members/approve/', ApproveMembersAPIView.as_view(), name='api-approve-members'),
    
    # Event endpoints
    path('events/', ListEventsAPIView.as_view(), name='api-list-events'),
    path('events/create/', CreateEventAPIView.as_view(), name='api-create-event'),
    path('events/<int:event_id>/', EventDetailAPIView.as_view(), name='api-event-detail'),
    
    # Session endpoints
    path('sessions/', ListSessionsAPIView.as_view(), name='api-list-sessions'),
    path('sessions/create/', CreateSessionAPIView.as_view(), name='api-create-session'),
    path('sessions/bulk-delete/', BulkDeleteSessionsAPIView.as_view(), name='api-bulk-delete-sessions'),
]

# Legacy URL patterns (keep for backward compatibility)
legacy_urlpatterns = [
    # Session and Event info endpoints
    url(r'^session_details/$', session_details.as_view()),
    url(r'^event_info/$', club_events.as_view()),
    url(r'^club_budgetinfo/$', club_budgetinfo.as_view()),
    
    # Academic administration
    url(r'^club_approve/$', views.club_approve, name='club_approve'),
    url(r'^club_reject/$', views.club_reject, name='club_reject'),
    url(r'^del_mem/$', views.del_mem, name='del_mem'),
    url(r'^del_club/$', views.del_club, name='del_club'),
    url(r'^approve_events/$', views.approve_events, name='approve_events'),
    url(r'^update-club-name/$', views.update_club_name, name='update-club-name'),
    url(r'^update-budget-amount/$', views.update_budget_amount, name='update_budget_amount'),
    
    # Budget approval/rejection
    url(r'^budget_approve/$', views.budget_approve, name='budget_approve'),
    url(r'^budget_reject/$', views.budget_reject, name='budget_reject'),
    
    # Authentication
    url(r'^login/$', obtain_auth_token, name='login'),
    
    # API endpoints (legacy)
    url(r'^clubdetails/$', Club_Details.as_view()),
    url(r'^Fest_budget/$', Fest_Budget.as_view(), name='Fest_budget'),
    url(r'^club_report/$', club_report.as_view()),
    url(r'^registration_form/$', Registraion_form.as_view()),
    url(r'^voting_polls/$', Voting_Polls.as_view()),
    url(r'^clubname/$', clubname.as_view()),
]

# Main HTML view patterns (keep for frontend)
html_urlpatterns = [
    # Main page
    url(r'^$', views.gymkhana, name='gymkhana'),
    
    # Club management
    url(r'^new_club/$', views.new_club, name='new_club'),
    url(r'^club_membership/$', views.club_membership, name='membership'),
    url(r'^change_head/$', views.change_head, name='change_head'),
    
    # Session and Event management
    url(r'^new_session/$', views.new_session, name='new_session'),
    url(r'^new_event/$', views.new_event, name='new_event'),
    url(r'^editsession/(?P<session_id>\d+)/$', views.editsession, name='editsession'),
    url(r'^edit_event/(?P<event_id>\d+)/$', views.edit_event, name='edit_event'),
    url(r'^delete_sessions/$', views.delete_sessions, name='delete_sessions'),
    url(r'^delete_events/$', views.delete_events, name='delete_events'),
    url(r'^date_sessions/$', views.date_sessions, name='date_sessions'),
    url(r'^date_events/$', views.date_events, name='date_events'),
    
    # Budget management
    url(r'^club_budget/$', views.club_budget, name='club_budget'),
    url(r'^festbudget/$', views.fest_budget, name='fest_budget'),
    
    # Report management
    url(r'^event_report/$', views.event_report, name='event_report'),
    url(r'^club_event_report/$', views.club_report, name='club_report'),
    
    # Calendar and activities
    url(r'^act_calender/$', views.act_calender, name='act_calender'),
    
    # Member management
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^reject/$', views.reject, name='reject'),
    url(r'^cancel/$', views.cancel, name='cancel'),
    url(r'^delete_memberform/$', views.delete_memberform, name='delete_memberform'),
    
    # Form management
    url(r'^form_avail/$', views.form_avail, name='form_avail'),
    url(r'^registration_form/$', views.registration_form, name='registration_form'),
    url(r'^delete_requests/$', views.delete_requests, name='delete_requests'),
    
    # Data fetching
    url(r'^faculty_data/$', views.facultyData, name='faculty_data'),
    url(r'^students_data/$', views.studentsData, name='students_data'),
    url(r'^get_venue/$', views.getVenue, name='get_venue'),
    
    # Core team and voting
    url(r'^core_team/$', views.core_team, name='core_team'),
    url(r'^voting_poll/$', views.voting_poll, name='voting_poll'),
    url(r'^delete_poll/(?P<poll_id>\d+)/$', views.delete_poll, name='delete_poll'),
    url(r'^(?P<poll_id>\d+)/$', views.vote, name='vote'),
]

# Combine all URL patterns
urlpatterns = [
    # API endpoints (new RESTful structure)
    path('api/', include(api_urlpatterns)),
    
    # Legacy API endpoints (keep for backward compatibility)
    path('api-legacy/', include(legacy_urlpatterns)),
    
    # HTML views (main application)
    path('', include(html_urlpatterns)),
]

# Optional: Add format suffix patterns for API endpoints
urlpatterns = format_suffix_patterns(urlpatterns)