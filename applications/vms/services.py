import base64
import csv
import io
import json
from datetime import date

import pyqrcode
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
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
    VerificationLog,
    VIPActivityLog,
    Visit,
    VisitingHours,
    Visitor,
    VisitorLocation,
    VisitorPass,
    VisitorRequest,
    calculate_valid_until,
)
from .selectors import (
    get_available_escorts,
    get_current_staff,
    is_escort_available,
)

# BR-046: default minimum VIP level that forces a dedicated escort when
# SystemConfig has not been seeded yet.
DEFAULT_ESCORT_THRESHOLD = 3


def _get_escort_threshold() -> int:
    """BR-046: minimum VIP level that mandates an escort, from SystemConfig."""
    cfg = SystemConfig.objects.filter(key="escort_threshold").first()
    if not cfg:
        return DEFAULT_ESCORT_THRESHOLD
    try:
        return max(1, int(cfg.value))
    except (TypeError, ValueError):
        return DEFAULT_ESCORT_THRESHOLD


class RegistrationError(Exception):
    pass


class WorkflowError(Exception):
    pass


class ConfigError(Exception):
    pass


class DataOperationError(Exception):
    pass


_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value):
    """Neutralise CSV formula-injection payloads (Excel/Sheets auto-eval)."""
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in _CSV_INJECTION_PREFIXES:
        return "'" + text
    return text


def _generate_pass_qr(visitor_pass, visit):
    """Generate a PNG QR code as a base64 data-URI string.

    Encodes only the opaque pass identifier and expiry. Visitor identity is
    resolved server-side on scan, so the printed pass cannot be lifted with a
    consumer QR scanner to reveal Aadhaar/passport or host details.
    """
    qr_payload = json.dumps({
        "pass_number": visitor_pass.pass_number,
        "visit_id": visit.id,
        "valid_until": visitor_pass.valid_until.isoformat(),
    })
    qr = pyqrcode.create(qr_payload, error="M")
    buffer = io.BytesIO()
    qr.png(buffer, scale=6, quiet_zone=2)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def register_visitor(data):
    """Register a visitor and create a new visit. Returns (visitor, visit).

    Enforces:
      BR-001  Valid ID required
      BR-002  ID format validation
      BR-003  Duration limits
      BR-007  Daily registration cap
      BR-018  Blacklist enforcement
      BR-063  Visiting hours check

    Triggers:
      BR-005  Request ID generation
      BR-006  Host notification

    Raises RegistrationError on any validation failure.
    """
    from .notifications import notify_host_visitor_request
    from .validators import validate_duration, validate_id_format, validate_visiting_hours

    # BR-001: valid ID required
    if not data.get("id_number") or not data.get("id_type"):
        raise RegistrationError("A valid identity document is required.")

    # BR-002: ID format validation
    valid, msg = validate_id_format(data["id_type"], data["id_number"])
    if not valid:
        raise RegistrationError(msg)

    # BR-003: duration limits
    duration = data.get("expected_duration_minutes", 60)
    is_vip = data.get("is_vip", False)
    valid, msg = validate_duration(duration, is_vip=is_vip)
    if not valid:
        raise RegistrationError(msg)

    # BR-063: visiting hours check
    valid, msg = validate_visiting_hours()
    if not valid:
        raise RegistrationError(msg)

    # BR-018: blacklist enforcement
    blacklist_hit = BlacklistEntry.objects.filter(
        id_number=data["id_number"], active=True,
    ).exists()
    if blacklist_hit:
        raise RegistrationError("Visitor is blacklisted; registration blocked.")

    visitor, _ = Visitor.objects.update_or_create(
        id_number=data["id_number"],
        defaults={
            "full_name": data["full_name"],
            "id_type": data["id_type"],
            "contact_phone": data["contact_phone"],
            "contact_email": data.get("contact_email", ""),
            "photo_reference": data.get("photo_reference", ""),
        },
    )

    # BR-046: allow registering with an explicit vip_level so the visit is
    # escort-eligible immediately. If is_vip is set but vip_level is 0,
    # coerce to 1 so the visit isn't silently downgraded.
    vip_level = int(data.get("vip_level") or 0)
    if is_vip and vip_level == 0:
        vip_level = 1

    visit = Visit.objects.create(
        visitor=visitor,
        purpose=data["purpose"],
        host_name=data["host_name"],
        host_department=data["host_department"],
        host_contact=data.get("host_contact", ""),
        expected_duration_minutes=duration,
        is_vip=is_vip,
        vip_level=vip_level,
    )

    # BR-005: unique request ID
    _create_request_id(visit)

    # BR-006: host notification
    notify_host_visitor_request(visit)

    return visitor, visit


