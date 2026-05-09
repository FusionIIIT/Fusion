"""
selectors.py — All database read queries for the notification module.

Source:
  - notifications_extension/views.py used:
      Notification.objects via get_object_or_404(Notification, recipient=..., id=...)
  - notification/views.py had no direct DB queries (used notify.send signal only)

Rules enforced:
  - Every .objects. call in the entire module lives ONLY here.
  - No business logic, no HTTP objects, no serialization.
"""

from django.utils import timezone
from notifications.models import Notification
from notifications.utils import slug2id

from .models import (
    Announcement, ArchivedNotification, NotificationEventType, NotificationPreference,
    GlobalsExtraInfo, GlobalsHoldsDesignation,
)


def _archived_ids(user):
    """Return set of notification IDs archived by this user (BR-NT-09)."""
    return set(
        ArchivedNotification.objects.filter(user=user).values_list("notification_id", flat=True)
    )


def _expired_announcement_ids():
    """
    BR-NT-06: announcements with expiry_date in the past must disappear from
    active UI. Returns the list of expired Announcement IDs so notification
    rows linked to them can be filtered out.
    """
    today = timezone.now().date()
    return list(
        Announcement.objects.filter(expiry_date__lt=today).values_list("id", flat=True)
    )


def _expired_notification_ids(qs):
    """For a given Notification queryset, return the set of row IDs whose
    data.announcement_id points to an expired Announcement (BR-NT-06)."""
    expired = set(_expired_announcement_ids())
    if not expired:
        return set()
    return {
        n.id for n in qs.only("id", "data")
        if isinstance(n.data, dict) and n.data.get("announcement_id") in expired
    }


def _exclude_expired(qs):
    """Exclude notification rows linked to an expired Announcement (BR-NT-06)."""
    bad_ids = _expired_notification_ids(qs)
    return qs.exclude(id__in=bad_ids) if bad_ids else qs


# ─────────────────────────────────────────────
#  Notification queries (django-notifications-hq)
# ─────────────────────────────────────────────

def get_notification_by_slug(slug, user):
    """
    Convert slug → id and return the matching Notification for the user.
    Returns None if not found.
    (Source: notifications_extension/views.py — slug2id + get_object_or_404)
    """
    notification_id = slug2id(slug)
    return Notification.objects.filter(
        recipient=user,
        id=notification_id,
    ).first()


def get_notification_by_id(notification_id, user):
    """Return a single Notification owned by the user. Returns None if not found."""
    return Notification.objects.filter(
        recipient=user,
        id=notification_id,
    ).first()


def get_all_notifications_for_user(user):
    """All non-archived notifications, expired announcements excluded (BR-NT-06, BR-NT-09)."""
    qs = Notification.objects.filter(recipient=user).exclude(id__in=_archived_ids(user))
    return _exclude_expired(qs).order_by("-timestamp")


def get_unread_notifications_for_user(user):
    """Unread, non-archived, non-expired notifications."""
    qs = Notification.objects.filter(recipient=user, unread=True).exclude(id__in=_archived_ids(user))
    return _exclude_expired(qs).order_by("-timestamp")


def get_read_notifications_for_user(user):
    """Read, non-archived, non-expired notifications."""
    qs = Notification.objects.filter(recipient=user, unread=False).exclude(id__in=_archived_ids(user))
    return _exclude_expired(qs).order_by("-timestamp")


def get_unread_count_for_user(user):
    """Count of unread, non-archived, non-expired notifications."""
    qs = Notification.objects.filter(recipient=user, unread=True).exclude(id__in=_archived_ids(user))
    return _exclude_expired(qs).count()


def get_notifications_by_module(user, module):
    """Module-filtered, non-archived, non-expired notifications."""
    archived = _archived_ids(user)
    expired = set(_expired_announcement_ids())
    return [
        n for n in Notification.objects.filter(recipient=user).order_by("-timestamp")
        if n.id not in archived
        and isinstance(n.data, dict)
        and n.data.get("module") == module
        and n.data.get("announcement_id") not in expired
    ]


# ─────────────────────────────────────────────
#  NotificationPreference queries
# ─────────────────────────────────────────────

def get_preference_for_user_and_module(user, module):
    """Return NotificationPreference for user+module, or None."""
    return NotificationPreference.objects.filter(user=user, module=module).first()


def get_all_preferences_for_user(user):
    """Return all NotificationPreference objects for a user."""
    return NotificationPreference.objects.filter(user=user).order_by("module")


def is_module_enabled_for_user(user, module):
    """
    Return True if user has notifications enabled for the given module.
    Defaults to True when no preference record exists.
    """
    pref = get_preference_for_user_and_module(user, module)
    return pref.is_enabled if pref is not None else True


# ─────────────────────────────────────────────
#  UC-NT-01: NotificationEventType queries
# ─────────────────────────────────────────────

def get_all_event_types():
    """Return all registered event types, active first."""
    return NotificationEventType.objects.all().order_by("-is_active", "module", "event_name")


def get_active_event_types():
    """Return only active registered event types."""
    return NotificationEventType.objects.filter(is_active=True).order_by("module", "event_name")


def get_event_type_by_event_id(event_id):
    """Return a NotificationEventType by its UUID event_id. Returns None if not found."""
    return NotificationEventType.objects.filter(event_id=event_id, is_active=True).first()


def get_event_type_by_name_and_module(event_name, module):
    """Return a NotificationEventType by event_name + module. Returns None if not found."""
    return NotificationEventType.objects.filter(
        event_name=event_name, module=module
    ).first()


# ─────────────────────────────────────────────
#  Fusionlab RBAC queries
#  (reads globals_extrainfo + globals_holdsdesignation)
# ─────────────────────────────────────────────

def get_users_by_type(user_type: str):
    """
    Return User queryset for a given user_type from globals_extrainfo.
    user_type values in fusionlab: 'student', 'staff'
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_ids = GlobalsExtraInfo.objects.filter(
        user_type__iexact=user_type
    ).values_list("user_id", flat=True)
    return User.objects.filter(id__in=user_ids)


def get_users_by_designation(designation_name: str):
    """
    Return User queryset for all users who currently hold a designation
    with the given name (e.g. 'Director', 'HOD (CSE)', 'Dean (P&D)').
    Matched case-insensitively against globals_designation.name.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_ids = GlobalsHoldsDesignation.objects.filter(
        designation__name__iexact=designation_name
    ).values_list("user_id", flat=True)
    return User.objects.filter(id__in=user_ids)


def get_user_type(user) -> str:
    """
    Return the user_type string for a user from globals_extrainfo.
    Returns empty string if no record found.
    """
    info = GlobalsExtraInfo.objects.filter(user_id=user.id).first()
    return info.user_type if info else ""


def get_user_designations(user):
    """
    Return list of designation names held by the user.
    """
    return list(
        GlobalsHoldsDesignation.objects.filter(user_id=user.id)
        .select_related("designation")
        .values_list("designation__name", flat=True)
    )


# ─────────────────────────────────────────────
#  UC-NT-03: Announcement queries
# ─────────────────────────────────────────────

def get_active_announcements():
    """Return all announcements whose expiry_date >= today."""
    return Announcement.objects.filter(
        expiry_date__gte=timezone.now().date()
    ).select_related("sender")


def get_all_announcements():
    """Return all announcements (admin view), newest first."""
    return Announcement.objects.all().select_related("sender")


def get_announcement_by_id(announcement_id):
    """Return a single Announcement by id. Returns None if not found."""
    return Announcement.objects.filter(id=announcement_id).first()
