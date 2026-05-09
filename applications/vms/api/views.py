from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from ..permissions import (
    CanBypassVIPApproval,
    CanRemoveBlacklist,
    IsSuperAdmin,
    IsVmsAdmin,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_MAX_LIST_LIMIT = 200


def _safe_limit(request, default: int) -> int:
    """Parse ?limit=N from query params, clamped to [1, _MAX_LIST_LIMIT]."""
    raw = request.query_params.get("limit", default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value < 1:
        return default
    return min(value, _MAX_LIST_LIMIT)


class VmsRegisterThrottle(UserRateThrottle):
    scope = "vms_register"
    rate = "30/min"
from ..selectors import (
    get_active_blacklist,
    get_active_visitors,
    get_all_config,
    get_all_zones,
    get_blacklist_audit_trail,
    get_config_change_history,
    get_data_operations,
    get_incident_history_for_visitor,
    get_incidents,
    get_overstaying_visitors,
    get_recent_visits,
    get_visitor_full_history,
    get_visitor_location_trail,
    get_visiting_hours,
    get_active_vip_visits,
    get_vip_activity_log,
    get_active_escorts,
    get_available_escorts,
)
from ..services import (
    ConfigError,
    DataOperationError,
    RegistrationError,
    WorkflowError,
    add_to_blacklist,
    assign_escort,
    configure_access_zone,
    configure_visiting_hours,
    deny_entry,
    export_visitor_data,
    generate_report,
    get_visitor_history,
    import_visitor_data,
    issue_pass,
    log_incident,
    manual_pass_verification,
    process_vip_visit,
    record_entry,
    record_exit,
    register_visitor,
    release_escort,
    remove_from_blacklist,
    scan_visitor_pass,
    update_config,
    verify_visitor,
)
from .serializers import (
    AccessZoneCreateSerializer,
    AccessZoneSerializer,
    BlacklistAuditLogSerializer,
    BlacklistCreateSerializer,
    BlacklistEntrySerializer,
    ConfigChangeLogSerializer,
    ConfigUpdateSerializer,
    DataExportSerializer,
    DataImportSerializer,
    DataOperationLogSerializer,
    DenialLogSerializer,
    DenyEntrySerializer,
    EscortAssignmentSerializer,
    EscortAssignSerializer,
    IssuePassSerializer,
    ManualVerificationSerializer,
    RecordMovementSerializer,
    RegisterVisitorSerializer,
    ReportRequestSerializer,
    ScanPassSerializer,
    ScanResultSerializer,
    SecurityIncidentCreateSerializer,
    SecurityIncidentSerializer,
    SystemConfigSerializer,
    VIPActivityLogSerializer,
    VIPProcessSerializer,
    VerifyVisitorSerializer,
    VisitingHoursCreateSerializer,
    VisitingHoursSerializer,
    VisitSerializer,
    VisitorLocationSerializer,
    VisitorPassSerializer,
    VisitorSerializer,
)


class RegisterVisitorView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [VmsRegisterThrottle]

    def post(self, request):
        serializer = RegisterVisitorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            visitor, visit = register_visitor(serializer.validated_data)
        except RegistrationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "visit_id": visit.id,
                "visitor": VisitorSerializer(visitor).data,
                "status": visit.status,
                "registered_at": visit.registered_at,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyVisitorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyVisitorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            visit = verify_visitor(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Verification successful.", "visit_status": visit.status})


class IssuePassView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IssuePassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            visit, visitor_pass, qr_data_uri = issue_pass(serializer.validated_data)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Pass issued",
            "visit_status": visit.status,
            "pass": VisitorPassSerializer(visitor_pass).data,
            "qr_code": qr_data_uri,
        })


class RecordEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            visit = record_entry(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Entry recorded", "visit_status": visit.status})


class RecordExitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            visit = record_exit(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Exit recorded", "visit_status": visit.status})


class DenyEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DenyEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _visit, denial = deny_entry(serializer.validated_data)
        return Response({"detail": "Entry denied", "denial": DenialLogSerializer(denial).data})


class ActiveVisitorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active = get_active_visitors()
        return Response(VisitSerializer(active, many=True).data)


class RecentVisitsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = _safe_limit(request, default=5)
        recent = get_recent_visits(limit=limit)
        return Response(VisitSerializer(recent, many=True).data)


class SecurityIncidentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = _safe_limit(request, default=20)
        incidents = get_incidents(limit=limit)
        return Response(SecurityIncidentSerializer(incidents, many=True).data)

    def post(self, request):
        serializer = SecurityIncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        incident = log_incident(serializer.validated_data, request.user)
        return Response(SecurityIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


# ============================================================================
# BR-019/020/021: Pass scan & validation
# ============================================================================
class ScanPassView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScanPassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            visit, result = scan_visitor_pass(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Scan successful", "result": result})


# ============================================================================
# BR-023: Manual verification fallback
# ============================================================================
class ManualVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ManualVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit = manual_pass_verification(serializer.validated_data, request.user)
        return Response({"detail": "Manual verification recorded", "visit_status": visit.status})


# ============================================================================
# BR-030–035: Blacklist management
# ============================================================================
class BlacklistView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsVmsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        entries = get_active_blacklist()
        return Response(BlacklistEntrySerializer(entries, many=True).data)

    def post(self, request):
        serializer = BlacklistCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = add_to_blacklist(serializer.validated_data, request.user)
        return Response(BlacklistEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class BlacklistRemoveView(APIView):
    permission_classes = [IsAuthenticated, CanRemoveBlacklist]

    def post(self, request, entry_id):
        entry = remove_from_blacklist(entry_id, request.user)
        return Response({"detail": f"Blacklist entry {entry.id_number} deactivated."})


class BlacklistAuditView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request, id_number):
        trail = get_blacklist_audit_trail(id_number)
        return Response(BlacklistAuditLogSerializer(trail, many=True).data)


# ============================================================================
# BR-030/031: Visitor & incident history (full PII — admin only)
# ============================================================================
class VisitorHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request, id_number):
        history = get_visitor_full_history(id_number)
        if history["visitor"] is None:
            return Response({"detail": "Visitor not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "visitor": VisitorSerializer(history["visitor"]).data,
            "visits": VisitSerializer(history["visits"], many=True).data,
            "incidents": SecurityIncidentSerializer(history["incidents"], many=True).data,
            "blacklist": BlacklistEntrySerializer(history["blacklist"], many=True).data,
        })


class WhoAmIView(APIView):
    """Return the current user's VMS authority level.

    Any authenticated user may call this; used by the frontend to render
    a role badge in the navbar and to conditionally show admin affordances.
    Returns {authority_level, can_approve_vip, is_vms_admin, is_super_admin}.
    No HostAuthority row → authority_level is null and both flags are false.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..models import HostAuthority

        authority = HostAuthority.objects.filter(user=request.user).first()
        level = authority.authority_level if authority else None
        return Response({
            "username": request.user.username,
            "authority_level": level,
            "can_approve_vip": bool(authority and authority.can_approve_vip),
            "is_vms_admin": level in (
                HostAuthority.LEVEL_ADMIN,
                HostAuthority.LEVEL_SUPER,
            ),
            "is_super_admin": level == HostAuthority.LEVEL_SUPER,
        })


class VisitorHistoryByVisitView(APIView):
    """Resolve a Visit ID → visitor → full history.

    Admin-only sister endpoint to VisitorHistoryView that lets the frontend
    use the Visit ID shown in Visitor Records (list responses mask the raw
    id_number so it can't be resolved client-side).
    """

    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request, visit_id):
        from ..models import Visit

        visit = Visit.objects.select_related("visitor").filter(id=visit_id).first()
        if visit is None:
            return Response(
                {"detail": f"Visit with id={visit_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        history = get_visitor_full_history(visit.visitor.id_number)
        if history["visitor"] is None:
            return Response(
                {"detail": "Visitor not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            "visitor": VisitorSerializer(history["visitor"]).data,
            "visits": VisitSerializer(history["visits"], many=True).data,
            "incidents": SecurityIncidentSerializer(history["incidents"], many=True).data,
            "blacklist": BlacklistEntrySerializer(history["blacklist"], many=True).data,
        })


class IncidentHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request, id_number):
        incidents = get_incident_history_for_visitor(id_number)
        return Response(SecurityIncidentSerializer(incidents, many=True).data)


# ============================================================================
# BR-041–047: VIP visitor processing
# ============================================================================
class VIPProcessView(APIView):
    """Mark a visit as VIP and optionally bypass verification.

    Plain VIP flagging requires IsVmsAdmin: marking a visit as VIP grants
    the +60-minute pass bonus, emits VIP arrival notifications, and
    creates VIPActivityLog rows — privileged state changes.

    `bypass_approval=True` additionally requires CanBypassVIPApproval
    (the `can_approve_vip` flag on HostAuthority).
    """

    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def post(self, request):
        serializer = VIPProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Approval bypass is privileged: only hosts with the explicit VIP
        # bypass authority may skip the standard verification flow.
        if serializer.validated_data.get("bypass_approval"):
            if not CanBypassVIPApproval().has_permission(request, self):
                raise PermissionDenied("Not authorised for VIP approval bypass.")

        visit, auto_escort = process_vip_visit(
            serializer.validated_data, request.user
        )
        payload = {
            "detail": "VIP processing complete",
            "visit": VisitSerializer(visit).data,
            "auto_escort": (
                EscortAssignmentSerializer(auto_escort).data if auto_escort else None
            ),
        }
        return Response(payload)


class VIPVisitorsView(APIView):
    """List active VIP visits. Admin-only — reveals VIP presence/schedule."""

    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request):
        visits = get_active_vip_visits()
        return Response(VisitSerializer(visits, many=True).data)


class EscortAssignView(APIView):
    """Manage escort assignments (BR-046). Staff-accessible: gate officers
    coordinate escorts directly when a high-level VIP arrives, so assignment
    must be available to the security-staff tier rather than admin-only."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        escorts = get_active_escorts()
        return Response(EscortAssignmentSerializer(escorts, many=True).data)

    def post(self, request):
        serializer = EscortAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = assign_escort(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            EscortAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )


class EscortReleaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        assignment = release_escort(assignment_id, request.user)
        return Response({"detail": "Escort released", "released_at": assignment.released_at})


class AvailableEscortsView(APIView):
    """BR-046: List qualified escort personnel who are currently available."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        escorts = get_available_escorts()
        data = [
            {
                "id": e.id,
                "name": (
                    getattr(e.user, "get_full_name", lambda: "")()
                    or getattr(e.user, "username", "")
                ),
                "department": getattr(
                    getattr(e, "department", None), "name", ""
                ),
            }
            for e in escorts
        ]
        return Response(data)


class VIPActivityView(APIView):
    """VIP-specific movement log for a given visit. Admin-only — sensitive
    VIP movement data (BR-047)."""

    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request, visit_id):
        logs = get_vip_activity_log(visit_id)
        return Response(VIPActivityLogSerializer(logs, many=True).data)


# ============================================================================
# BR-025–029: Report generation
# ============================================================================
class ReportGenerationView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def post(self, request):
        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report = generate_report(serializer.validated_data, request.user)
        except WorkflowError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(report)


# ============================================================================
# BR-024: Overstay detection
# ============================================================================
class OverstayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        visits = get_overstaying_visitors()
        return Response(VisitSerializer(visits, many=True).data)


# ============================================================================
# BR-036–040: Location tracking
# ============================================================================
class VisitorLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, visit_id):
        trail = get_visitor_location_trail(visit_id)
        return Response(VisitorLocationSerializer(trail, many=True).data)


# ============================================================================
# BR-057–066: System configuration
# ============================================================================
class SystemConfigView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        configs = get_all_config()
        return Response(SystemConfigSerializer(configs, many=True).data)

    def post(self, request):
        serializer = ConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            config = update_config(
                serializer.validated_data["key"],
                serializer.validated_data["value"],
                request.user,
                serializer.validated_data.get("description", ""),
            )
        except ConfigError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SystemConfigSerializer(config).data)


class ConfigChangeHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        key = request.query_params.get("key")
        history = get_config_change_history(key=key)
        return Response(ConfigChangeLogSerializer(history, many=True).data)


# ============================================================================
# BR-063: Visiting hours
# ============================================================================
class VisitingHoursView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsVmsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        hours = get_visiting_hours()
        return Response(VisitingHoursSerializer(hours, many=True).data)

    def post(self, request):
        serializer = VisitingHoursCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hours = configure_visiting_hours(serializer.validated_data)
        return Response(VisitingHoursSerializer(hours).data, status=status.HTTP_201_CREATED)


# ============================================================================
# BR-064: Access zones
# ============================================================================
class AccessZoneView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsVmsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        zones = get_all_zones()
        return Response(AccessZoneSerializer(zones, many=True).data)

    def post(self, request):
        serializer = AccessZoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zone = configure_access_zone(serializer.validated_data)
        return Response(AccessZoneSerializer(zone).data, status=status.HTTP_201_CREATED)


# ============================================================================
# BR-067–074: Data export / import
# ============================================================================
class DataExportView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def post(self, request):
        serializer = DataExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result, op_log = export_visitor_data(serializer.validated_data, request.user)
        except DataOperationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "detail": op_log.result_summary,
            "operation_id": op_log.id,
            "data": result,
        })


class DataImportView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def post(self, request):
        serializer = DataImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            visitors, op_log = import_visitor_data(
                serializer.validated_data["data_content"],
                serializer.validated_data["format"],
                serializer.validated_data["field_mapping"],
                request.user,
            )
        except DataOperationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "detail": op_log.result_summary,
            "operation_id": op_log.id,
            "records_processed": op_log.records_processed,
        }, status=status.HTTP_201_CREATED)


class DataOperationsView(APIView):
    permission_classes = [IsAuthenticated, IsVmsAdmin]

    def get(self, request):
        ops = get_data_operations()
        return Response(DataOperationLogSerializer(ops, many=True).data)