def verify_visitor(data, user):
    """Verify a visitor's identity. Returns (visit, passed).

    Raises WorkflowError on verification failure.
    """
    visit = get_object_or_404(Visit, id=data["visit_id"])
    verifier = get_current_staff(user)

    VerificationLog.objects.create(
        visit=visit,
        verifier=verifier,
        method=data["method"],
        result=data["result"],
        notes=data.get("notes", ""),
    )

    if not data["result"]:
        visit.status = Visit.STATUS_DENIED
        visit.denial_reason = "verification_failed"
        visit.denial_remarks = data.get("notes", "")
        visit.save(update_fields=["status", "denial_reason", "denial_remarks"])
        DenialLog.objects.create(
            visit=visit,
            reason="verification_failed",
            remarks=data.get("notes", ""),
            escalated=True,
        )
        raise WorkflowError("Verification failed; entry denied.")

    visit.status = Visit.STATUS_VERIFIED
    visit.verified_at = timezone.now()
    visit.save(update_fields=["status", "verified_at"])
    return visit


def issue_pass(data):
    """Issue a visitor pass with QR code. Returns (visit, visitor_pass, qr_data_uri).

    Raises WorkflowError if the visit is in an invalid state.
    """
    visit = get_object_or_404(Visit, id=data["visit_id"])

    if visit.status in {Visit.STATUS_DENIED, Visit.STATUS_EXITED}:
        raise WorkflowError("Cannot issue pass for denied or closed visit.")
    if visit.status not in {Visit.STATUS_VERIFIED, Visit.STATUS_PASS_ISSUED}:
        raise WorkflowError("Visit must be verified before issuing a pass.")

    now = timezone.now()
    valid_until = calculate_valid_until(now, visit.expected_duration_minutes, visit.is_vip)
    visitor_pass, _ = VisitorPass.objects.update_or_create(
        visit=visit,
        defaults={
            "valid_from": now,
            "valid_until": valid_until,
            "authorized_zones": data.get("authorized_zones", "public"),
            "status": VisitorPass.PASS_ISSUED,
            "is_vip_pass": visit.is_vip,
        },
    )

    qr_data_uri = _generate_pass_qr(visitor_pass, visit)
    visitor_pass.barcode_data = qr_data_uri
    visitor_pass.save(update_fields=["barcode_data"])

    visit.status = Visit.STATUS_PASS_ISSUED
    visit.pass_issued_at = now
    visit.save(update_fields=["status", "pass_issued_at"])

    # BR-016: approval notification to visitor + security
    from .notifications import notify_approval
    notify_approval(visit, visitor_pass)

    # BR-047: VIP activity logging
    if visit.is_vip:
        VIPActivityLog.objects.create(
            visit=visit,
            action="pass_issued",
            details=f"VIP pass {visitor_pass.pass_number} issued, zones: {visitor_pass.authorized_zones}",
        )

    return visit, visitor_pass, qr_data_uri


def record_entry(data, user):
    """Record a visitor entry. Returns the visit.

    Raises WorkflowError if the visit is in an invalid state.
    """
    visit = get_object_or_404(Visit, id=data["visit_id"])
    if visit.status not in {Visit.STATUS_PASS_ISSUED, Visit.STATUS_INSIDE}:
        raise WorkflowError("Pass must be issued before entry.")

    EntryExitLog.objects.create(
        visit=visit,
        action=EntryExitLog.ACTION_ENTRY,
        gate_name=data["gate_name"],
        recorded_by=get_current_staff(user),
        items_declared=data.get("items_declared", ""),
    )

    visit.status = Visit.STATUS_INSIDE
    visit.entry_at = visit.entry_at or timezone.now()
    visit.save(update_fields=["status", "entry_at"])

    # BR-036: activate location tracking
    from .tasks import activate_location_tracking
    activate_location_tracking(visit, data["gate_name"], recorded_by=get_current_staff(user))

    # BR-045: VIP arrival notification
    if visit.is_vip:
        from .notifications import notify_vip_arrival
        notify_vip_arrival(visit)
        VIPActivityLog.objects.create(
            visit=visit,
            action="campus_entry",
            details=f"VIP entered via {data['gate_name']}",
            recorded_by=get_current_staff(user),
        )

    return visit


