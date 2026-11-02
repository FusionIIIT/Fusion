"""Gate, checkout, offline and zone services.

VMS-UC-018 gate validation, VMS-UC-019 manual override, VMS-UC-020 manual visit
log, VMS-UC-021/031 checkout, VMS-UC-028/039 offline entry and reconciliation,
VMS-UC-023/024/025 zone access, elevation and alert handling.
"""

import datetime

from django.db import transaction

from .. import audit, conf, workflow
from ..constants import (
    AlertStatus,
    AlertType,
    Checkpoint,
    CredentialType,
    EventStatus,
    GateAttemptStatus,
    GateFailure,
    LogMethod,
    LogType,
    NotificationEvent,
    OfflineEventStatus,
    VisitStatus,
    VmsRole,
)
from ..errors import Conflict, NotAuthorized, NotFound, Unavailable, ValidationFailed
from ..models import (
    Gate,
    GateAttempt,
    OfflineGateEvent,
    SecurityAlert,
    VisitLog,
    VisitPass,
    VisitRequest,
    Zone,
    ZoneElevation,
)
from ..notifications import notify_role, notify_user, notify_users
from ..selectors import admin_covers, admins_covering, now, security_covers, security_users
from .common import (
    deactivate_pass,
    mask,
    raise_registry_alerts,
    registry_check,
    route_admin,
    zone_permission,
    zones_from_codes,
)

CREDENTIAL_METHOD = {
    CredentialType.QR: LogMethod.QR,
    CredentialType.BARCODE: LogMethod.QR,
    CredentialType.OTP: LogMethod.OTP,
    CredentialType.BADGE: LogMethod.BADGE,
}


def get_gate(code, required=True):
    if not code:
        if required:
            raise ValidationFailed("A gate is required.", details={"gate": ["required"]})
        return None
    gate = Gate.objects.select_related("zone").filter(code=code, is_active=True).first()
    if gate is None:
        raise ValidationFailed("Unknown or inactive gate.", details={"gate": [code]})
    return gate


def resolve_pass(credential_type, credential, otp=None):
    """QR -> qr_token; BARCODE/BADGE -> pass number; OTP -> pass number + one-time OTP."""
    credential = (credential or "").strip()
    if not credential:
        return None
    query = VisitPass.objects.select_related("visit", "visit__visitor", "visit__host__user")
    if credential_type == CredentialType.QR:
        return query.filter(qr_token=credential).first()
    visit_pass = query.filter(pass_number=credential.upper()).first()
    if credential_type == CredentialType.OTP:
        if visit_pass is None or not otp or visit_pass.otp != str(otp).strip():
            return None
    return visit_pass


def _log(visit, log_type, method, actor, at=None, gate=None, zone=None, device_id="", detail="", **extra):
    hostel = bool((zone and zone.is_hostel_area) or (gate and gate.zone_id and gate.zone.is_hostel_area))
    return VisitLog.objects.create(
        visit=visit, log_type=log_type, method=method, occurred_at=at or now(), gate=gate, zone=zone,
        device_id=device_id or "", recorded_by=actor if (actor and actor.is_authenticated) else None,
        detail=detail, hostel_area=hostel, **extra)


def visit_summary(visit):
    visit_pass = getattr(visit, "visit_pass", None)
    return {
        "reference": visit.reference,
        "status": visit.status,
        "visitor": visit.visitor.full_name,
        "organization": visit.visitor.organization,
        "photo": visit.visitor.photo.url if visit.visitor.photo else None,
        "host": visit.host.user.get_full_name() or visit.host.user.username,
        "special_instructions": visit.special_instructions,
        "pass_type": visit_pass.pass_type if visit_pass else None,
        "valid_until": visit_pass.valid_until if visit_pass else None,
        "permitted_zones": list(visit_pass.permitted_zones.values_list("code", flat=True)) if visit_pass else [],
        "watchlist_flag": visit.watchlist_flag,
    }


# --------------------------------------------------------------------------
# VMS-UC-018 Validate Visitor Pass at Gate
# --------------------------------------------------------------------------

def _gate_failures(visit_pass, credential_type, gate, current, actor):
    failures, registry_result = [], None
    if visit_pass is None:
        return [GateFailure.UNKNOWN_CREDENTIAL], None
    visit = visit_pass.visit
    if not visit_pass.is_active:
        failures.append(GateFailure.PASS_INACTIVE)                       # VMS-BR-077
    if visit.status != VisitStatus.PASS_ACTIVE:
        failures.append(GateFailure.VISIT_NOT_ENTERABLE)
    if not (visit_pass.valid_from <= current <= visit_pass.valid_until):
        failures.append(GateFailure.OUTSIDE_VALIDITY_WINDOW)             # VMS-BR-190
    if credential_type == CredentialType.OTP and visit_pass.otp_used_at:
        failures.append(GateFailure.OTP_ALREADY_USED)
    registry_result = registry_check(visit.visitor, Checkpoint.GATE, current)  # VMS-BR-112/120
    if registry_result.disqualifying:
        failures.append(GateFailure.BLACKLIST_MATCH)                     # VMS-BR-116
    if gate is not None and gate.zone_id:
        allowed, _ = zone_permission(visit, gate.zone, current)          # AFR-080
        if not allowed:
            failures.append(GateFailure.GATE_ZONE_NOT_PERMITTED)
    return failures, registry_result


