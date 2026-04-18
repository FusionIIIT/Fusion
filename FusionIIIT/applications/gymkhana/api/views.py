import json
import datetime
import logging

from django.contrib.auth.models import User
from django.core import serializers as django_serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from applications.academic_information.models import Student
from applications.globals.models import (
    Designation,
    ExtraInfo,
    Faculty,
    HoldsDesignation,
)
from notification.views import (
    gymkhana_event,
    gymkhana_session,
    gymkhana_voting,
)

from applications.gymkhana.models import (
    Club_budget,
    Club_info,
    Club_member,
    Club_report,
    Constants,
    Event_info,
    Fest_budget,
    Form_available,
    Other_report,
    Registration_form,
    Session_info,
    Voting_choices,
    Voting_polls,
    Voting_voters,
)
from applications.gymkhana.selectors import (
    get_all_clubs,
    get_club_by_coordinator,
    get_club_detail,
    get_club_sessions,
    get_upcoming_events,
)
from applications.gymkhana.services import (
    approve_membership,
    bulk_delete_objects,
    create_club,
    create_event,
    create_session,
)
from applications.gymkhana.api.serializers import (
    ClubCreateSerializer,
    ClubMemberCreateSerializer,
    ClubMemberSerializer,
    ClubSerializer,
    EventCreateSerializer,
    EventSerializer,
    SessionCreateSerializer,
    SessionSerializer,
)
from applications.gymkhana.api.utils import json_response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers (previously in views.py)
# ---------------------------------------------------------------------------

def _coordinator_club(request):
    """Return the Club_info for which the requesting user is coordinator/co-coordinator."""
    for details in Club_info.objects.select_related(
        "co_ordinator", "co_ordinator__id", "co_ordinator__id__user",
        "co_ordinator__id__department", "co_coordinator", "co_coordinator__id",
        "co_coordinator__id__user", "co_coordinator__id__department",
        "faculty_incharge", "faculty_incharge__id", "faculty_incharge__id__user",
        "faculty_incharge__id__department",
    ).all():
        co_ord = str(details.co_ordinator).split(" ")[0]
        co_coord = str(details.co_coordinator).split(" ")[0]
        if co_ord == str(request.user) or co_coord == str(request.user):
            return details
    return None


def _conflict_algorithm_session(date, start_time, end_time, venue):
    """Return 'success' if the slot is free, 'error' if it conflicts."""
    start = datetime.datetime.strptime(start_time, "%H:%M").time()
    end = datetime.datetime.strptime(end_time, "%H:%M").time()
    if start >= end:
        return "error"
    booked = Session_info.objects.filter(date=date, venue=venue)
    slots = sorted([(start, end)] + [(s.start_time, s.end_time) for s in booked])
    if len(slots) == 1:
        return "success"
    counter = slots[0][1]
    for s, e in slots[1:]:
        if s < counter:
            return "error"
        counter = e
    return "success"


def _conflict_algorithm_event(date, start_time, end_time, venue):
    """Return 'success' if the slot is free, 'error' if it conflicts."""
    start = datetime.datetime.strptime(start_time, "%H:%M").time()
    end = datetime.datetime.strptime(end_time, "%H:%M").time()
    if start >= end:
        return "error"
    booked = Event_info.objects.filter(date=date, venue=venue)
    slots = sorted([(start, end)] + [(e.start_time, e.end_time) for e in booked])
    if len(slots) == 1:
        return "success"
    counter = slots[0][1]
    for s, e in slots[1:]:
        if s < counter:
            return "error"
        counter = e
    return "success"


def _get_target_user(groups):
    """Convert a list of 'batch:branch' strings into a JSON dict."""
    dic = {}
    for entry in groups:
        if ":" not in entry:
            logger.warning("get_target_user: skipping malformed entry '%s'", entry)
            continue
        batch, branch = [v.strip() for v in entry.split(":", 1)]
        if not batch or not branch:
            continue
        if dic.get(batch):
            if dic[batch][0] != "All":
                dic[batch].append(branch)
        else:
            dic[batch] = [branch]
    return json.dumps(dic)


# ---------------------------------------------------------------------------
# Club Endpoints
# ---------------------------------------------------------------------------

class ListClubsAPIView(APIView):
    """GET /api/clubs/ — List all clubs."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clubs = get_all_clubs()
        serializer = ClubSerializer(clubs, many=True)
        return json_response(success=True, data=serializer.data)


class CreateClubAPIView(APIView):
    """POST /api/clubs/create/ — Create a new club."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClubCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = create_club(serializer.validated_data, request.user)
            if result["success"]:
                return json_response(success=True, message=result["message"])
            return json_response(success=False, message=result["message"],
                                 status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors,
                             status_code=status.HTTP_400_BAD_REQUEST)


