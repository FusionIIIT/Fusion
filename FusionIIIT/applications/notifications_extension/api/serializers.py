"""
api/serializers.py — DRF serializers for the notification module.

Rules enforced:
  - Field-level validation only. No business logic.
  - No .objects. calls. No service calls.
"""

from notifications.models import Notification
from rest_framework import serializers

from applications.notifications_extension.models import (
    Announcement,
    AudienceType,
    EventPriority,
    ModuleName,
    NotificationEventType,
    NotificationPreference,
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
)


# ─────────────────────────────────────────────
#  Read serializers
# ─────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for a django-notifications-hq Notification.
    Exposes actor info, module, url, flag from the data JSON field.
    """
    sender = serializers.SerializerMethodField()
    module = serializers.SerializerMethodField()
    url    = serializers.SerializerMethodField()
    flag   = serializers.SerializerMethodField()
    data   = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = (
            "id",
            "sender",
            "verb",
            "description",
            "module",
            "url",
            "flag",
            "data",
            "unread",
            "timestamp",
        )
        read_only_fields = fields

    def get_sender(self, obj):
        actor = obj.actor
        if actor is None:
            return None
        return {
            "id":        actor.id,
            "username":  actor.username,
            "full_name": actor.get_full_name(),
        }

    def get_module(self, obj):
        if obj.data and isinstance(obj.data, dict):
            return obj.data.get("module", "")
        return ""

    def get_url(self, obj):
        if obj.data and isinstance(obj.data, dict):
            return obj.data.get("url", "#")
        return "#"

    def get_flag(self, obj):
        if obj.data and isinstance(obj.data, dict):
            return obj.data.get("flag", "")
        return ""

    def get_data(self, obj):
        if not isinstance(obj.data, dict):
            return {}
        out = dict(obj.data)
        # Enrich announcement rows with expiry_date if missing (older rows
        # didn't store it in the JSON blob — read it from the Announcement table)
        if out.get("flag") == "announcement" and "expiry_date" not in out:
            ann_id = out.get("announcement_id")
            if ann_id is not None:
                try:
                    ann = Announcement.objects.only("expiry_date").get(pk=ann_id)
                    out["expiry_date"] = ann.expiry_date.isoformat()
                except Announcement.DoesNotExist:
                    pass
        return out


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Read serializer for a user's module notification preference."""
    module_display = serializers.CharField(source="get_module_display", read_only=True)

    class Meta:
        model  = NotificationPreference
        fields = ("id", "module", "module_display", "is_enabled", "updated_at")
        read_only_fields = ("id", "module_display", "updated_at")


# ─────────────────────────────────────────────
#  Input serializers
# ─────────────────────────────────────────────

class SetPreferenceSerializer(serializers.Serializer):
    """Input: set notification preference for a module."""
    module     = serializers.ChoiceField(choices=ModuleName.choices)
    is_enabled = serializers.BooleanField()