@transaction.atomic
def validate_at_gate(actor, data):
    current = now()
    gate = get_gate(data.get("gate"))
    if not security_covers(actor, gate=gate):
        raise NotAuthorized("Only Security Personnel assigned to this gate can validate passes.")
    credential_type = data.get("credential_type")
    if credential_type not in {c for c, _ in CredentialType.CHOICES}:
        raise ValidationFailed("Unsupported credential type.", details={"credential_type": [credential_type]})
    visit_pass = resolve_pass(credential_type, data.get("credential"), data.get("otp"))
    if visit_pass is not None:
        visit_pass = VisitPass.objects.select_for_update(of=("self",)).select_related(
            "visit", "visit__visitor", "visit__host__user").get(pk=visit_pass.pk)
    visit = visit_pass.visit if visit_pass else None
    lane = data.get("lane") or VisitRequest.LANE_NORMAL
    if lane == VisitRequest.LANE_FAST:
        # AFR-160: same validation obligations, only for events that enabled the lane.
        event = visit.event if visit else None
        if event is None or not event.fast_lane_enabled or event.status != EventStatus.CONTROLS_ACTIVE:
            raise ValidationFailed("Fast-lane scanning is not enabled for this pass.", code="lane_disabled")

    failures, registry_result = _gate_failures(visit_pass, credential_type, gate, current, actor)
    flagged = bool(registry_result and (registry_result.disqualifying or registry_result.flags))
    attempt = GateAttempt.objects.create(
        visit=visit, gate=gate, device_id=data.get("device_id", ""), credential_type=credential_type,
        credential_hint=mask(data.get("credential", "")), lane=lane,
        status=GateAttemptStatus.BLOCKED if failures else GateAttemptStatus.ALLOWED,
        failure_reasons=failures, flagged=flagged, attempted_by=actor, attempted_at=current,
        override_eligible=bool(failures and visit and set(failures) <= conf.override_eligible_failures()),
    )
    if registry_result and (registry_result.disqualifying or registry_result.flags):
        raise_registry_alerts(registry_result, Checkpoint.GATE, actor=actor, actor_role=VmsRole.SECURITY,
                              visitor=visit.visitor, visit=visit, gate=gate, gate_attempt=attempt,
                              identity={"full_name": visit.visitor.full_name, "phone": visit.visitor.phone,
                                        "email": visit.visitor.email, "id_doc_number": visit.visitor.id_doc_number})

    if failures:
        # VMS-BR-082: block and record the reason (AFR-082/083/084).
        _log(visit, LogType.ACCESS_DENIED, CREDENTIAL_METHOD.get(credential_type, LogMethod.QR), actor, current,
             gate=gate, device_id=data.get("device_id", ""), detail=", ".join(failures), gate_attempt=attempt)
        audit.record(actor, VmsRole.SECURITY, "GATE_ENTRY_BLOCKED", attempt,
                     visitor=visit.visitor if visit else None, message=", ".join(failures),
                     metadata={"gate": gate.code, "visit": visit.reference if visit else None})
        return {"allowed": False, "attempt_id": attempt.pk, "failure_reasons": failures,
                "override_eligible": attempt.override_eligible, "flagged": flagged,
                "visit": visit_summary(visit) if visit else None}

    visit.check_in_at = current
    visit.entry_gate = gate
    visit.last_seen_zone = gate.zone
    visit.last_seen_at = current
    workflow.apply(visit, "GATE_CHECK_IN", actor=actor, actor_role=VmsRole.SECURITY)
    if credential_type == CredentialType.OTP:
        visit_pass.otp_used_at = current
        visit_pass.save(update_fields=["otp_used_at"])
    _log(visit, LogType.CHECK_IN, CREDENTIAL_METHOD[credential_type], actor, current, gate=gate,
         zone=gate.zone, device_id=data.get("device_id", ""), gate_attempt=attempt,
         detail="Fast lane" if lane == VisitRequest.LANE_FAST else "")
    audit.record(actor, VmsRole.SECURITY, "VISITOR_CHECKED_IN", visit, visitor=visit.visitor,
                 metadata={"gate": gate.code, "device_id": data.get("device_id", ""), "lane": lane})
    notify_user(visit.host.user, NotificationEvent.VISITOR_CHECKED_IN, "Your visitor has arrived",
                "{} checked in at {} ({}).".format(visit.visitor.full_name, gate.name, current.strftime("%H:%M")),
                visit=visit, email=False)  # AFR-019 / AFR-168
    return {"allowed": True, "attempt_id": attempt.pk, "failure_reasons": [], "visit": visit_summary(visit)}


