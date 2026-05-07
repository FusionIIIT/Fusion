import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Budget, Club, ClubMember, Event, GalleryItem, Poll, PollOption
from ..selectors import (
    find_venue_conflict,
    get_budgets_queryset,
    get_clubs_queryset,
    get_events_queryset,
    get_faculty_suggestions,
    get_gallery_queryset,
    get_members_queryset,
    get_polls_queryset,
    get_user_by_roll_no,
    get_user_search_queryset,
    get_user_role,
    get_venue_choices,
)
from ..services import (
    approve_budget,
    cast_vote as cast_vote_service,
    create_budget,
    create_event,
    create_gallery_item,
    create_membership_request,
    create_poll,
    delete_gallery_item,
    delete_poll,
    reject_budget,
    update_club_status,
    update_event_status,
    update_membership,
    upload_club_calendar,
)
from .serializers import BudgetSerializer, ClubMemberSerializer, ClubSerializer, ClubWriteSerializer, EventSerializer, GalleryItemSerializer, PollCreateSerializer, PollSerializer, UserSerializer


logger = logging.getLogger(__name__)


def _is_admin(user):
    return get_user_role(user) in ("counsellor", "dean")


def _is_coord(user):
    return get_user_role(user) == "coordinator"


def _is_student(user):
    return get_user_role(user) == "student"


def _err(message, code=400, request=None, details=None):
    log_details = f" details={details}" if details else ""
    logger.warning("GYMKHANA_V1_CONSTRAINT: method=%s path=%s user=%s message=%s%s", getattr(request, "method", "N/A"), getattr(request, "path", "N/A"), getattr(getattr(request, "user", None), "username", "anonymous"), message, log_details)
    return Response({"error": message}, status=code)