def record_exit(data, user):
    """Record a visitor exit. Returns the visit.

    Also auto-releases any active escort assignments on the visit, since
    the escort's duty ends the moment the VIP leaves campus.

    Raises WorkflowError if the visitor is not inside.
    """
    visit = get_object_or_404(Visit, id=data["visit_id"])
    if visit.status != Visit.STATUS_INSIDE:
        raise WorkflowError("Visitor is not inside.")

    staff = get_current_staff(user)
    EntryExitLog.objects.create(
        visit=visit,
        action=EntryExitLog.ACTION_EXIT,
        gate_name=data["gate_name"],
        recorded_by=staff,
        items_declared=data.get("items_declared", ""),
    )

    visit.status = Visit.STATUS_EXITED
    visit.exit_at = timezone.now()
    visit.save(update_fields=["status", "exit_at"])

    visitor_pass = getattr(visit, "visitor_pass", None)
    if visitor_pass:
        visitor_pass.status = VisitorPass.PASS_RETURNED
        visitor_pass.save(update_fields=["status"])

    # Auto-release any active escort assignments — the escort's duty ends
    # when the visitor leaves campus.
    active_escorts = EscortAssignment.objects.filter(
        visit=visit, released_at__isnull=True
    )
    for assignment in active_escorts:
        assignment.released_at = timezone.now()
        assignment.save(update_fields=["released_at"])
        VIPActivityLog.objects.create(
            visit=visit,
            action="escort_auto_released",
            details=f"Escort {assignment.escort} released on visitor exit",
            recorded_by=staff,
        )

    return visit


def deny_entry(data):
    """Deny entry for a visit. Returns (visit, denial_log)."""
    visit = get_object_or_404(Visit, id=data["visit_id"])
    visit.status = Visit.STATUS_DENIED
    visit.denial_reason = data["reason"]
    visit.denial_remarks = data.get("remarks", "")
    visit.save(update_fields=["status", "denial_reason", "denial_remarks"])

    denial = DenialLog.objects.create(
        visit=visit,
        reason=data["reason"],
        remarks=data.get("remarks", ""),
        escalated=data.get("escalated", False),
    )
    return visit, denial


def log_incident(data, user):
    """Log a security incident. Returns the incident."""
    visit = None
    visitor = None
    if data.get("visit_id"):
        visit = get_object_or_404(Visit, id=data["visit_id"])
        visitor = visit.visitor
    elif data.get("visitor_id"):
        visitor = get_object_or_404(Visitor, id=data["visitor_id"])

    incident = SecurityIncident.objects.create(
        visit=visit,
        visitor=visitor,
        recorded_by=get_current_staff(user),
        severity=data["severity"],
        issue_type=data["issue_type"],
        description=data["description"],
    )

    # BR-050 / BR-053 / BR-055 / BR-056: escalation + status update + severity response
    from .notifications import (
        notify_escalation,
        notify_high_severity_response,
        notify_low_severity,
    )
    from .tasks import determine_containment_actions, update_visitor_status_on_incident

    notify_escalation(incident)
    determine_containment_actions(incident)
    update_visitor_status_on_incident(incident)

    if incident.severity == SecurityIncident.SEVERITY_CRITICAL:
        notify_high_severity_response(incident)
    elif incident.severity == SecurityIncident.SEVERITY_LOW:
        notify_low_severity(incident)

    return incident


# ============================================================================
# BR-004: Host verification
# ============================================================================
def verify_host(visit, user):
    """Verify the host exists and has authority to receive visitors."""
    authority = HostAuthority.objects.filter(user=user).first()
    if authority is None:
        raise WorkflowError("Host does not have a registered authority record.")
    return authority


