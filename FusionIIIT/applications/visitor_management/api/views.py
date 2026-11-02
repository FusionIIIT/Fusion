"""VMS REST API (DRF, Token/Session auth as configured for Fusion).

Routes are mounted under ``/vms/`` (see Fusion/urls.py) so every path here is
``/vms/api/...``. Visitors have no Fusion account: public endpoints are
anonymous and throttled, and the visitor portal uses the ``X-Visitor-Token``
header issued at registration. External systems (ACS, Hostel and Event
Management) use ``X-VMS-Integration-Key``.
"""

import functools
import hmac

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from applications.globals.models import ExtraInfo

from .. import selectors
from ..constants import (
    ExtensionStatus,
    GateAttemptStatus,
    IntegrationKey,
    MusterStatus,
    NotificationEvent,
    OfflineEventStatus,
    VisitStatus,
    VmsRole,
)
from ..errors import NotAuthenticated, NotAuthorized, NotFound, ServiceError, Unavailable, ValidationFailed
from ..models import (
    AccessPolicy,
    BulkVisitorList,
    EmergencyMuster,
    ExtensionRequest,
    Gate,
    GateAttempt,
    IntegrationConfig,
    OfflineGateEvent,
    PreAuthorization,
    RegistryEntry,
    RegistryPublication,
    SecurityAlert,
    VipPermission,
    Visitor,
    VisitLog,
    VisitorEvent,
    VisitPass,
    VisitRequest,
    VmsNotification,
    VmsRoleAssignment,
    Zone,
)
from ..services import configuration, emergency, gate as gate_services, lifecycle, registration, reports
from ..services.common import hash_secret
from . import serializers as s


class PublicThrottle(AnonRateThrottle):
    scope = "vms_public"
    rate = "30/min"


class IntegrationThrottle(AnonRateThrottle):
    """Door readers and turnstiles call far more often than people do."""

    scope = "vms_integration"
    rate = "600/min"


