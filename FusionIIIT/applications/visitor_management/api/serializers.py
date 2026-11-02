"""DRF serializers. Input serializers only parse/shape data; business rules live in services."""

import os

from django.utils import timezone
from rest_framework import serializers

from .. import conf
from ..constants import (
    BulkListKind,
    CredentialType,
    IdDocumentType,
    IntegrationStatus,
    LogType,
    Purpose,
    RegistryListType,
    RoleScope,
    RollCallStatus,
    SafeListScope,
    Severity,
    VmsRole,
)
from ..models import (
    AccessPolicy,
    AuditLog,
    BulkVisitorList,
    EmergencyMuster,
    ExtensionRequest,
    Gate,
    GateAttempt,
    IntegrationConfig,
    MusterRosterEntry,
    OfflineGateEvent,
    PreAuthorization,
    RegistryEntry,
    SecurityAlert,
    VipPermission,
    VisitLog,
    VisitorEvent,
    VisitPass,
    VisitRequest,
    VisitStateHistory,
    VmsNotification,
    VmsRoleAssignment,
    Zone,
)
from ..services.common import mask


# --------------------------------------------------------------------------
# Field helpers
# --------------------------------------------------------------------------

class LocalDateTimeField(serializers.DateTimeField):
    """Fusion runs with USE_TZ=False in Asia/Kolkata: store aware input as local naive time."""

    def enforce_timezone(self, value):
        if timezone.is_aware(value):
            return timezone.make_naive(value, timezone.get_default_timezone())
        return value


class CodeListField(serializers.ListField):
    """Accepts a JSON list or a comma-separated string (multipart forms)."""

    child = serializers.CharField()

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = [part.strip() for part in data.split(",") if part.strip()]
        elif isinstance(data, list) and len(data) == 1 and isinstance(data[0], str) and "," in data[0]:
            data = [part.strip() for part in data[0].split(",") if part.strip()]
        return super().to_internal_value(data)

    def get_value(self, dictionary):
        if hasattr(dictionary, "getlist") and self.field_name in dictionary:
            values = dictionary.getlist(self.field_name)
            return values if len(values) != 1 else values[0]
        return super().get_value(dictionary)


ALLOWED_DOC_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_upload(upload):
    if upload is None:
        return upload
    ext = os.path.splitext(upload.name or "")[1].lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise serializers.ValidationError("Upload a PDF, JPG or PNG file.")
    if upload.size > conf.id_document_max_bytes():
        raise serializers.ValidationError("File is too large.")
    return upload