# ============================================================================
# BR-005: Request ID generation (called from register_visitor)
# ============================================================================
def _create_request_id(visit):
    """Generate and persist a unique request ID for the visit."""
    request_id = VisitorRequest.generate_request_id()
    return VisitorRequest.objects.create(request_id=request_id, visit=visit)


# ============================================================================
# BR-019 / BR-020 / BR-021: Pass scan & validation
# ============================================================================
def scan_visitor_pass(data, user):
    """
    Validate a visitor pass on scan: authenticity, expiry, and area access.
    Returns (visit, scan_result_dict).
    """
    from .notifications import notify_invalid_pass_scan, notify_unauthorized_area
    from .permissions import check_zone_access
    from .tasks import activate_location_tracking
    from .validators import validate_pass_expiry

    visit = get_object_or_404(Visit, id=data["visit_id"])
    checkpoint = data.get("checkpoint_name", "Unknown")
    staff = get_current_staff(user)

    visitor_pass = getattr(visit, "visitor_pass", None)
    if visitor_pass is None:
        notify_invalid_pass_scan(visit, checkpoint)
        raise WorkflowError("No pass found for this visit.")

    # BR-020: expiry check
    valid, msg = validate_pass_expiry(visitor_pass)
    if not valid:
        notify_invalid_pass_scan(visit, checkpoint)
        raise WorkflowError(msg)

    # BR-021: area/zone access
    zone_name = data.get("zone_name", "")
    if zone_name:
        allowed, zone_msg = check_zone_access(visitor_pass, zone_name)
        if not allowed:
            notify_unauthorized_area(visit, zone_name)
            raise WorkflowError(zone_msg)

    # BR-036: activate location tracking
    activate_location_tracking(visit, checkpoint, recorded_by=staff)

    # BR-022: log entry/exit
    EntryExitLog.objects.create(
        visit=visit,
        action=EntryExitLog.ACTION_ENTRY,
        gate_name=checkpoint,
        recorded_by=staff,
        items_declared=data.get("items_declared", ""),
    )

    return visit, {
        "valid": True,
        "pass_number": visitor_pass.pass_number,
        "visitor": visit.visitor.full_name,
        "zones": visitor_pass.authorized_zones,
        "valid_until": visitor_pass.valid_until.isoformat(),
    }


# ============================================================================
# BR-023: Manual verification fallback
# ============================================================================
def manual_pass_verification(data, user):
    """Fallback when QR scan fails — manual identity check by security."""
    visit = get_object_or_404(Visit, id=data["visit_id"])
    staff = get_current_staff(user)

    VerificationLog.objects.create(
        visit=visit,
        verifier=staff,
        method=VerificationLog.METHOD_MANUAL,
        result=data.get("result", True),
        notes=data.get("notes", "Manual verification — scan failed"),
    )

    return visit


# ============================================================================
# BR-030–035: Blacklist management
# ============================================================================
def add_to_blacklist(data, user):
    """Add a visitor to the blacklist with reason and evidence (BR-032)."""
    from .notifications import notify_checkpoints_blacklist

    staff = get_current_staff(user)
    entry = BlacklistEntry.objects.create(
        id_number=data["id_number"],
        reason=data["reason"],
        evidence=data.get("evidence", ""),
        added_by=staff,
        active=True,
    )

    # BR-034: audit log
    BlacklistAuditLog.objects.create(
        blacklist_entry=entry,
        action=BlacklistAuditLog.ACTION_ADD,
        performed_by=staff,
        id_number=entry.id_number,
        reason=entry.reason,
        evidence=entry.evidence,
    )

    # BR-033: checkpoint alert
    notify_checkpoints_blacklist(entry, "added")

    return entry