@transaction.atomic
def refer_attempt(actor, attempt_id, note=""):
    """VMS-UC-018 alt flow: refer an override-eligible block to Admin (VMS-UC-019)."""
    attempt = GateAttempt.objects.select_for_update(of=("self",)).select_related("gate", "visit").filter(pk=attempt_id).first()
    if attempt is None:
        raise NotFound("Gate attempt not found.")
    if not security_covers(actor, gate=attempt.gate):
        raise NotAuthorized("Only Security Personnel at this gate can refer the attempt.")
    if attempt.status != GateAttemptStatus.BLOCKED:
        raise Conflict("Only blocked attempts can be referred.", code="not_blocked")
    if not attempt.override_eligible:
        raise Conflict("This failure type is not eligible for override.", code="not_override_eligible")
    zones = list(attempt.visit.requested_zones.all()) if attempt.visit else []
    attempt.assigned_admin = route_admin(zones, attempt.gate)
    attempt.override_requested_at = now()
    attempt.escalation_note = note
    attempt.save(update_fields=["assigned_admin", "override_requested_at", "escalation_note"])
    if attempt.assigned_admin:
        notify_user(attempt.assigned_admin, NotificationEvent.OVERRIDE_REQUESTED, "Gate override requested",
                    "Blocked entry at {} ({}). Reasons: {}.".format(
                        attempt.gate.name if attempt.gate else "gate",
                        attempt.visit.reference if attempt.visit else "unknown", ", ".join(attempt.failure_reasons)),
                    visit=attempt.visit)
    audit.record(actor, VmsRole.SECURITY, "GATE_OVERRIDE_REQUESTED", attempt, message=note)
    return attempt


# --------------------------------------------------------------------------
# VMS-UC-019 Process Manual Gate Override (VMS-BR-085)
# --------------------------------------------------------------------------

@transaction.atomic
def decide_override(actor, attempt_id, decision, justification):
    attempt = GateAttempt.objects.select_for_update(of=("self",)).select_related("gate", "visit").filter(pk=attempt_id).first()
    if attempt is None:
        raise NotFound("Gate attempt not found.")
    zones = list(attempt.visit.requested_zones.all()) if attempt.visit else []
    if not admin_covers(actor, zones=zones, gate=attempt.gate):
        raise NotAuthorized("Only an authorised Admin for this gate can override (VMS-BR-085).")
    if not (justification or "").strip():
        raise ValidationFailed("A justification is required for every override decision.",
                               details={"justification": ["required"]})
    if attempt.status != GateAttemptStatus.BLOCKED:
        raise Conflict("Only a blocked attempt can be overridden.", code="not_blocked")
    if not attempt.override_eligible:
        raise Conflict("This failure type is not eligible for override.", code="not_override_eligible")
    if decision not in ("AUTHORIZE", "DENY"):
        raise ValidationFailed("decision must be AUTHORIZE or DENY.", details={"decision": [decision]})
    attempt.status = GateAttemptStatus.OVERRIDE_AUTHORIZED if decision == "AUTHORIZE" else GateAttemptStatus.OVERRIDE_DENIED
    attempt.override_decided_by = actor
    attempt.override_decided_at = now()
    attempt.override_justification = justification.strip()
    attempt.save()
    audit.record(actor, VmsRole.ADMIN, "GATE_OVERRIDE_" + decision, attempt,
                 visitor=attempt.visit.visitor if attempt.visit else None, message=attempt.override_justification,
                 metadata={"failures": attempt.failure_reasons, "gate": attempt.gate.code if attempt.gate else None})
    if attempt.attempted_by:
        notify_user(attempt.attempted_by, NotificationEvent.OVERRIDE_REQUESTED,
                    "Override {}".format("authorised" if decision == "AUTHORIZE" else "denied"),
                    "Admin {} the override for {}.".format(
                        "authorised" if decision == "AUTHORIZE" else "denied",
                        attempt.visit.reference if attempt.visit else "the blocked attempt"),
                    visit=attempt.visit, email=False)
    return attempt


# --------------------------------------------------------------------------
# VMS-UC-020 Record Manual Visit Log
# --------------------------------------------------------------------------