class ClubDetailAPIView(APIView):
    """GET /api/clubs/<club_name>/ — Get club details."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, club_name):
        try:
            club = get_club_detail(club_name)
            return json_response(success=True, data=ClubSerializer(club).data)
        except Club_info.DoesNotExist:
            return json_response(success=False, message="Club not found",
                                 status_code=status.HTTP_404_NOT_FOUND)


class ClubMembersAPIView(APIView):
    """GET/POST /api/clubs/<club_name>/members/ — List or add club members."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, club_name):
        members = Club_member.objects.filter(club__club_name=club_name)
        return json_response(success=True, data=ClubMemberSerializer(members, many=True).data)

    def post(self, request, club_name):
        serializer = ClubMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            return json_response(success=True, message="Membership request sent")
        return json_response(success=False, message=serializer.errors,
                             status_code=status.HTTP_400_BAD_REQUEST)


class ApproveMembersAPIView(APIView):
    """POST /api/clubs/<club_name>/members/approve/ — Approve pending members."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, club_name):
        member_ids = request.data.get("member_ids", [])
        remarks = request.data.get("remarks", [])
        result = approve_membership(club_name, member_ids, remarks)
        if result["success"]:
            return json_response(success=True, message=result["message"])
        return json_response(success=False, message=result["message"],
                             status_code=status.HTTP_400_BAD_REQUEST)


class UpdateClubNameAPIView(APIView):
    """POST /api/clubs/update-name/ — Rename a club atomically."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_id = request.data.get("club_id")
        new_name = request.data.get("new_name")
        if not club_id or not new_name:
            return json_response(success=False, message="club_id and new_name are required",
                                 status_code=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                club = Club_info.objects.get(club_name=club_id)
                Club_info.objects.create(
                    club_name=new_name,
                    co_ordinator_id=club.co_ordinator_id,
                    co_coordinator_id=club.co_coordinator_id,
                    faculty_incharge_id=club.faculty_incharge_id,
                    status="open",
                    description=club.description,
                    activity_calender=club.activity_calender,
                    category=club.category,
                )
                club.delete()
            return json_response(success=True, message="Club renamed successfully")
        except Club_info.DoesNotExist:
            return json_response(success=False, message="Club not found",
                                 status_code=status.HTTP_404_NOT_FOUND)


class ClubApproveAPIView(APIView):
    """POST /api/clubs/approve/ — Approve one or more clubs (admin)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_list = request.data.get("clubs", [])
        for club_name in club_list:
            club_info = get_object_or_404(Club_info, club_name=club_name)
            club_info.status = "confirmed"
            club_info.created_on = timezone.now()
            club_info.save()

            extra1 = get_object_or_404(ExtraInfo, id=str(club_info.co_ordinator_id))
            student1 = get_object_or_404(Student, id=extra1)
            extra2 = get_object_or_404(ExtraInfo, id=str(club_info.co_coordinator_id))
            student2 = get_object_or_404(Student, id=extra2)

            co_user = User.objects.get(username=club_info.co_ordinator_id)
            co_co_user = User.objects.get(username=club_info.co_coordinator_id)
            HoldsDesignation.objects.create(designation_id=56, user_id=co_user.id, working_id=co_user.id)
            HoldsDesignation.objects.create(designation_id=57, user_id=co_co_user.id, working_id=co_co_user.id)
            Club_member.objects.create(club_id=club_info.club_name, member=student1, status="confirmed")
            Club_member.objects.create(club_id=club_info.club_name, member=student2, status="confirmed")

        return json_response(success=True, message="Clubs approved successfully")


class ClubRejectAPIView(APIView):
    """POST /api/clubs/reject/ — Reject one or more clubs (admin)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_list = request.data.get("clubs", [])
        for club_name in club_list:
            club = get_object_or_404(Club_info, club_name=club_name)
            club.status = "rejected"
            club.save()
        return json_response(success=True, message="Clubs rejected successfully")


class DeleteClubAPIView(APIView):
    """POST /api/clubs/delete/ — Delete one or more clubs and clean up designations."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_list = request.data.get("clubs", [])
        for club_name in club_list:
            try:
                club_info = Club_info.objects.get(club_name=club_name)
                Club_budget.objects.filter(club_id=club_name).update(status="rejected")
                co_user = User.objects.get(username=club_info.co_ordinator_id)
                co_co_user = User.objects.get(username=club_info.co_coordinator_id)
                HoldsDesignation.objects.filter(user_id=co_user, working_id=co_user, designation_id=56).delete()
                HoldsDesignation.objects.filter(user_id=co_co_user, working_id=co_co_user, designation_id=57).delete()
                club_info.delete()
            except Club_info.DoesNotExist:
                return json_response(success=False, message=f"Club '{club_name}' not found",
                                     status_code=status.HTTP_404_NOT_FOUND)
        return json_response(success=True, message="Clubs deleted successfully")


class ChangeClubHeadAPIView(APIView):
    """POST /api/clubs/change-head/ — Change coordinator / co-coordinator of a club."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if _coordinator_club(request) is None:
            return json_response(success=False, message="Unauthorized: only club coordinators can change leadership.",
                                 status_code=status.HTTP_403_FORBIDDEN)

        club_name = request.data.get("club")
        co_ordinator = request.data.get("co")
        co_coordinator = request.data.get("coco")
        message = ""

        club_info = get_object_or_404(Club_info, club_name=club_name)

        if co_ordinator:
            if not Club_member.objects.filter(club_id=club_name, member_id=co_ordinator).exists():
                return json_response(success=False, message="Selected student is not a member of the club",
                                     status_code=status.HTTP_400_BAD_REQUEST)
            co_student = Student.objects.get(id_id=co_ordinator)
            old_co = club_info.co_ordinator_id
            club_info.co_ordinator_id = co_student
            HoldsDesignation.objects.create(
                user=User.objects.get(username=co_ordinator),
                working=User.objects.get(username=co_ordinator),
                designation=Designation.objects.get(name="co-ordinator"),
            )
            HoldsDesignation.objects.filter(
                user__username=old_co,
                designation=Designation.objects.get(name="co-ordinator"),
            ).delete()
            message += "Successfully changed co-ordinator. "

        if co_coordinator:
            if not Club_member.objects.filter(club_id=club_name, member_id=co_coordinator).exists():
                return json_response(success=False, message="Selected student is not a member of the club",
                                     status_code=status.HTTP_400_BAD_REQUEST)
            coco_student = Student.objects.get(id_id=co_coordinator)
            old_coco = club_info.co_coordinator_id
            club_info.co_coordinator_id = coco_student
            HoldsDesignation.objects.create(
                user=User.objects.get(username=co_coordinator),
                working=User.objects.get(username=co_coordinator),
                designation=Designation.objects.get(name="co co-ordinator"),
            )
            HoldsDesignation.objects.filter(
                user__username=old_coco,
                designation=Designation.objects.get(name="co co-ordinator"),
            ).delete()
            message += "Successfully changed co-coordinator."

        club_info.head_changed_on = timezone.now()
        club_info.save()
        return json_response(success=True, message=message)


class ActivityCalendarAPIView(APIView):
    """POST /api/clubs/activity-calendar/ — Upload a club activity calendar PDF."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_name = request.data.get("club")
        act_file = request.FILES.get("act_file")
        if not club_name or not act_file:
            return json_response(success=False, message="club and act_file are required",
                                 status_code=status.HTTP_400_BAD_REQUEST)
        act_file.name = club_name + "_act_calender.pdf"
        club_info = get_object_or_404(Club_info, club_name=club_name)
        club_info.activity_calender = act_file
        club_info.save()
        return json_response(success=True, message="Successfully uploaded the calendar")


# ---------------------------------------------------------------------------
# Member Endpoints
# ---------------------------------------------------------------------------

class MembershipRequestAPIView(APIView):
    """POST /api/members/join/ — Request to join a club."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_name_raw = request.data.get("user_name")
            club = request.data.get("club")
            achievements = request.data.get("achievements", "")

            parts = user_name_raw.split(" - ")
            user_obj = get_object_or_404(User, username=parts[1])
            extra = get_object_or_404(ExtraInfo, id=parts[0], user=user_obj)
            student = get_object_or_404(Student, id=extra)
            club_obj = get_object_or_404(Club_info, club_name=club)
            Club_member.objects.create(member=student, club=club_obj, description=achievements)
            return json_response(success=True, message="Membership request sent")
        except Exception:
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_400_BAD_REQUEST)