def remove_from_blacklist(entry_id, user):
    """Deactivate a blacklist entry (BR-035: requires admin authority)."""
    from .notifications import notify_checkpoints_blacklist

    staff = get_current_staff(user)
    entry = get_object_or_404(BlacklistEntry, id=entry_id)
    entry.active = False
    entry.save(update_fields=["active"])

    BlacklistAuditLog.objects.create(
        blacklist_entry=entry,
        action=BlacklistAuditLog.ACTION_REMOVE,
        performed_by=staff,
        id_number=entry.id_number,
        reason="Removed from blacklist",
    )
    notify_checkpoints_blacklist(entry, "removed")

    return entry


# ============================================================================
# BR-041–047: VIP processing
# ============================================================================
def identify_vip(visit):
    """BR-041: Check if visitor is VIP via DB lookup or admin designation."""
    visitor = visit.visitor
    # Check if visitor has any active VIP visits
    has_vip_history = Visit.objects.filter(visitor=visitor, is_vip=True).exists()
    return visit.is_vip or has_vip_history


def process_vip_visit(data, user):
    """BR-042/043/046: VIP processing with optional bypass and auto-escort."""
    from .notifications import notify_vip_arrival
    from applications.globals.models import ExtraInfo

    visit = get_object_or_404(Visit, id=data["visit_id"])

    # BR-046 input: a numeric VIP level; legacy callers who only send the
    # boolean flag still get a sensible value (=1, plain VIP, no escort).
    raw_level = data.get("vip_level")
    if raw_level is None:
        new_level = max(visit.vip_level, 1)
    else:
        try:
            new_level = max(0, int(raw_level))
        except (TypeError, ValueError):
            new_level = visit.vip_level

    update_fields = []
    if not visit.is_vip:
        visit.is_vip = True
        update_fields.append("is_vip")
    if new_level != visit.vip_level:
        visit.vip_level = new_level
        update_fields.append("vip_level")
    if update_fields:
        visit.save(update_fields=update_fields)

    # BR-043: bypass standard approval for authorised VIPs
    if data.get("bypass_approval", False):
        visit.status = Visit.STATUS_VERIFIED
        visit.verified_at = timezone.now()
        visit.save(update_fields=["status", "verified_at"])

    # BR-045: VIP arrival notification
    notify_vip_arrival(visit)

    staff = get_current_staff(user)

    # BR-046: when vip_level crosses the threshold, auto-assign an available
    # qualified escort if one exists and none is currently on this visit.
    auto_escort = None
    threshold = _get_escort_threshold()
    already_assigned = EscortAssignment.objects.filter(
        visit=visit, released_at__isnull=True
    ).exists()
    if visit.vip_level >= threshold and not already_assigned:
        candidate_id = data.get("escort_id")
        candidate = None
        if candidate_id:
            candidate = ExtraInfo.objects.filter(id=candidate_id).first()
            if candidate and not is_escort_available(candidate.id):
                candidate = None
        if candidate is None:
            candidate = get_available_escorts().first()
        if candidate is not None:
            auto_escort = EscortAssignment.objects.create(
                visit=visit,
                escort=candidate,
                notes="Auto-assigned per BR-046 (vip_level >= escort_threshold).",
            )
            VIPActivityLog.objects.create(
                visit=visit,
                action="escort_auto_assigned",
                details=f"Escort: {candidate} (vip_level={visit.vip_level}, threshold={threshold})",
                recorded_by=staff,
            )

    # BR-047: enhanced VIP activity logging
    VIPActivityLog.objects.create(
        visit=visit,
        action="vip_processing_initiated",
        details=json.dumps({**data, "resolved_vip_level": visit.vip_level}),
        recorded_by=staff,
    )

    return visit, auto_escort


