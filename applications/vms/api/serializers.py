from datetime import date

from rest_framework import serializers

from ..models import (
    AccessZone,
    BlacklistAuditLog,
    BlacklistEntry,
    ConfigChangeLog,
    DataOperationLog,
    DenialLog,
    EntryExitLog,
    EscortAssignment,
    HostAuthority,
    RegistrationQuota,
    SecurityIncident,
    SystemConfig,
    VIPActivityLog,
    VerificationLog,
    Visit,
    Visitor,
    VisitorLocation,
    VisitorPass,
    VisitorRequest,
    VisitingHours,
)


class VisitorSerializer(serializers.ModelSerializer):
    """Full visitor record. Use only for admin endpoints (visitor history, etc.)."""

    class Meta:
        model = Visitor
        fields = "__all__"


def _mask_id_number(value: str) -> str:
    """Return only the last 4 chars of an ID, masking the rest."""
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


class VisitorPublicSerializer(serializers.ModelSerializer):
    """Slimmed visitor view for list endpoints — no raw PII."""

    id_number = serializers.SerializerMethodField()

    class Meta:
        model = Visitor
        fields = ("id", "full_name", "id_type", "id_number")

    def get_id_number(self, obj):
        return _mask_id_number(obj.id_number)


class VisitSerializer(serializers.ModelSerializer):
    visitor = VisitorPublicSerializer()
    gate_name = serializers.SerializerMethodField()
    authorized_zones = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = "__all__"

    def get_gate_name(self, obj):
        last_log = obj.movement_logs.order_by("-created_at").first()
        return last_log.gate_name if last_log else ""

    def get_authorized_zones(self, obj):
        try:
            return obj.visitor_pass.authorized_zones
        except VisitorPass.DoesNotExist:
            return ""


class VisitorPassSerializer(serializers.ModelSerializer):
    """Pass record without the raw QR data URI — fetched separately on issue."""

    class Meta:
        model = VisitorPass
        exclude = ("barcode_data",)


class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationLog
        fields = "__all__"


class DenialLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialLog
        fields = "__all__"


class EntryExitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryExitLog
        fields = "__all__"


class SecurityIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityIncident
        fields = "__all__"


class RegisterVisitorSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    id_number = serializers.CharField()
    id_type = serializers.ChoiceField(choices=Visitor.ID_TYPES)
    contact_phone = serializers.CharField()
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    photo_reference = serializers.CharField(required=False, allow_blank=True)
    purpose = serializers.CharField()
    host_name = serializers.CharField()
    host_department = serializers.CharField()
    host_contact = serializers.CharField(required=False, allow_blank=True)
    expected_duration_minutes = serializers.IntegerField(min_value=5, default=60)
    is_vip = serializers.BooleanField(default=False)
    # BR-046: optional numeric VIP level at registration time so Staff can
    # flag a visit as escort-eligible (>= configured escort_threshold) without
    # a separate VIP-process step. Defaults to 0 (non-VIP).
    vip_level = serializers.IntegerField(
        required=False, min_value=0, max_value=10, default=0
    )


class VerifyVisitorSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=VerificationLog.METHODS, default=VerificationLog.METHOD_MANUAL)
    result = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)


class IssuePassSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    authorized_zones = serializers.CharField(default="public")


class RecordMovementSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    gate_name = serializers.CharField()
    items_declared = serializers.CharField(required=False, allow_blank=True)


class DenyEntrySerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    reason = serializers.CharField()
    remarks = serializers.CharField(required=False, allow_blank=True)
    escalated = serializers.BooleanField(default=False)


class SecurityIncidentCreateSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField(required=False)
    visitor_id = serializers.IntegerField(required=False)
    severity = serializers.ChoiceField(choices=SecurityIncident.SEVERITIES)
    issue_type = serializers.ChoiceField(choices=SecurityIncident.ISSUE_TYPES)
    description = serializers.CharField()


# ============================================================================
# New serializers for missing BR / UC / WF coverage
# ============================================================================

# --- Pass scan (BR-019/020/021) ---
class ScanPassSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    checkpoint_name = serializers.CharField()
    zone_name = serializers.CharField(required=False, allow_blank=True)
    items_declared = serializers.CharField(required=False, allow_blank=True)


class ScanResultSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    pass_number = serializers.CharField()
    visitor = serializers.CharField()
    zones = serializers.CharField()
    valid_until = serializers.CharField()


# --- Manual verification (BR-023) ---
class ManualVerificationSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    result = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True)


# --- Blacklist management (BR-030–035) ---
class BlacklistCreateSerializer(serializers.Serializer):
    # Accept either the raw id_number OR a visit_id that resolves to one.
    # Exactly one of the two must be supplied.
    id_number = serializers.CharField(required=False, allow_blank=True)
    visit_id = serializers.IntegerField(required=False, allow_null=True)
    reason = serializers.CharField()
    evidence = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        id_number = (attrs.get("id_number") or "").strip()
        visit_id = attrs.get("visit_id")
        if not id_number and not visit_id:
            raise serializers.ValidationError(
                "Provide either id_number or visit_id."
            )
        if visit_id and not id_number:
            from ..models import Visit
            try:
                visit = Visit.objects.select_related("visitor").get(id=visit_id)
            except Visit.DoesNotExist as exc:
                raise serializers.ValidationError(
                    f"Visit id={visit_id} not found."
                ) from exc
            attrs["id_number"] = visit.visitor.id_number
        else:
            attrs["id_number"] = id_number
        return attrs


class BlacklistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistEntry
        fields = "__all__"


class BlacklistAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistAuditLog
        fields = "__all__"


# --- Visitor history (BR-030/031) ---
class VisitorHistorySerializer(serializers.Serializer):
    visitor = VisitorSerializer()
    visits = VisitSerializer(many=True)
    incidents = SecurityIncidentSerializer(many=True)
    blacklist_entries = BlacklistEntrySerializer(many=True)


# --- VIP processing (BR-041–047) ---
class VIPProcessSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    bypass_approval = serializers.BooleanField(default=False)
    # BR-046: numeric VIP level drives escort auto-assignment.
    vip_level = serializers.IntegerField(
        required=False, min_value=0, max_value=10
    )
    # Optional specific escort for auto-assignment at VIP processing time.
    escort_id = serializers.IntegerField(required=False, allow_null=True)


class EscortAssignSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()
    # BR-046: optional — when omitted the service auto-picks an available
    # qualified escort.
    escort_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class EscortAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscortAssignment
        fields = "__all__"


class VIPActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIPActivityLog
        fields = "__all__"


# --- Report generation (BR-025–029) ---
class ReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=["visitor_summary", "incident_summary", "access_log", "vip_report", "full_audit"]
    )
    start_date = serializers.DateField()
    end_date = serializers.DateField()


# --- System config (BR-057–066) ---
class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = "__all__"


class ConfigUpdateSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class ConfigChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigChangeLog
        fields = "__all__"


# --- Visiting hours (BR-063) ---
class VisitingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitingHours
        fields = "__all__"


class VisitingHoursCreateSerializer(serializers.Serializer):
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_holiday = serializers.BooleanField(default=False)
    holiday_name = serializers.CharField(required=False, allow_blank=True)
    active = serializers.BooleanField(default=True)


# --- Access zones (BR-064) ---
class AccessZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessZone
        fields = "__all__"


class AccessZoneCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    requires_vip = serializers.BooleanField(default=False)
    requires_escort = serializers.BooleanField(default=False)
    is_restricted = serializers.BooleanField(default=False)
    active = serializers.BooleanField(default=True)


# --- Location tracking (BR-036–040) ---
class VisitorLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorLocation
        fields = "__all__"


# --- Data export/import (BR-067–074) ---
class DataExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=["csv", "json", "xlsx"], default="csv")
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class DataImportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=["csv", "json"], default="csv")
    data_content = serializers.CharField()
    field_mapping = serializers.DictField(child=serializers.CharField())


class DataOperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataOperationLog
        fields = "__all__"


# --- Request ID (BR-005) ---
class VisitorRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorRequest
        fields = "__all__"


# --- Host authority (BR-011) ---
class HostAuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = HostAuthority
        fields = "__all__"
