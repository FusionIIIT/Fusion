"""
services.py — All business logic for the notification module.

Source mapping:
  notification/views.py           → all module-specific notif functions moved here
  notifications_extension/views.py → mark_as_read_and_redirect logic moved here

Rules enforced:
  - All business logic lives here.
  - Calls selectors for reads; uses ORM directly only for writes/updates.
  - No Django HTTP objects (request/response) — those belong in api/views.py.
  - Raises custom exceptions on failure.
  - No hardcoded strings — all module names and types use TextChoices from models.py.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from notifications.signals import notify

from . import selectors

logger = logging.getLogger(__name__)


def _get_content_type(obj):
    """Cached ContentType lookup for a model instance (used by bulk_create)."""
    return ContentType.objects.get_for_model(obj.__class__)
from .models import (
    Announcement,
    AudienceType,
    ModuleName,
    NotificationEventType,
    LeaveNotifType,
    MessNotifType,
    VisitorHostelNotifType,
    HealthcareNotifType,
    ScholarshipNotifType,
    OfficeDeanPnDNotifType,
    OfficeDeanSNotifType,
    OfficeDeanRSPCNotifType,
    GymkhanaNotifType,
    ResearchProceduresNotifType,
    NotificationPreference,
)

User = get_user_model()


# ─────────────────────────────────────────────
#  Custom Exceptions
# ─────────────────────────────────────────────

class NotificationNotFound(Exception):
    """Raised when a notification cannot be found for the given user."""


class InvalidModuleName(Exception):
    """Raised when an unrecognised module name is provided."""


class InvalidNotificationType(Exception):
    """Raised when an unrecognised notification type is provided for a module."""


class UnauthorizedSender(Exception):
    """BR-NT-03: Raised when a non-authorized user tries to perform admin actions."""


class DuplicateNotification(Exception):
    """BR-NT-04: Raised when a duplicate notification is sent within cooldown window."""


# ─────────────────────────────────────────────
#  Internal helper
# ─────────────────────────────────────────────

def _send(*, sender, recipient, url: str, module: str, verb: str,
          description: str = "", flag: str = "", priority: str = "medium"):
    """
    Central wrapper around notify.send.
    BR-NT-05: Critical priority bypasses user preferences + triggers email.
    BR-NT-06: Per-module opt-out — disabled modules are silently skipped.
    """
    if priority != "critical" and not selectors.is_module_enabled_for_user(recipient, module):
        return  # User opted out — silently skip.

    kwargs = dict(
        sender=sender,
        recipient=recipient,
        url=url,
        module=module,
        verb=verb,
    )
    if description:
        kwargs["description"] = description
    if flag:
        kwargs["flag"] = flag

    notify.send(**kwargs)
    logger.info("notification.sent user=%s module=%s priority=%s",
                recipient.username, module, priority)

    # BR-NT-05: Critical notifications trigger immediate email (bypasses mute/DND)
    if priority == "critical":
        try:
            from django.core.mail import send_mail
            recipient_email = recipient.email or f"{recipient.username}@fusion.edu"
            send_mail(
                subject=f"[CRITICAL] {verb}",
                message=(
                    f"This is a critical notification from Fusion ({module}).\n\n"
                    f"{verb}\n\n"
                    f"{description}\n\n"
                    f"-- Fusion Notification System (NAM)\n"
                    f"   This message bypasses Do Not Disturb settings (BR-NT-05)."
                ),
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            logger.info("critical.email.sent user=%s", recipient.username)
        except Exception as exc:
            logger.error("critical.email.failed user=%s err=%s",
                         recipient.username, exc)
            # Do not propagate — notification is more important than email


# ─────────────────────────────────────────────
#  Mark as read + return redirect URL
#  (Source: notifications_extension/views.py)
# ─────────────────────────────────────────────

def mark_as_read_and_get_redirect_url(*, slug, user):
    """
    Mark a notification as read and return the redirect URL.

    Source: notifications_extension/views.py::mark_as_read_and_redirect
    The original view used HttpResponseRedirect directly — redirect logic is
    extracted here so the view stays thin.

    Returns:
        dict with keys:
            'url_name'    : str  — Django URL name to reverse
            'kwargs'      : dict — URL kwargs for reverse()
            'is_complaint': bool — True only for Complaint System module

    Raises:
        NotificationNotFound: if notification not found for user/slug.
    """
    notification = selectors.get_notification_by_slug(slug, user)
    if notification is None:
        raise NotificationNotFound(
            f"Notification with slug '{slug}' not found for user '{user.username}'."
        )

    notification.mark_as_read()

    is_complaint = (
        notification.data.get("module") == ModuleName.COMPLAINT_SYSTEM
    )

    url_name = notification.data.get("url", "")
    redirect_kwargs = {}

    if is_complaint:
        complaint_id = notification.description
        redirect_kwargs = {"detailcomp_id1": complaint_id}

    return {
        "url_name":     url_name,
        "kwargs":       redirect_kwargs,
        "is_complaint": is_complaint,
    }


# ─────────────────────────────────────────────
#  Mark as read / unread (single)
# ─────────────────────────────────────────────

def mark_notification_as_read(*, notification_id: int, user):
    """
    Mark a single notification as read.
    Raises NotificationNotFound if not found.
    """
    notification = selectors.get_notification_by_id(notification_id, user)
    if notification is None:
        raise NotificationNotFound(
            f"Notification {notification_id} not found for user '{user.username}'."
        )
    if notification.unread:
        notification.mark_as_read()
    return notification


def mark_notification_as_unread(*, notification_id: int, user):
    """
    Mark a single notification as unread.
    Raises NotificationNotFound if not found.
    """
    notification = selectors.get_notification_by_id(notification_id, user)
    if notification is None:
        raise NotificationNotFound(
            f"Notification {notification_id} not found for user '{user.username}'."
        )
    if not notification.unread:
        notification.mark_as_unread()
    return notification


def mark_all_notifications_as_read(*, user):
    """Mark every unread notification for the user as read."""
    selectors.get_unread_notifications_for_user(user).mark_all_as_read()


def mark_all_notifications_as_unread(*, user):
    """Mark every read notification for the user as unread."""
    from notifications.models import Notification
    Notification.objects.filter(recipient=user, unread=False).update(unread=True)


# ─────────────────────────────────────────────
#  Delete notifications
# ─────────────────────────────────────────────

def delete_notification(*, notification_id: int, user):
    """
    BR-NT-09: Soft-archive a notification (retained 180 days).
    Creates an ArchivedNotification record instead of hard-deleting.
    Raises NotificationNotFound if not found.
    """
    from notifications.models import Notification as _Notification
    from .models import ArchivedNotification
    exists = _Notification.objects.filter(recipient=user, id=notification_id).exists()
    if not exists:
        raise NotificationNotFound(
            f"Notification {notification_id} not found for user '{user.username}'."
        )
    ArchivedNotification.objects.get_or_create(user=user, notification_id=notification_id)


def delete_all_notifications(*, user):
    """BR-NT-09: Soft-archive all notifications for the user (retained 180 days)."""
    from notifications.models import Notification as _Notification
    from .models import ArchivedNotification
    ids = _Notification.objects.filter(recipient=user).values_list("id", flat=True)
    existing = set(
        ArchivedNotification.objects.filter(user=user).values_list("notification_id", flat=True)
    )
    ArchivedNotification.objects.bulk_create([
        ArchivedNotification(user=user, notification_id=nid)
        for nid in ids if nid not in existing
    ])


# ─────────────────────────────────────────────
#  Notification Preferences
# ─────────────────────────────────────────────

def send_notification_from_module(*, sender, recipient, module: str, verb: str,
                                   description: str = "", url: str = "#",
                                   priority: str = "medium"):
    """
    Generic entry-point called by other Fusion modules via the REST API.
    Validates the module name, then delegates to _send() which also
    checks the recipient's preference before dispatching.
    BR-NT-05: priority="critical" bypasses preferences and sends email.

    Raises:
        InvalidModuleName: if module is not a recognised ModuleName value.
    """
    valid_modules = {choice[0] for choice in ModuleName.choices}
    if module not in valid_modules:
        raise InvalidModuleName(f"'{module}' is not a recognised Fusion module.")

    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, description=description, priority=priority)


def initialize_default_preferences(*, user):
    """
    Create a default (enabled) NotificationPreference for every module
    if none exist yet for this user. Called lazily on first GET /preferences/.
    """
    if NotificationPreference.objects.filter(user=user).exists():
        return
    NotificationPreference.objects.bulk_create([
        NotificationPreference(user=user, module=module, is_enabled=True)
        for module, _ in ModuleName.choices
    ])


def set_notification_preference(*, user, module: str, is_enabled: bool):
    """
    Create or update a NotificationPreference.
    Raises InvalidModuleName if the module is not recognised.
    """
    valid_modules = {choice[0] for choice in ModuleName.choices}
    if module not in valid_modules:
        raise InvalidModuleName(f"'{module}' is not a recognised Fusion module.")

    pref, _ = NotificationPreference.objects.update_or_create(
        user=user,
        module=module,
        defaults={"is_enabled": is_enabled},
    )
    return pref


# ─────────────────────────────────────────────
#  Module-specific notification senders
#  Source: notification/views.py (all functions)
# ─────────────────────────────────────────────

def leave_module_notif(*, sender, recipient, type: str, date: str = None):
    """
    Source: notification/views.py::leave_module_notif
    All verb strings moved from hardcoded to here; module uses ModuleName.LEAVE_MODULE.
    """
    url    = "leave:leave"
    module = ModuleName.LEAVE_MODULE
    verb   = ""

    if type == LeaveNotifType.LEAVE_APPLIED:
        verb = "Your leave has been successfully submitted."
    elif type == LeaveNotifType.REQUEST_ACCEPTED:
        verb = "Your responsibility has been accepted."
    elif type == LeaveNotifType.REQUEST_DECLINED:
        verb = "Your responsibility has been declined."
    elif type == LeaveNotifType.LEAVE_ACCEPTED:
        verb = "Your leave request has been accepted."
    elif type == LeaveNotifType.LEAVE_FORWARDED:
        verb = "Your leave request has been forwarded."
    elif type == LeaveNotifType.LEAVE_REJECTED:
        verb = "Your leave request has been rejected."
    elif type == LeaveNotifType.OFFLINE_LEAVE:
        verb = "Your offline leave has been updated."
    elif type == LeaveNotifType.REPLACEMENT_REQUEST:
        verb = "You have a replacement request."
    elif type == LeaveNotifType.LEAVE_REQUEST:
        verb = "You have a leave request."
    elif type == LeaveNotifType.LEAVE_WITHDRAWN:
        verb = f"The leave has been withdrawn for {date}."
    elif type == LeaveNotifType.REPLACEMENT_CANCEL:
        verb = f"Your replacement has been cancelled for {date}."
    else:
        raise InvalidNotificationType(f"Unknown leave notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def placement_cell_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::placement_cell_notif"""
    url    = "placement:placement"
    module = ModuleName.PLACEMENT_CELL
    verb   = type  # Placement cell verb == type directly (as in source)
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def academics_module_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::academics_module_notif"""
    url    = ""
    module = ModuleName.ACADEMICS_MODULE
    verb   = type
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def office_module_notif(*, sender, recipient):
    """Source: notification/views.py::office_module_notif"""
    url    = "office_module:officeOfRegistrar"
    module = ModuleName.ACADEMICS_MODULE
    verb   = "New file received."
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def central_mess_notif(*, sender, recipient, type: str, message: str = None):
    """Source: notification/views.py::central_mess_notif"""
    url    = "mess:mess"
    module = ModuleName.CENTRAL_MESS
    verb   = ""

    if type == MessNotifType.FEEDBACK_SUBMITTED:
        verb = "Your feedback has been successfully submitted."
    elif type == MessNotifType.MENU_CHANGE_ACCEPTED:
        verb = "Menu request has been approved."
    elif type == MessNotifType.LEAVE_REQUEST:
        verb = message
    elif type == MessNotifType.VACATION_REQUEST:
        verb = f"Your vacation request has been {message}."
    elif type == MessNotifType.MEETING_INVITATION:
        verb = message
    elif type == MessNotifType.SPECIAL_REQUEST:
        verb = f"Your special food request has been {message}."
    elif type == MessNotifType.ADDED_COMMITTEE:
        verb = "You have been added to the mess committee."
    else:
        raise InvalidNotificationType(f"Unknown mess notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def visitors_hostel_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::visitors_hostel_notif"""
    url    = "visitorhostel:visitorhostel"
    module = ModuleName.VISITORS_HOSTEL
    verb   = ""

    if type == VisitorHostelNotifType.BOOKING_CONFIRMATION:
        verb = "Your booking has been confirmed."
    elif type == VisitorHostelNotifType.BOOKING_CANCELLATION_REQ_ACCEPTED:
        verb = "Your Booking Cancellation Request has been accepted."
    elif type == VisitorHostelNotifType.BOOKING_REQUEST:
        verb = "New Booking Request."
    elif type == VisitorHostelNotifType.CANCELLATION_REQUEST_PLACED:
        verb = "New Booking Cancellation Request."
    elif type == VisitorHostelNotifType.BOOKING_FORWARDED:
        verb = "New Forwarded Booking Request."
    elif type == VisitorHostelNotifType.BOOKING_REJECTED:
        verb = "Your Booking Request has been rejected."
    else:
        raise InvalidNotificationType(f"Unknown visitor hostel notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def healthcare_center_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::healthcare_center_notif"""
    url    = "healthcenter:healthcenter"
    module = ModuleName.HEALTHCARE_CENTER
    verb   = ""

    if type == HealthcareNotifType.APPOINTMENT_BOOKED:
        verb = "Your Appointment has been booked."
    elif type == HealthcareNotifType.AMBULANCE_REQUEST:
        verb = "Your Ambulance request has been placed."
    elif type == HealthcareNotifType.PRESCRIPTION:
        verb = "You have been prescribed some medicine."
    elif type == HealthcareNotifType.APPOINTMENT_REQUEST:
        verb = "You have a new appointment request."
    elif type == HealthcareNotifType.AMBULANCE_REQ:
        verb = "You have a new ambulance request."
    else:
        raise InvalidNotificationType(f"Unknown healthcare notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def file_tracking_notif(*, sender, recipient, title: str):
    """Source: notification/views.py::file_tracking_notif"""
    url    = "filetracking:inward"
    module = ModuleName.FILE_TRACKING
    verb   = title
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def scholarship_portal_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::scholarship_portal_notif"""
    url    = "spacs:spacs"
    module = ModuleName.SCHOLARSHIP_PORTAL
    verb   = ""

    if type.startswith("award"):
        award_name = type.split("_", 1)[1]
        verb = f"Invitation to apply for {award_name}."
    elif type == ScholarshipNotifType.ACCEPT_MCM:
        verb = "Your MCM form has been accepted."
    elif type == ScholarshipNotifType.REJECT_MCM:
        verb = "Your MCM form has been rejected as you have not fulfilled the required criteria."
    elif type == ScholarshipNotifType.ACCEPT_GOLD:
        verb = "Your Convocation form for Director's Gold Medal has been accepted."
    elif type == ScholarshipNotifType.REJECT_GOLD:
        verb = "Your Convocation form for Director's Gold Medal has been rejected."
    elif type == ScholarshipNotifType.ACCEPT_SILVER:
        verb = "Your Convocation form for Director's Silver Medal has been accepted."
    elif type == ScholarshipNotifType.REJECT_SILVER:
        verb = "Your Convocation form for Director's Silver Medal has been rejected."
    elif type == ScholarshipNotifType.ACCEPT_DM:
        verb = "Your Convocation form for D&M Proficiency Gold Medal has been accepted."
    else:
        raise InvalidNotificationType(f"Unknown scholarship notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def complaint_system_notif(*, sender, recipient, type: str, complaint_id, is_student: bool, message: str):
    """
    Source: notification/views.py::complaint_system_notif
    Original used student==0 integer flag; replaced with bool is_student.
    """
    url = "complaint:detail2" if is_student else "complaint:detail"
    module      = ModuleName.COMPLAINT_SYSTEM
    verb        = message
    description = str(complaint_id)
    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, description=description)


def office_dean_pnd_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::office_dean_PnD_notif"""
    url    = "office_module:officeOfDeanPnD"
    module = ModuleName.OFFICE_DEAN_PND
    verb   = ""

    if type == OfficeDeanPnDNotifType.REQUISITION_FILED:
        verb = "Your requisition has been successfully submitted."
    elif type == OfficeDeanPnDNotifType.REQUEST_ACCEPTED:
        verb = "Your requisition has been accepted."
    elif type == OfficeDeanPnDNotifType.REQUEST_REJECTED:
        verb = "Your requisition has been rejected."
    elif type == OfficeDeanPnDNotifType.ASSIGNMENT_CREATED:
        verb = "Assignment has been created."
    elif type == OfficeDeanPnDNotifType.ASSIGNMENT_RECEIVED:
        verb = "You have received an assignment."
    elif type == OfficeDeanPnDNotifType.ASSIGNMENT_REVERTED:
        verb = "Assignment has been reverted."
    elif type == OfficeDeanPnDNotifType.ASSIGNMENT_APPROVED:
        verb = "Assignment has been approved."
    elif type == OfficeDeanPnDNotifType.ASSIGNMENT_REJECTED:
        verb = "Assignment has been rejected."
    else:
        raise InvalidNotificationType(f"Unknown Dean PnD notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def office_module_deans_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::office_module_DeanS_notif"""
    url    = "office_module:officeOfDeanStudents"
    module = ModuleName.OFFICE_MODULE
    verb   = ""

    if type == OfficeDeanSNotifType.HOSTEL_ALLOTED:
        verb = "Hostel has been allotted successfully."
    elif type == OfficeDeanSNotifType.INSUFFICIENT_FUNDS:
        verb = "Insufficient Funds! Please contact Junior Superintendent to allot funds."
    elif type == OfficeDeanSNotifType.MOM_SUBMITTED:
        verb = "MOM of the meeting has been submitted successfully."
    elif type == OfficeDeanSNotifType.BUDGET_APPROVED:
        verb = "Budget has been approved by Dean Students."
    elif type == OfficeDeanSNotifType.BUDGET_REJECTED:
        verb = "Budget has been rejected by Dean Students."
    elif type == OfficeDeanSNotifType.CLUB_APPROVED:
        verb = "New Club has been approved by Dean Students."
    elif type == OfficeDeanSNotifType.CLUB_REJECTED:
        verb = "New Club has been rejected by Dean Students."
    elif type == OfficeDeanSNotifType.MEETING_BOOKED:
        verb = "Meeting has been booked and members have been notified."
    elif type == OfficeDeanSNotifType.SESSION_APPROVED:
        verb = "Club session has been approved."
    elif type == OfficeDeanSNotifType.SESSION_REJECTED:
        verb = "Club session has been rejected."
    elif type == OfficeDeanSNotifType.BUDGET_ALLOTED:
        verb = "Budget has been allotted by Junior Superintendent."
    else:
        raise InvalidNotificationType(f"Unknown Dean Students notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def gymkhana_voting_notif(*, sender, recipient, type: str, title: str, desc: str):
    """Source: notification/views.py::gymkhana_voting"""
    url    = "gymkhana:gymkhana"
    module = ModuleName.GYMKHANA_MODULE
    verb   = ""

    if type == GymkhanaNotifType.VOTING_OPEN:
        verb = f"Voting is open for {title}."
    else:
        raise InvalidNotificationType(f"Unknown gymkhana voting notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, description=desc)


def gymkhana_session_notif(*, sender, recipient, type: str, club: str, desc: str, venue: str):
    """Source: notification/views.py::gymkhana_session"""
    url    = "gymkhana:gymkhana"
    module = ModuleName.GYMKHANA_MODULE
    verb   = ""

    if type == GymkhanaNotifType.NEW_SESSION:
        verb = f"A session by {club} Club will be organised in {venue}."
    else:
        raise InvalidNotificationType(f"Unknown gymkhana session notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, description=desc)


def gymkhana_event_notif(*, sender, recipient, type: str, club: str,
                         event_name: str, desc: str, venue: str):
    """Source: notification/views.py::gymkhana_event"""
    url    = "gymkhana:gymkhana"
    module = ModuleName.GYMKHANA_MODULE
    verb   = ""

    if type == GymkhanaNotifType.NEW_EVENT:
        verb = f"{event_name} event by {club} Club will be organised in {venue}."
    else:
        raise InvalidNotificationType(f"Unknown gymkhana event notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, description=desc)


def assistantship_claim_notify(*, sender, recipient, month: str, year: str):
    """Source: notification/views.py::AssistantshipClaim_notify"""
    url    = "academic-procedures:academic_procedures"
    module = ModuleName.ASSISTANTSHIP_REQUEST
    verb   = f"Your Assistantship claim of {month} month year {year} is approved."
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def assistantship_claim_faculty_notify(*, sender, recipient):
    """Source: notification/views.py::AssistantshipClaim_faculty_notify"""
    url    = "academic-procedures:academic_procedures"
    module = ModuleName.ASSISTANTSHIP_REQUEST
    verb   = "Assistantship claim is requested."
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def assistantship_claim_acad_notify(*, sender, recipient):
    """Source: notification/views.py::AssistantshipClaim_acad_notify"""
    url    = "academic-procedures:academic_procedures"
    module = ModuleName.ASSISTANTSHIP_REQUEST
    verb   = "Assistantship claim is requested."
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def assistantship_claim_account_notify(*, sender, stu, recipient):
    """Source: notification/views.py::AssistantshipClaim_account_notify"""
    url    = "academic-procedures:academic_procedures"
    module = ModuleName.ASSISTANTSHIP_REQUEST
    verb   = f"Assistantship claim of {stu} is forwarded."
    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def department_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::department_notif"""
    url    = "dep:dep"
    module = ModuleName.DEPARTMENT
    verb   = type
    flag   = "department"
    _send(sender=sender, recipient=recipient, url=url, module=module,
          verb=verb, flag=flag)


def office_module_dean_rspc_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::office_module_DeanRSPC_notif"""
    url    = "office:officeOfDeanRSPC"
    module = ModuleName.OFFICE_MODULE
    verb   = ""

    if type == OfficeDeanRSPCNotifType.APPROVE:
        verb = "Your Project request has been accepted."
    elif type == OfficeDeanRSPCNotifType.DISAPPROVE:
        verb = "Your project request got rejected."
    elif type == OfficeDeanRSPCNotifType.PENDING:
        verb = "Kindly wait for the response."
    else:
        raise InvalidNotificationType(f"Unknown Dean RSPC notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def research_procedures_notif(*, sender, recipient, type: str):
    """Source: notification/views.py::research_procedures_notif"""
    url    = "research_procedures:patent_registration"
    module = ModuleName.RESEARCH_PROCEDURES
    verb   = ""

    if type == ResearchProceduresNotifType.APPROVED:
        verb = "Your Patent has been Approved."
    elif type == ResearchProceduresNotifType.DISAPPROVED:
        verb = "Your Patent has been Rejected."
    elif type == ResearchProceduresNotifType.PENDING:
        verb = "Your Patent is Pending, wait for the response."
    elif type == ResearchProceduresNotifType.SUBMITTED:
        verb = "Your Patent has been Submitted, wait for the response."
    elif type == ResearchProceduresNotifType.CREATED:
        verb = "A new Patent has been Created."
    else:
        raise InvalidNotificationType(f"Unknown research procedures notification type: '{type}'")

    _send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


# ─────────────────────────────────────────────
#  UC-NT-01: Register / manage event types
# ─────────────────────────────────────────────

class EventTypeAlreadyExists(Exception):
    """Raised when an event type with the same name+module already exists."""


def register_event_type(*, registered_by, event_name: str, module: str,
                         default_priority: str = "medium", description: str = "") -> NotificationEventType:
    """
    UC-NT-01 Main Flow step 1-3:
    Validate the module, assign a unique Event_ID (UUID), map to notification template.

    Raises:
        InvalidModuleName:      if module is not a recognised ModuleName.
        EventTypeAlreadyExists: if (event_name, module) already registered.
    """
    valid_modules = {choice[0] for choice in ModuleName.choices}
    if module not in valid_modules:
        raise InvalidModuleName(f"'{module}' is not a recognised Fusion module.")

    existing = selectors.get_event_type_by_name_and_module(event_name, module)
    if existing is not None:
        raise EventTypeAlreadyExists(
            f"Event '{event_name}' is already registered for module '{module}'."
        )

    event_type = NotificationEventType.objects.create(
        event_name=event_name,
        module=module,
        default_priority=default_priority,
        description=description,
        registered_by=registered_by,
        is_active=True,
    )
    return event_type


def deactivate_event_type(*, event_id: str) -> NotificationEventType:
    """Deactivate a registered event type so it can no longer trigger notifications."""
    event_type = selectors.get_event_type_by_event_id(event_id)
    if event_type is None:
        raise NotificationNotFound(f"Event type with event_id '{event_id}' not found.")
    event_type.is_active = False
    event_type.save(update_fields=["is_active"])
    return event_type


# ─────────────────────────────────────────────
#  UC-NT-02: Trigger notification via Event ID
# ─────────────────────────────────────────────

_recent_triggers = {}  # BR-NT-04: in-memory dedup cache {(user_id, event_id): timestamp}

def trigger_notification_by_event_id(*, event_id: str, sender, recipient,
                                      message_content: str, deep_link: str = "#") -> None:
    """
    UC-NT-02 Main Flow:
    External module calls NAM with Event_ID, User_ID, Message_Content, Deep_Link.
    NAM resolves recipient preferences, records the notification, pushes to tray.

    BR-NT-03: Only registered event types can trigger (event_id must exist).
    BR-NT-04: Deduplication — suppress duplicate for same User_ID + Event_ID within 60s.
    BR-NT-05: Critical priority bypasses user preferences.

    Raises:
        NotificationNotFound: if event_id is not a registered active event type.
        DuplicateNotification: if same user+event triggered within 60s.
    """
    from django.utils import timezone

    event_type = selectors.get_event_type_by_event_id(event_id)
    if event_type is None:
        raise NotificationNotFound(
            f"No active event type found with event_id '{event_id}'."
        )

    # BR-NT-04: Deduplication — 60-second cooldown per (recipient, event_id)
    dedup_key = (recipient.id, event_id)
    now = timezone.now()
    if dedup_key in _recent_triggers:
        elapsed = (now - _recent_triggers[dedup_key]).total_seconds()
        if elapsed < 60:
            raise DuplicateNotification(
                f"Duplicate suppressed. Same notification sent {int(elapsed)}s ago (BR-NT-04: 60s cooldown)."
            )
    _recent_triggers[dedup_key] = now

    # BR-NT-05: pass priority so critical bypasses preferences
    _send(
        sender=sender,
        recipient=recipient,
        url=deep_link,
        module=event_type.module,
        verb=message_content,
        description=f"Triggered by event: {event_type.event_name}",
        priority=event_type.default_priority,
    )


# ─────────────────────────────────────────────
#  UC-NT-03: Broadcast Manual Announcement
# ─────────────────────────────────────────────

def _resolve_audience(audience_type: str, audience_value: str):
    """
    Return queryset of User objects for the given audience.

    audience_type values:
        ALL        → every auth_user in the database
        STUDENTS   → globals_extrainfo.user_type = 'student'
        FACULTY    → globals_extrainfo.user_type = 'faculty'
        STAFF      → globals_extrainfo.user_type = 'staff'
        GROUP      → audience_value = designation name
                     e.g. 'Director', 'HOD (CSE)', 'mess_warden'
        DEPARTMENT → audience_value = department name
                     e.g. 'CSE', 'ECE', 'ME', 'Design', 'SM'
        BATCH      → audience_value = batch prefix
                     e.g. '23BCS', '22BEC', '24BME'
    """
    from .models import GlobalsExtraInfo

    if audience_type == AudienceType.ALL:
        return User.objects.filter(is_active=True)
    elif audience_type == AudienceType.STUDENTS:
        return selectors.get_users_by_type("student")
    elif audience_type == AudienceType.FACULTY:
        qs = selectors.get_users_by_type("faculty")
        if not qs.exists():
            qs = selectors.get_users_by_type("staff")
        return qs
    elif audience_type == AudienceType.STAFF:
        return selectors.get_users_by_type("staff")
    elif audience_type == AudienceType.GROUP:
        return selectors.get_users_by_designation(audience_value)
    elif audience_type == AudienceType.DEPARTMENT:
        dept_user_ids = GlobalsExtraInfo.objects.filter(
            department__name=audience_value
        ).values_list("user_id", flat=True)
        return User.objects.filter(id__in=dept_user_ids, is_active=True)
    elif audience_type == AudienceType.BATCH:
        return User.objects.filter(
            username__istartswith=audience_value, is_active=True
        )
    elif audience_type == AudienceType.SPECIFIC_USER:
        # audience_value may be a single username or a comma-separated list
        usernames = [u.strip() for u in str(audience_value).split(",") if u.strip()]
        return User.objects.filter(username__in=usernames, is_active=True)
    return User.objects.none()


def broadcast_announcement(*, sender, title: str, message: str,
                            audience_type: str, audience_value: str = "",
                            expiry_date, priority: str = "medium") -> Announcement:
    """
    UC-NT-03 Main Flow:
    Admin drafts a message, selects audience, sets expiry date.
    NAM fetches recipient list (BR-NT-07: RBAC) and publishes to all.

    BR-NT-03: Only authorized senders (staff/superuser) can broadcast.

    Returns the created Announcement instance.
    """
    # BR-NT-03: Only admin/staff can broadcast announcements
    if not (sender.is_staff or sender.is_superuser):
        raise UnauthorizedSender("Only authorized senders (admin/staff) can broadcast announcements (BR-NT-03).")

    valid_audience = {choice[0] for choice in AudienceType.choices}
    if audience_type not in valid_audience:
        raise InvalidModuleName(f"'{audience_type}' is not a valid audience type.")

    # Wrap announcement row + fan-out in a single transaction. If any recipient
    # insert fails the announcement is rolled back, preventing orphaned records.
    with transaction.atomic():
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            sender=sender,
            audience_type=audience_type,
            audience_value=audience_value,
            expiry_date=expiry_date,
        )

        recipients = _resolve_audience(audience_type, audience_value)

        # Single-query opt-out exclusion (BR-NT-06) — users who disabled the
        # OFFICE_MODULE preference don't receive the announcement.
        if priority != "critical":
            from .models import NotificationPreference
            opted_out = NotificationPreference.objects.filter(
                module=ModuleName.OFFICE_MODULE, is_enabled=False
            ).values_list("user_id", flat=True)
            recipients = recipients.exclude(id__in=opted_out)

        # Single-statement fan-out: INSERT INTO notifications (...) SELECT user_id, ...
        # FROM auth_user WHERE id IN (recipients). 3000+ rows in ~50ms instead of 15s.
        from django.db import connection
        from notifications.models import Notification
        from django.utils import timezone
        import json

        now = timezone.now()
        sender_ct_id = _get_content_type(sender).pk
        recipient_ids = list(recipients.values_list("id", flat=True))
        delivered = len(recipient_ids)

        if recipient_ids:
            data_json = json.dumps({
                "module":          ModuleName.OFFICE_MODULE,
                "url":             "/notifications/announcements/",
                "flag":            "announcement",
                "announcement_id": announcement.id,
                "priority":        priority,
                "expiry_date":     announcement.expiry_date.isoformat(),
            })
            table = Notification._meta.db_table
            # 9 placeholders + 3 hardcoded booleans (unread/public TRUE, deleted/emailed FALSE)
            placeholders = ",".join(
                ["(%s, %s, %s, %s, %s, %s, TRUE, TRUE, FALSE, FALSE, %s, %s)"] * len(recipient_ids)
            )
            sql = (
                f"INSERT INTO {table} "
                "(recipient_id, actor_content_type_id, actor_object_id, "
                "verb, description, level, "
                "unread, public, deleted, emailed, "
                "timestamp, data) "
                f"VALUES {placeholders}"
            )
            params = []
            for uid in recipient_ids:
                params.extend([
                    uid,
                    sender_ct_id,
                    str(sender.pk),
                    title,
                    message,
                    "info",
                    now,
                    data_json,
                ])
            with connection.cursor() as cur:
                cur.execute(sql, params)

    logger.info("announcement.broadcast id=%s audience=%s delivered=%s",
                announcement.id, audience_type, delivered)
    return announcement