def assign_escort(data, user):
    """BR-046: Assign a dedicated escort to a VIP visitor.

    Policy (staff-tier manual assignment):
        IF visit.is_vip AND escort_available
        THEN assign_escort(qualified_personnel)

    The numeric `escort_threshold` is retained as the *auto*-escort trigger
    inside `process_vip_visit`. Manual assignment by Security Staff only
    requires that the visit is flagged VIP, so a gate officer can request
    an escort for any VIP without first elevating vip_level via admin
    tooling.

    Enforcement:
      * The visit must be VIP (`is_vip=True`).
      * If a specific escort_id is supplied it must not currently hold an
        unreleased assignment; if omitted we pick the first available
        qualified staff member.
      * Only one active escort per visit at a time.
      * Raises WorkflowError when the precondition is not met.
    """
    from applications.globals.models import ExtraInfo

    visit = get_object_or_404(Visit, id=data["visit_id"])

    if not visit.is_vip:
        raise WorkflowError(
            "Escort assignment requires the visit to be marked VIP. "
            "Re-register the visitor with the VIP flag, or have an admin "
            "run VIP processing on this visit first."
        )

    # Resolve the escort. Explicit escort_id wins; fall back to auto-pick.
    escort_staff = None
    candidate_id = data.get("escort_id")
    if candidate_id:
        escort_staff = ExtraInfo.objects.filter(id=candidate_id).first()
        if escort_staff is None:
            raise WorkflowError(f"Escort id={candidate_id} not found.")
        if not is_escort_available(escort_staff.id):
            raise WorkflowError(
                f"Escort {escort_staff} is already on an active assignment."
            )
    else:
        escort_staff = get_available_escorts().first()
        if escort_staff is None:
            raise WorkflowError("No qualified escorts are currently available.")

    # BR-046: prevent duplicating an escort on the same active visit.
    if EscortAssignment.objects.filter(
        visit=visit, released_at__isnull=True
    ).exists():
        raise WorkflowError("Visit already has an active escort assignment.")

    assignment = EscortAssignment.objects.create(
        visit=visit,
        escort=escort_staff,
        notes=data.get("notes", ""),
    )

    recorder = get_current_staff(user) or escort_staff
    VIPActivityLog.objects.create(
        visit=visit,
        action="escort_assigned",
        details=(
            f"Escort: {escort_staff} (vip_level={visit.vip_level}, "
            f"auto_escort_threshold={_get_escort_threshold()})"
        ),
        recorded_by=recorder,
    )

    return assignment


def release_escort(assignment_id, user):
    """Release an escort assignment when VIP visit concludes."""
    assignment = get_object_or_404(EscortAssignment, id=assignment_id)
    if assignment.released_at is not None:
        return assignment
    assignment.released_at = timezone.now()
    assignment.save(update_fields=["released_at"])

    recorder = get_current_staff(user)
    VIPActivityLog.objects.create(
        visit=assignment.visit,
        action="escort_released",
        details=f"Escort: {assignment.escort}",
        recorded_by=recorder,
    )
    return assignment


# ============================================================================
# BR-025–029: Report generation
# ============================================================================
def generate_report(params, user):
    """Generate a visitor report with statistics (BR-025–029)."""
    from .validators import validate_report_params

    valid, msg = validate_report_params(params)
    if not valid:
        raise WorkflowError(msg)

    start_date = params["start_date"]
    end_date = params["end_date"]
    report_type = params["report_type"]

    visits = Visit.objects.filter(
        registered_at__date__gte=start_date,
        registered_at__date__lte=end_date,
    )

    # BR-028: Statistics calculation
    total_visits = visits.count()
    status_breakdown = dict(visits.values_list("status").annotate(count=Count("id")))
    vip_visits = visits.filter(is_vip=True).count()

    incidents = SecurityIncident.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    total_incidents = incidents.count()
    severity_breakdown = dict(incidents.values_list("severity").annotate(count=Count("id")))

    # BR-029: Standard report format
    report = {
        "report_type": report_type,
        "generated_at": timezone.now().isoformat(),
        "generated_by": str(user),
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "summary": {
            "total_visits": total_visits,
            "status_breakdown": status_breakdown,
            "vip_visits": vip_visits,
            "total_incidents": total_incidents,
            "severity_breakdown": severity_breakdown,
        },
        "trends": {
            "daily_averages": round(total_visits / max((end_date - start_date).days, 1), 2),
            "incident_rate": round(total_incidents / max(total_visits, 1) * 100, 2),
        },
    }

    return report


# ============================================================================
# BR-030–031: Visitor / incident history
# ============================================================================
def get_visitor_history(id_number: str):
    """BR-030: Full visitor history for blacklist evaluation."""
    visitor = get_object_or_404(Visitor, id_number=id_number)
    visits = Visit.objects.filter(visitor=visitor).order_by("-registered_at")
    incidents = SecurityIncident.objects.filter(visitor=visitor).order_by("-created_at")
    blacklist_entries = BlacklistEntry.objects.filter(id_number=id_number)

    return {
        "visitor": visitor,
        "visits": visits,
        "incidents": incidents,
        "blacklist_entries": blacklist_entries,
    }