class ApproveMembershipAPIView(APIView):
    """POST /api/members/approve/ — Approve membership requests."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if _coordinator_club(request) is None:
            return json_response(success=False,
                                 message="Unauthorized: only club coordinators can approve memberships.",
                                 status_code=status.HTTP_403_FORBIDDEN)

        approve_list = request.data.get("members", [])
        for item in approve_list:
            remark = item.get("remarks", "")
            user_club = item.get("user_club", "")
            parts = user_club.split(",")
            info = parts[0].split(" - ")
            user_obj = get_object_or_404(User, username=info[1])
            extra = get_object_or_404(ExtraInfo, id=info[0], user=user_obj)
            student = get_object_or_404(Student, id=extra)
            club_name = parts[1] if len(parts) > 1 else ""

            existing = Club_member.objects.filter(club=club_name, member=student).first()
            if existing:
                existing.status = "confirmed"
                existing.remarks = remark
                existing.save()
                Club_member.objects.filter(club=club_name, member=student).exclude(id=existing.id).delete()
            else:
                Club_member.objects.create(club=club_name, member=student, status="confirmed", remarks=remark)

        return json_response(success=True, message="Members approved successfully")


class RejectMembershipAPIView(APIView):
    """POST /api/members/reject/ — Reject membership requests."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reject_list = request.data.get("members", [])
        for item in reject_list:
            remark = item.get("remarks", "")
            user_club = item.get("user_club", "")
            parts = user_club.split(",")
            info = parts[0].split(" - ")
            user_obj = get_object_or_404(User, username=info[1])
            extra = get_object_or_404(ExtraInfo, id=info[0], user=user_obj)
            student = get_object_or_404(Student, id=extra)
            club_name = parts[1] if len(parts) > 1 else ""
            member = get_object_or_404(Club_member, club=club_name, member=student)
            member.status = "rejected"
            member.remarks = remark
            member.save()
        return json_response(success=True, message="Members rejected")


