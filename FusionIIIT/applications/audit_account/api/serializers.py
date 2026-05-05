from rest_framework import serializers

from applications.audit_account.models import (
    ActionLog,
    AuditObservation,
    ObservationAttachment,
    ObservationAttachmentKind,
    Request,
    TravelAllowance,
)

FINANCE_ROLES = {
    "finance",
    "finance staff",
    "accounts",
    "accounts staff",
    "accountant",
    "accounts admin",
    "administrator",
    "adminstrator",
    "admin",
}
DEAN_ROLES = {"dean academic", "dean_s", "dean_rspc", "dean (p&d)", "dean (r&d)", "dean"}
DIRECTOR_ROLES = {"director"}
HOD_ROLES = {"hod", "head of department", "dept_admin", "department admin"}


class ActionLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ActionLog
        fields = "__all__"

    def get_actor_name(self, obj):
        if not obj.actor:
            return "System"
        return obj.actor.get_full_name() or obj.actor.username


class RequestSerializer(serializers.ModelSerializer):
    creator_name = serializers.SerializerMethodField()
    action_logs = ActionLogSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "created_by_user",
            "created_at",
            "updated_at",
            "processed_at",
            "closed_at",
            "current_approver_role",
            "anomaly_reason",
        ]

    def get_creator_name(self, obj):
        if not obj.created_by_user:
            return str(obj.created_by)
        return obj.created_by_user.get_full_name() or obj.created_by_user.username

    def get_attachments(self, obj):
        return GenericAttachmentSerializer(obj.attachments.all(), many=True).data


class TravelAllowanceSerializer(serializers.ModelSerializer):
    employee_username = serializers.SerializerMethodField()
    action_logs = ActionLogSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = TravelAllowance
        fields = "__all__"
        read_only_fields = [
            "id",
            "employee",
            "employee_name",
            "status",
            "high_value",
            "created_at",
            "updated_at",
            "closed_at",
        ]

    def get_employee_username(self, obj):
        if not obj.employee:
            return obj.employee_name
        return obj.employee.get_full_name() or obj.employee.username

    def get_attachments(self, obj):
        return GenericAttachmentSerializer(obj.attachments.all(), many=True).data


class AuditObservationSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.SerializerMethodField()
    responded_by_name = serializers.SerializerMethodField()
    closed_by_name = serializers.SerializerMethodField()
    action_logs = ActionLogSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()
    response_attachments = serializers.SerializerMethodField()
    can_respond = serializers.SerializerMethodField()

    class Meta:
        model = AuditObservation
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "raised_by",
            "responded_by",
            "closed_by",
            "created_at",
            "updated_at",
            "closed_at",
        ]

    def get_raised_by_name(self, obj):
        return _display_user(obj.raised_by)

    def get_responded_by_name(self, obj):
        return _display_user(obj.responded_by)

    def get_closed_by_name(self, obj):
        return _display_user(obj.closed_by)

    def get_attachments(self, obj):
        files = obj.attachments.filter(
            attachment_kind=ObservationAttachmentKind.OBSERVATION
        )
        return GenericAttachmentSerializer(files, many=True).data

    def get_response_attachments(self, obj):
        files = obj.attachments.filter(
            attachment_kind=ObservationAttachmentKind.RESPONSE
        )
        return GenericAttachmentSerializer(files, many=True).data

    def get_can_respond(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False
        if obj.request:
            if obj.request.created_by == user.id:
                return True
            return _request_role_allowed(user, obj.request.current_approver_role or "finance")
        if obj.travel_allowance:
            if obj.travel_allowance.employee_id == user.id:
                return True
            return _request_role_allowed(
                user, obj.travel_allowance.current_approver_role or "finance"
            )
        return False


class GenericAttachmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    original_name = serializers.CharField(read_only=True)
    file = serializers.FileField(read_only=True)
    file_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    attachment_kind = serializers.CharField(read_only=True, required=False)

    def get_file_url(self, obj):
        try:
            return f"/{obj.file.name}"
        except ValueError:
            return ""


def _display_user(user):
    if not user:
        return ""
    return user.get_full_name() or user.username


def _normalize_role(role):
    return role.strip().lower() if isinstance(role, str) else ""


def _roles_for_user(user):
    roles = list(user.current_designation.all().values_list("designation__name", flat=True))
    user_type = getattr(getattr(user, "extrainfo", None), "user_type", None)
    if user_type:
        roles.append(user_type)
    if user.is_staff:
        roles.append("administrator")
    return {_normalize_role(role) for role in roles if role}


def _request_role_allowed(user, role):
    roles = _roles_for_user(user)
    normalized = _normalize_role(role)
    if normalized == "finance":
        return bool(roles & FINANCE_ROLES)
    if normalized == "hod":
        return bool(roles & (HOD_ROLES | DEAN_ROLES | DIRECTOR_ROLES))
    if normalized == "dean":
        return bool(roles & (DEAN_ROLES | DIRECTOR_ROLES))
    if normalized == "director":
        return bool(roles & DIRECTOR_ROLES)
    return False