class IdentityInput(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    organization = serializers.CharField(max_length=200, required=False, allow_blank=True)
    id_doc_type = serializers.ChoiceField(choices=IdDocumentType.CHOICES)
    id_doc_number = serializers.CharField(max_length=60)
    id_document = serializers.FileField(required=False, allow_null=True, validators=[validate_upload])
    photo = serializers.ImageField(required=False, allow_null=True, validators=[validate_upload])


# --------------------------------------------------------------------------
# Input serializers
# --------------------------------------------------------------------------

class PreRegistrationInput(IdentityInput):
    purpose = serializers.ChoiceField(choices=Purpose.CHOICES)
    purpose_details = serializers.CharField(required=False, allow_blank=True)
    host_id = serializers.CharField(max_length=20)
    scheduled_start = LocalDateTimeField()
    scheduled_end = LocalDateTimeField()
    requested_zones = CodeListField(required=False)
    is_urgent = serializers.BooleanField(required=False, default=False)


class WalkInInput(IdentityInput):
    purpose = serializers.ChoiceField(choices=Purpose.CHOICES)
    purpose_details = serializers.CharField(required=False, allow_blank=True)
    host_id = serializers.CharField(max_length=20)
    gate = serializers.CharField(max_length=30)
    requested_zones = CodeListField(required=False)
    host_unavailable = serializers.BooleanField(required=False, default=False)
    event_id = serializers.IntegerField(required=False, allow_null=True)
    lane = serializers.ChoiceField(choices=VisitRequest.LANE_CHOICES, required=False)


class HostDecisionInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    special_instructions = serializers.CharField(required=False, allow_blank=True)
    permitted_zones = CodeListField(required=False, allow_null=True)
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField(required=False, allow_null=True)


class BulkHostDecisionInput(HostDecisionInput):
    references = serializers.ListField(child=serializers.CharField(), min_length=1, max_length=200)


class AdminDecisionInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    note = serializers.CharField(required=False, allow_blank=True)


class PreAuthorizationInput(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    id_doc_type = serializers.ChoiceField(choices=IdDocumentType.CHOICES, required=False, allow_blank=True)
    id_doc_number = serializers.CharField(max_length=60, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    purpose = serializers.ChoiceField(choices=Purpose.CHOICES, required=False, allow_blank=True)
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField()
    permitted_zones = CodeListField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class AvailabilityInput(serializers.Serializer):
    is_available = serializers.BooleanField()
    unavailable_until = LocalDateTimeField(required=False, allow_null=True)


class VipInput(serializers.Serializer):
    visit_reference = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    id_doc_type = serializers.ChoiceField(choices=IdDocumentType.CHOICES, required=False, allow_blank=True)
    id_doc_number = serializers.CharField(max_length=60, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    bypass_host_approval = serializers.BooleanField(required=False)
    zone_scope = serializers.ChoiceField(choices=VipPermission.ZONE_SCOPE_CHOICES, required=False)
    zones = CodeListField(required=False, allow_null=True)
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class PolicyInput(serializers.Serializer):
    based_on_version = serializers.IntegerField(required=False, allow_null=True)
    visiting_hours_start = serializers.TimeField(required=False, allow_null=True)
    visiting_hours_end = serializers.TimeField(required=False, allow_null=True)
    max_visit_duration_minutes = serializers.IntegerField(required=False, min_value=1)
    walk_in_pass_duration_minutes = serializers.IntegerField(required=False, min_value=1)
    approval_timeout_minutes = serializers.IntegerField(required=False, min_value=1)
    advance_registration_minutes = serializers.IntegerField(required=False, min_value=0)
    contingency_sla_minutes = serializers.IntegerField(required=False, min_value=1)
    reminder_offsets_minutes = serializers.ListField(child=serializers.IntegerField(), required=False)
    restricted_zones = CodeListField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class RegistryEntryInput(serializers.Serializer):
    list_type = serializers.ChoiceField(choices=RegistryListType.CHOICES, required=False)
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    id_doc_type = serializers.ChoiceField(choices=IdDocumentType.CHOICES, required=False, allow_blank=True)
    id_doc_number = serializers.CharField(max_length=60, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.ChoiceField(choices=Severity.CHOICES, required=False)
    expires_at = LocalDateTimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    safelist_scope = serializers.ChoiceField(choices=SafeListScope.CHOICES, required=False)


class RoleAssignmentInput(serializers.Serializer):
    user = serializers.CharField(help_text="Username, ExtraInfo id or user id")
    role = serializers.ChoiceField(choices=VmsRole.ASSIGNABLE)
    scope_type = serializers.ChoiceField(choices=RoleScope.CHOICES)
    zone = serializers.CharField(required=False, allow_blank=True)
    gate = serializers.CharField(required=False, allow_blank=True)
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField()


class ReassignInput(serializers.Serializer):
    user = serializers.CharField()
    valid_until = LocalDateTimeField(required=False, allow_null=True)


class IntegrationInput(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False, default=True)
    status = serializers.ChoiceField(choices=IntegrationStatus.CHOICES, required=False)
    endpoint_url = serializers.CharField(required=False, allow_blank=True)
    settings = serializers.JSONField(required=False)


class CredentialInput(serializers.Serializer):
    credential_type = serializers.ChoiceField(choices=CredentialType.CHOICES)
    credential = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=100, required=False, allow_blank=True)


class GateValidateInput(CredentialInput):
    gate = serializers.CharField(max_length=30)
    lane = serializers.ChoiceField(choices=VisitRequest.LANE_CHOICES, required=False)


class OverrideInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["AUTHORIZE", "DENY"])
    justification = serializers.CharField(allow_blank=True)


class ReferInput(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class ManualLogInput(serializers.Serializer):
    reference = serializers.CharField()
    log_type = serializers.ChoiceField(choices=[LogType.CHECK_IN, LogType.CHECK_OUT, LogType.ACCESS_DENIED])
    gate = serializers.CharField(required=False, allow_blank=True)
    zone = serializers.CharField(required=False, allow_blank=True)
    attempt_id = serializers.IntegerField(required=False, allow_null=True)
    device_id = serializers.CharField(required=False, allow_blank=True)
    detail = serializers.CharField(required=False, allow_blank=True)


class CheckOutInput(serializers.Serializer):
    reference = serializers.CharField(required=False, allow_blank=True)
    credential_type = serializers.ChoiceField(choices=CredentialType.CHOICES, required=False)
    credential = serializers.CharField(required=False, allow_blank=True)
    otp = serializers.CharField(required=False, allow_blank=True)
    gate = serializers.CharField(required=False, allow_blank=True)
    device_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("reference") and not (attrs.get("credential_type") and attrs.get("credential")):
            raise serializers.ValidationError("Give a visit reference or a credential.")
        return attrs


class OfflineEventInput(serializers.Serializer):
    client_event_id = serializers.CharField(max_length=64)
    event_type = serializers.ChoiceField(choices=OfflineGateEvent.EVENT_CHOICES)
    credential_type = serializers.ChoiceField(choices=CredentialType.CHOICES)
    credential = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6, required=False, allow_blank=True)
    occurred_at = LocalDateTimeField()


class OfflineUploadInput(serializers.Serializer):
    gate = serializers.CharField()
    device_id = serializers.CharField(required=False, allow_blank=True)
    events = OfflineEventInput(many=True)


class ZoneValidateInput(CredentialInput):
    zone = serializers.CharField(max_length=30)


class ElevationInput(serializers.Serializer):
    zones = CodeListField()
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField()
    reason = serializers.CharField(allow_blank=True)


class AlertHandleInput(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=["HANDLED", "ESCALATED", "FALSE_ALARM"])
    note = serializers.CharField(allow_blank=True)


class EscalateInput(serializers.Serializer):
    note = serializers.CharField(allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)
    attempt_id = serializers.IntegerField(required=False, allow_null=True)
    gate = serializers.CharField(required=False, allow_blank=True)


class TerminateInput(serializers.Serializer):
    reason = serializers.CharField(allow_blank=True)


class ExtensionInput(serializers.Serializer):
    requested_valid_until = LocalDateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True)


class MusterTriggerInput(serializers.Serializer):
    assembly_instructions = serializers.CharField(required=False, allow_blank=True)
    cached_roster = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    offline_triggered_at = LocalDateTimeField(required=False, allow_null=True)


class RollCallItemInput(serializers.Serializer):
    entry_id = serializers.IntegerField(required=False)
    reference = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=RollCallStatus.CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    recorded_at = LocalDateTimeField(required=False, allow_null=True)


class RollCallInput(serializers.Serializer):
    source = serializers.ChoiceField(choices=["live", "cached"], required=False, default="live")
    updates = RollCallItemInput(many=True)


class EventInput(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    host_id = serializers.CharField(max_length=20)
    starts_at = LocalDateTimeField()
    ends_at = LocalDateTimeField()
    venue_zones = CodeListField(required=False)
    external_event_ref = serializers.CharField(required=False, allow_blank=True)


class EventControlsInput(serializers.Serializer):
    fast_lane_enabled = serializers.BooleanField(required=False)
    overflow_walk_in_enabled = serializers.BooleanField(required=False)
    walk_in_rate_limit_per_hour = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class BulkUploadInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=BulkListKind.CHOICES)
    event_id = serializers.IntegerField(required=False, allow_null=True)
    host_id = serializers.CharField(required=False, allow_blank=True)
    valid_from = LocalDateTimeField(required=False, allow_null=True)
    valid_until = LocalDateTimeField(required=False, allow_null=True)
    zones = CodeListField(required=False)
    file = serializers.FileField(required=False)
    rows = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("rows"):
            raise serializers.ValidationError("Upload a CSV/XLSX file or give rows.")
        return attrs


# --------------------------------------------------------------------------
# Output serializers
# --------------------------------------------------------------------------

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["code", "name", "description", "access_level", "is_hostel_area"]


class GateSerializer(serializers.ModelSerializer):
    zone = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = Gate
        fields = ["code", "name", "zone"]


def _codes(manager):
    return list(manager.values_list("code", flat=True))


class StaffPassSerializer(serializers.ModelSerializer):
    """Staff views never expose the visitor's QR token or OTP."""

    permitted_zones = serializers.SerializerMethodField()

    class Meta:
        model = VisitPass
        fields = ["pass_number", "pass_type", "valid_from", "valid_until", "is_active", "permitted_zones",
                  "issued_at", "deactivated_at", "deactivation_reason", "otp_used_at"]

    def get_permitted_zones(self, obj):
        return _codes(obj.permitted_zones)


class VisitorPassSerializer(StaffPassSerializer):
    """VMS-UC-012: the visitor's own credentials."""

    class Meta(StaffPassSerializer.Meta):
        fields = StaffPassSerializer.Meta.fields + ["qr_token", "otp"]


def _host_dict(extra):
    return {
        "id": extra.pk,
        "name": extra.user.get_full_name() or extra.user.username,
        "department": extra.department.name if extra.department_id else None,
    }


class VisitSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    visitor = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    requested_zones = serializers.SerializerMethodField()
    visit_pass = serializers.SerializerMethodField()
    last_seen_zone = serializers.SlugRelatedField(slug_field="code", read_only=True)
    entry_gate = serializers.SlugRelatedField(slug_field="code", read_only=True)
    registration_gate = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = VisitRequest
        fields = [
            "reference", "status", "status_display", "channel", "lane", "purpose", "purpose_details",
            "scheduled_start", "scheduled_end", "is_urgent", "visitor", "host", "requested_zones", "visit_pass",
            "submitted_at", "approval_deadline", "contingency_deadline", "decided_at", "special_instructions",
            "decision_notes", "rejection_reason", "check_in_at", "check_out_at", "checkout_method", "entry_gate",
            "registration_gate", "host_unavailable", "last_seen_zone", "last_seen_at", "terminated_at",
            "termination_reason", "watchlist_flag", "event", "policy_snapshot",
        ]

    def get_visitor(self, obj):
        v = obj.visitor
        return {"name": v.full_name, "phone": v.phone, "email": v.email, "organization": v.organization,
                "id_doc_type": v.id_doc_type, "id_doc_number": mask(v.id_doc_number),
                "photo": v.photo.url if v.photo else None}

    def get_host(self, obj):
        return _host_dict(obj.host)

    def get_requested_zones(self, obj):
        return _codes(obj.requested_zones)

    def get_visit_pass(self, obj):
        visit_pass = getattr(obj, "visit_pass", None)
        return StaffPassSerializer(visit_pass).data if visit_pass else None


class VisitorVisitSerializer(VisitSerializer):
    """VMS-UC-011 visitor's own view."""

    class Meta(VisitSerializer.Meta):
        fields = ["reference", "status", "status_display", "channel", "purpose", "purpose_details",
                  "scheduled_start", "scheduled_end", "host", "requested_zones", "visit_pass", "submitted_at",
                  "decided_at", "special_instructions", "rejection_reason", "check_in_at", "check_out_at"]

    def get_visit_pass(self, obj):
        visit_pass = getattr(obj, "visit_pass", None)
        return VisitorPassSerializer(visit_pass).data if visit_pass else None


class HistorySerializer(serializers.ModelSerializer):
    actor = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = VisitStateHistory
        fields = ["from_status", "to_status", "transition_ref", "uc_ref", "actor", "actor_role", "note", "created_at"]


class VisitLogSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True, default=None)
    gate = serializers.SlugRelatedField(slug_field="code", read_only=True)
    zone = serializers.SlugRelatedField(slug_field="code", read_only=True)
    recorded_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = VisitLog
        fields = ["id", "reference", "log_type", "method", "occurred_at", "gate", "zone", "device_id",
                  "recorded_by", "detail", "is_manual", "is_offline", "hostel_area"]


class GateAttemptSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True, default=None)
    gate = serializers.SlugRelatedField(slug_field="code", read_only=True)
    attempted_by = serializers.SlugRelatedField(slug_field="username", read_only=True)
    override_decided_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = GateAttempt
        fields = ["id", "reference", "gate", "device_id", "credential_type", "credential_hint", "lane", "status",
                  "failure_reasons", "override_eligible", "flagged", "attempted_by", "attempted_at",
                  "override_requested_at", "escalation_note", "override_decided_by", "override_decided_at",
                  "override_justification"]


class NotificationSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True, default=None)

    class Meta:
        model = VmsNotification
        fields = ["id", "event_type", "title", "message", "reference", "delivery", "created_at", "read_at"]


class VisitorNotificationSerializer(NotificationSerializer):
    class Meta(NotificationSerializer.Meta):
        fields = ["id", "event_type", "title", "message", "reference", "created_at", "read_at"]


class AlertSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True, default=None)
    zone = serializers.SlugRelatedField(slug_field="code", read_only=True)
    gate = serializers.SlugRelatedField(slug_field="code", read_only=True)
    assigned_to = serializers.SlugRelatedField(slug_field="username", read_only=True)
    handled_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = SecurityAlert
        fields = ["id", "alert_type", "status", "checkpoint", "reference", "zone", "gate", "message", "metadata",
                  "assigned_to", "created_at", "handled_by", "handled_at", "handling_note", "escalated_to_admin"]


class PolicySerializer(serializers.ModelSerializer):
    restricted_zones = serializers.SerializerMethodField()
    based_on = serializers.SlugRelatedField(slug_field="version", read_only=True)

    class Meta:
        model = AccessPolicy
        fields = ["version", "status", "based_on", "visiting_hours_start", "visiting_hours_end",
                  "max_visit_duration_minutes", "walk_in_pass_duration_minutes", "approval_timeout_minutes",
                  "advance_registration_minutes", "contingency_sla_minutes", "reminder_offsets_minutes",
                  "restricted_zones", "notes", "created_at", "published_at"]

    def get_restricted_zones(self, obj):
        return _codes(obj.restricted_zones)


