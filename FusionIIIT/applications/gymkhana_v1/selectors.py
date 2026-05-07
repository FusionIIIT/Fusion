from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from applications.globals.models import Faculty

from .models import Budget, Club, ClubMember, Event, GalleryItem, INDOOR_VENUES, OUTDOOR_VENUES, Poll, VENUE_CHOICES


User = get_user_model()


def normalize_role_value(value):
    normalized = str(value or "").strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    if not normalized:
        return "student"
    if "dean" in normalized:
        return "dean"
    if "counsellor" in normalized or normalized in {"fic", "professor", "faculty"}:
        return "counsellor"
    if "coord" in normalized:
        return "coordinator"
    if "student" in normalized:
        return "student"
    return "student"


def get_user_role(user):
    if not getattr(user, "is_authenticated", False):
        return ""
    extra = getattr(user, "extrainfo", None)
    if extra:
        if extra.last_selected_role:
            return normalize_role_value(extra.last_selected_role)
        if extra.user_type:
            return normalize_role_value(extra.user_type)
    designation_names = [str(getattr(item.designation, "name", item.designation)) for item in user.current_designation.all()]
    for designation in designation_names:
        normalized = normalize_role_value(designation)
        if normalized != "student":
            return normalized
    return "student"


def get_user_roll_no(user):
    extra = getattr(user, "extrainfo", None)
    if extra and extra.id:
        return extra.id
    return user.username


def resolve_auth_username(identifier):
    if not identifier:
        return identifier
    if "@" in identifier:
        matched_user = User.objects.filter(email__iexact=identifier).first()
        return matched_user.username if matched_user else identifier
    matched_user = User.objects.filter(
        Q(username__iexact=identifier) | Q(extrainfo__id__iexact=identifier)
    ).first()
    return matched_user.username if matched_user else identifier


def get_user_by_roll_no(roll_no):
    return User.objects.get(Q(username=roll_no) | Q(extrainfo__id=roll_no))


def get_user_search_queryset(query="", role=""):
    qs = User.objects.all()
    if query:
        qs = qs.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
            | Q(extrainfo__id__icontains=query)
        )
    if role:
        target_role = normalize_role_value(role)
        user_ids = [user.id for user in qs if get_user_role(user) == target_role]
        qs = qs.filter(id__in=user_ids)
    return qs


def get_faculty_suggestions(query=""):
    qs = Faculty.objects.select_related("id__user").all()
    if query:
        qs = qs.filter(
            Q(id__user__first_name__icontains=query)
            | Q(id__user__last_name__icontains=query)
            | Q(id__id__icontains=query)
        )
    return qs[:30]


def get_venue_choices(venue_type="all"):
    if venue_type == "indoor":
        return INDOOR_VENUES
    if venue_type == "outdoor":
        return OUTDOOR_VENUES
    return [value for value, _label in VENUE_CHOICES]


def get_coord_clubs(user):
    return Club.objects.filter(
        Q(coordinator=user)
        | Q(co_coordinator=user)
        | Q(members__student=user, members__status__in=["coordinator", "Co-cordinator"])
    ).distinct()


def get_clubs_queryset(*, status=None, category=None, query=None):
    qs = Club.objects.all()
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    if query:
        qs = qs.filter(name__icontains=query)
    return qs


def get_members_queryset(user, *, is_student=False, is_coord=False, club_id=None, club_name=None, student_id=None, status=None):
    if club_id or club_name:
        qs = ClubMember.objects.select_related("student", "club").all()
        if club_id:
            qs = qs.filter(club_id=club_id)
        if club_name:
            qs = qs.filter(club__name=club_name)
        if is_student:
            qs = qs.filter(status__in=["member", "coordinator", "Co-cordinator"])
    else:
        if is_student:
            qs = ClubMember.objects.select_related("student", "club").filter(student=user)
        else:
            qs = ClubMember.objects.select_related("student", "club").all()
            if is_coord:
                qs = qs.filter(club_id__in=get_coord_clubs(user).values_list("id", flat=True))
    if student_id:
        qs = qs.filter(student_id=student_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def get_events_queryset(*, when=None, club=None, status=None, query=None, date=None):
    qs = Event.objects.select_related("club").all()
    today = timezone.localdate()
    if when:
        qs = qs.filter(date__gte=today) if when == "upcoming" else qs.filter(date__lt=today)
    if club:
        qs = qs.filter(club__name=club)
    if status:
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(details__icontains=query))
    if date:
        qs = qs.filter(date=date)
    return qs.order_by("date", "start_time")


def find_venue_conflict(venue, date, start, end, exclude_event_pk=None):
    qs = Event.objects.filter(
        venue=venue,
        date=date,
        status="confirmed",
        start_time__lt=end,
        end_time__gt=start,
    )
    if exclude_event_pk:
        qs = qs.exclude(pk=exclude_event_pk)
    return qs.first()


def get_budgets_queryset(user, *, is_student=False, is_coord=False, club=None, status=None, budget_type=None):
    if is_student:
        return Budget.objects.none()
    qs = Budget.objects.select_related("club").all()
    if is_coord:
        qs = qs.filter(club_id__in=get_coord_clubs(user).values_list("id", flat=True))
    if club:
        qs = qs.filter(club__name=club)
    if status:
        qs = qs.filter(status=status)
    if budget_type:
        qs = qs.filter(budget_type=budget_type)
    return qs


def get_polls_queryset():
    return Poll.objects.prefetch_related("options").all().order_by("-pub_date")


def get_gallery_queryset(*, club_id=None, event_id=None):
    qs = GalleryItem.objects.select_related("club", "event").all().order_by("-uploaded_at")
    if club_id:
        qs = qs.filter(club_id=club_id)
    if event_id:
        qs = qs.filter(event_id=event_id)
    return qs