def get_incident_history(id_number: str):
    """BR-031: Incident history for blacklist decision-making."""
    visitor = Visitor.objects.filter(id_number=id_number).first()
    if visitor is None:
        return []
    return SecurityIncident.objects.filter(visitor=visitor).order_by("-created_at")


# ============================================================================
# BR-057–066: System configuration management
# ============================================================================
def get_or_create_config(key: str, default: str = "", description: str = "") -> SystemConfig:
    """Retrieve a config entry, creating it with the default if absent."""
    config, _ = SystemConfig.objects.get_or_create(
        key=key, defaults={"value": default, "description": description}
    )
    return config


def update_config(key: str, value: str, user, description: str = ""):
    """
    Update a system configuration value with validation, conflict detection,
    logging, cache refresh, and user notification.
    """
    from .notifications import notify_config_change
    from .tasks import refresh_config_cache
    from .validators import detect_config_conflicts, validate_config_value

    # BR-058: validate
    valid, msg = validate_config_value(key, value)
    if not valid:
        raise ConfigError(msg)

    # BR-059: conflict detection
    current_config = {c.key: c.value for c in SystemConfig.objects.all()}
    conflicts = detect_config_conflicts({key: value}, current_config)
    if conflicts:
        raise ConfigError(f"Configuration conflicts detected: {conflicts}")

    staff = get_current_staff(user)
    config, created = SystemConfig.objects.get_or_create(
        key=key, defaults={"value": value, "description": description, "updated_by": staff}
    )

    if not created:
        old_value = config.value
        config.value = value
        config.updated_by = staff
        if description:
            config.description = description
        config.save()

        # BR-061: change logging
        ConfigChangeLog.objects.create(
            config=config,
            old_value=old_value,
            new_value=value,
            changed_by=staff,
        )

    # BR-060: cache refresh
    refresh_config_cache()

    # BR-062: user notification
    notify_config_change(config, str(user))

    return config


# ============================================================================
# BR-063: Visiting hours management
# ============================================================================
def configure_visiting_hours(data):
    """Create or update visiting hours configuration."""
    hours, _ = VisitingHours.objects.update_or_create(
        day_of_week=data["day_of_week"],
        defaults={
            "start_time": data["start_time"],
            "end_time": data["end_time"],
            "is_holiday": data.get("is_holiday", False),
            "holiday_name": data.get("holiday_name", ""),
            "active": data.get("active", True),
        },
    )
    return hours


# ============================================================================
# BR-064: Access zone configuration
# ============================================================================
def configure_access_zone(data):
    """Create or update an access zone."""
    zone, _ = AccessZone.objects.update_or_create(
        name=data["name"],
        defaults={
            "description": data.get("description", ""),
            "requires_vip": data.get("requires_vip", False),
            "requires_escort": data.get("requires_escort", False),
            "is_restricted": data.get("is_restricted", False),
            "active": data.get("active", True),
        },
    )
    return zone