@transaction.atomic
def record_manual_log(actor, data):
    log_type = data.get("log_type")
    gate = get_gate(data.get("gate"), required=False)
    zone = Zone.objects.filter(code=data.get("zone"), is_active=True).first() if data.get("zone") else None
    if not security_covers(actor, gate=gate, zone=zone):
        raise NotAuthorized("Only assigned Security Personnel can record visit logs.")
    visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").filter(
        reference=data.get("reference")).first()
    if visit is None:
        raise NotFound("Visit not found.")
    current = now()
    if log_type == LogType.CHECK_IN:
        attempt = GateAttempt.objects.select_for_update(of=("self",)).filter(
            pk=data.get("attempt_id"), visit=visit, status=GateAttemptStatus.OVERRIDE_AUTHORIZED).first()
        if attempt is None:
            # UC-020 minimal guarantee: no fabricated successful entry.
            raise Conflict("A manual check-in needs an Admin-authorised override for this visit.",
                           code="override_required")
        gate = gate or attempt.gate
        visit.check_in_at = current
        visit.entry_gate = gate
        visit.last_seen_zone = zone or (gate.zone if gate else None)
        visit.last_seen_at = current
        workflow.apply(visit, "MANUAL_ENTRY", actor=actor, actor_role=VmsRole.SECURITY,
                       note="Override attempt {}".format(attempt.pk))
        log = _log(visit, LogType.CHECK_IN, LogMethod.MANUAL, actor, current, gate=gate, zone=visit.last_seen_zone,
                   device_id=data.get("device_id", ""), detail=data.get("detail", "Authorised override"),
                   is_manual=True, gate_attempt=attempt)
        attempt.status = GateAttemptStatus.MANUAL_ENTRY_RECORDED
        attempt.save(update_fields=["status"])
        notify_user(visit.host.user, NotificationEvent.VISITOR_CHECKED_IN, "Your visitor has arrived",
                    "{} was admitted at {} after an authorised override.".format(
                        visit.visitor.full_name, gate.name if gate else "the gate"), visit=visit, email=False)
    elif log_type == LogType.CHECK_OUT:
        return check_out(actor, {"reference": visit.reference, "gate": gate.code if gate else None,
                                 "device_id": data.get("device_id", "")}, method=LogMethod.MANUAL)
    elif log_type == LogType.ACCESS_DENIED:
        log = _log(visit, LogType.ACCESS_DENIED, LogMethod.MANUAL, actor, current, gate=gate, zone=zone,
                   device_id=data.get("device_id", ""), detail=data.get("detail", ""), is_manual=True)
    else:
        raise ValidationFailed("log_type must be CHECK_IN, CHECK_OUT or ACCESS_DENIED.", details={"log_type": [log_type]})
    audit.record(actor, VmsRole.SECURITY, "MANUAL_LOG_" + log_type, log, visitor=visit.visitor,
                 metadata={"visit": visit.reference})
    return log


# --------------------------------------------------------------------------
# VMS-UC-021 / 031 / 038 checkout (VMS-BR-105)
# --------------------------------------------------------------------------

ACTION_FOR_METHOD = {
    LogMethod.KIOSK: "SELF_CHECK_OUT",
    LogMethod.APP: "SELF_CHECK_OUT",
    LogMethod.AUTO: "AUTO_CHECK_OUT",
    LogMethod.OFFLINE: "OFFLINE_CHECK_OUT",
}


def complete_visit(visit, method, actor=None, actor_role=VmsRole.SYSTEM, at=None, gate=None, device_id="",
                   offline_event=None):
    at = at or now()
    if visit.status not in VisitStatus.ON_CAMPUS:
        raise Conflict("Visit {} is not on-site; nothing to check out.".format(visit.reference), code="not_on_site")
    visit.check_out_at = at
    visit.checkout_method = method
    workflow.apply(visit, ACTION_FOR_METHOD.get(method, "GATE_CHECK_OUT"), actor=actor, actor_role=actor_role)
    _log(visit, LogType.CHECK_OUT, method, actor, at, gate=gate, zone=gate.zone if gate else None, device_id=device_id,
         is_offline=method == LogMethod.OFFLINE, offline_event=offline_event,
         is_manual=method == LogMethod.MANUAL)
    deactivate_pass(getattr(visit, "visit_pass", None), actor, "VISIT_COMPLETED")
    audit.record(actor, actor_role, "VISITOR_CHECKED_OUT", visit, visitor=visit.visitor,
                 metadata={"method": method, "in": visit.check_in_at, "out": at})
    notify_user(visit.host.user, NotificationEvent.VISITOR_CHECKED_OUT, "Your visitor has left",
                "{} checked out at {} ({}).".format(visit.visitor.full_name, at.strftime("%H:%M"), method.lower()),
                visit=visit, email=False)  # AFR-169, in-app only "where configured"
    return visit