class CancelMembershipAPIView(APIView):
    """POST /api/members/cancel/ — Cancel (remove) a member from a club."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cancel_list = request.data.get("members", [])
        for item in cancel_list:
            parts = item.split(",")
            info = parts[0].split(" - ")
            user_obj = get_object_or_404(User, username=info[1])
            extra = get_object_or_404(ExtraInfo, id=info[0], user=user_obj)
            student = get_object_or_404(Student, id=extra)
            club_name = parts[1] if len(parts) > 1 else ""
            member = get_object_or_404(Club_member, club=club_name, member=student)
            member.delete()
        return json_response(success=True, message="Members removed successfully")


class DeleteMemberFormAPIView(APIView):
    """POST /api/members/delete-form/ — Delete member form entries by ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get("ids", [])
        try:
            for mid in ids:
                Club_member.objects.get(id=mid).delete()
            return json_response(success=True, message="Deleted successfully")
        except Exception:
            return json_response(success=False, message="An error was encountered",
                                 status_code=status.HTTP_400_BAD_REQUEST)


class DeleteMemberAPIView(APIView):
    """POST /api/members/del-mem/ — Mark members as rejected by member ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get("members", [])
        for mid in ids:
            member = get_object_or_404(Club_member, member_id=mid)
            member.status = "rejected"
            member.save()
        return json_response(success=True, message="Members updated")


# ---------------------------------------------------------------------------
# Event Endpoints
# ---------------------------------------------------------------------------

class ListEventsAPIView(APIView):
    """GET /api/events/ — List all upcoming events."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = get_upcoming_events()
        return json_response(success=True, data=EventSerializer(events, many=True).data)


class CreateEventAPIView(APIView):
    """POST /api/events/create/ — Create a new event."""
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
            if result["success"]:
                return json_response(success=True, message=result["message"])
            return json_response(success=False, message=result["message"],
                                 status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors,
                             status_code=status.HTTP_400_BAD_REQUEST)


class EventDetailAPIView(APIView):
    """GET/PUT/DELETE /api/events/<event_id>/ — Get, update or delete an event."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = Event_info.objects.get(id=event_id)
            return json_response(success=True, data=EventSerializer(event).data)
        except Event_info.DoesNotExist:
            return json_response(success=False, message="Event not found",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, event_id):
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


class NewEventAPIView(APIView):
    """POST/PUT /api/events/new/ — Create event with conflict checking and notifications."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_name = _coordinator_club(request)
        if club_name is None:
            return json_response(success=False,
                                 message="Unauthorized: only club coordinators can book events.",
                                 status_code=status.HTTP_403_FORBIDDEN)
        try:
            event_name = request.data.get("event_name")
            incharge = request.data.get("incharge")
            venue = request.data.get("venue_type")
            event_poster = request.FILES.get("event_poster")
            date = request.data.get("date")
            start_time = request.data.get("start_time")
            end_time = request.data.get("end_time")
            desc = request.data.get("d_d")

            result = _conflict_algorithm_event(date, start_time, end_time, venue)
            if result == "success":
                event = Event_info.objects.create(
                    club=club_name, event_name=event_name, incharge=incharge,
                    venue=venue, date=date, start_time=start_time, end_time=end_time,
                    event_poster=event_poster, details=desc,
                )
                recipients = User.objects.filter(
                    extrainfo__in=ExtraInfo.objects.filter(user_type="student")
                )
                gymkhana_event(request.user, recipients, "new_event", club_name, event_name, desc, venue)
                return json_response(success=True, message="Your form has been dispatched for further process")
            return json_response(success=False,
                                 message="The selected time slot conflicts with an already booked event",
                                 status_code=status.HTTP_409_CONFLICT)
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        return self.post(request)


