from django.urls import path
from applications.gymkhana.api.views import *

urlpatterns = [
    # Club endpoints
    path('clubs/', ListClubsAPIView.as_view(), name='list-clubs'),
    path('clubs/create/', CreateClubAPIView.as_view(), name='create-club'),
    path('clubs/<str:club_name>/', ClubDetailAPIView.as_view(), name='club-detail'),
    path('clubs/<str:club_name>/members/', ClubMembersAPIView.as_view(), name='club-members'),
    path('clubs/<str:club_name>/members/approve/', ApproveMembersAPIView.as_view(), name='approve-members'),
    
    # Event endpoints
    path('events/', ListEventsAPIView.as_view(), name='list-events'),
    path('events/create/', CreateEventAPIView.as_view(), name='create-event'),
    path('events/<int:event_id>/', EventDetailAPIView.as_view(), name='event-detail'),
    
    # Session endpoints
    path('sessions/', ListSessionsAPIView.as_view(), name='list-sessions'),
    path('sessions/create/', CreateSessionAPIView.as_view(), name='create-session'),
    path('sessions/bulk-delete/', BulkDeleteSessionsAPIView.as_view(), name='bulk-delete-sessions'),
]