@transaction.atomic
def check_out(actor, data, method=None):
    gate = get_gate(data.get("gate"), required=False)
    if not security_covers(actor, gate=gate):
        raise NotAuthorized("Only assigned Security Personnel can check visitors out.")
    if data.get("reference"):
        visit = VisitRequest.objects.select_for_update(of=("self",)).filter(reference=data["reference"]).first()
        credential_type = None
    else:
        credential_type = data.get("credential_type")
        visit_pass = resolve_pass(credential_type, data.get("credential"), data.get("otp"))
        visit = VisitRequest.objects.select_for_update(of=("self",)).filter(pk=visit_pass.visit_id).first() if visit_pass else None
    if visit is None:
        raise NotFound("Unknown visit; no exit was recorded.", code="unknown_visit")
    method = method or CREDENTIAL_METHOD.get(credential_type, LogMethod.BADGE)
    return complete_visit(visit, method, actor=actor, actor_role=VmsRole.SECURITY, gate=gate,
                          device_id=data.get("device_id", ""))


@transaction.atomic
def self_check_out(visit, method):
    if not conf.self_checkout_enabled():
        raise Unavailable("Self-checkout is not available here; please check out at the gate.",
                          code="self_checkout_unavailable")
    visit = VisitRequest.objects.select_for_update(of=("self",)).get(pk=visit.pk)
    return complete_visit(visit, method, actor_role=VmsRole.VISITOR)


# --------------------------------------------------------------------------
# VMS-UC-028 / 039 offline entry and reconciliation (BW-VMS-11)
# --------------------------------------------------------------------------

def offline_snapshot(actor, gate_code, hours=24):
    gate = get_gate(gate_code)
    if not security_covers(actor, gate=gate):
        raise NotAuthorized("Only Security Personnel at this gate can download the offline cache.")
    current = now()
    passes = VisitPass.objects.filter(
        is_active=True, visit__status__in=[VisitStatus.PASS_ACTIVE, VisitStatus.ON_SITE],
        valid_until__gte=current, valid_from__lte=current + datetime.timedelta(hours=hours),
    ).select_related("visit", "visit__visitor").prefetch_related("permitted_zones")
    from .common import hash_secret
    return {
        "gate": gate.code,
        "generated_at": current,
        "passes": [{
            "reference": p.visit.reference,
            "visitor": p.visit.visitor.full_name,
            "pass_number": p.pass_number,
            "qr_token": p.qr_token,
            "otp_digest": hash_secret(p.pass_number + p.otp),
            "pass_type": p.pass_type,
            "valid_from": p.valid_from,
            "valid_until": p.valid_until,
            "zones": [z.code for z in p.permitted_zones.all()],
            "status": p.visit.status,
        } for p in passes],
    }


@transaction.atomic
def upload_offline_events(actor, data):
    gate = get_gate(data.get("gate"))
    if not security_covers(actor, gate=gate):
        raise NotAuthorized("Only Security Personnel at this gate can upload cached events.")
    created = []
    for raw in data.get("events") or []:
        client_id = str(raw.get("client_event_id") or "").strip()
        if not client_id:
            raise ValidationFailed("Every cached event needs a client_event_id.", details={"events": ["client_event_id"]})
        existing = OfflineGateEvent.objects.filter(client_event_id=client_id).first()
        if existing:  # idempotent re-upload: never duplicated, never silently discarded
            created.append(existing)
            continue
        if raw.get("event_type") not in (OfflineGateEvent.EVENT_CHECK_IN, OfflineGateEvent.EVENT_CHECK_OUT):
            raise ValidationFailed("event_type must be CHECK_IN or CHECK_OUT.", details={"events": [client_id]})
        if raw.get("credential_type") not in {c for c, _ in CredentialType.CHOICES} or not raw.get("occurred_at"):
            raise ValidationFailed("Cached event is missing its credential or time.", details={"events": [client_id]})
        created.append(OfflineGateEvent.objects.create(
            client_event_id=client_id, gate=gate, device_id=data.get("device_id", ""),
            credential_type=raw["credential_type"], credential_value=str(raw.get("credential", ""))[:64],
            otp=str(raw.get("otp", ""))[:6], event_type=raw["event_type"], occurred_at=raw["occurred_at"],
            uploaded_by=actor,
        ))
    audit.record(actor, VmsRole.SECURITY, "OFFLINE_EVENTS_UPLOADED", None,
                 message="{} cached event(s) from {}".format(len(created), gate.code))
    reconcile_offline_events([e.pk for e in created])
    return OfflineGateEvent.objects.filter(pk__in=[e.pk for e in created])