class MarkReadBySlugSerializer(serializers.Serializer):
    """Input: mark a notification as read using its slug (from notifications_extension)."""
    slug = serializers.CharField(max_length=64)

    def validate_slug(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("slug must be a numeric string.")
        return value


class NotificationIdSerializer(serializers.Serializer):
    """Input: single notification_id."""
    notification_id = serializers.IntegerField(min_value=1)


class SendNotificationSerializer(serializers.Serializer):
    """
    Input: used by other modules to send a notification to a recipient.
    The authenticated caller becomes the sender.
    """
    recipient_username = serializers.CharField()
    module             = serializers.ChoiceField(choices=ModuleName.choices)
    verb               = serializers.CharField()
    description        = serializers.CharField(required=False, allow_blank=True, default="")
    url                = serializers.CharField(required=False, allow_blank=True, default="#")
    priority           = serializers.ChoiceField(
        choices=EventPriority.choices, required=False, default="medium"
    )


# ─────────────────────────────────────────────
#  Module-specific input serializers
#  (used by other Fusion modules via REST API)
# ─────────────────────────────────────────────

class _RecipientMixin(serializers.Serializer):
    """Common recipient field for all module notification serializers."""
    recipient_username = serializers.CharField()


class LeaveNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/leave/"""
    type = serializers.ChoiceField(choices=LeaveNotifType.choices)
    date = serializers.CharField(required=False, allow_blank=True, default=None)


class MessNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/mess/"""
    type    = serializers.ChoiceField(choices=MessNotifType.choices)
    message = serializers.CharField(required=False, allow_blank=True, default=None)


class HostelNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/hostel/"""
    type = serializers.ChoiceField(choices=VisitorHostelNotifType.choices)


class HealthcareNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/healthcare/"""
    type = serializers.ChoiceField(choices=HealthcareNotifType.choices)


class ScholarshipNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/scholarship/"""
    type = serializers.ChoiceField(choices=ScholarshipNotifType.choices)


class DeanPnDNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/dean-pnd/"""
    type = serializers.ChoiceField(choices=OfficeDeanPnDNotifType.choices)


class DeanStudentsNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/dean-students/"""
    type = serializers.ChoiceField(choices=OfficeDeanSNotifType.choices)


class DeanRSPCNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/dean-rspc/"""
    type = serializers.ChoiceField(choices=OfficeDeanRSPCNotifType.choices)


class GymkhanaVotingNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/gymkhana/voting/"""
    title = serializers.CharField()
    desc  = serializers.CharField()


class GymkhanaSessionNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/gymkhana/session/"""
    club  = serializers.CharField()
    desc  = serializers.CharField()
    venue = serializers.CharField()


class GymkhanaEventNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/gymkhana/event/"""
    club       = serializers.CharField()
    event_name = serializers.CharField()
    desc       = serializers.CharField()
    venue      = serializers.CharField()


class ResearchNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/research/"""
    type = serializers.ChoiceField(choices=ResearchProceduresNotifType.choices)


class AssistantshipClaimSerializer(_RecipientMixin):
    """POST /api/notifications/notify/assistantship/claim-approved/"""
    month = serializers.CharField()
    year  = serializers.CharField()


class AssistantshipForwardSerializer(_RecipientMixin):
    """POST /api/notifications/notify/assistantship/forwarded/"""
    student_username = serializers.CharField()


class ComplaintNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/complaint/"""
    complaint_id = serializers.IntegerField()
    is_student   = serializers.BooleanField()
    message      = serializers.CharField()


class FileTrackingNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/file-tracking/"""
    title = serializers.CharField()


class PlacementNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/placement/"""
    message = serializers.CharField()


class AcademicsNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/academics/"""
    message = serializers.CharField()


class DepartmentNotifSerializer(_RecipientMixin):
    """POST /api/notifications/notify/department/"""
    message = serializers.CharField()


# ─────────────────────────────────────────────
#  UC-NT-01: Event Type Registry serializers
# ─────────────────────────────────────────────

class NotificationEventTypeSerializer(serializers.ModelSerializer):
    """Read serializer for a registered event type."""
    registered_by_username = serializers.SerializerMethodField()

    class Meta:
        model  = NotificationEventType
        fields = (
            "id", "event_id", "event_name", "module",
            "default_priority", "description",
            "is_active", "registered_by_username", "created_at",
        )
        read_only_fields = fields

    def get_registered_by_username(self, obj):
        return obj.registered_by.username if obj.registered_by else None


class RegisterEventTypeSerializer(serializers.Serializer):
    """Input: register a new notification event type (UC-NT-01)."""
    event_name       = serializers.CharField(max_length=100)
    module           = serializers.ChoiceField(choices=ModuleName.choices)
    default_priority = serializers.ChoiceField(
        choices=EventPriority.choices, default=EventPriority.MEDIUM
    )
    description      = serializers.CharField(required=False, allow_blank=True, default="")


class TriggerEventNotificationSerializer(serializers.Serializer):
    """Input: trigger a notification via a registered event_id (UC-NT-02)."""
    event_id          = serializers.UUIDField()
    recipient_username = serializers.CharField()
    message_content   = serializers.CharField()
    deep_link         = serializers.CharField(required=False, allow_blank=True, default="#")


# ─────────────────────────────────────────────
#  UC-NT-03: Announcement serializers
# ─────────────────────────────────────────────

class AnnouncementSerializer(serializers.ModelSerializer):
    """Read serializer for an Announcement."""
    sender_username = serializers.SerializerMethodField()
    is_active       = serializers.SerializerMethodField()

    class Meta:
        model  = Announcement
        fields = (
            "id", "title", "message",
            "sender_username", "audience_type", "audience_value",
            "expiry_date", "created_at", "is_active",
            "approval_id",
        )
        read_only_fields = fields

    def get_sender_username(self, obj):
        return obj.sender.username

    def get_is_active(self, obj):
        return obj.is_active


class BroadcastAnnouncementSerializer(serializers.Serializer):
    """Input: create and broadcast a manual announcement (UC-NT-03)."""
    title          = serializers.CharField(max_length=200)
    message        = serializers.CharField()
    audience_type  = serializers.ChoiceField(choices=AudienceType.choices)
    audience_value = serializers.CharField(required=False, allow_blank=True, default="")
    expiry_date    = serializers.DateField()
    priority       = serializers.ChoiceField(
        choices=EventPriority.choices, default=EventPriority.MEDIUM, required=False
    )

    def validate(self, attrs):
        if attrs["audience_type"] == AudienceType.GROUP and not attrs.get("audience_value"):
            raise serializers.ValidationError(
                {"audience_value": "audience_value is required when audience_type is 'group'."}
            )
        return attrs