class RegistryEntrySerializer(serializers.ModelSerializer):
    publication_version = serializers.IntegerField(source="publication.version", read_only=True, default=None)

    class Meta:
        model = RegistryEntry
        fields = ["id", "list_type", "state", "revision_of", "full_name", "id_doc_type", "id_doc_number", "phone",
                  "email", "reason", "severity", "expires_at", "is_active", "safelist_scope", "created_at",
                  "publication_version"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    zone = serializers.SlugRelatedField(slug_field="code", read_only=True)
    gate = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = VmsRoleAssignment
        fields = ["id", "user", "role", "scope_type", "zone", "gate", "valid_from", "valid_until", "is_active",
                  "reassigned_from", "ended_at", "end_reason", "created_at"]


class IntegrationSerializer(serializers.ModelSerializer):
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationConfig
        fields = ["key", "is_enabled", "status", "endpoint_url", "settings", "has_api_key", "updated_at"]

    def get_has_api_key(self, obj):
        return bool(obj.api_key_hash)


class VipSerializer(serializers.ModelSerializer):
    zones = serializers.SerializerMethodField()
    visit_reference = serializers.CharField(source="visit.reference", read_only=True, default=None)

    class Meta:
        model = VipPermission
        fields = ["id", "visit_reference", "full_name", "id_doc_type", "id_doc_number", "phone", "email",
                  "bypass_host_approval", "zone_scope", "zones", "valid_from", "valid_until", "notes", "is_active",
                  "granted_at", "revoked_at"]

    def get_zones(self, obj):
        return _codes(obj.zones)


class PreAuthorizationSerializer(serializers.ModelSerializer):
    permitted_zones = serializers.SerializerMethodField()

    class Meta:
        model = PreAuthorization
        fields = ["id", "full_name", "id_doc_type", "id_doc_number", "phone", "email", "purpose", "valid_from",
                  "valid_until", "permitted_zones", "notes", "is_active", "revoked_at", "created_at"]

    def get_permitted_zones(self, obj):
        return _codes(obj.permitted_zones)


class EventSerializer(serializers.ModelSerializer):
    venue_zones = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()

    class Meta:
        model = VisitorEvent
        fields = ["id", "name", "external_event_ref", "host", "venue_zones", "starts_at", "ends_at", "status",
                  "fast_lane_enabled", "overflow_walk_in_enabled", "walk_in_rate_limit_per_hour"]

    def get_venue_zones(self, obj):
        return _codes(obj.venue_zones)

    def get_host(self, obj):
        return _host_dict(obj.host)


class BulkListSerializer(serializers.ModelSerializer):
    zones = serializers.SerializerMethodField()

    class Meta:
        model = BulkVisitorList
        fields = ["id", "kind", "event", "valid_from", "valid_until", "zones", "rows_total", "rows_accepted",
                  "rows_rejected", "row_errors", "uploaded_at"]

    def get_zones(self, obj):
        return _codes(obj.zones)


class ExtensionSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True)
    requested_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = ExtensionRequest
        fields = ["id", "reference", "requested_by", "requested_by_role", "current_valid_until",
                  "requested_valid_until", "reason", "status", "decided_at", "decision_note", "created_at"]


class RosterEntrySerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True)

    class Meta:
        model = MusterRosterEntry
        fields = ["id", "reference", "visitor_name", "visitor_phone", "visitor_email", "host_name", "host_contact",
                  "last_seen_zone", "last_seen_at", "status", "in_live_roster", "in_cached_roster", "discrepancy",
                  "note", "updated_at"]


class MusterSerializer(serializers.ModelSerializer):
    roster = RosterEntrySerializer(many=True, read_only=True)

    class Meta:
        model = EmergencyMuster
        fields = ["id", "status", "triggered_by_role", "triggered_at", "assembly_instructions", "roster_source",
                  "roster_incomplete", "roster_note", "finalized_at", "report", "roster"]


class OfflineEventSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="visit.reference", read_only=True, default=None)

    class Meta:
        model = OfflineGateEvent
        fields = ["id", "client_event_id", "event_type", "credential_type", "occurred_at", "status",
                  "conflict_reason", "reference", "reconciled_at", "reviewed_at", "review_note"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.SlugRelatedField(slug_field="username", read_only=True)
    visitor = serializers.CharField(source="visitor.full_name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ["id", "created_at", "actor", "actor_role", "action", "entity_type", "entity_id", "visitor",
                  "message", "metadata"]