def _conflict(event, reason):
    event.status = OfflineEventStatus.CONFLICT
    event.conflict_reason = reason
    event.save(update_fields=["status", "conflict_reason"])
    return event


def _reconcile_one(event):
    current = now()
    visit_pass = resolve_pass(event.credential_type, event.credential_value, event.otp)
    if visit_pass is None:
        return _conflict(event, "Credential does not match any pass.")
    visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").get(pk=visit_pass.visit_id)
    event.visit = visit
    at = event.occurred_at
    if event.event_type == OfflineGateEvent.EVENT_CHECK_IN:
        if visit.status in VisitStatus.ON_CAMPUS | {VisitStatus.COMPLETED} and visit.check_in_at and \
                abs((visit.check_in_at - at).total_seconds()) <= 120:
            pass  # already applied (duplicate upload of the same entry)
        elif visit.status != VisitStatus.PASS_ACTIVE:
            return _conflict(event, "Visit was {} when the cached entry was synchronised.".format(visit.status))
        elif not (visit_pass.valid_from <= at <= visit_pass.valid_until):
            return _conflict(event, "Cached entry time is outside the pass validity window.")
        elif not visit_pass.is_active and not (visit_pass.deactivated_at and visit_pass.deactivated_at > at):
            return _conflict(event, "Pass was inactive at the cached entry time.")
        elif registry_check(visit.visitor, Checkpoint.GATE, current).disqualifying:
            return _conflict(event, "Visitor matches the published blacklist.")
        else:
            visit.check_in_at = at
            visit.entry_gate = event.gate
            visit.last_seen_zone = event.gate.zone if event.gate else None
            visit.last_seen_at = at
            workflow.apply(visit, "OFFLINE_CHECK_IN", actor_role=VmsRole.SYSTEM,
                           note="Offline event {}".format(event.client_event_id))
            _log(visit, LogType.CHECK_IN, LogMethod.OFFLINE, event.uploaded_by, at, gate=event.gate,
                 zone=visit.last_seen_zone, device_id=event.device_id, is_offline=True, offline_event=event)
            if event.credential_type == CredentialType.OTP and not visit_pass.otp_used_at:
                visit_pass.otp_used_at = at
                visit_pass.save(update_fields=["otp_used_at"])
    else:
        if visit.status == VisitStatus.COMPLETED and visit.check_out_at and \
                abs((visit.check_out_at - at).total_seconds()) <= 120:
            pass
        elif visit.status not in VisitStatus.ON_CAMPUS:
            return _conflict(event, "Visit was {} when the cached exit was synchronised.".format(visit.status))
        elif visit.check_in_at and at < visit.check_in_at:
            return _conflict(event, "Cached exit precedes the recorded entry.")
        else:
            complete_visit(visit, LogMethod.OFFLINE, actor=None, actor_role=VmsRole.SYSTEM, at=at, gate=event.gate,
                           device_id=event.device_id, offline_event=event)
    event.status = OfflineEventStatus.RECONCILED
    event.reconciled_at = current
    event.save(update_fields=["status", "reconciled_at", "visit"])
    return event


def reconcile_offline_events(event_ids=None):
    """VMS-UC-039 (System): synchronise cached events; flag conflicts, never overwrite."""
    query = OfflineGateEvent.objects.filter(status=OfflineEventStatus.PENDING).order_by("occurred_at", "id")
    if event_ids is not None:
        query = query.filter(pk__in=event_ids)
    processed, conflicts = [], []
    for event in query:
        with transaction.atomic():
            event = OfflineGateEvent.objects.select_for_update(of=("self",)).get(pk=event.pk)
            if event.status != OfflineEventStatus.PENDING:
                continue
            try:
                result = _reconcile_one(event)
            except Conflict as exc:
                result = _conflict(event, exc.message)
            processed.append(result)
            if result.status == OfflineEventStatus.CONFLICT:
                conflicts.append(result)
                audit.record(None, VmsRole.SYSTEM, "OFFLINE_RECONCILIATION_CONFLICT", result,
                             message=result.conflict_reason)
            else:
                audit.record(None, VmsRole.SYSTEM, "OFFLINE_EVENT_RECONCILED", result,
                             metadata={"visit": result.visit.reference if result.visit else None})
    if conflicts:
        notify_users(admins_covering(), NotificationEvent.OVERRIDE_REQUESTED, "Offline reconciliation conflicts",
                     "{} cached gate event(s) need review.".format(len(conflicts)), email=False)
    return processed