class EditEventAPIView(APIView):
    """PUT /api/events/<event_id>/edit/ — Edit event with conflict checking."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, event_id):
        club_name = _coordinator_club(request)
        try:
            venue = request.data.get("venue_type")
            date = request.data.get("date")
            start_time = request.data.get("start_time")
            end_time = request.data.get("end_time")
            result = _conflict_algorithm_event(date, start_time, end_time, venue)
            if result == "success":
                event = Event_info.objects.get(id=event_id)
                event.club = club_name
                event.event_name = request.data.get("event_name")
                event.incharge = request.data.get("incharge")
                event.venue = venue
                event.date = date
                event.start_time = start_time
                event.end_time = end_time
                event.event_poster = request.FILES.get("event_poster", event.event_poster)
                event.details = request.data.get("d_d")
                event.status = "confirmed"
                event.save()
                return json_response(success=True, message="Event updated successfully")
            return json_response(success=False,
                                 message="The selected time slot conflicts with an already booked event",
                                 status_code=status.HTTP_409_CONFLICT)
        except Event_info.DoesNotExist:
            return json_response(success=False, message="Event not found",
                                 status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApproveEventsAPIView(APIView):
    """POST/PUT /api/events/approve/ — Approve an event by ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _approve(self, request):
        # Accept 'id' (single, from frontend) or 'ids' (list, legacy)
        single_id = request.data.get("id")
        ids = [single_id] if single_id else request.data.get("ids", [])
        if not ids:
            return json_response(success=False, message="No event ID provided",
                                 status_code=status.HTTP_400_BAD_REQUEST)
        try:
            for event_id in ids:
                event = Event_info.objects.get(pk=event_id)
                event.status = "confirmed"
                event.save()
            return json_response(success=True, message="Events approved")
        except ObjectDoesNotExist:
            return json_response(success=False, message=f"Event {event_id} not found",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        return self._approve(request)

    def put(self, request):
        return self._approve(request)


class DeleteEventsAPIView(APIView):
    """DELETE/PUT /api/events/delete/ — Delete or reject events by ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _delete(self, request):
        single_id = request.data.get("id")
        ids = [single_id] if single_id else request.data.get("ids", [])
        try:
            for eid in ids:
                Event_info.objects.get(id=eid).delete()
            return json_response(success=True, message="Events deleted")
        except Exception:
            return json_response(success=False, message="An error was encountered",
                                 status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        return self._delete(request)

    def put(self, request):
        return self._delete(request)


class DateEventsAPIView(APIView):
    """POST /api/events/by-date/ — Get events on a specific date."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        date = request.data.get("date")
        events = Event_info.objects.filter(date=date).order_by("start_time")
        data = django_serializers.serialize("json", list(events))
        return json_response(success=True, data=json.loads(data))


class EventReportAPIView(APIView):
    """POST /api/events/report/ — Submit an event report."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.data.get("st_inc")
            event = request.data.get("event")
            description = request.data.get("d_d")
            date = request.data.get("date")
            time = request.data.get("time")
            report = request.FILES.get("report")
            report.name = event + "_report"

            parts = user.split(" - ")
            user_obj = get_object_or_404(User, username=parts[1])
            extra = get_object_or_404(ExtraInfo, id=parts[0], user=user_obj)

            Other_report.objects.create(
                incharge=extra, event_name=event,
                date=date + " " + time, event_details=report, description=description,
            )
            return json_response(success=True, message="Report saved successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Session Endpoints
# ---------------------------------------------------------------------------

class ListSessionsAPIView(APIView):
    """GET /api/sessions/ — List sessions."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        club = get_club_by_coordinator(request.user)
        sessions = (get_club_sessions(club.club_name) if club
                    else Session_info.objects.filter(date__gte=datetime.date.today()))
        return json_response(success=True, data=SessionSerializer(sessions, many=True).data)


class CreateSessionAPIView(APIView):
    """POST /api/sessions/create/ — Create a new session."""
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
            if result["success"]:
                return json_response(success=True, message=result["message"])
            return json_response(success=False, message=result["message"],
                                 status_code=status.HTTP_400_BAD_REQUEST)
        return json_response(success=False, message=serializer.errors,
                             status_code=status.HTTP_400_BAD_REQUEST)


class BulkDeleteSessionsAPIView(APIView):
    """DELETE /api/sessions/bulk-delete/ — Delete multiple sessions."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ids = request.data.get("ids", [])
        club = get_club_by_coordinator(request.user)
        if not club:
            return json_response(success=False, message="Permission denied",
                                 status_code=status.HTTP_403_FORBIDDEN)
        sessions = Session_info.objects.filter(id__in=ids, club=club)
        ids_to_delete = list(sessions.values_list("id", flat=True))
        result = bulk_delete_objects(Session_info, ids_to_delete, request.user)
        if result["success"]:
            return json_response(success=True, message=result["message"])
        return json_response(success=False, message=result["message"],
                             status_code=status.HTTP_400_BAD_REQUEST)


class NewSessionAPIView(APIView):
    """POST /api/sessions/new/ — Create session with conflict checking and notifications."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        club_name = _coordinator_club(request)
        if club_name is None:
            return json_response(success=False,
                                 message="Unauthorized: only club coordinators can book sessions.",
                                 status_code=status.HTTP_403_FORBIDDEN)
        try:
            venue = request.data.get("venue_type")
            session_poster = request.FILES.get("session_poster")
            date = request.data.get("date")
            start_time = request.data.get("start_time")
            end_time = request.data.get("end_time")
            desc = request.data.get("d_d")

            result = _conflict_algorithm_session(date, start_time, end_time, venue)
            if result == "success":
                Session_info.objects.create(
                    club=club_name, venue=venue, date=date,
                    start_time=start_time, end_time=end_time,
                    session_poster=session_poster, details=desc,
                )
                recipients = User.objects.filter(
                    extrainfo__in=ExtraInfo.objects.filter(user_type="student")
                )
                gymkhana_session(request.user, recipients, "new_session", club_name, desc, venue)
                return json_response(success=True, message="Session booked successfully")
            return json_response(success=False,
                                 message="The selected time slot conflicts with an already booked session",
                                 status_code=status.HTTP_409_CONFLICT)
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditSessionAPIView(APIView):
    """PUT /api/sessions/<session_id>/edit/ — Edit a session with conflict checking."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, session_id):
        club_name = _coordinator_club(request)
        try:
            venue = request.data.get("venue_type")
            date = request.data.get("date")
            start_time = request.data.get("start_time")
            end_time = request.data.get("end_time")
            result = _conflict_algorithm_session(date, start_time, end_time, venue)
            if result == "success":
                session = Session_info.objects.get(id=session_id)
                session.club = club_name
                session.venue = venue
                session.date = date
                session.start_time = start_time
                session.end_time = end_time
                session.session_poster = request.FILES.get("session_poster", session.session_poster)
                session.details = request.data.get("d_d")
                session.save()
                return json_response(success=True, message="Session updated successfully")
            return json_response(success=False,
                                 message="The selected time slot conflicts with an already booked session",
                                 status_code=status.HTTP_409_CONFLICT)
        except Session_info.DoesNotExist:
            return json_response(success=False, message="Session not found",
                                 status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteSessionsAPIView(APIView):
    """DELETE /api/sessions/delete/ — Delete sessions by ID list."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ids = request.data.get("ids", [])
        try:
            for sid in ids:
                Session_info.objects.get(id=sid).delete()
            return json_response(success=True, message="Sessions deleted")
        except Exception:
            return json_response(success=False, message="An error was encountered",
                                 status_code=status.HTTP_400_BAD_REQUEST)


class DateSessionsAPIView(APIView):
    """POST /api/sessions/by-date/ — Get sessions on a specific date."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        date = request.data.get("date")
        sessions = Session_info.objects.filter(date=date).order_by("start_time")
        data = django_serializers.serialize("json", list(sessions))
        return json_response(success=True, data=json.loads(data))


# ---------------------------------------------------------------------------
# Budget Endpoints
# ---------------------------------------------------------------------------

class ClubBudgetAPIView(APIView):
    """POST /api/budget/club/ — Submit a club budget request."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            club = request.data.get("club")
            budget_for = request.data.get("budget_for")
            budget_amount = request.data.get("amount")
            budget_file = request.FILES.get("budget_file")
            description = request.data.get("d_d")
            budget_file.name = club + "_budget"
            club_obj = get_object_or_404(Club_info, club_name=club)
            Club_budget.objects.create(
                club_id=club_obj, budget_amt=budget_amount, budget_file=budget_file,
                budget_for=budget_for, description=description, status="open",
            )
            return json_response(success=True, message="Budget request submitted successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FestBudgetAPIView(APIView):
    """POST /api/budget/fest/ — Submit a fest budget."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            fest = request.data.get("fest")
            budget_amt = request.data.get("amount")
            budget_file = request.FILES.get("file")
            desc = request.data.get("d_d")
            year = request.data.get("year")
            budget_file.name = fest + "_budget_" + year
            Fest_budget.objects.create(
                fest=fest, budget_amt=budget_amt, budget_file=budget_file,
                description=desc, year=year,
            )
            return json_response(success=True, message="Fest budget uploaded successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BudgetApproveAPIView(APIView):
    """POST/PUT /api/budget/approve/ — Approve a club budget by ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _approve(self, request):
        budget_id = request.data.get("id")
        if not budget_id:
            return json_response(success=False, message="Budget ID is required",
                                 status_code=status.HTTP_400_BAD_REQUEST)
        try:
            budget = Club_budget.objects.get(id=budget_id)
            budget.status = "confirmed"
            budget.save()
            return json_response(success=True, message="Budget approved")
        except Club_budget.DoesNotExist:
            return json_response(success=False, message="Budget not found",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        return self._approve(request)

    def put(self, request):
        return self._approve(request)


class BudgetRejectAPIView(APIView):
    """POST/PUT /api/budget/reject/ — Reject a club budget by ID."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _reject(self, request):
        budget_id = request.data.get("id")
        if not budget_id:
            return json_response(success=False, message="Budget ID is required",
                                 status_code=status.HTTP_400_BAD_REQUEST)
        try:
            budget = Club_budget.objects.get(id=budget_id)
            budget.status = "rejected"
            budget.save()
            return json_response(success=True, message="Budget rejected")
        except Club_budget.DoesNotExist:
            return json_response(success=False, message="Budget not found",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        return self._reject(request)

    def put(self, request):
        return self._reject(request)


class UpdateBudgetAmountAPIView(APIView):
    """POST/PUT /api/budget/update-amount/ — Update or deduct a club budget amount."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _update(self, request):
        # Accept 'id' (sent by frontend) or 'budget_id' (legacy)
        budget_id = request.data.get("id") or request.data.get("budget_id")
        req_id = request.data.get("req_id")
        new_budget = request.data.get("new_budget")

        try:
            budget = Club_budget.objects.get(id=budget_id)
            if req_id == "spent":
                new_budget = float(new_budget)
                if new_budget > budget.budget_amt:
                    return json_response(success=False,
                                         message="Spent amount cannot be greater than available amount",
                                         status_code=status.HTTP_400_BAD_REQUEST)
                budget.budget_amt -= new_budget
            else:
                budget.budget_amt = new_budget
            budget.save()
            return json_response(success=True, message="Budget updated successfully")
        except Club_budget.DoesNotExist:
            return json_response(success=False, message="Budget not found",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        return self._update(request)

    def put(self, request):
        return self._update(request)


# ---------------------------------------------------------------------------
# Report Endpoints
# ---------------------------------------------------------------------------

class ClubReportAPIView(APIView):
    """POST /api/reports/club/ — Submit a club event report."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            club = request.data.get("club")
            user = request.data.get("s_inc")
            event = request.data.get("event")
            d_d = request.data.get("d_d")
            date = request.data.get("date")
            time = request.data.get("time")
            report = request.FILES.get("report")

            if not date or not time:
                return json_response(success=False, message="Both date and time are required",
                                     status_code=status.HTTP_400_BAD_REQUEST)

            report.name = club + "_" + event + "_report"
            parts = user.split(" - ")
            user_obj = get_object_or_404(User, username=parts[1])
            extra = get_object_or_404(ExtraInfo, id=parts[0], user=user_obj)
            club_obj = get_object_or_404(Club_info, club_name=club)

            Club_report.objects.create(
                club=club_obj, incharge=extra, event_name=event,
                date=date + " " + time, event_details=report, description=d_d,
            )
            return json_response(success=True, message="Report updated successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Registration / Form Endpoints
# ---------------------------------------------------------------------------

class RegistrationFormAPIView(APIView):
    """POST /api/registration/ — Submit a club registration form."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_name = request.data.get("user_name")
            roll = request.data.get("roll")
            cpi = request.data.get("cpi")
            branch = request.data.get("branch")
            programme = request.data.get("programme")
            Registration_form.objects.create(
                user_name=user_name, branch=branch, roll=roll, cpi=cpi, programme=programme,
            )
            return json_response(success=True, message="The form has been dispatched for further process")
        except Exception:
            return json_response(success=False, message="You have already filled the form",
                                 status_code=status.HTTP_400_BAD_REQUEST)


class FormAvailAPIView(APIView):
    """POST /api/registration/form-availability/ — Toggle form availability."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            form_name = request.data.get("registration")
            available = request.data.get("available")
            is_available = available == "On"
            roll = request.user.username

            rob = Form_available.objects.get(roll=roll)
            if rob.form_name != form_name:
                Registration_form.objects.all().delete()
            rob.form_name = form_name
            rob.status = is_available
            rob.save()
            return json_response(success=True, message="Form availability updated")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="You've already filled the form",
                                 status_code=status.HTTP_400_BAD_REQUEST)


class DeleteRequestsAPIView(APIView):
    """DELETE /api/registration/delete-requests/ — Delete all registration form records."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            Registration_form.objects.all().delete()
            return json_response(success=True, message="Data deleted")
        except Exception:
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Data / Lookup Endpoints
# ---------------------------------------------------------------------------

class FacultyDataAPIView(APIView):
    """POST /api/data/faculty/ — Search faculty by name."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_value = request.data.get("current_value", "")
        try:
            faculty = ExtraInfo.objects.filter(user_type="faculty")
            names = []
            for lecturer in faculty:
                name = lecturer.user.first_name + " " + lecturer.user.last_name
                if not current_value or current_value.lower() in name.lower():
                    names.append(name)
            return json_response(success=True, data=names)
        except Exception:
            return json_response(success=False, message="Error fetching faculty",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentsDataAPIView(APIView):
    """POST /api/data/students/ — Search students by roll number prefix."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_value = request.data.get("current_value", "")
        try:
            students = ExtraInfo.objects.filter(user_type="student", id__startswith=current_value)
            data = json.loads(django_serializers.serialize("json", list(students)))
            return json_response(success=True, data=data)
        except Exception:
            return json_response(success=False, message="Error fetching students",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetVenueAPIView(APIView):
    """POST /api/data/venues/ — Get venues by type."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        selected = (request.data.get("venueType") or "").strip()
        venue_details = {}
        venue_types = []
        idd = 0
        for rooms in Constants.venue:
            for room in rooms:
                if idd % 2 == 0:
                    venue_types.append(room)
                else:
                    venue_details[venue_types[int(idd / 2)]] = [v[0] for v in room]
                idd += 1
        result = [v.strip() for v in venue_details.get(selected, [])]
        return json_response(success=True, data=result)


# ---------------------------------------------------------------------------
# Voting Endpoints
# ---------------------------------------------------------------------------

class VotingPollAPIView(APIView):
    """POST /api/voting/polls/ — Create a new voting poll."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if _coordinator_club(request) is None:
            return json_response(success=False,
                                 message="Unauthorized: only club coordinators can create polls.",
                                 status_code=status.HTTP_403_FORBIDDEN)
        try:
            title = request.data.get("title")
            description = request.data.get("desc")
            choices = request.data.getlist("choices")
            exp_date = request.data.get("expire_date")
            groups = request.data.getlist("groups")

            if len(choices) < 2:
                return json_response(success=False, message="A poll must have at least 2 choices.",
                                     status_code=status.HTTP_400_BAD_REQUEST)

            target_groups = _get_target_user(groups)
            created_by = f"{request.user.first_name} {request.user.last_name}:{request.user}"
            poll = Voting_polls.objects.create(
                title=title, description=description, exp_date=exp_date,
                created_by=created_by, groups=target_groups,
            )
            for choice in choices:
                Voting_choices.objects.create(poll_event=poll, title=choice, votes=0)

            for entry in groups:
                if ":" not in entry:
                    continue
                batch, branch = [v.strip() for v in entry.split(":", 1)]
                allbatch = User.objects.filter(username__contains=batch)
                if branch == "All":
                    gymkhana_voting(request.user, allbatch, "voting_open", title, description)
                else:
                    selbranch = ExtraInfo.objects.filter(department__name=branch)
                    batchbranch = User.objects.filter(username__contains=batch, extrainfo__in=selbranch)
                    gymkhana_voting(request.user, batchbranch, "voting_open", title, description)

            return json_response(success=True, message="Poll created successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VoteAPIView(APIView):
    """POST /api/voting/polls/<poll_id>/vote/ — Cast a vote on a poll."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, poll_id):
        from django.db import models as django_models
        poll = get_object_or_404(Voting_polls, pk=poll_id)
        try:
            target = json.loads(poll.groups) if poll.groups else {}
            if target:
                extra = get_object_or_404(ExtraInfo, user=request.user)
                student_batch = str(request.user.username)[:4]
                student_branch = extra.department.name if extra.department else None
                allowed = any(
                    batch == student_batch and ("All" in branches or student_branch in branches)
                    for batch, branches in target.items()
                )
                if not allowed:
                    return json_response(success=False, message="You are not eligible to vote in this poll.",
                                         status_code=status.HTTP_403_FORBIDDEN)

            submitted_choice = request.data.get("choice")
            updated = Voting_choices.objects.filter(pk=submitted_choice, poll_event=poll).update(
                votes=F("votes") + 1
            )
            if updated == 0:
                return json_response(success=False, message="Invalid choice selected.",
                                     status_code=status.HTTP_400_BAD_REQUEST)

            Voting_voters.objects.create(poll_event=poll, student_id=str(request.user))
            return json_response(success=True, message="Vote cast successfully")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeletePollAPIView(APIView):
    """DELETE /api/voting/polls/<poll_id>/ — Delete a voting poll."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, poll_id):
        try:
            Voting_polls.objects.filter(pk=poll_id).delete()
            return json_response(success=True, message="Poll deleted")
        except Exception as e:
            logger.exception(e)
            return json_response(success=False, message="Some error occurred",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)