# ============================================================================
# BR-067–074: Data export / import
# ============================================================================
def export_visitor_data(params, user):
    """Export visitor data with validation and logging (BR-067–072)."""
    from .validators import validate_data_format, validate_date_range

    fmt = params.get("format", "csv")
    valid, msg = validate_data_format(fmt)
    if not valid:
        raise DataOperationError(msg)

    start_date = params.get("start_date")
    end_date = params.get("end_date")
    if start_date and end_date:
        valid, msg = validate_date_range(start_date, end_date)
        if not valid:
            raise DataOperationError(msg)

    staff = get_current_staff(user)
    # Convert date objects to strings for JSON serialization
    safe_params = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in params.items()}
    op_log = DataOperationLog.objects.create(
        operation_type=DataOperationLog.OP_EXPORT,
        status=DataOperationLog.STATUS_RUNNING,
        initiated_by=staff,
        parameters=safe_params,
    )

    try:
        visits_qs = Visit.objects.select_related("visitor").order_by("-registered_at")
        if start_date and end_date:
            visits_qs = visits_qs.filter(
                registered_at__date__gte=start_date,
                registered_at__date__lte=end_date,
            )

        # BR-069: data transformation. All string-typed values are passed
        # through _csv_safe to neutralise CSV formula injection.
        rows = []
        for v in visits_qs:
            rows.append({
                "visit_id": v.id,
                "visitor_name": _csv_safe(v.visitor.full_name),
                "id_number": _csv_safe(v.visitor.id_number),
                "id_type": _csv_safe(v.visitor.id_type),
                "purpose": _csv_safe(v.purpose),
                "host_name": _csv_safe(v.host_name),
                "host_department": _csv_safe(v.host_department),
                "status": _csv_safe(v.status),
                "is_vip": v.is_vip,
                "registered_at": v.registered_at.isoformat() if v.registered_at else "",
                "entry_at": v.entry_at.isoformat() if v.entry_at else "",
                "exit_at": v.exit_at.isoformat() if v.exit_at else "",
            })

        if fmt == "csv":
            output = io.StringIO()
            if rows:
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            result = output.getvalue()
        else:
            result = json.dumps(rows, indent=2)

        # BR-071: completion validation
        op_log.status = DataOperationLog.STATUS_COMPLETED
        op_log.records_processed = len(rows)
        op_log.result_summary = f"Exported {len(rows)} records in {fmt} format."
        op_log.completed_at = timezone.now()
        op_log.save()

        return result, op_log

    except Exception as exc:
        # BR-070 / BR-074: error handling + recovery. Exception details are
        # persisted to the operation log for ops review but not echoed to the
        # client (avoids schema/stack disclosure).
        op_log.status = DataOperationLog.STATUS_FAILED
        op_log.error_details = str(exc)
        op_log.completed_at = timezone.now()
        op_log.save()
        raise DataOperationError("Export failed; see operation log for details.") from exc


def import_visitor_data(data_content: str, fmt: str, field_mapping: dict, user):
    """Import visitor data with field mapping and rollback (BR-067–074)."""
    from .validators import validate_data_format

    valid, msg = validate_data_format(fmt)
    if not valid:
        raise DataOperationError(msg)

    staff = get_current_staff(user)
    op_log = DataOperationLog.objects.create(
        operation_type=DataOperationLog.OP_IMPORT,
        status=DataOperationLog.STATUS_RUNNING,
        initiated_by=staff,
        parameters={"format": fmt, "field_mapping": field_mapping},
    )

    created_visitors = []
    try:
        if fmt == "csv":
            reader = csv.DictReader(io.StringIO(data_content))
            records = list(reader)
        else:
            records = json.loads(data_content)

        # BR-073: field mapping
        mapped_records = []
        for record in records:
            mapped = {}
            for source_field, target_field in field_mapping.items():
                mapped[target_field] = record.get(source_field, "")
            mapped_records.append(mapped)

        # BR-069: data transformation & creation
        for row in mapped_records:
            visitor, _ = Visitor.objects.update_or_create(
                id_number=row.get("id_number", ""),
                defaults={
                    "full_name": row.get("full_name", "Unknown"),
                    "id_type": row.get("id_type", "national_id"),
                    "contact_phone": row.get("contact_phone", ""),
                    "contact_email": row.get("contact_email", ""),
                },
            )
            created_visitors.append(visitor)

        # BR-071: completion validation
        op_log.status = DataOperationLog.STATUS_COMPLETED
        op_log.records_processed = len(created_visitors)
        op_log.result_summary = f"Imported {len(created_visitors)} visitor records."
        op_log.completed_at = timezone.now()
        op_log.save()

        return created_visitors, op_log

    except Exception as exc:
        # BR-070 / BR-074: rollback on failure
        for v in created_visitors:
            v.delete()

        op_log.status = DataOperationLog.STATUS_ROLLED_BACK
        op_log.error_details = str(exc)
        op_log.completed_at = timezone.now()
        op_log.save()
        raise DataOperationError("Import failed and rolled back; see operation log for details.") from exc