@transaction.atomic
def review_offline_conflict(actor, event_id, note):
    from .configuration import require_admin
    require_admin(actor)
    event = OfflineGateEvent.objects.select_for_update(of=("self",)).filter(pk=event_id, status=OfflineEventStatus.CONFLICT).first()
    if event is None:
        raise NotFound("Conflicted offline event not found.")
    if not (note or "").strip():
        raise ValidationFailed("A review note is required.", details={"note": ["required"]})
    event.status = OfflineEventStatus.REVIEWED
    event.reviewed_by, event.reviewed_at, event.review_note = actor, now(), note.strip()
    event.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note"])
    audit.record(actor, VmsRole.ADMIN, "OFFLINE_CONFLICT_REVIEWED", event, message=event.review_note)
    return event


# --------------------------------------------------------------------------
# VMS-UC-023 Validate Zone Access (VMS-BR-127/191/192/197)
# --------------------------------------------------------------------------

def _zone_alert(visit, zone, log, actor, basis):
    assignees = security_users(zone=zone)
    alert = SecurityAlert.objects.create(
        alert_type=AlertType.ZONE_VIOLATION, visit=visit, visitor=visit.visitor if visit else None, zone=zone,
        visit_log=log, message="Unauthorised access attempt to {} ({}).".format(zone.name, basis),
        metadata={"basis": basis}, assigned_to=assignees[0] if assignees else None,
    )
    notify_users(assignees + admins_covering(zones=[zone]), NotificationEvent.ZONE_VIOLATION, "Zone access violation",
                 "{} attempted to enter {}.".format(visit.visitor.full_name if visit else "Unknown credential",
                                                     zone.name), visit=visit, email=False)  # AFR-094 / AFR-172
    return alert


def evaluate_zone_access(visit_pass, zone, actor=None, method=LogMethod.QR, device_id="", actor_role=VmsRole.SECURITY):
    current = now()
    visit = visit_pass.visit if visit_pass else None
    if visit is None:
        allowed, basis = False, "UNKNOWN_CREDENTIAL"
    elif not visit_pass.is_active or visit.status != VisitStatus.ON_SITE:
        allowed, basis = False, "VISITOR_NOT_ACTIVE_ON_SITE"
    elif not (visit_pass.valid_from <= current <= visit_pass.valid_until):
        allowed, basis = False, "OUTSIDE_VALIDITY_WINDOW"
    else:
        allowed, basis = zone_permission(visit, zone, current)
    if allowed:
        log = _log(visit, LogType.ZONE_ACCESS, method, actor, current, zone=zone, device_id=device_id, detail=basis)
        visit.last_seen_zone, visit.last_seen_at = zone, current
        visit.save(update_fields=["last_seen_zone", "last_seen_at", "updated_at"])
        return {"allowed": True, "basis": basis, "log_id": log.pk, "visit": visit_summary(visit)}
    log = _log(visit, LogType.ACCESS_DENIED, method, actor, current, zone=zone, device_id=device_id, detail=basis)
    alert = _zone_alert(visit, zone, log, actor, basis) if visit else None
    if visit:
        audit.record(actor, actor_role, "ZONE_ACCESS_DENIED", log, visitor=visit.visitor,
                     metadata={"zone": zone.code, "basis": basis})
    return {"allowed": False, "basis": basis, "log_id": log.pk, "alert_id": alert.pk if alert else None,
            "visit": visit_summary(visit) if visit else None}


@transaction.atomic
def validate_zone_access(actor, data):
    zone = Zone.objects.filter(code=data.get("zone"), is_active=True).first()
    if zone is None:
        raise ValidationFailed("Unknown or inactive zone.", details={"zone": [data.get("zone")]})
    if not security_covers(actor, zone=zone):
        raise NotAuthorized("Only Security Personnel at this zone checkpoint can validate access.")
    visit_pass = resolve_pass(data.get("credential_type") or CredentialType.QR, data.get("credential"), data.get("otp"))
    return evaluate_zone_access(visit_pass, zone, actor=actor,
                                method=CREDENTIAL_METHOD.get(data.get("credential_type"), LogMethod.QR),
                                device_id=data.get("device_id", ""))


# --------------------------------------------------------------------------
# VMS-UC-024 Grant Temporary Zone Elevation (VMS-BR-096)
# --------------------------------------------------------------------------