def handle_errors(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except ServiceError as exc:
            return Response(exc.as_dict(), status=exc.status_code)
    return wrapper


def public(methods):
    """Anonymous endpoint, throttled, no session (so no CSRF dependency)."""
    def decorator(view):
        view = handle_errors(view)
        view = throttle_classes([PublicThrottle])(view)
        view = permission_classes([AllowAny])(view)
        view = authentication_classes([])(view)
        return api_view(methods)(view)
    return decorator


def integration(methods):
    """External system endpoint authenticated by X-VMS-Integration-Key."""
    def decorator(view):
        view = handle_errors(view)
        view = throttle_classes([IntegrationThrottle])(view)
        view = permission_classes([AllowAny])(view)
        view = authentication_classes([])(view)
        return api_view(methods)(view)
    return decorator


def staff(methods):
    """Authenticated Fusion user (DEFAULT_PERMISSION_CLASSES = IsAuthenticated)."""
    def decorator(view):
        return api_view(methods)(handle_errors(view))
    return decorator


def parse(serializer_class, request, partial=False):
    serializer = serializer_class(data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def paginate(request, queryset, serializer_class, many_kwargs=None):
    try:
        limit = max(1, min(int(request.query_params.get("limit", 50)), 500))
        offset = max(0, int(request.query_params.get("offset", 0)))
    except ValueError:
        raise ValidationFailed("limit/offset must be integers.")
    total = queryset.count()
    items = queryset[offset:offset + limit]
    return Response({"count": total, "limit": limit, "offset": offset,
                     "results": serializer_class(items, many=True, **(many_kwargs or {})).data})


def file_response(content, filename, content_type):
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
    return response


def require(condition, message):
    if not condition:
        raise NotAuthorized(message)


def visit_or_404(reference):
    visit = VisitRequest.objects.select_related("visitor", "host__user", "host__department").filter(
        reference=reference).first()
    if visit is None:
        raise NotFound("Visit not found.")
    return visit


def current_visitor(request):
    token = request.META.get("HTTP_X_VISITOR_TOKEN", "")
    visitor = Visitor.objects.filter(access_token_hash=hash_secret(token)).first() if token else None
    if visitor is None:
        raise NotAuthenticated("A valid visitor access token is required (X-Visitor-Token).")
    return visitor


def visitor_visit(request, reference):
    visitor = current_visitor(request)
    visit = VisitRequest.objects.select_related("host__user", "host__department").filter(
        reference=reference, visitor=visitor).first()
    if visit is None:  # UC-011 exception: another visitor's records are never shown
        raise NotFound("Visit not found.")
    return visit


def integration_caller(request, key):
    raw = request.META.get("HTTP_X_VMS_INTEGRATION_KEY", "")
    config = IntegrationConfig.objects.filter(key=key).first()
    if not raw or config is None or not config.api_key_hash or not hmac.compare_digest(
            config.api_key_hash, hash_secret(raw)):
        raise NotAuthenticated("A valid integration key is required.")
    if not config.is_usable:
        raise Unavailable("This integration is disabled or unavailable.")
    return config


def is_staff_viewer(user, visit):
    host = selectors.host_extrainfo(user)
    return bool((host and host.pk == visit.host_id) or selectors.is_admin(user) or selectors.is_security(user)
                or selectors.is_super_admin(user))


# ==========================================================================
# Shared
# ==========================================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def module_root(request):
    """Back-compat target for the notification URL name ``vms:vms``."""
    return Response({"module": "Visitor Management System", "api": "/vms/api/"})


@staff(["GET"])
def me(request):
    return Response({"username": request.user.username, "roles": selectors.roles_for(request.user)})


@staff(["GET"])
def zones_list(request):
    return Response(s.ZoneSerializer(Zone.objects.filter(is_active=True), many=True).data)


@staff(["GET"])
def gates_list(request):
    return Response(s.GateSerializer(Gate.objects.filter(is_active=True).select_related("zone"), many=True).data)


@staff(["GET"])
def my_notifications(request):
    user = request.user
    roles = []
    if selectors.is_security(user):
        roles.append(VmsRole.SECURITY)
    if selectors.is_admin(user):
        roles.append(VmsRole.ADMIN)
    query = VmsNotification.objects.filter(Q(recipient_user=user) | Q(recipient_role__in=roles)).select_related("visit")
    if request.query_params.get("unread") in ("1", "true"):
        query = query.filter(read_at__isnull=True)
    return paginate(request, query, s.NotificationSerializer)


@staff(["POST"])
def mark_notification_read(request, notification_id):
    note = VmsNotification.objects.filter(pk=notification_id, recipient_user=request.user).first()
    if note is None:
        raise NotFound("Notification not found.")
    note.read_at = note.read_at or selectors.now()
    note.save(update_fields=["read_at"])
    return Response(s.NotificationSerializer(note).data)


@staff(["GET"])
def visit_detail(request, reference):
    visit = visit_or_404(reference)
    require(is_staff_viewer(request.user, visit), "You cannot view this visit.")
    data = s.VisitSerializer(visit).data
    data["history"] = s.HistorySerializer(visit.history.select_related("actor"), many=True).data
    data["logs"] = s.VisitLogSerializer(visit.logs.select_related("gate", "zone", "recorded_by"), many=True).data
    data["extensions"] = s.ExtensionSerializer(visit.extension_requests.all(), many=True).data
    return Response(data)


@staff(["GET"])
def visit_search(request):
    user = request.user
    require(selectors.is_admin(user) or selectors.is_security(user), "Only Admin or Security can search visits.")
    query = VisitRequest.objects.select_related("visitor", "host__user", "host__department")
    term = request.query_params.get("q")
    if term:
        query = query.filter(Q(reference__icontains=term) | Q(visitor__full_name__icontains=term)
                             | Q(visitor__phone__icontains=term) | Q(visit_pass__pass_number=term.upper()))
    if request.query_params.get("status"):
        query = query.filter(status__in=request.query_params["status"].split(","))
    if request.query_params.get("date"):
        query = query.filter(scheduled_start__date=request.query_params["date"])
    return paginate(request, query, s.VisitSerializer)


@staff(["POST"])
def request_extension(request, reference):
    """VMS-UC-034 entry point (Host of the visit or authorised Admin)."""
    data = parse(s.ExtensionInput, request)
    extension, visit = lifecycle.request_extension(request.user, reference, data["requested_valid_until"],
                                                   data.get("reason", ""))
    if extension is None:
        return Response({"applied": True, "visit": s.VisitSerializer(visit).data})
    return Response({"applied": False, "extension": s.ExtensionSerializer(extension).data},
                    status=status.HTTP_201_CREATED)


@staff(["GET"])
def dashboard(request):
    """VMS-UC-022 (Security Personnel; Admin dashboards per PS 3.5)."""
    require(selectors.is_security(request.user) or selectors.is_admin(request.user),
            "Only Security Personnel or Admin can view the live dashboard.")
    return Response(reports.live_dashboard())


@staff(["GET"])
def audit_logs(request):
    """VMS-UC-004 Review Audit Trails (Super Admin; Admin as supporting actor)."""
    require(selectors.is_super_admin(request.user) or selectors.is_admin(request.user),
            "Only Super Admin or Admin can review audit trails.")
    return paginate(request, reports.audit_queryset(request.query_params), s.AuditLogSerializer)


# ==========================================================================
# Public + Visitor portal (VMS-UC-010, 011, 012, 030, 031)
# ==========================================================================

@public(["GET"])
def public_hosts(request):
    term = (request.query_params.get("q") or "").strip()
    if len(term) < 2:
        return Response([])
    if not selectors.integration_usable(IntegrationKey.CAMPUS_ID, default=True):
        raise Unavailable("Host lookup is currently unavailable.", code="host_lookup_unavailable")
    hosts = ExtraInfo.objects.filter(user_type__in=selectors.HOST_USER_TYPES, user__is_active=True).filter(
        Q(user__first_name__icontains=term) | Q(user__last_name__icontains=term) | Q(id__iexact=term)
    ).select_related("user", "department")[:15]
    return Response([s._host_dict(h) for h in hosts])


@public(["GET"])
def public_zones(request):
    return Response(s.ZoneSerializer(Zone.objects.filter(is_active=True), many=True).data)


@public(["POST"])
def public_pre_register(request):
    data = parse(s.PreRegistrationInput, request)
    token = request.META.get("HTTP_X_VISITOR_TOKEN", "")
    visit, new_token = registration.pre_register(data, visitor_token_hash=hash_secret(token) if token else None)
    payload = {"visit": s.VisitorVisitSerializer(visit).data}
    if new_token:
        payload["visitor_token"] = new_token
    return Response(payload, status=status.HTTP_201_CREATED)


@public(["GET"])
def visitor_visits(request):
    visitor = current_visitor(request)
    visits = visitor.visits.select_related("host__user", "host__department").order_by("-submitted_at")
    return Response({"visitor": visitor.full_name, "results": s.VisitorVisitSerializer(visits, many=True).data})


@public(["GET"])
def visitor_visit_detail(request, reference):
    visit = visitor_visit(request, reference)
    data = s.VisitorVisitSerializer(visit).data
    data["history"] = [{"status": h.to_status, "at": h.created_at} for h in visit.history.all()]
    return Response(data)


@public(["GET"])
def visitor_pass(request, reference):
    visit = visitor_visit(request, reference)
    visit_pass = getattr(visit, "visit_pass", None)
    if visit_pass is None:
        raise NotFound("No pass has been issued for this visit yet.", code="no_pass")
    return Response(s.VisitorPassSerializer(visit_pass).data)


@public(["GET"])
def visitor_pass_pdf(request, reference):
    visit = visitor_visit(request, reference)
    visit_pass = getattr(visit, "visit_pass", None)
    if visit_pass is None:
        raise NotFound("No pass has been issued for this visit yet.", code="no_pass")
    from .pass_pdf import render_pass_pdf
    return file_response(render_pass_pdf(visit, visit_pass), "{}.pdf".format(visit_pass.pass_number),
                         "application/pdf")


@public(["GET"])
def visitor_notifications(request):
    visitor = current_visitor(request)
    return Response(s.VisitorNotificationSerializer(visitor.notifications.select_related("visit")[:200], many=True).data)


@public(["POST"])
def visitor_self_check_out(request, reference):
    visit = visitor_visit(request, reference)
    from ..constants import LogMethod
    gate_services.self_check_out(visit, LogMethod.APP)
    visit.refresh_from_db()
    return Response(s.VisitorVisitSerializer(visit).data)


@public(["POST"])
def kiosk_check_out(request):
    from ..constants import LogMethod
    token = (request.data.get("qr_token") or "").strip()
    visit_pass = VisitPass.objects.select_related("visit").filter(qr_token=token).first() if token else None
    if visit_pass is None:
        raise NotFound("Pass not recognised.", code="unknown_pass")
    visit = gate_services.self_check_out(visit_pass.visit, LogMethod.KIOSK)
    return Response({"reference": visit.reference, "status": visit.status, "check_out_at": visit.check_out_at})


# ==========================================================================
# Host (VMS-UC-013, 014, 015, 016)
# ==========================================================================

def _host(request):
    host = selectors.host_extrainfo(request.user)
    require(host is not None, "Only Faculty/Staff hosts can use this endpoint.")
    return host


@staff(["GET"])
def host_pending_requests(request):
    host = _host(request)
    lifecycle.expire_pending_requests()  # never show a request whose window has passed
    query = VisitRequest.objects.filter(host=host, status=VisitStatus.PENDING_HOST_APPROVAL).select_related(
        "visitor", "host__user", "host__department").order_by("approval_deadline")
    return paginate(request, query, s.VisitSerializer)


@staff(["GET"])
def host_visits(request):
    host = _host(request)
    query = VisitRequest.objects.filter(host=host).select_related("visitor", "host__user", "host__department")
    if request.query_params.get("status"):
        query = query.filter(status__in=request.query_params["status"].split(","))
    return paginate(request, query, s.VisitSerializer)


@staff(["POST"])
def host_decide(request, reference):
    data = parse(s.HostDecisionInput, request)
    visit = registration.decide_visit(request.user, reference, data.pop("decision"), data)
    return Response(s.VisitSerializer(visit).data)


@staff(["POST"])
def host_bulk_decide(request):
    data = parse(s.BulkHostDecisionInput, request)
    references = data.pop("references")
    results = registration.bulk_decide(request.user, references, data.pop("decision"), data)
    return Response({"results": results})


@staff(["GET"])
def host_arrivals(request):
    """VMS-UC-015 View Visitor Arrival Updates."""
    host = _host(request)
    today = selectors.now().date()
    arrivals = VisitRequest.objects.filter(host=host, check_in_at__date=today).select_related(
        "visitor", "host__user", "host__department")
    updates = VmsNotification.objects.filter(recipient_user=request.user, event_type__in=[
        NotificationEvent.VISITOR_CHECKED_IN, NotificationEvent.VISITOR_CHECKED_OUT])[:50]
    return Response({"arrivals_today": s.VisitSerializer(arrivals, many=True).data,
                     "updates": s.NotificationSerializer(updates, many=True).data})


@staff(["GET", "POST"])
def host_preauthorizations(request):
    host = _host(request)
    if request.method == "GET":
        query = PreAuthorization.objects.filter(host=host)
        return paginate(request, query, s.PreAuthorizationSerializer)
    preauth = registration.create_preauthorization(request.user, parse(s.PreAuthorizationInput, request))
    return Response(s.PreAuthorizationSerializer(preauth).data, status=status.HTTP_201_CREATED)


@staff(["POST"])
def host_revoke_preauthorization(request, preauth_id):
    preauth = registration.revoke_preauthorization(request.user, preauth_id)
    return Response(s.PreAuthorizationSerializer(preauth).data)


@staff(["GET", "PUT"])
def host_availability(request):
    host = _host(request)
    if request.method == "GET":
        from ..models import HostProfile
        profile = HostProfile.objects.filter(extra_info=host).first()
        return Response({"is_available": profile.is_available if profile else True,
                         "unavailable_until": profile.unavailable_until if profile else None})
    data = parse(s.AvailabilityInput, request)
    profile = registration.set_host_availability(request.user, data["is_available"], data.get("unavailable_until"))
    return Response({"is_available": profile.is_available, "unavailable_until": profile.unavailable_until})


@staff(["POST"])
def host_terminate(request, reference):
    data = parse(s.TerminateInput, request)
    visit = lifecycle.terminate_visit(request.user, reference, data["reason"], VmsRole.HOST)
    return Response(s.VisitSerializer(visit).data)


# ==========================================================================
# Security Personnel (VMS-UC-017..028)
# ==========================================================================

@staff(["POST"])
def security_walk_in(request):
    visit, token = registration.register_walk_in(request.user, parse(s.WalkInInput, request))
    payload = {"visit": s.VisitSerializer(visit).data}
    if token:
        payload["visitor_token"] = token
    return Response(payload, status=status.HTTP_201_CREATED)


@staff(["POST"])
def security_gate_validate(request):
    result = gate_services.validate_at_gate(request.user, parse(s.GateValidateInput, request))
    return Response(result)


@staff(["POST"])
def security_refer_attempt(request, attempt_id):
    data = parse(s.ReferInput, request)
    attempt = gate_services.refer_attempt(request.user, attempt_id, data.get("note", ""))
    return Response(s.GateAttemptSerializer(attempt).data)


@staff(["POST"])
def security_manual_log(request):
    result = gate_services.record_manual_log(request.user, parse(s.ManualLogInput, request))
    if isinstance(result, VisitRequest):
        return Response(s.VisitSerializer(result).data)
    return Response(s.VisitLogSerializer(result).data, status=status.HTTP_201_CREATED)


@staff(["POST"])
def security_check_out(request):
    visit = gate_services.check_out(request.user, parse(s.CheckOutInput, request))
    return Response(s.VisitSerializer(visit).data)


@staff(["GET"])
def security_offline_snapshot(request):
    return Response(gate_services.offline_snapshot(request.user, request.query_params.get("gate")))


@staff(["POST"])
def security_offline_upload(request):
    events = gate_services.upload_offline_events(request.user, parse(s.OfflineUploadInput, request))
    return Response({"results": s.OfflineEventSerializer(events, many=True).data})


@staff(["POST"])
def security_zone_validate(request):
    return Response(gate_services.validate_zone_access(request.user, parse(s.ZoneValidateInput, request)))


@staff(["GET"])
def security_alerts(request):
    require(selectors.is_security(request.user) or selectors.is_admin(request.user),
            "Only Security Personnel or Admin can view alerts.")
    query = SecurityAlert.objects.select_related("visit", "zone", "gate", "assigned_to", "handled_by")
    wanted = request.query_params.get("status", "OPEN,ESCALATED")
    if wanted != "ALL":
        query = query.filter(status__in=wanted.split(","))
    if request.query_params.get("type"):
        query = query.filter(alert_type=request.query_params["type"])
    return paginate(request, query, s.AlertSerializer)


@staff(["POST"])
def security_handle_alert(request, alert_id):
    data = parse(s.AlertHandleInput, request)
    alert = gate_services.handle_alert(request.user, alert_id, data["outcome"], data["note"])
    return Response(s.AlertSerializer(alert).data)


@staff(["POST"])
def security_escalate(request):
    alert = gate_services.escalate_suspicious_case(request.user, parse(s.EscalateInput, request))
    return Response(s.AlertSerializer(alert).data, status=status.HTTP_201_CREATED)


@staff(["GET"])
def security_expected_arrivals(request):
    require(selectors.is_security(request.user), "Only Security Personnel can view expected arrivals.")
    current = selectors.now()
    query = VisitRequest.objects.filter(status=VisitStatus.PASS_ACTIVE, visit_pass__is_active=True,
                                        visit_pass__valid_until__gte=current,
                                        visit_pass__valid_from__date=current.date()).select_related(
        "visitor", "host__user", "host__department").order_by("visit_pass__valid_from")
    return paginate(request, query, s.VisitSerializer)


# ==========================================================================
# Emergency muster (VMS-UC-026, 027, 032)
# ==========================================================================

@staff(["POST"])
def muster_trigger(request):
    data = parse(s.MusterTriggerInput, request)
    requested = request.data.get("as_role")
    as_role = requested if requested in (VmsRole.ADMIN, VmsRole.SECURITY) else (
        VmsRole.ADMIN if selectors.is_admin(request.user) else VmsRole.SECURITY)
    muster = emergency.trigger_muster(request.user, as_role, data.get("assembly_instructions", ""),
                                      cached_roster=data.get("cached_roster"),
                                      offline_triggered_at=data.get("offline_triggered_at"))
    return Response(s.MusterSerializer(muster).data, status=status.HTTP_201_CREATED)


def _muster_viewer(user):
    require(selectors.is_security(user) or selectors.is_admin(user), "Only Security Personnel or Admin.")


@staff(["GET"])
def muster_active(request):
    _muster_viewer(request.user)
    muster = EmergencyMuster.objects.filter(status=MusterStatus.ACTIVE).first()
    return Response(s.MusterSerializer(muster).data if muster else None)


@staff(["GET"])
def muster_detail(request, muster_id):
    _muster_viewer(request.user)
    muster = EmergencyMuster.objects.filter(pk=muster_id).first()
    if muster is None:
        raise NotFound("Muster not found.")
    return Response(s.MusterSerializer(muster).data)


@staff(["POST"])
def muster_roll_call(request, muster_id):
    data = parse(s.RollCallInput, request)
    applied, skipped = emergency.update_roll_call(request.user, muster_id, data["updates"], data.get("source", "live"))
    return Response({"applied": applied, "skipped": skipped})


@staff(["POST"])
def muster_finalize(request, muster_id):
    muster = emergency.finalize_muster(request.user, muster_id)
    return Response(s.MusterSerializer(muster).data)


@staff(["GET"])
def muster_report(request, muster_id):
    """AFR-137 post-event report (JSON, CSV or PDF)."""
    _muster_viewer(request.user)
    muster = EmergencyMuster.objects.filter(pk=muster_id).first()
    if muster is None:
        raise NotFound("Muster not found.")
    report = muster.report or emergency.build_report(muster)
    fmt = request.query_params.get("export", "json")  # ``format`` is reserved by DRF
    if fmt in ("csv", "pdf"):
        tabular = {"report_type": "emergency_muster", "date_from": report["triggered_at"][:10],
                   "date_to": (report.get("finalized_at") or report["triggered_at"])[:10], "anonymized": False,
                   "rows": s.RosterEntrySerializer(muster.roster.all(), many=True).data}
        tabular["rows"] = [dict(r) for r in tabular["rows"]]
        if fmt == "csv":
            return file_response(reports.export_csv(tabular), "muster-{}.csv".format(muster.pk), "text/csv")
        return file_response(reports.export_pdf(tabular), "muster-{}.pdf".format(muster.pk), "application/pdf")
    return Response(report)


@staff(["GET"])
def muster_roster_snapshot(request):
    """Current on-site roster for the gate device's offline cache (AFR-140)."""
    _muster_viewer(request.user)
    return Response({"generated_at": selectors.now(), "roster": reports.live_dashboard()["roster"]})


# ==========================================================================
# Admin (VMS-UC-005..009, 019, 024, 033..036)
# ==========================================================================

def _admin(request):
    require(selectors.is_admin(request.user), "An active VMS Admin role is required.")


@staff(["GET"])
def admin_exception_queue(request):
    _admin(request)
    query = VisitRequest.objects.filter(status=VisitStatus.PENDING_ADMIN_EXCEPTION).select_related(
        "visitor", "host__user", "host__department")
    return paginate(request, query, s.VisitSerializer)


@staff(["POST"])
def admin_decide_exception(request, reference):
    data = parse(s.AdminDecisionInput, request)
    visit = registration.decide_urgent_exception(request.user, reference, data["decision"], data.get("note", ""))
    return Response(s.VisitSerializer(visit).data)


@staff(["GET"])
def admin_contingency_queue(request):
    _admin(request)
    query = VisitRequest.objects.filter(status=VisitStatus.PENDING_ADMIN_CONTINGENCY).select_related(
        "visitor", "host__user", "host__department").order_by("contingency_deadline")
    return paginate(request, query, s.VisitSerializer)


@staff(["POST"])
def admin_decide_contingency(request, reference):
    data = parse(s.AdminDecisionInput, request)
    visit = registration.decide_contingency(request.user, reference, data["decision"], data.get("note", ""))
    return Response(s.VisitSerializer(visit).data)


@staff(["GET"])
def admin_override_queue(request):
    _admin(request)
    query = GateAttempt.objects.filter(status=GateAttemptStatus.BLOCKED, override_eligible=True).select_related(
        "visit", "gate", "attempted_by")
    return paginate(request, query, s.GateAttemptSerializer)


@staff(["POST"])
def admin_override(request, attempt_id):
    data = parse(s.OverrideInput, request)
    attempt = gate_services.decide_override(request.user, attempt_id, data["decision"], data["justification"])
    return Response(s.GateAttemptSerializer(attempt).data)


@staff(["POST"])
def admin_terminate(request, reference):
    data = parse(s.TerminateInput, request)
    visit = lifecycle.terminate_visit(request.user, reference, data["reason"], VmsRole.ADMIN)
    return Response(s.VisitSerializer(visit).data)


@staff(["POST"])
def admin_zone_elevation(request, reference):
    elevation = gate_services.grant_zone_elevation(request.user, reference, parse(s.ElevationInput, request))
    return Response({"id": elevation.pk, "zones": list(elevation.zones.values_list("code", flat=True)),
                     "valid_from": elevation.valid_from, "valid_until": elevation.valid_until},
                    status=status.HTTP_201_CREATED)


@staff(["GET"])
def admin_extension_queue(request):
    _admin(request)
    query = ExtensionRequest.objects.filter(status=ExtensionStatus.PENDING).select_related("visit", "requested_by")
    return paginate(request, query, s.ExtensionSerializer)


@staff(["POST"])
def admin_decide_extension(request, extension_id):
    data = parse(s.AdminDecisionInput, request)
    extension = lifecycle.decide_extension(request.user, extension_id, data["decision"], data.get("note", ""))
    return Response(s.ExtensionSerializer(extension).data)


# ---- access policies (VMS-UC-005) ----------------------------------------

@staff(["GET", "POST"])
def admin_policies(request):
    _admin(request)
    if request.method == "GET":
        return paginate(request, AccessPolicy.objects.all(), s.PolicySerializer)
    data = parse(s.PolicyInput, request)
    policy = configuration.create_policy_version(request.user, data, data.pop("based_on_version", None))
    return Response(s.PolicySerializer(policy).data, status=status.HTTP_201_CREATED)


@staff(["GET"])
def admin_current_policy(request):
    _admin(request)
    policy = selectors.get_published_policy()
    return Response({"policy": s.PolicySerializer(policy).data if policy else None,
                     "runtime_values": selectors.policy_snapshot(policy)})


@staff(["GET", "PATCH"])
def admin_policy_detail(request, version):
    _admin(request)
    if request.method == "GET":
        policy = AccessPolicy.objects.filter(version=version).first()
        if policy is None:
            raise NotFound("Policy version not found.")
        return Response(s.PolicySerializer(policy).data)
    data = parse(s.PolicyInput, request, partial=True)
    data.pop("based_on_version", None)
    return Response(s.PolicySerializer(configuration.update_policy_draft(request.user, version, data)).data)


@staff(["POST"])
def admin_publish_policy(request, version):
    return Response(s.PolicySerializer(configuration.publish_policy(request.user, version)).data)


# ---- registry (VMS-UC-006) -----------------------------------------------

@staff(["GET", "POST"])
def admin_registry(request):
    _admin(request)
    if request.method == "GET":
        query = RegistryEntry.objects.select_related("publication")
        for param in ("state", "list_type"):
            if request.query_params.get(param):
                query = query.filter(**{param: request.query_params[param]})
        if request.query_params.get("q"):
            term = request.query_params["q"]
            query = query.filter(Q(full_name__icontains=term) | Q(id_doc_number__icontains=term) | Q(phone__icontains=term))
        return paginate(request, query, s.RegistryEntrySerializer)
    entry = configuration.create_registry_entry(request.user, parse(s.RegistryEntryInput, request))
    return Response(s.RegistryEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@staff(["PATCH"])
def admin_registry_entry(request, entry_id):
    entry = configuration.revise_registry_entry(request.user, entry_id, parse(s.RegistryEntryInput, request, partial=True))
    return Response(s.RegistryEntrySerializer(entry).data)


@staff(["POST"])
def admin_registry_discard(request, entry_id):
    return Response(s.RegistryEntrySerializer(configuration.discard_registry_draft(request.user, entry_id)).data)


@staff(["POST"])
def admin_registry_publish(request):
    publication = configuration.publish_registry(request.user, request.data.get("notes", ""))
    return Response({"version": publication.version, "entries_changed": publication.entries_changed,
                     "published_at": publication.published_at})


@staff(["GET"])
def admin_registry_publications(request):
    _admin(request)
    return Response([{"version": p.version, "entries_changed": p.entries_changed, "published_at": p.published_at,
                      "published_by": p.published_by.username if p.published_by else None, "notes": p.notes}
                     for p in RegistryPublication.objects.select_related("published_by")[:100]])


# ---- reports (VMS-UC-007) ------------------------------------------------

@staff(["GET"])
def admin_report(request, report_type):
    _admin(request)
    report = reports.generate_report(report_type, request.query_params)
    fmt = request.query_params.get("export", "json")  # ``format`` is reserved by DRF content negotiation
    if fmt == "csv":
        return file_response(reports.export_csv(report), "vms-{}.csv".format(report_type), "text/csv")
    if fmt == "pdf":
        return file_response(reports.export_pdf(report), "vms-{}.pdf".format(report_type), "application/pdf")
    return Response(report)


# ---- events and bulk lists (VMS-UC-008/009) ------------------------------

@staff(["GET", "POST"])
def admin_events(request):
    _admin(request)
    if request.method == "GET":
        return paginate(request, VisitorEvent.objects.select_related("host__user", "host__department"),
                        s.EventSerializer)
    event = registration.create_event(request.user, parse(s.EventInput, request))
    return Response(s.EventSerializer(event).data, status=status.HTTP_201_CREATED)


@staff(["GET"])
def admin_event_detail(request, event_id):
    _admin(request)
    event = VisitorEvent.objects.filter(pk=event_id).first()
    if event is None:
        raise NotFound("Event not found.")
    data = s.EventSerializer(event).data
    data["attendance"] = reports.event_attendance(event)
    data["bulk_lists"] = s.BulkListSerializer(event.bulk_lists.all(), many=True).data
    return Response(data)


@staff(["POST"])
def admin_event_controls(request, event_id):
    event = registration.configure_event_controls(request.user, event_id, parse(s.EventControlsInput, request))
    return Response(s.EventSerializer(event).data)


@staff(["GET", "POST"])
def admin_bulk_lists(request):
    _admin(request)
    if request.method == "GET":
        return paginate(request, BulkVisitorList.objects.all(), s.BulkListSerializer)
    data = parse(s.BulkUploadInput, request)
    upload = data.pop("file", None)
    rows = data.pop("rows", None) or registration.parse_bulk_file(upload)
    if upload is not None:
        upload.seek(0)
    bulk = registration.process_bulk_list(request.user, data, rows, source_file=upload)
    return Response(s.BulkListSerializer(bulk).data, status=status.HTTP_201_CREATED)


# ---- offline conflicts (VMS-UC-039 review) --------------------------------

@staff(["GET"])
def admin_offline_conflicts(request):
    _admin(request)
    query = OfflineGateEvent.objects.filter(status=OfflineEventStatus.CONFLICT).select_related("visit")
    return paginate(request, query, s.OfflineEventSerializer)


@staff(["POST"])
def admin_review_offline_conflict(request, event_id):
    event = gate_services.review_offline_conflict(request.user, event_id, request.data.get("note", ""))
    return Response(s.OfflineEventSerializer(event).data)


# ---- campus topology (AFR-123 / AFR-213) ----------------------------------

@staff(["GET", "POST"])
def admin_zones(request):
    if request.method == "GET":
        _admin(request)
        return Response(s.ZoneSerializer(Zone.objects.all(), many=True).data)
    configuration.require_campus_admin(request.user)
    serializer = s.ZoneSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    zone = serializer.save()
    from .. import audit
    audit.record(request.user, VmsRole.ADMIN, "ZONE_CREATED", zone, message=zone.code)
    return Response(s.ZoneSerializer(zone).data, status=status.HTTP_201_CREATED)


@staff(["PATCH"])
def admin_zone_detail(request, code):
    configuration.require_campus_admin(request.user)
    zone = Zone.objects.filter(code=code).first()
    if zone is None:
        raise NotFound("Zone not found.")
    serializer = s.ZoneSerializer(zone, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    zone = serializer.save()
    if "is_active" in request.data:
        zone.is_active = str(request.data["is_active"]).lower() in ("1", "true")
        zone.save(update_fields=["is_active", "updated_at"])
    from .. import audit
    audit.record(request.user, VmsRole.ADMIN, "ZONE_UPDATED", zone, message=zone.code)
    return Response(s.ZoneSerializer(zone).data)


@staff(["POST"])
def admin_gates(request):
    configuration.require_campus_admin(request.user)
    code, name = request.data.get("code"), request.data.get("name")
    if not code or not name:
        raise ValidationFailed("code and name are required.", details={"code": ["required"]})
    if Gate.objects.filter(code=code).exists():
        raise ValidationFailed("Gate code already exists.", details={"code": [code]})
    zone = Zone.objects.filter(code=request.data.get("zone")).first() if request.data.get("zone") else None
    gate = Gate.objects.create(code=code, name=name, zone=zone)
    from .. import audit
    audit.record(request.user, VmsRole.ADMIN, "GATE_CREATED", gate, message=code)
    return Response(s.GateSerializer(gate).data, status=status.HTTP_201_CREATED)


# ==========================================================================
# Super Admin (VMS-UC-001, 002, 003)
# ==========================================================================

def _super(request):
    require(selectors.is_super_admin(request.user), "Only the VMS Super Admin can perform this action.")


@staff(["GET", "POST"])
def super_roles(request):
    _super(request)
    if request.method == "GET":
        query = VmsRoleAssignment.objects.select_related("user", "zone", "gate")
        if request.query_params.get("active") in ("1", "true"):
            current = selectors.now()
            query = query.filter(is_active=True, valid_from__lte=current, valid_until__gt=current)
        return paginate(request, query, s.RoleAssignmentSerializer)
    data = parse(s.RoleAssignmentInput, request)
    assignment = configuration.assign_role(request.user, data["user"], data["role"], data["scope_type"],
                                           data["valid_until"], data.get("valid_from"), data.get("zone"),
                                           data.get("gate"))
    return Response(s.RoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


@staff(["POST"])
def super_reassign_role(request, assignment_id):
    data = parse(s.ReassignInput, request)
    assignment, moved = configuration.reassign_role(request.user, assignment_id, data["user"], data.get("valid_until"))
    return Response({"assignment": s.RoleAssignmentSerializer(assignment).data, "handoff": moved})


@staff(["POST"])
def super_revoke_role(request, assignment_id):
    assignment = configuration.revoke_role(request.user, assignment_id, request.data.get("reason", ""))
    return Response(s.RoleAssignmentSerializer(assignment).data)


@staff(["GET"])
def super_integrations(request):
    _super(request)
    return Response(s.IntegrationSerializer(IntegrationConfig.objects.all(), many=True).data)


@staff(["PUT"])
def super_integration_detail(request, key):
    data = parse(s.IntegrationInput, request)
    config = configuration.configure_integration(request.user, key, data)
    return Response(s.IntegrationSerializer(config).data)


@staff(["POST"])
def super_rotate_integration_key(request, key):
    config, raw = configuration.rotate_integration_key(request.user, key)
    return Response({"key": config.key, "api_key": raw,
                     "detail": "Store this key now; it cannot be shown again."}, status=status.HTTP_201_CREATED)


@staff(["GET", "POST"])
def super_vip(request):
    _super(request)
    if request.method == "GET":
        return paginate(request, VipPermission.objects.select_related("visit"), s.VipSerializer)
    permission = configuration.grant_vip(request.user, parse(s.VipInput, request))
    return Response(s.VipSerializer(permission).data, status=status.HTTP_201_CREATED)


@staff(["PATCH"])
def super_vip_detail(request, permission_id):
    permission = configuration.revise_vip(request.user, permission_id, parse(s.VipInput, request, partial=True))
    return Response(s.VipSerializer(permission).data)


@staff(["POST"])
def super_vip_revoke(request, permission_id):
    return Response(s.VipSerializer(configuration.revoke_vip(request.user, permission_id)).data)


# ==========================================================================
# External integrations (AFR-089/222/223 ACS, AFR-224 Event Mgmt, AFR-225 Hostel Mgmt)
# ==========================================================================

@integration(["POST"])
def integration_acs_validate(request):
    integration_caller(request, IntegrationKey.ACCESS_CONTROL)
    data = parse(s.ZoneValidateInput, request)
    zone = Zone.objects.filter(code=data["zone"], is_active=True).first()
    if zone is None:
        raise ValidationFailed("Unknown zone.", details={"zone": [data["zone"]]})
    from ..constants import LogMethod
    visit_pass = gate_services.resolve_pass(data["credential_type"], data["credential"], data.get("otp"))
    from django.db import transaction
    with transaction.atomic():
        result = gate_services.evaluate_zone_access(visit_pass, zone, actor=None, method=LogMethod.ACS,
                                                    device_id=data.get("device_id", ""), actor_role=VmsRole.SYSTEM)
    return Response({"allowed": result["allowed"], "basis": result["basis"]})


@integration(["GET"])
def integration_hostel_logs(request):
    integration_caller(request, IntegrationKey.HOSTEL_MANAGEMENT)
    query = VisitLog.objects.filter(hostel_area=True).select_related("visit", "gate", "zone", "recorded_by")
    since = request.query_params.get("since")
    if since:
        from django.utils.dateparse import parse_datetime
        moment = parse_datetime(since)
        if moment is None:
            raise ValidationFailed("since must be an ISO datetime.")
        query = query.filter(recorded_at__gt=moment)
    return paginate(request, query.order_by("recorded_at"), s.VisitLogSerializer)


@integration(["GET"])
def integration_event_attendance(request, external_ref):
    integration_caller(request, IntegrationKey.EVENT_MANAGEMENT)
    event = VisitorEvent.objects.filter(external_event_ref=external_ref).first()
    if event is None:
        raise NotFound("No VMS event for this reference.")
    attendance = reports.event_attendance(event)
    attendance.pop("throughput", None)
    return Response(attendance)
