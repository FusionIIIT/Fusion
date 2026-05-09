"""
api/views.py — API endpoints for the notification module.

Source mapping:
  notifications_extension/views.py::mark_as_read_and_redirect → mark_as_read_and_redirect()
  notification/views.py (all functions)                        → called via services.py

Rules enforced:
  - Thin views: validate input → call service/selector → return Response.
  - NO .objects. calls.
  - NO business logic.
  - Every view has @api_view, @authentication_classes, @permission_classes.
  - All responses use DRF Response.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from applications.notifications_extension import selectors, services
from applications.notifications_extension.services import (
    NotificationNotFound,
    InvalidModuleName,
    InvalidNotificationType,
    EventTypeAlreadyExists,
    UnauthorizedSender,
    DuplicateNotification,
)

from .serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    SetPreferenceSerializer,
    MarkReadBySlugSerializer,
    NotificationIdSerializer,
    SendNotificationSerializer,
    LeaveNotifSerializer,
    MessNotifSerializer,
    HostelNotifSerializer,
    HealthcareNotifSerializer,
    ScholarshipNotifSerializer,
    DeanPnDNotifSerializer,
    DeanStudentsNotifSerializer,
    DeanRSPCNotifSerializer,
    GymkhanaVotingNotifSerializer,
    GymkhanaSessionNotifSerializer,
    GymkhanaEventNotifSerializer,
    ResearchNotifSerializer,
    AssistantshipClaimSerializer,
    AssistantshipForwardSerializer,
    ComplaintNotifSerializer,
    FileTrackingNotifSerializer,
    PlacementNotifSerializer,
    AcademicsNotifSerializer,
    DepartmentNotifSerializer,
    # UC-NT-01
    NotificationEventTypeSerializer,
    RegisterEventTypeSerializer,
    TriggerEventNotificationSerializer,
    # UC-NT-03
    AnnouncementSerializer,
    BroadcastAnnouncementSerializer,
)

_AUTH = [SessionAuthentication, TokenAuthentication]
_PERM = [IsAuthenticated]
# BR-NT-03: Only staff/admin can trigger module-specific notifications
_PERM_STAFF = [IsAuthenticated, IsAdminUser]


# ─────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────

def _error(msg, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({"error": msg}, status=http_status)


# ─────────────────────────────────────────────
#  1. Mark as read and redirect
#     Source: notifications_extension/views.py::mark_as_read_and_redirect
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_as_read_and_redirect(request, slug):
    """
    GET /api/notifications/mark-as-read-and-redirect/<slug>/

    Marks a notification as read and redirects the user to the relevant page.
    Source: notifications_extension/views.py::mark_as_read_and_redirect
    """
    try:
        redirect_info = services.mark_as_read_and_get_redirect_url(
            slug=slug, user=request.user
        )
    except NotificationNotFound as exc:
        return _error(str(exc), status.HTTP_404_NOT_FOUND)

    url_name = redirect_info["url_name"]
    kwargs   = redirect_info["kwargs"]

    try:
        redirect_url = reverse(url_name, kwargs=kwargs) if kwargs else reverse(url_name)
    except NoReverseMatch:
        return _error(f"Cannot resolve URL for '{url_name}'.", status.HTTP_400_BAD_REQUEST)

    return HttpResponseRedirect(redirect_url)


# ─────────────────────────────────────────────
#  2. List all notifications
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_all_notifications(request):
    """
    GET /api/notifications/?page=1&page_size=50
    Paginated to avoid loading thousands of rows into memory at once.
    """
    try:
        page      = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 50)), 1), 200)
    except (TypeError, ValueError):
        return _error("page and page_size must be integers.")

    qs    = selectors.get_all_notifications_for_user(request.user)
    total = qs.count()
    start = (page - 1) * page_size
    end   = start + page_size
    serializer = NotificationSerializer(qs[start:end], many=True)
    return Response({
        "notifications": serializer.data,
        "pagination": {
            "page":       page,
            "page_size":  page_size,
            "total":      total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  3. List unread notifications
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_unread_notifications(request):
    """GET /api/notifications/unread/"""
    notifications = selectors.get_unread_notifications_for_user(request.user)
    serializer    = NotificationSerializer(notifications, many=True)
    return Response(
        {"unread_count": notifications.count(), "notifications": serializer.data},
        status=status.HTTP_200_OK,
    )


# ─────────────────────────────────────────────
#  4. Unread count
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_unread_count(request):
    """GET /api/notifications/unread-count/"""
    count = selectors.get_unread_count_for_user(request.user)
    return Response({"unread_count": count}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  5. Filter by module
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_notifications_by_module(request, module):
    """GET /api/notifications/module/<module>/"""
    notifications = selectors.get_notifications_by_module(request.user, module)
    serializer    = NotificationSerializer(notifications, many=True)
    return Response({"notifications": serializer.data}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  6. Mark single notification as read
# ─────────────────────────────────────────────

@api_view(["PATCH"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_as_read(request, notification_id):
    """PATCH /api/notifications/<notification_id>/mark-read/"""
    try:
        notification = services.mark_notification_as_read(
            notification_id=notification_id, user=request.user
        )
    except NotificationNotFound as exc:
        return _error(str(exc), status.HTTP_404_NOT_FOUND)

    return Response(
        {"message": "Notification marked as read.", "id": notification.id},
        status=status.HTTP_200_OK,
    )


# ─────────────────────────────────────────────
#  7. Mark single notification as unread
# ─────────────────────────────────────────────

@api_view(["PATCH"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_as_unread(request, notification_id):
    """PATCH /api/notifications/<notification_id>/mark-unread/"""
    try:
        notification = services.mark_notification_as_unread(
            notification_id=notification_id, user=request.user
        )
    except NotificationNotFound as exc:
        return _error(str(exc), status.HTTP_404_NOT_FOUND)

    return Response(
        {"message": "Notification marked as unread.", "id": notification.id},
        status=status.HTTP_200_OK,
    )


# ─────────────────────────────────────────────
#  8. Mark ALL as read
# ─────────────────────────────────────────────

@api_view(["PATCH"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_all_as_read(request):
    """PATCH /api/notifications/mark-all-read/"""
    services.mark_all_notifications_as_read(user=request.user)
    return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_all_as_unread(request):
    """PATCH /api/notifications/mark-all-unread/"""
    services.mark_all_notifications_as_unread(user=request.user)
    return Response({"message": "All notifications marked as unread."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  9. Delete single notification
# ─────────────────────────────────────────────

@api_view(["PATCH"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def toggle_star(request, notification_id):
    """
    PATCH /api/notifications/<id>/star/
    Flips the boolean `starred` flag inside the notification's data JSON.
    Returns the new value so the UI can update without re-fetching the list.
    """
    from notifications.models import Notification
    try:
        n = Notification.objects.get(pk=notification_id, recipient=request.user)
    except Notification.DoesNotExist:
        return _error("Notification not found.", status.HTTP_404_NOT_FOUND)
    data = n.data if isinstance(n.data, dict) else {}
    data["starred"] = not bool(data.get("starred"))
    n.data = data
    n.save(update_fields=["data"])
    return Response({"id": n.id, "starred": data["starred"]})


@api_view(["DELETE"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def delete_notification(request, notification_id):
    """DELETE /api/notifications/<notification_id>/delete/"""
    try:
        services.delete_notification(
            notification_id=notification_id, user=request.user
        )
    except NotificationNotFound as exc:
        return _error(str(exc), status.HTTP_404_NOT_FOUND)

    return Response({"message": "Notification deleted."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  10. Delete ALL notifications
# ─────────────────────────────────────────────

@api_view(["DELETE"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def delete_all_notifications(request):
    """DELETE /api/notifications/delete-all/"""
    services.delete_all_notifications(user=request.user)
    return Response({"message": "All notifications deleted."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  11. Get preferences
# ─────────────────────────────────────────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_preferences(request):
    """GET /api/notifications/preferences/"""
    services.initialize_default_preferences(user=request.user)
    preferences = selectors.get_all_preferences_for_user(request.user)
    serializer  = NotificationPreferenceSerializer(preferences, many=True)
    return Response({"preferences": serializer.data}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  12. Set preference
# ─────────────────────────────────────────────

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_preference(request):
    """
    POST /api/notifications/preferences/set/
    Body: { "module": "<ModuleName value>", "is_enabled": true/false }
    """
    serializer = SetPreferenceSerializer(data=request.data)
    if not serializer.is_valid():
        return _error(serializer.errors)

    try:
        pref = services.set_notification_preference(
            user=request.user,
            module=serializer.validated_data["module"],
            is_enabled=serializer.validated_data["is_enabled"],
        )
    except InvalidModuleName as exc:
        return _error(str(exc))

    out = NotificationPreferenceSerializer(pref)
    return Response({"preference": out.data}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  13. Receive a notification from another module
# ─────────────────────────────────────────────

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def receive_notification(request):
    """
    POST /api/notifications/send/

    Called by other Fusion modules to push a notification to a user.
    Only staff/admin users (module backends) can call this endpoint.

    Body:
        {
            "recipient_username": "<username>",
            "module":             "<ModuleName value>",
            "verb":               "<notification message>",
            "description":        "<optional extra detail>",
            "url":                "<optional destination url name>",
            "priority":           "low|medium|high|critical"
        }
    """
    serializer = SendNotificationSerializer(data=request.data)
    if not serializer.is_valid():
        return _error(serializer.errors)

    data = serializer.validated_data

    User = get_user_model()
    try:
        recipient = User.objects.get(username=data["recipient_username"])
    except User.DoesNotExist:
        return _error(
            f"User '{data['recipient_username']}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    try:
        services.send_notification_from_module(
            sender=request.user,
            recipient=recipient,
            module=data["module"],
            verb=data["verb"],
            description=data["description"],
            url=data["url"],
            priority=data.get("priority", "medium"),
        )
    except InvalidModuleName as exc:
        return _error(str(exc))

    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def send_group_notification(request):
    """
    POST /api/notifications/send-group/

    Send notification to a group of users (staff/admin only).

    Body:
        {
            "audience": "all|students|faculty|staff|group|department|batch",
            "audience_value": "<designation OR department OR batch prefix>",
            "module": "<ModuleName>",
            "verb": "<notification message>",
            "description": "<optional>",
            "priority": "low|medium|high|critical"
        }
    """
    import logging
    logger = logging.getLogger(__name__)

    audience = request.data.get("audience", "").lower().strip()
    audience_value = request.data.get("audience_value", "").strip()
    module = request.data.get("module", "")
    verb = request.data.get("verb", "")
    description = request.data.get("description", "")
    priority = request.data.get("priority", "medium")

    if not audience or not module or not verb:
        return _error("audience, module, and verb are required.")

    from applications.notifications_extension.models import ModuleName, AudienceType
    valid_modules = {choice[0] for choice in ModuleName.choices}
    if module not in valid_modules:
        return _error(f"'{module}' is not a valid module.")

    # Map legacy names to AudienceType values
    audience_map = {
        "all_students": AudienceType.STUDENTS,
        "all_faculty":  AudienceType.FACULTY,
        "all_staff":    AudienceType.STAFF,
    }
    audience = audience_map.get(audience, audience)

    valid_audiences = {choice[0] for choice in AudienceType.choices}
    if audience not in valid_audiences:
        return _error(f"Invalid audience '{audience}'. Must be one of: {sorted(valid_audiences)}")

    if audience in (AudienceType.GROUP, AudienceType.DEPARTMENT, AudienceType.BATCH) and not audience_value:
        return _error(f"audience_value is required for '{audience}' audience.")

    from django.db import transaction
    recipients = services._resolve_audience(audience, audience_value)
    total = recipients.count()

    count = 0
    failed = 0
    # Use atomic block so partial failures roll back cleanly instead of leaving
    # a half-sent group. Individual recipient errors are caught and counted.
    with transaction.atomic():
        for recipient in recipients.iterator(chunk_size=500):
            try:
                services.send_notification_from_module(
                    sender=request.user, recipient=recipient,
                    module=module, verb=verb, description=description,
                    priority=priority,
                )
                count += 1
            except Exception as exc:
                failed += 1
                logger.warning("group.send.fail user=%s audience=%s err=%s",
                               recipient.username, audience, exc)

    logger.info("group.send.done audience=%s value=%s delivered=%s failed=%s total=%s",
                audience, audience_value, count, failed, total)
    return Response(
        {"message": f"Notification sent to {count} of {total} users.",
         "delivered": count, "failed": failed, "total": total},
        status=status.HTTP_201_CREATED,
    )


# ═════════════════════════════════════════════
#  MODULE-SPECIFIC NOTIFICATION ENDPOINTS
#  Called by other Fusion modules via REST API
# ═════════════════════════════════════════════

User = get_user_model()


def _resolve_recipient(username):
    """Return (user, error_response) — one of the two will be None."""
    try:
        return User.objects.get(username=username), None
    except User.DoesNotExist:
        return None, _error(f"User '{username}' not found.", status.HTTP_404_NOT_FOUND)


def _module_view(serializer_cls, handler):
    """
    Factory that builds a standard module-notification view:
      - validates input with serializer_cls
      - resolves recipient
      - calls handler(sender, recipient, data)
    BR-NT-03: Only staff/admin users can trigger module notifications.
    """
    @api_view(["POST"])
    @authentication_classes(_AUTH)
    @permission_classes(_PERM_STAFF)
    def view(request):
        ser = serializer_cls(data=request.data)
        if not ser.is_valid():
            return _error(ser.errors)
        data = ser.validated_data
        recipient, err = _resolve_recipient(data["recipient_username"])
        if err:
            return err
        try:
            handler(request.user, recipient, data)
        except Exception as exc:
            return _error(str(exc))
        return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)
    return view


# ── Leave Module ──────────────────────────────────────────────────────────────
def _leave_handler(sender, recipient, data):
    services.leave_module_notif(
        sender=sender, recipient=recipient,
        type=data["type"], date=data.get("date")
    )

notify_leave = _module_view(LeaveNotifSerializer, _leave_handler)


# ── Central Mess ──────────────────────────────────────────────────────────────
def _mess_handler(sender, recipient, data):
    services.central_mess_notif(
        sender=sender, recipient=recipient,
        type=data["type"], message=data.get("message")
    )

notify_mess = _module_view(MessNotifSerializer, _mess_handler)


# ── Visitor's Hostel ──────────────────────────────────────────────────────────
def _hostel_handler(sender, recipient, data):
    services.visitors_hostel_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_hostel = _module_view(HostelNotifSerializer, _hostel_handler)


# ── Healthcare Center ─────────────────────────────────────────────────────────
def _healthcare_handler(sender, recipient, data):
    services.healthcare_center_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_healthcare = _module_view(HealthcareNotifSerializer, _healthcare_handler)


# ── Scholarship Portal ────────────────────────────────────────────────────────
def _scholarship_handler(sender, recipient, data):
    services.scholarship_portal_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_scholarship = _module_view(ScholarshipNotifSerializer, _scholarship_handler)


# ── Office of Dean PnD ────────────────────────────────────────────────────────
def _dean_pnd_handler(sender, recipient, data):
    services.office_dean_pnd_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_dean_pnd = _module_view(DeanPnDNotifSerializer, _dean_pnd_handler)


# ── Office Module — Dean Students ─────────────────────────────────────────────
def _dean_students_handler(sender, recipient, data):
    services.office_module_deans_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_dean_students = _module_view(DeanStudentsNotifSerializer, _dean_students_handler)


# ── Office Module — Dean RSPC ─────────────────────────────────────────────────
def _dean_rspc_handler(sender, recipient, data):
    services.office_module_dean_rspc_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_dean_rspc = _module_view(DeanRSPCNotifSerializer, _dean_rspc_handler)


# ── Gymkhana — Voting ─────────────────────────────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_gymkhana_voting(request):
    """POST /api/notifications/notify/gymkhana/voting/"""
    ser = GymkhanaVotingNotifSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.gymkhana_voting_notif(
        sender=request.user, recipient=recipient,
        type="voting_open", title=data["title"], desc=data["desc"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Gymkhana — Session ────────────────────────────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_gymkhana_session(request):
    """POST /api/notifications/notify/gymkhana/session/"""
    ser = GymkhanaSessionNotifSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.gymkhana_session_notif(
        sender=request.user, recipient=recipient,
        type="new_session", club=data["club"],
        desc=data["desc"], venue=data["venue"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Gymkhana — Event ──────────────────────────────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_gymkhana_event(request):
    """POST /api/notifications/notify/gymkhana/event/"""
    ser = GymkhanaEventNotifSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.gymkhana_event_notif(
        sender=request.user, recipient=recipient,
        type="new_event", club=data["club"],
        event_name=data["event_name"], desc=data["desc"], venue=data["venue"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Research Procedures ───────────────────────────────────────────────────────
def _research_handler(sender, recipient, data):
    services.research_procedures_notif(
        sender=sender, recipient=recipient, type=data["type"]
    )

notify_research = _module_view(ResearchNotifSerializer, _research_handler)


# ── Assistantship — Claim Approved (student) ──────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_assistantship_approved(request):
    """POST /api/notifications/notify/assistantship/approved/"""
    ser = AssistantshipClaimSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.assistantship_claim_notify(
        sender=request.user, recipient=recipient,
        month=data["month"], year=data["year"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Assistantship — Faculty notified ─────────────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_assistantship_faculty(request):
    """POST /api/notifications/notify/assistantship/faculty/"""
    from .serializers import _RecipientMixin
    class S(_RecipientMixin): pass
    ser = S(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    recipient, err = _resolve_recipient(ser.validated_data["recipient_username"])
    if err:
        return err
    services.assistantship_claim_faculty_notify(sender=request.user, recipient=recipient)
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Assistantship — Academic section notified ─────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_assistantship_acad(request):
    """POST /api/notifications/notify/assistantship/acad/"""
    from .serializers import _RecipientMixin
    class S(_RecipientMixin): pass
    ser = S(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    recipient, err = _resolve_recipient(ser.validated_data["recipient_username"])
    if err:
        return err
    services.assistantship_claim_acad_notify(sender=request.user, recipient=recipient)
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Assistantship — Accounts section notified ────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_assistantship_accounts(request):
    """POST /api/notifications/notify/assistantship/accounts/"""
    ser = AssistantshipForwardSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.assistantship_claim_account_notify(
        sender=request.user, recipient=recipient,
        stu=data["student_username"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── Complaint System ──────────────────────────────────────────────────────────
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def notify_complaint(request):
    """POST /api/notifications/notify/complaint/"""
    ser = ComplaintNotifSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    recipient, err = _resolve_recipient(data["recipient_username"])
    if err:
        return err
    services.complaint_system_notif(
        sender=request.user, recipient=recipient,
        type="complaint", complaint_id=data["complaint_id"],
        is_student=data["is_student"], message=data["message"]
    )
    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


# ── File Tracking ─────────────────────────────────────────────────────────────
def _file_tracking_handler(sender, recipient, data):
    services.file_tracking_notif(
        sender=sender, recipient=recipient, title=data["title"]
    )

notify_file_tracking = _module_view(FileTrackingNotifSerializer, _file_tracking_handler)


# ── Placement Cell ────────────────────────────────────────────────────────────
def _placement_handler(sender, recipient, data):
    services.placement_cell_notif(
        sender=sender, recipient=recipient, type=data["message"]
    )

notify_placement = _module_view(PlacementNotifSerializer, _placement_handler)


# ── Academics Module ──────────────────────────────────────────────────────────
def _academics_handler(sender, recipient, data):
    services.academics_module_notif(
        sender=sender, recipient=recipient, type=data["message"]
    )

notify_academics = _module_view(AcademicsNotifSerializer, _academics_handler)


# ── Department ────────────────────────────────────────────────────────────────
def _department_handler(sender, recipient, data):
    services.department_notif(
        sender=sender, recipient=recipient, type=data["message"]
    )

notify_department = _module_view(DepartmentNotifSerializer, _department_handler)


# ═════════════════════════════════════════════
#  UC-NT-01: Event Type Registry
# ═════════════════════════════════════════════

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def register_event_type(request):
    """
    POST /api/notifications/event-types/register/

    UC-NT-01: External module registers a new notification event type with NAM.
    Only staff/admin can register event types (BR-NT-03).

    Body: { "event_name": "...", "module": "...", "default_priority": "...", "description": "..." }
    """
    ser = RegisterEventTypeSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    try:
        event_type = services.register_event_type(
            registered_by=request.user,
            event_name=data["event_name"],
            module=data["module"],
            default_priority=data["default_priority"],
            description=data["description"],
        )
    except (InvalidModuleName, EventTypeAlreadyExists) as exc:
        return _error(str(exc))
    out = NotificationEventTypeSerializer(event_type)
    return Response({"event_type": out.data}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_event_types(request):
    """
    GET /api/notifications/event-types/
    Returns all registered event types (active only by default).
    Pass ?all=true to include inactive ones.
    """
    if request.query_params.get("all") == "true":
        event_types = selectors.get_all_event_types()
    else:
        event_types = selectors.get_active_event_types()
    ser = NotificationEventTypeSerializer(event_types, many=True)
    return Response({"event_types": ser.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def get_event_type(request, event_id):
    """
    GET /api/notifications/event-types/<event_id>/
    Returns a single registered event type by its UUID event_id.
    """
    event_type = selectors.get_event_type_by_event_id(event_id)
    if event_type is None:
        return _error(f"Event type '{event_id}' not found.", status.HTTP_404_NOT_FOUND)
    ser = NotificationEventTypeSerializer(event_type)
    return Response({"event_type": ser.data}, status=status.HTTP_200_OK)


# ═════════════════════════════════════════════
#  UC-NT-02: Trigger notification via Event ID
# ═════════════════════════════════════════════

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM_STAFF)
def trigger_event_notification(request):
    """
    POST /api/notifications/trigger/

    UC-NT-02: External module calls NAM with Event_ID + User_ID + Message_Content + Deep_Link.
    Only staff/admin (module backends) can trigger notifications (BR-NT-03).
    NAM resolves preferences, records the notification, pushes to Navbar Tray.

    Body: { "event_id": "<uuid>", "recipient_username": "...", "message_content": "...", "deep_link": "..." }
    """
    ser = TriggerEventNotificationSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data

    try:
        recipient = User.objects.get(username=data["recipient_username"])
    except User.DoesNotExist:
        return _error(f"User '{data['recipient_username']}' not found.", status.HTTP_404_NOT_FOUND)

    try:
        services.trigger_notification_by_event_id(
            event_id=str(data["event_id"]),
            sender=request.user,
            recipient=recipient,
            message_content=data["message_content"],
            deep_link=data["deep_link"],
        )
    except NotificationNotFound as exc:
        return _error(str(exc), status.HTTP_404_NOT_FOUND)
    except DuplicateNotification as exc:
        return _error(str(exc), status.HTTP_429_TOO_MANY_REQUESTS)

    return Response({"message": "Notification sent."}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def mark_read_return_url(request, notification_id):
    """
    GET /api/notifications/<notification_id>/open/

    UC-NT-04 deep-link support: marks the notification as read and returns
    the stored deep_link URL as JSON so the SPA can navigate client-side.

    Returns: { "url": "/some/path" }
    """
    from applications.notifications_extension.selectors import get_notification_by_id
    notification = get_notification_by_id(notification_id, request.user)
    if notification is None:
        return _error("Notification not found.", status.HTTP_404_NOT_FOUND)
    if notification.unread:
        notification.mark_as_read()
    url = "#"
    if notification.data and isinstance(notification.data, dict):
        url = notification.data.get("url", "#")
    return Response({"url": url}, status=status.HTTP_200_OK)


# ═════════════════════════════════════════════
#  UC-NT-03: Announcements (Manual Broadcast)
# ═════════════════════════════════════════════

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def broadcast_announcement(request):
    """
    POST /api/notifications/announcements/

    UC-NT-03: Admin creates a broadcast announcement.
    NAM resolves audience from Fusion RBAC groups and publishes to all dashboards.

    Body: { "title": "...", "message": "...", "audience_type": "...",
            "audience_value": "...", "expiry_date": "YYYY-MM-DD" }
    """
    ser = BroadcastAnnouncementSerializer(data=request.data)
    if not ser.is_valid():
        return _error(ser.errors)
    data = ser.validated_data
    try:
        announcement = services.broadcast_announcement(
            sender=request.user,
            title=data["title"],
            message=data["message"],
            audience_type=data["audience_type"],
            audience_value=data["audience_value"],
            expiry_date=data["expiry_date"],
            priority=data.get("priority", "medium"),
        )
    except UnauthorizedSender as exc:
        return _error(str(exc), status.HTTP_403_FORBIDDEN)
    except InvalidModuleName as exc:
        return _error(str(exc))
    out = AnnouncementSerializer(announcement)
    return Response({"announcement": out.data}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def preview_audience(request):
    """
    GET /api/notifications/announcements/preview-audience/
    ?audience_type=students&audience_value=

    Returns list of usernames that would receive a broadcast for the given audience.
    """
    from applications.notifications_extension.services import _resolve_audience
    audience_type = request.query_params.get("audience_type", "all")
    audience_value = request.query_params.get("audience_value", "")
    try:
        users = _resolve_audience(audience_type, audience_value)
        return Response({
            "count": users.count(),
            "users": list(users.values_list("username", flat=True)),
        })
    except Exception as exc:
        return Response({"count": 0, "users": [], "error": str(exc)})


# ── Audience option lists (powers UC-NT-03 dashboard modal dropdowns) ──────────

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_departments(request):
    """GET /api/notifications/audience/departments/ — names of every department."""
    from applications.globals.models import DepartmentInfo
    names = list(DepartmentInfo.objects.order_by("name").values_list("name", flat=True))
    return Response({"departments": names})


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_designations(request):
    """GET /api/notifications/audience/designations/ — names of every designation."""
    from applications.globals.models import Designation
    names = list(Designation.objects.order_by("name").values_list("name", flat=True))
    return Response({"designations": names})


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_users(request):
    """
    GET /api/notifications/audience/users/
    Active users as [{value, label}] pairs the Mantine Select can consume directly.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).only(
        "username", "first_name", "last_name"
    ).order_by("username")
    out = []
    for u in users:
        full = f"{u.first_name} {u.last_name}".strip()
        out.append({"value": u.username, "label": f"{u.username} — {full}" if full else u.username})
    return Response({"users": out})


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_batches(request):
    """
    GET /api/notifications/audience/batches/
    Distinct batch prefixes derived from usernames matching ^\\d{2}[A-Z]{3}.
    """
    import re
    from django.contrib.auth import get_user_model
    User = get_user_model()
    seen = set()
    for u in User.objects.values_list("username", flat=True):
        if not u:
            continue
        m = re.match(r"^(\d{2}[A-Za-z]{3})", u)
        if m:
            seen.add(m.group(1).upper())
    return Response({"batches": sorted(seen)})


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_active_announcements(request):
    """
    GET /api/notifications/announcements/

    UC-NT-03 Post-condition: returns all announcements that haven't expired yet.
    Shown on user dashboards until the expiry date.
    """
    announcements = selectors.get_active_announcements()
    ser = AnnouncementSerializer(announcements, many=True)
    return Response({"announcements": ser.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def list_all_announcements(request):
    """
    GET /api/notifications/announcements/all/
    Admin view — returns all announcements including expired ones.
    """
    announcements = selectors.get_all_announcements()
    ser = AnnouncementSerializer(announcements, many=True)
    return Response({"announcements": ser.data}, status=status.HTTP_200_OK)