@transaction.atomic
def grant_zone_elevation(actor, reference, data):
    visit = VisitRequest.objects.select_for_update(of=("self",)).filter(reference=reference).first()
    if visit is None:
        raise NotFound("Visit not found.")
    zones = zones_from_codes(data.get("zones"), "zones")
    if not zones:
        raise ValidationFailed("Name the zone(s) to elevate.", details={"zones": ["required"]})
    for zone in zones:
        if not admin_covers(actor, zones=[zone]):
            raise NotAuthorized("You are not an authorised Admin for zone {}.".format(zone.code))
    visit_pass = getattr(visit, "visit_pass", None)
    if visit.status not in (VisitStatus.PASS_ACTIVE, VisitStatus.ON_SITE) or not (visit_pass and visit_pass.is_active):
        raise Conflict("Elevation needs an active visit and pass.", code="visit_not_active")
    valid_from = data.get("valid_from") or now()
    valid_until = data.get("valid_until")
    if not valid_until or valid_until <= valid_from or valid_until <= now():
        raise ValidationFailed("Temporary elevation must be time-boxed with a future end (VMS-BR-096).",
                               details={"valid_until": ["required"]})
    if not (data.get("reason") or "").strip():
        raise ValidationFailed("A reason is required.", details={"reason": ["required"]})
    elevation = ZoneElevation.objects.create(visit=visit, valid_from=valid_from, valid_until=valid_until,
                                             reason=data["reason"].strip(), granted_by=actor)
    elevation.zones.set(zones)
    audit.record(actor, VmsRole.ADMIN, "ZONE_ELEVATION_GRANTED", elevation, visitor=visit.visitor,
                 metadata={"zones": [z.code for z in zones], "valid_until": valid_until, "visit": visit.reference})
    notify_role(VmsRole.SECURITY, NotificationEvent.REQUEST_APPROVED, "Temporary zone elevation",
                "{} may enter {} until {}.".format(visit.visitor.full_name, ", ".join(z.name for z in zones),
                                                  valid_until.strftime("%H:%M")), visit=visit)
    return elevation


# --------------------------------------------------------------------------
# VMS-UC-025 Handle Zone Violation Alert / suspicious-case escalation (AFR-024)
# --------------------------------------------------------------------------

@transaction.atomic
def handle_alert(actor, alert_id, outcome, note):
    from ..selectors import is_admin, is_security
    alert = SecurityAlert.objects.select_for_update(of=("self",)).select_related("zone", "gate", "visit").filter(pk=alert_id).first()
    if alert is None:
        raise NotFound("Alert not found.")
    if not (is_security(actor) or is_admin(actor)):
        raise NotAuthorized("Only Security Personnel or Admin can handle alerts.")
    if not (note or "").strip():
        raise ValidationFailed("Record the handling outcome.", details={"note": ["required"]})
    if outcome not in (AlertStatus.HANDLED, AlertStatus.ESCALATED, AlertStatus.FALSE_ALARM):
        raise ValidationFailed("outcome must be HANDLED, ESCALATED or FALSE_ALARM.", details={"outcome": [outcome]})
    if alert.status not in (AlertStatus.OPEN, AlertStatus.ESCALATED):
        raise Conflict("This alert is already closed.", code="alert_closed")
    if outcome == AlertStatus.ESCALATED and alert.status == AlertStatus.ESCALATED:
        raise Conflict("This alert is already escalated.", code="alert_escalated")
    alert.status = outcome
    alert.handled_by, alert.handled_at, alert.handling_note = actor, now(), note.strip()
    if outcome == AlertStatus.ESCALATED:
        alert.escalated_to_admin = True
        notify_users(admins_covering(zones=[alert.zone] if alert.zone else (), gate=alert.gate),
                     NotificationEvent.ALERT_ESCALATED, "Security alert escalated", alert.message + " " + note,
                     visit=alert.visit)
    alert.save()
    audit.record(actor, VmsRole.SECURITY, "ALERT_" + outcome, alert, visitor=alert.visitor, message=note)
    return alert


@transaction.atomic
def escalate_suspicious_case(actor, data):
    from ..selectors import is_security
    if not is_security(actor):
        raise NotAuthorized("Only Security Personnel can escalate suspicious cases.")
    if not (data.get("note") or "").strip():
        raise ValidationFailed("Describe the suspicious case.", details={"note": ["required"]})
    visit = VisitRequest.objects.filter(reference=data.get("reference")).first() if data.get("reference") else None
    attempt = GateAttempt.objects.filter(pk=data.get("attempt_id")).first() if data.get("attempt_id") else None
    gate = attempt.gate if attempt else get_gate(data.get("gate"), required=False)
    if visit is None and attempt is not None:
        visit = attempt.visit
    alert = SecurityAlert.objects.create(
        alert_type=AlertType.SUSPICIOUS_CASE, status=AlertStatus.ESCALATED, escalated_to_admin=True,
        visit=visit, visitor=visit.visitor if visit else None, gate=gate, gate_attempt=attempt,
        message=data["note"].strip(), handled_by=actor, handled_at=now(),
    )
    notify_users(admins_covering(gate=gate), NotificationEvent.ALERT_ESCALATED, "Suspicious case escalated",
                 alert.message, visit=visit)
    audit.record(actor, VmsRole.SECURITY, "SUSPICIOUS_CASE_ESCALATED", alert, visitor=alert.visitor,
                 message=alert.message)
    return alert