def _invalid(serializer, request=None, code=400):
    return _err("Serializer validation failed.", code=code, request=request, details=serializer.errors)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_search(request):
    roll_no = request.query_params.get("roll_no", "").strip()
    if roll_no:
        try:
            user = get_user_by_roll_no(roll_no)
        except Exception:
            return _err("User not found.", 404, request=request)
        return Response(UserSerializer(user).data)

    query = request.query_params.get("q", "").strip()
    role = request.query_params.get("role", "").strip()
    users = get_user_search_queryset(query, role)
    return Response(UserSerializer(users[:40], many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faculty_search(request):
    query = request.query_params.get("q", "").strip()
    faculties = get_faculty_suggestions(query)
    results = []
    for faculty in faculties:
        full_name = f"{faculty.id.user.first_name} {faculty.id.user.last_name}".strip()
        results.append(
            {
                "id": faculty.id.id,
                "name": full_name or faculty.id.user.username,
            }
        )
    return Response({"results": results})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def venue_lookup(request):
    venue_type = request.query_params.get("type", "all")
    return Response({"venues": get_venue_choices(venue_type)})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def clubs_list(request):
    if request.method == "GET":
        qs = get_clubs_queryset(
            status=request.query_params.get("status"),
            category=request.query_params.get("category"),
            query=request.query_params.get("q"),
        )
        return Response(ClubSerializer(qs, many=True).data)
    return _err("Club creation is disabled.", 403, request=request)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def club_detail(request, pk):
    try:
        club = Club.objects.get(pk=pk)
    except Club.DoesNotExist:
        return _err("Club not found.", 404, request=request)
    if request.method == "GET":
        return Response(ClubSerializer(club).data)
    if request.method == "PATCH":
        if not (_is_admin(request.user) or club.coordinator == request.user):
            return _err("Permission denied.", 403, request=request)
        serializer = ClubWriteSerializer(club, data=request.data, partial=True)
        if not serializer.is_valid():
            return _invalid(serializer, request=request)
        serializer.save()
        return Response(ClubSerializer(club).data)
    if not _is_admin(request.user):
        return _err("Only admins can delete clubs.", 403, request=request)
    club.delete()
    return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def club_approve(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        club = Club.objects.get(pk=pk)
    except Club.DoesNotExist:
        return _err("Club not found.", 404, request=request)
    update_club_status(club, "confirmed")
    return Response(ClubSerializer(club).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def club_reject(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        club = Club.objects.get(pk=pk)
    except Club.DoesNotExist:
        return _err("Club not found.", 404, request=request)
    update_club_status(club, "rejected")
    return Response(ClubSerializer(club).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def club_upload_calendar(request, pk):
    try:
        club = Club.objects.get(pk=pk)
    except Club.DoesNotExist:
        return _err("Club not found.", 404, request=request)
    if not (_is_admin(request.user) or club.coordinator == request.user):
        return _err("Permission denied.", 403, request=request)
    file_url = request.data.get("file_url", "").strip()
    if not file_url:
        return _err("file_url is required.", request=request)
    upload_club_calendar(club, file_url)
    return Response(ClubSerializer(club).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def members_list(request):
    if request.method == "GET":
        qs = get_members_queryset(
            request.user,
            is_student=_is_student(request.user),
            is_coord=_is_coord(request.user),
            club_id=request.query_params.get("club_id"),
            club_name=request.query_params.get("club"),
            student_id=request.query_params.get("student"),
            status=request.query_params.get("status"),
        )
        return Response(ClubMemberSerializer(qs, many=True).data)
    club_id = request.data.get("club")
    try:
        club = Club.objects.get(pk=club_id, status="confirmed")
    except Club.DoesNotExist:
        return _err("Club not found or not active.", 404, request=request, details={"club": club_id})
    if ClubMember.objects.filter(student=request.user, club=club).exists():
        return _err("You already have a request for this club.", request=request, details={"club": club_id})
    membership = create_membership_request(user=request.user, club=club, description=request.data.get("description", ""))
    return Response(ClubMemberSerializer(membership).data, status=201)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def member_update(request, pk):
    try:
        membership = ClubMember.objects.select_related("club").get(pk=pk)
    except ClubMember.DoesNotExist:
        return _err("Not found.", 404, request=request)
    is_club_coord = ClubMember.objects.filter(student=request.user, club=membership.club, status__in=["coordinator", "Co-cordinator"]).exists()
    if not (_is_admin(request.user) or is_club_coord):
        return _err("Permission denied.", 403, request=request)
    new_status = request.data.get("status")
    if new_status not in ("member", "rejected", "coordinator", "Co-cordinator"):
        return _err("Invalid status.", request=request, details={"status": new_status})
    update_membership(membership, status=new_status, remarks=request.data.get("remarks", membership.remarks))
    return Response(ClubMemberSerializer(membership).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def events_list(request):
    if request.method == "GET":
        qs = get_events_queryset(
            when=request.query_params.get("when"),
            club=request.query_params.get("club"),
            status=request.query_params.get("status"),
            query=request.query_params.get("q"),
            date=request.query_params.get("date"),
        )
        return Response(EventSerializer(qs, many=True).data)
    if _is_student(request.user):
        return _err("Students cannot create events.", 403, request=request)
    serializer = EventSerializer(data=request.data)
    if not serializer.is_valid():
        return _invalid(serializer, request=request)
    club = serializer.validated_data["club"]
    if _is_coord(request.user):
        allowed = ClubMember.objects.filter(student=request.user, club=club, status__in=["coordinator", "Co-cordinator"]).exists()
        if not allowed:
            return _err("You can only create events for your own club.", 403, request=request, details={"club": club.id})
    event = create_event(serializer=serializer, created_by=request.user)
    return Response(EventSerializer(event).data, status=201)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def event_detail(request, pk):
    try:
        event = Event.objects.select_related("club").get(pk=pk)
    except Event.DoesNotExist:
        return _err("Event not found.", 404, request=request)
    if request.method == "GET":
        return Response(EventSerializer(event).data)
    if request.method == "DELETE":
        if not _is_admin(request.user):
            return _err("Only admins can delete events.", 403, request=request)
        event.delete()
        return Response(status=204)
    if not (_is_admin(request.user) or event.created_by == request.user):
        return _err("Permission denied.", 403, request=request)
    serializer = EventSerializer(event, data=request.data, partial=True)
    if not serializer.is_valid():
        return _invalid(serializer, request=request)
    next_club = serializer.validated_data.get("club", event.club)
    if _is_coord(request.user):
        allowed = ClubMember.objects.filter(student=request.user, club=next_club, status__in=["coordinator", "Co-cordinator"]).exists()
        if not allowed:
            return _err("You can only edit events for your own club.", 403, request=request, details={"club": next_club.id})
    serializer.save()
    return Response(EventSerializer(event).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def event_approve(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        event = Event.objects.select_related("club").get(pk=pk)
    except Event.DoesNotExist:
        return _err("Event not found.", 404, request=request)
    if event.status == "confirmed":
        return _err("Already approved.", request=request)
    conflict = find_venue_conflict(event.venue, event.date, event.start_time, event.end_time, exclude_event_pk=event.pk)
    if conflict:
        return _err(
            f'Venue conflict: "{conflict.name}" ({conflict.club.name}) already booked at {event.venue} from {conflict.start_time} to {conflict.end_time}.',
            request=request,
        )
    update_event_status(event, "confirmed")
    return Response(EventSerializer(event).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def event_reject(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return _err("Event not found.", 404, request=request)
    update_event_status(event, "rejected")
    return Response(EventSerializer(event).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def budget_list(request):
    if request.method == "GET":
        if _is_student(request.user):
            return _err("Students cannot view budgets.", 403, request=request)
        qs = get_budgets_queryset(
            request.user,
            is_student=_is_student(request.user),
            is_coord=_is_coord(request.user),
            club=request.query_params.get("club"),
            status=request.query_params.get("status"),
            budget_type=request.query_params.get("type"),
        )
        return Response(BudgetSerializer(qs, many=True).data)
    if _is_student(request.user):
        return _err("Students cannot request budget.", 403, request=request)
    serializer = BudgetSerializer(data=request.data)
    if not serializer.is_valid():
        return _invalid(serializer, request=request)
    club = serializer.validated_data["club"]
    if _is_coord(request.user):
        allowed = ClubMember.objects.filter(student=request.user, club=club, status__in=["coordinator", "Co-cordinator"]).exists()
        if not allowed:
            return _err("You can only request budget for your own club.", 403, request=request, details={"club": club.id})
    budget = create_budget(serializer=serializer, requested_by=request.user)
    return Response(BudgetSerializer(budget).data, status=201)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def budget_detail(request, pk):
    if _is_student(request.user):
        return _err("Students cannot access budgets.", 403, request=request)
    try:
        budget = Budget.objects.select_related("club").get(pk=pk)
    except Budget.DoesNotExist:
        return _err("Not found.", 404, request=request)
    if request.method == "GET":
        return Response(BudgetSerializer(budget).data)
    if not (_is_admin(request.user) or budget.requested_by == request.user):
        return _err("Permission denied.", 403, request=request)
    if budget.status != "open":
        return _err("Cannot withdraw a decided request.", request=request)
    budget.delete()
    return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def budget_approve(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        with transaction.atomic():
            budget = Budget.objects.select_for_update().select_related("club").get(pk=pk)
            if budget.status == "confirmed":
                return _err("Already approved.", request=request)
            club = Club.objects.select_for_update().get(pk=budget.club_id)
            available = club.alloted_budget - club.spent_budget
            if budget.amount > available:
                return _err(
                    f"Insufficient budget. Available: Rs.{available:,}, Requested: Rs.{budget.amount:,}.",
                    request=request,
                    details={"available": available, "requested": budget.amount},
                )
            budget, club, available = approve_budget(pk, remarks=request.data.get("remarks", "Approved"))
    except Budget.DoesNotExist:
        return _err("Not found.", 404, request=request)
    return Response(BudgetSerializer(budget).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def budget_reject(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        budget = Budget.objects.get(pk=pk)
    except Budget.DoesNotExist:
        return _err("Not found.", 404, request=request)
    reject_budget(budget, remarks=request.data.get("remarks", "Rejected"))
    return Response(BudgetSerializer(budget).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def polls_list(request):
    if request.method == "GET":
        polls = get_polls_queryset()
        return Response(PollSerializer(polls, many=True, context={"request": request}).data)
    if not _is_admin(request.user):
        return _err("Only dean/counsellor can create polls.", 403, request=request)
    serializer = PollCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return _invalid(serializer, request=request)
    poll = create_poll(serializer=serializer, created_by=request.user)
    return Response(PollSerializer(poll, context={"request": request}).data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def poll_delete(request, pk):
    if not _is_admin(request.user):
        return _err("Permission denied.", 403, request=request)
    try:
        poll = Poll.objects.get(pk=pk)
    except Poll.DoesNotExist:
        return _err("Not found.", 404, request=request)
    delete_poll(poll)
    return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cast_vote(request, poll_id, option_id):
    try:
        poll = Poll.objects.get(pk=poll_id)
        option = PollOption.objects.get(pk=option_id, poll=poll)
    except (Poll.DoesNotExist, PollOption.DoesNotExist):
        return _err("Poll or option not found.", 404, request=request)
    if not poll.is_active:
        return _err("This poll has ended.", request=request)
    try:
        cast_vote_service(poll=poll, option=option, voter=request.user)
    except IntegrityError:
        return _err("You have already voted on this poll.", request=request)
    return Response(PollSerializer(poll, context={"request": request}).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def gallery_list(request):
    if request.method == "GET":
        items = get_gallery_queryset(
            club_id=request.query_params.get("club"),
            event_id=request.query_params.get("event"),
        )
        return Response(GalleryItemSerializer(items, many=True).data)
    if _is_student(request.user):
        return _err("Students cannot upload gallery items.", 403, request=request)
    serializer = GalleryItemSerializer(data=request.data)
    if not serializer.is_valid():
        return _invalid(serializer, request=request)
    item = create_gallery_item(serializer=serializer, uploaded_by=request.user)
    return Response(GalleryItemSerializer(item).data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def gallery_detail(request, pk):
    try:
        item = GalleryItem.objects.get(pk=pk)
    except GalleryItem.DoesNotExist:
        return _err("Not found.", 404, request=request)
    if not (_is_admin(request.user) or item.uploaded_by == request.user):
        return _err("Permission denied.", 403, request=request)
    delete_gallery_item(item)
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    today = timezone.localdate()
    memberships = ClubMember.objects.filter(student=user, status__in=["member", "coordinator", "Co-cordinator"]).select_related("club")
    upcoming = Event.objects.filter(date__gte=today, status="confirmed").order_by("date", "start_time")[:4]
    data = {
        "stats": {
            "total_clubs": Club.objects.count(),
            "upcoming_events": Event.objects.filter(date__gte=today, status="confirmed").count(),
            "my_memberships": memberships.count(),
        },
        "upcoming_events": EventSerializer(upcoming, many=True).data,
        "my_clubs": ClubMemberSerializer(memberships, many=True).data,
    }
    if not _is_student(user):
        data["stats"]["pending_budgets"] = Budget.objects.filter(status="open").count()
        data["stats"]["pending_events"] = Event.objects.filter(status="open").count()
        data["stats"]["pending_members"] = ClubMember.objects.filter(status="open").count()
    return Response(data)
