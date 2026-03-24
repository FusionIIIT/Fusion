from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from applications.gymkhana.selectors import *
from applications.gymkhana.services import *
from applications.gymkhana.api.serializers import *
from applications.gymkhana.api.utils import json_response
from applications.gymkhana.models import Club_info, Club_member, Session_info, Event_info
from rest_framework import status

# Club Endpoints
class ListClubsAPIView(APIView):
    """GET /api/clubs/ - List all clubs"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        clubs = get_all_clubs()
        serializer = ClubSerializer(clubs, many=True)
        return json_response(success=True, data=serializer.data)

class CreateClubAPIView(APIView):
    """POST /api/clubs/ - Create new club"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ClubCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = create_club(serializer.validated_data, request.user)
            if result['success']:
                return json_response(success=True, message=result['message'])
            return json_response(success=False, message=result['message'], 
                                status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors, 
                            status_code=status.HTTP_400_BAD_REQUEST)

class ClubDetailAPIView(APIView):
    """GET /api/clubs/{id}/ - Get club details"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, club_name):
        try:
            club = get_club_detail(club_name)
            serializer = ClubSerializer(club)
            return json_response(success=True, data=serializer.data)
        except Club_info.DoesNotExist:
            return json_response(success=False, message="Club not found", 
                                status_code=status.HTTP_404_NOT_FOUND)

class ClubMembersAPIView(APIView):
    """GET /api/clubs/{id}/members/ - List club members"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, club_name):
        members = Club_member.objects.filter(club__club_name=club_name)
        serializer = ClubMemberSerializer(members, many=True)
        return json_response(success=True, data=serializer.data)
    
    def post(self, request, club_name):
        """Add member to club"""
        serializer = ClubMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Add member logic here
            return json_response(success=True, message="Membership request sent")
        return json_response(success=False, message=serializer.errors, 
                            status_code=status.HTTP_400_BAD_REQUEST)

class ApproveMembersAPIView(APIView):
    """POST /api/clubs/{id}/members/approve/ - Approve pending members"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, club_name):
        member_ids = request.data.get('member_ids', [])
        remarks = request.data.get('remarks', [])
        
        result = approve_membership(club_name, member_ids, remarks)
        if result['success']:
            return json_response(success=True, message=result['message'])
        return json_response(success=False, message=result['message'], 
                            status_code=status.HTTP_400_BAD_REQUEST)

# Event Endpoints
class ListEventsAPIView(APIView):
    """GET /api/events/ - List all events"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        events = get_upcoming_events()
        serializer = EventSerializer(events, many=True)
        return json_response(success=True, data=serializer.data)

class CreateEventAPIView(APIView):
    """POST /api/events/ - Create new event"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        club = get_club_by_coordinator(request.user)
        if not club:
            return json_response(success=False, message="You are not a club coordinator", 
                                status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = EventCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = create_event(serializer.validated_data, club, request.user)
            if result['success']:
                return json_response(success=True, message=result['message'])
            return json_response(success=False, message=result['message'], 
                                status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors, 
                            status_code=status.HTTP_400_BAD_REQUEST)

class EventDetailAPIView(APIView):
    """GET /api/events/{id}/ - Get event details"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = Event_info.objects.get(id=event_id)
            serializer = EventSerializer(event)
            return json_response(success=True, data=serializer.data)
        except Event_info.DoesNotExist:
            return json_response(success=False, message="Event not found", 
                                status_code=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, event_id):
        """Update event"""
        try:
            event = Event_info.objects.get(id=event_id)
            club = get_club_by_coordinator(request.user)
            
            if not club or event.club != club:
                return json_response(success=False, message="Permission denied", 
                                    status_code=status.HTTP_403_FORBIDDEN)
            
            serializer = EventCreateSerializer(event, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return json_response(success=True, message="Event updated")
            return json_response(success=False, message=serializer.errors, 
                                status_code=status.HTTP_400_BAD_REQUEST)
        except Event_info.DoesNotExist:
            return json_response(success=False, message="Event not found", 
                                status_code=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, event_id):
        """Delete event"""
        try:
            event = Event_info.objects.get(id=event_id)
            club = get_club_by_coordinator(request.user)
            
            if not club or event.club != club:
                return json_response(success=False, message="Permission denied", 
                                    status_code=status.HTTP_403_FORBIDDEN)
            
            event.delete()
            return json_response(success=True, message="Event deleted")
        except Event_info.DoesNotExist:
            return json_response(success=False, message="Event not found", 
                                status_code=status.HTTP_404_NOT_FOUND)

# Session Endpoints
class ListSessionsAPIView(APIView):
    """GET /api/sessions/ - List sessions"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        club = get_club_by_coordinator(request.user)
        if club:
            sessions = get_club_sessions(club.club_name)
        else:
            sessions = Session_info.objects.filter(date__gte=datetime.date.today())
        
        serializer = SessionSerializer(sessions, many=True)
        return json_response(success=True, data=serializer.data)

class CreateSessionAPIView(APIView):
    """POST /api/sessions/ - Create new session"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        club = get_club_by_coordinator(request.user)
        if not club:
            return json_response(success=False, message="You are not a club coordinator", 
                                status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = SessionCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = create_session(serializer.validated_data, club, request.user)
            if result['success']:
                return json_response(success=True, message=result['message'])
            return json_response(success=False, message=result['message'], 
                                status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors, 
                            status_code=status.HTTP_400_BAD_REQUEST)

# Bulk Delete Endpoints
class BulkDeleteSessionsAPIView(APIView):
    """DELETE /api/sessions/bulk-delete/ - Delete multiple sessions"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        ids = request.data.get('ids', [])
        club = get_club_by_coordinator(request.user)
        
        if not club:
            return json_response(success=False, message="Permission denied", 
                                status_code=status.HTTP_403_FORBIDDEN)
        
        # Verify sessions belong to user's club
        sessions = Session_info.objects.filter(id__in=ids, club=club)
        ids_to_delete = list(sessions.values_list('id', flat=True))
        
        result = bulk_delete_objects(Session_info, ids_to_delete, request.user)
        if result['success']:
            return json_response(success=True, message=result['message'])
        return json_response(success=False, message=result['message'], 
                            status_code=status.HTTP_400_BAD_REQUEST)