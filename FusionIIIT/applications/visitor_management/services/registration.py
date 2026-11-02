"""Registration and approval services.

VMS-UC-010 pre-register, VMS-UC-013 host decision, VMS-UC-014 pre-authorisation,
VMS-UC-017 walk-in, VMS-UC-033 contingency approval, VMS-UC-035 same-day urgent
exception, VMS-UC-008/009 bulk and special-event handling.
"""

import csv
import datetime
import io

from django.db import transaction
from django.utils.dateparse import parse_datetime

from applications.globals.models import ExtraInfo

from .. import audit, workflow
from ..constants import (
    BulkListKind,
    Channel,
    Checkpoint,
    EventStatus,
    IdDocumentType,
    IntegrationKey,
    NotificationEvent,
    PassType,
    VisitStatus,
    VmsRole,
)
from ..errors import Conflict, NotAuthorized, NotFound, RateLimited, Unavailable, ValidationFailed
from ..matching import identity_keys, strong_identity_q
from ..models import BulkVisitorList, HostProfile, PreAuthorization, Visitor, VisitorEvent, VisitRequest
from ..notifications import notify_role, notify_user, notify_visitor
from ..selectors import (
    admin_covers,
    host_extrainfo,
    integration_usable,
    is_eligible_host,
    now,
    policy_snapshot,
    security_covers,
)
from .common import (
    generate_reference,
    issue_pass,
    issue_visitor_token,
    minutes,
    raise_registry_alerts,
    registry_check,
    restricted_zone_ids,
    route_admin,
    validate_schedule,
    within_visiting_hours,
    zones_from_codes,
    find_preauthorization,
    find_vip_permission,
)
from .configuration import require_admin, require_campus_admin

IDENTITY_FIELDS = ("full_name", "id_doc_type", "id_doc_number", "phone", "email")


def resolve_host(host_id):
    """VMS-BR-185 host recognition through the institutional directory (AFR-217/218)."""
    if not integration_usable(IntegrationKey.CAMPUS_ID, default=True):
        raise Unavailable("Host lookup through the campus directory is currently unavailable.", code="host_lookup_unavailable")
    host = ExtraInfo.objects.select_related("user", "department").filter(pk=str(host_id)).first()
    if not is_eligible_host(host):
        raise ValidationFailed("Select a valid Faculty/Staff host.", details={"host_id": ["Not a valid host."]})
    return host


def host_is_available(host, at=None):
    profile = HostProfile.objects.filter(extra_info=host).first()
    if profile is None or profile.is_available:
        return True
    return bool(profile.unavailable_until and profile.unavailable_until <= (at or now()))


def _identity_payload(data):
    return {k: (data.get(k) or "").strip() for k in IDENTITY_FIELDS}


def _validate_identity(identity):
    """VMS-BR-037 mandatory fields, VMS-BR-186/187 identity document."""
    errors = {}
    if not identity["full_name"]:
        errors["full_name"] = ["This field is required."]
    if not identity["phone"]:
        errors["phone"] = ["This field is required."]
    if identity["id_doc_type"] not in {c for c, _ in IdDocumentType.CHOICES}:
        errors["id_doc_type"] = ["Must be one of Passport, National ID, Driver's License or Other (VMS-BR-187)."]
    if len(identity["id_doc_number"].replace(" ", "")) < 4:
        errors["id_doc_number"] = ["A valid government-issued ID document number is required (VMS-BR-186)."]
    if errors:
        raise ValidationFailed("Registration details are incomplete or invalid.", details=errors)


def _visitor_for(identity, extra, visitor_token_hash=None):
    """Re-use the caller's own visitor profile when they present their portal token."""
    visitor = None
    if visitor_token_hash:
        visitor = Visitor.objects.filter(access_token_hash=visitor_token_hash).first()
    if visitor is None:
        visitor = Visitor(**identity)
        is_new = True
    else:
        for key, value in identity.items():
            setattr(visitor, key, value)
        is_new = False
    visitor.organization = extra.get("organization", visitor.organization or "") or ""
    if extra.get("id_document"):
        visitor.id_document = extra["id_document"]
    if extra.get("photo"):
        visitor.photo = extra["photo"]
    visitor.save()
    return visitor, is_new


def _duplicate_exists(identity, host, start, end):
    """VMS-BR-038: an open request for the same visitor, host and overlapping time."""
    keys = identity_keys(**{k: identity[k] for k in ("full_name", "id_doc_number", "phone", "email")})
    return VisitRequest.objects.filter(
        host=host, status__in=VisitStatus.OPEN, scheduled_start__lt=end, scheduled_end__gt=start,
    ).filter(strong_identity_q(keys, prefix="visitor__")).exists()


def _host_zone_check(zones, snapshot):
    restricted = restricted_zone_ids(snapshot)
    blocked = [z.code for z in zones if z.pk in restricted]
    if blocked:
        raise ValidationFailed(
            "Restricted zones need a temporary Admin elevation or a VIP override.",
            code="restricted_zone", details={"permitted_zones": blocked})


# --------------------------------------------------------------------------
# VMS-UC-010 Pre-register Visit
# --------------------------------------------------------------------------

def pre_register(data, visitor_token_hash=None):
    current = now()
    snapshot = policy_snapshot()
    identity = _identity_payload(data)
    _validate_identity(identity)
    host = resolve_host(data.get("host_id"))
    purpose = data.get("purpose")
    start, end = data.get("scheduled_start"), data.get("scheduled_end")
    if not start or not end:
        raise ValidationFailed("Visit schedule is required.", details={"scheduled_start": ["required"]})
    if start <= current:
        raise ValidationFailed("Visit must be scheduled in the future.", details={"scheduled_start": ["past"]})
    validate_schedule(snapshot, start, end, current)
    zones = zones_from_codes(data.get("requested_zones"), "requested_zones")

    keys = identity_keys(identity["full_name"], identity["id_doc_number"], identity["phone"], identity["email"])
    result = registry_check(keys, Checkpoint.PRE_REGISTRATION, current)
    if result.disqualifying:
        # VMS-BR-051 reject, VMS-BR-117 alert. No request is created.
        raise_registry_alerts(result, Checkpoint.PRE_REGISTRATION, actor_role=VmsRole.VISITOR, identity=identity)
        raise NotAuthorized("The visit request could not be accepted. Please contact the campus security office.",
                            code="registration_rejected")
    if _duplicate_exists(identity, host, start, end):
        raise Conflict("A visit request for this visitor, host and time already exists.", code="duplicate_request")

    vip = find_vip_permission(keys, start, end)
    preauth = None if vip else find_preauthorization(host, keys, start, end, zones, purpose)
    window_ok = (start - current) >= minutes(snapshot["advance_registration_minutes"])
    urgent = bool(data.get("is_urgent"))

    if vip:
        action = "SUBMIT_VIP"
    elif preauth:
        action = "SUBMIT_PREAUTHORIZED"
    elif window_ok:
        action = "SUBMIT_STANDARD"
    elif urgent and start.date() == current.date():
        action = "SUBMIT_URGENT"  # VMS-BR-203
    else:
        raise ValidationFailed(
            "Visits must be registered at least {} minutes ahead (VMS-BR-202). Mark same-day urgent visits as urgent "
            "for Admin review.".format(snapshot["advance_registration_minutes"]),
            code="advance_window", details={"scheduled_start": ["inside advance-registration window"]})

    with transaction.atomic():
        visitor, is_new = _visitor_for(identity, data, visitor_token_hash)
        visit = VisitRequest(
            reference=generate_reference(), visitor=visitor, host=host, purpose=purpose,
            purpose_details=data.get("purpose_details", ""), scheduled_start=start, scheduled_end=end,
            channel=Channel.ONLINE, status="", is_urgent=urgent and action == "SUBMIT_URGENT",
            policy_id=None, policy_snapshot=snapshot, submitted_at=current,
            preauthorization=preauth, vip_permission=vip, watchlist_flag=bool(result.flags),
        )
        if snapshot.get("version"):
            from ..models import AccessPolicy
            visit.policy = AccessPolicy.objects.filter(version=snapshot["version"]).first()
        if action == "SUBMIT_STANDARD":
            visit.approval_deadline = current + minutes(snapshot["approval_timeout_minutes"])
        if action == "SUBMIT_URGENT":
            visit.assigned_admin = route_admin(zones)
        visit.save()
        visit.requested_zones.set(zones)
        workflow.apply(visit, action, actor_role=VmsRole.VISITOR)
        if result.flags:
            raise_registry_alerts(result, Checkpoint.PRE_REGISTRATION, actor_role=VmsRole.VISITOR, visitor=visitor,
                                  visit=visit, identity=identity)

        token = issue_visitor_token(visitor) if is_new else None
        audit.record(None, VmsRole.VISITOR, "VISIT_PRE_REGISTERED", visit, visitor=visitor,
                     message="{} submitted ({})".format(visit.reference, action),
                     metadata={"status": visit.status, "host": host.pk})
        submitted_msg = "Your visit request {} with {} has been received. Status: {}.".format(
            visit.reference, host.user.get_full_name() or host.user.username, visit.get_status_display())
        if token:
            submitted_msg += "\nVisitor portal access token: {}".format(token)
        notify_visitor(visitor, NotificationEvent.REQUEST_SUBMITTED, "Visit request received", submitted_msg, visit=visit)

        if action == "SUBMIT_STANDARD":
            notify_user(host.user, NotificationEvent.REQUEST_PENDING_FOR_HOST, "Visit request awaiting your decision",
                        "{} has requested a visit on {} ({}).".format(visitor.full_name, start.strftime("%d %b %H:%M"),
                                                                     visit.reference), visit=visit)
        elif action == "SUBMIT_URGENT":
            if visit.assigned_admin:
                notify_user(visit.assigned_admin, NotificationEvent.REQUEST_PENDING_FOR_ADMIN,
                            "Same-day urgent visit needs an exception decision",
                            "{} requested an urgent visit with {} ({}).".format(
                                visitor.full_name, host.user.get_full_name() or host.user.username, visit.reference),
                            visit=visit)
        else:
            pass_type = PassType.VIP if action == "SUBMIT_VIP" else PassType.PRE_REGISTERED
            pass_zones = zones if zones else ([] if vip else list(preauth.permitted_zones.all()))
            if not vip:
                pass_zones = [z for z in pass_zones if z.pk not in restricted_zone_ids(snapshot)]
            issue_pass(visit, pass_type, start, end, pass_zones, actor_role=VmsRole.SYSTEM, visitor_token=None)
            notify_user(host.user, NotificationEvent.REQUEST_APPROVED, "Visit authorised by bypass",
                        "{} ({}) was authorised through {}.".format(
                            visitor.full_name, visit.reference, "VIP override" if vip else "your pre-authorization"),
                        visit=visit, email=False)
            notify_role(VmsRole.SECURITY, NotificationEvent.REQUEST_APPROVED, "Expected visitor",
                        "{} expected {} ({}).".format(visitor.full_name, start.strftime("%d %b %H:%M"), visit.reference),
                        visit=visit)
        return visit, token


# --------------------------------------------------------------------------
# VMS-UC-017 Register Walk-in Visitor at Gate
# --------------------------------------------------------------------------

def _gate_or_error(gate_code):
    from ..models import Gate
    if not gate_code:
        return None
    gate = Gate.objects.select_related("zone").filter(code=gate_code, is_active=True).first()
    if gate is None:
        raise ValidationFailed("Unknown or inactive gate.", details={"gate": [gate_code]})
    return gate


def register_walk_in(actor, data):
    current = now()
    gate = _gate_or_error(data.get("gate"))
    if not security_covers(actor, gate=gate):
        raise NotAuthorized("Only Security Personnel assigned to this gate can register walk-ins.")
    snapshot = policy_snapshot()
    identity = _identity_payload(data)
    _validate_identity(identity)
    host = resolve_host(data.get("host_id"))
    if not within_visiting_hours(snapshot, current):
        raise ValidationFailed("Walk-in registration is outside visiting hours.", code="outside_visiting_hours")
    zones = zones_from_codes(data.get("requested_zones"), "requested_zones")

    event, lane = None, VisitRequest.LANE_NORMAL
    if data.get("event_id"):
        event = VisitorEvent.objects.filter(pk=data["event_id"]).first()
        if event is None:
            raise ValidationFailed("Unknown event.", details={"event_id": ["not found"]})
        if data.get("lane") == VisitRequest.LANE_OVERFLOW:
            # AFR-163 walk-in lane rate-limit control
            if not (event.overflow_walk_in_enabled and event.status == EventStatus.CONTROLS_ACTIVE):
                raise ValidationFailed("The overflow walk-in lane is not enabled for this event.", code="lane_disabled")
            lane = VisitRequest.LANE_OVERFLOW
            limit = event.walk_in_rate_limit_per_hour
            recent = VisitRequest.objects.filter(event=event, lane=VisitRequest.LANE_OVERFLOW,
                                                 submitted_at__gte=current - datetime.timedelta(hours=1)).count()
            if limit and recent >= limit:
                raise RateLimited("Overflow walk-in lane limit of {} per hour reached.".format(limit),
                                  code="overflow_rate_limited")

    keys = identity_keys(identity["full_name"], identity["id_doc_number"], identity["phone"], identity["email"])
    result = registry_check(keys, Checkpoint.WALK_IN, current)
    if result.disqualifying:
        raise_registry_alerts(result, Checkpoint.WALK_IN, actor=actor, actor_role=VmsRole.SECURITY, gate=gate,
                              identity=identity)
        raise NotAuthorized("Visitor matches an active blacklist entry. Walk-in registration blocked (VMS-BR-051).",
                            code="blacklist_match", details={"severity": [e.severity for e in result.disqualifying]})

    host_unavailable = bool(data.get("host_unavailable")) or not host_is_available(host, current)
    walk_in_minutes = snapshot["walk_in_pass_duration_minutes"]
    with transaction.atomic():
        visitor, is_new = _visitor_for(identity, data)
        visit = VisitRequest(
            reference=generate_reference(), visitor=visitor, host=host, purpose=data.get("purpose"),
            purpose_details=data.get("purpose_details", ""), scheduled_start=current,
            scheduled_end=current + minutes(walk_in_minutes), channel=Channel.WALK_IN, lane=lane, status="",
            policy_snapshot=snapshot, submitted_at=current, registered_by=actor, registration_gate=gate,
            host_unavailable=host_unavailable, event=event, watchlist_flag=bool(result.flags),
        )
        if snapshot.get("version"):
            from ..models import AccessPolicy
            visit.policy = AccessPolicy.objects.filter(version=snapshot["version"]).first()
        if host_unavailable:
            visit.contingency_deadline = current + minutes(snapshot["contingency_sla_minutes"])
            visit.assigned_admin = route_admin(zones, gate)
            action = "WALKIN_HOST_UNAVAILABLE"
        else:
            visit.approval_deadline = current + minutes(snapshot["approval_timeout_minutes"])
            action = "WALKIN_HOST_AVAILABLE"
        visit.save()
        visit.requested_zones.set(zones)
        workflow.apply(visit, action, actor=actor, actor_role=VmsRole.SECURITY)
        if result.flags:
            raise_registry_alerts(result, Checkpoint.WALK_IN, actor=actor, actor_role=VmsRole.SECURITY, visitor=visitor,
                                  visit=visit, gate=gate, identity=identity)
        token = issue_visitor_token(visitor) if is_new else None
        audit.record(actor, VmsRole.SECURITY, "WALK_IN_REGISTERED", visit, visitor=visitor,
                     message="{} registered at {} ({})".format(visit.reference, gate.code if gate else "gate", action))
        if host_unavailable:
            if visit.assigned_admin:
                notify_user(visit.assigned_admin, NotificationEvent.REQUEST_PENDING_FOR_ADMIN,
                            "Walk-in contingency approval needed",
                            "Host unavailable for walk-in {} ({}). Decide within {} minutes.".format(
                                visitor.full_name, visit.reference, snapshot["contingency_sla_minutes"]), visit=visit)
        else:
            notify_user(host.user, NotificationEvent.REQUEST_PENDING_FOR_HOST, "Walk-in visitor waiting at the gate",
                        "{} is at {} asking to see you ({}).".format(
                            visitor.full_name, gate.name if gate else "the gate", visit.reference), visit=visit)
        return visit, token


# --------------------------------------------------------------------------
# Lazy expiry used before any pending decision (VMS-UC-013 exception flow)
# --------------------------------------------------------------------------

def expire_if_due(visit, current=None):
    from .lifecycle import expire_visit
    current = current or now()
    if (visit.status == VisitStatus.PENDING_HOST_APPROVAL and visit.approval_deadline
            and visit.approval_deadline <= current):
        expire_visit(visit, current)
        return True
    return False


def _locked_visit(reference):
    visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").filter(
        reference=reference).first()
    if visit is None:
        raise NotFound("Visit request not found.")
    return visit


# --------------------------------------------------------------------------
# VMS-UC-013 Decide Visit Request
# --------------------------------------------------------------------------

def _decide_one(actor, visit, decision, data, current):
    host = host_extrainfo(actor)
    if host is None or visit.host_id != host.pk:
        raise NotAuthorized("Only the Host assigned to this request can decide it.")
    if expire_if_due(visit, current):
        raise Conflict("The approval window has elapsed; the request expired (VMS-BR-062).", code="request_expired")
    if visit.status != VisitStatus.PENDING_HOST_APPROVAL:
        raise Conflict("Only pending requests can be decided.", code="not_pending")
    snapshot = visit.policy_snapshot

    if decision == "REJECT":
        visit.decided_at, visit.decided_by = current, actor
        visit.rejection_reason = data.get("reason", "")
        visit.decision_notes = data.get("notes", "")
        workflow.apply(visit, "HOST_REJECT", actor=actor, actor_role=VmsRole.HOST, note=visit.rejection_reason)
        audit.record(actor, VmsRole.HOST, "VISIT_REJECTED", visit, visitor=visit.visitor, message=visit.rejection_reason)
        notify_visitor(visit.visitor, NotificationEvent.REQUEST_REJECTED, "Visit request rejected",
                       "Your visit request {} was rejected.{}".format(
                           visit.reference, " Reason: " + visit.rejection_reason if visit.rejection_reason else ""),
                       visit=visit)
        if visit.registered_by:
            notify_user(visit.registered_by, NotificationEvent.REQUEST_REJECTED, "Walk-in rejected by host",
                        "{} ({}) was rejected by the host.".format(visit.visitor.full_name, visit.reference),
                        visit=visit, email=False)
        return visit

    if decision != "APPROVE":
        raise ValidationFailed("decision must be APPROVE or REJECT.", details={"decision": [decision]})

    # Optional restrictions (AFR-015..017, 057..059)
    if data.get("permitted_zones") is not None:
        zones = zones_from_codes(data["permitted_zones"], "permitted_zones")
        _host_zone_check(zones, snapshot)
    else:
        restricted = restricted_zone_ids(snapshot)
        zones = [z for z in visit.requested_zones.all() if z.pk not in restricted]
    if visit.channel == Channel.WALK_IN:
        valid_from = current
        valid_until = current + minutes(snapshot["walk_in_pass_duration_minutes"])  # VMS-BR-053
        if data.get("valid_until"):
            if not (current < data["valid_until"] <= valid_until):
                raise ValidationFailed("A walk-in pass can only be shortened within the walk-in duration.",
                                       details={"valid_until": ["out of range"]})
            valid_until = data["valid_until"]
        pass_type = PassType.WALK_IN
    else:
        valid_from = data.get("valid_from") or visit.scheduled_start
        valid_until = data.get("valid_until") or visit.scheduled_end
        validate_schedule(snapshot, valid_from, valid_until, current)
        pass_type = PassType.PRE_REGISTERED
    visit.scheduled_start, visit.scheduled_end = valid_from, valid_until
    visit.decided_at, visit.decided_by = current, actor
    visit.special_instructions = data.get("special_instructions", "")
    visit.decision_notes = data.get("notes", "")
    workflow.apply(visit, "HOST_APPROVE", actor=actor, actor_role=VmsRole.HOST)
    issue_pass(visit, pass_type, valid_from, valid_until, zones, issued_by=actor, actor_role=VmsRole.HOST)
    audit.record(actor, VmsRole.HOST, "VISIT_APPROVED", visit, visitor=visit.visitor,
                 metadata={"zones": [z.code for z in zones], "valid_from": valid_from, "valid_until": valid_until})
    notify_visitor(visit.visitor, NotificationEvent.REQUEST_APPROVED, "Visit request approved",
                   "Your visit request {} was approved.{}".format(
                       visit.reference,
                       " Instructions: " + visit.special_instructions if visit.special_instructions else ""),
                   visit=visit)
    if visit.registered_by:
        notify_user(visit.registered_by, NotificationEvent.REQUEST_APPROVED, "Walk-in approved",
                    "{} ({}) was approved; a WALK_IN pass is active.".format(visit.visitor.full_name, visit.reference),
                    visit=visit, email=False)
    else:
        notify_role(VmsRole.SECURITY, NotificationEvent.REQUEST_APPROVED, "Expected visitor",
                    "{} expected {} ({}).".format(visit.visitor.full_name, valid_from.strftime("%d %b %H:%M"),
                                                  visit.reference), visit=visit)
    return visit


def _expire_late(reference):
    """Apply a due expiry in its own transaction so it survives the rejected decision."""
    with transaction.atomic():
        return expire_if_due(_locked_visit(reference))


def decide_visit(actor, reference, decision, data=None):
    if _expire_late(reference):
        raise Conflict("The approval window has elapsed; the request expired (VMS-BR-062).", code="request_expired")
    with transaction.atomic():
        visit = _locked_visit(reference)
        return _decide_one(actor, visit, decision, data or {}, now())


def bulk_decide(actor, references, decision, data=None):
    """AFR-060/061 bulk approval. Each request is decided independently."""
    results = []
    for reference in references:
        try:
            if _expire_late(reference):
                raise Conflict("The approval window has elapsed; the request expired.", code="request_expired")
            with transaction.atomic():
                visit = _locked_visit(reference)
                _decide_one(actor, visit, decision, data or {}, now())
                results.append({"reference": reference, "ok": True, "status": visit.status})
        except (Conflict, NotAuthorized, NotFound, ValidationFailed) as exc:
            results.append({"reference": reference, "ok": False, "detail": exc.message, "code": exc.code})
    return results


# --------------------------------------------------------------------------
# VMS-UC-035 Same-day urgent exception / VMS-UC-033 Walk-in contingency
# --------------------------------------------------------------------------

@transaction.atomic
def decide_urgent_exception(actor, reference, decision, note=""):
    visit = _locked_visit(reference)
    if not admin_covers(actor, zones=visit.requested_zones.all()):
        raise NotAuthorized("You are not an authorised Admin for this request.")
    if visit.status != VisitStatus.PENDING_ADMIN_EXCEPTION:
        raise Conflict("This request is not awaiting a same-day exception decision.", code="not_pending")
    current = now()
    visit.exception_decided_by, visit.exception_decided_at, visit.exception_note = actor, current, note
    if decision == "APPROVE":
        visit.approval_deadline = current + minutes(visit.policy_snapshot["approval_timeout_minutes"])
        workflow.apply(visit, "EXCEPTION_APPROVE", actor=actor, actor_role=VmsRole.ADMIN, note=note)
        notify_user(visit.host.user, NotificationEvent.REQUEST_PENDING_FOR_HOST, "Urgent visit awaiting your decision",
                    "Admin approved the same-day exception for {} ({}).".format(visit.visitor.full_name, visit.reference),
                    visit=visit)
    elif decision == "REJECT":
        visit.rejection_reason = note
        workflow.apply(visit, "EXCEPTION_REJECT", actor=actor, actor_role=VmsRole.ADMIN, note=note)
        notify_visitor(visit.visitor, NotificationEvent.REQUEST_REJECTED, "Urgent visit not approved",
                       "Your same-day urgent request {} was not approved.".format(visit.reference), visit=visit)
    else:
        raise ValidationFailed("decision must be APPROVE or REJECT.", details={"decision": [decision]})
    audit.record(actor, VmsRole.ADMIN, "URGENT_EXCEPTION_" + decision, visit, visitor=visit.visitor, message=note)
    return visit


@transaction.atomic
def decide_contingency(actor, reference, decision, note=""):
    visit = _locked_visit(reference)
    if not admin_covers(actor, zones=visit.requested_zones.all(), gate=visit.registration_gate):
        raise NotAuthorized("Only the relevant Admin may give contingency approval (VMS-BR-049).")
    if visit.status != VisitStatus.PENDING_ADMIN_CONTINGENCY:
        raise Conflict("This walk-in is not awaiting contingency approval.", code="not_pending")
    current = now()
    if decision == "APPROVE":
        if visit.contingency_deadline and current > visit.contingency_deadline:
            # VMS-BR-050: no pass through this path once the SLA window has passed.
            raise Conflict("The contingency SLA window has elapsed; this walk-in cannot be approved.",
                           code="contingency_sla_elapsed")
        snapshot = visit.policy_snapshot
        restricted = restricted_zone_ids(snapshot)
        zones = [z for z in visit.requested_zones.all() if z.pk not in restricted]
        valid_until = current + minutes(snapshot["walk_in_pass_duration_minutes"])
        visit.decided_at, visit.decided_by, visit.decision_notes = current, actor, note
        visit.scheduled_start, visit.scheduled_end = current, valid_until
        workflow.apply(visit, "CONTINGENCY_APPROVE", actor=actor, actor_role=VmsRole.ADMIN, note=note)
        issue_pass(visit, PassType.WALK_IN, current, valid_until, zones, issued_by=actor, actor_role=VmsRole.ADMIN)
        if visit.registered_by:
            notify_user(visit.registered_by, NotificationEvent.REQUEST_APPROVED, "Contingency approval granted",
                        "{} ({}) approved by Admin; WALK_IN pass active.".format(visit.visitor.full_name,
                                                                                 visit.reference),
                        visit=visit, email=False)
    elif decision == "REJECT":
        visit.decided_at, visit.decided_by, visit.rejection_reason = current, actor, note
        workflow.apply(visit, "CONTINGENCY_REJECT", actor=actor, actor_role=VmsRole.ADMIN, note=note)
        if visit.registered_by:
            notify_user(visit.registered_by, NotificationEvent.REQUEST_REJECTED, "Contingency approval refused",
                        "{} ({}) was not approved.".format(visit.visitor.full_name, visit.reference),
                        visit=visit, email=False)
    else:
        raise ValidationFailed("decision must be APPROVE or REJECT.", details={"decision": [decision]})
    audit.record(actor, VmsRole.ADMIN, "CONTINGENCY_" + decision, visit, visitor=visit.visitor, message=note)
    return visit


# --------------------------------------------------------------------------
# VMS-UC-014 Pre-authorize Recurring Visitor
# --------------------------------------------------------------------------

@transaction.atomic
def create_preauthorization(actor, data):
    host = host_extrainfo(actor)
    if host is None:
        raise NotAuthorized("Only Faculty/Staff hosts can pre-authorize visitors.")
    identity = _identity_payload(data)
    errors = {}
    if not identity["full_name"]:
        errors["full_name"] = ["This field is required."]
    if not (identity["id_doc_number"] or identity["phone"]):
        errors["identity"] = ["Give the visitor's ID document number or phone."]
    valid_from = data.get("valid_from") or now()
    valid_until = data.get("valid_until")
    if not valid_until or valid_until <= valid_from or valid_until <= now():
        errors["valid_until"] = ["Give a future end after valid_from."]
    if errors:
        raise ValidationFailed("Invalid pre-authorization.", details=errors)
    zones = zones_from_codes(data.get("permitted_zones"), "permitted_zones")
    _host_zone_check(zones, policy_snapshot())
    preauth = PreAuthorization(host=host, purpose=data.get("purpose") or "", valid_from=valid_from,
                               valid_until=valid_until, notes=data.get("notes", ""), **identity)
    preauth.save()
    preauth.permitted_zones.set(zones)
    audit.record(actor, VmsRole.HOST, "PREAUTHORIZATION_CREATED", preauth,
                 message="Pre-authorized {}".format(identity["full_name"]),
                 metadata={"valid_until": valid_until, "zones": [z.code for z in zones]})
    return preauth


@transaction.atomic
def revoke_preauthorization(actor, preauth_id):
    host = host_extrainfo(actor)
    preauth = PreAuthorization.objects.filter(pk=preauth_id, host=host, is_active=True).first() if host else None
    if preauth is None:
        raise NotFound("Active pre-authorization not found.")
    preauth.is_active = False
    preauth.revoked_at = now()
    preauth.save(update_fields=["is_active", "revoked_at"])
    audit.record(actor, VmsRole.HOST, "PREAUTHORIZATION_REVOKED", preauth)
    return preauth


def set_host_availability(actor, is_available, unavailable_until=None):
    host = host_extrainfo(actor)
    if host is None:
        raise NotAuthorized("Only Faculty/Staff hosts have an availability setting.")
    profile, _ = HostProfile.objects.get_or_create(extra_info=host)
    profile.is_available = bool(is_available)
    profile.unavailable_until = None if is_available else unavailable_until
    profile.save()
    return profile


# --------------------------------------------------------------------------
# VMS-UC-008 / 009 Bulk lists and special events (CW-VMS-07)
# --------------------------------------------------------------------------

@transaction.atomic
def create_event(actor, data):
    require_campus_admin(actor)
    host = resolve_host(data.get("host_id"))
    starts_at, ends_at = data.get("starts_at"), data.get("ends_at")
    if not starts_at or not ends_at or ends_at <= starts_at:
        raise ValidationFailed("Event needs a start before its end.", details={"ends_at": ["invalid"]})
    zones = zones_from_codes(data.get("venue_zones"), "venue_zones")
    event = VisitorEvent.objects.create(name=data.get("name") or "Event", host=host, starts_at=starts_at,
                                        ends_at=ends_at, external_event_ref=data.get("external_event_ref", ""),
                                        created_by=actor)
    event.venue_zones.set(zones)
    audit.record(actor, VmsRole.ADMIN, "EVENT_CREATED", event, message=event.name)
    return event


BULK_COLUMNS = ("full_name", "phone", "email", "organization", "id_doc_type", "id_doc_number", "slot_start", "slot_end")


def parse_bulk_file(uploaded):
    """CSV or XLSX with a header row. Raises ValidationFailed when unreadable (UC-008 exception flow)."""
    name = (getattr(uploaded, "name", "") or "").lower()
    try:
        if name.endswith(".xlsx"):
            import openpyxl
            workbook = openpyxl.load_workbook(uploaded, read_only=True, data_only=True)
            rows = list(workbook.active.iter_rows(values_only=True))
            header = [str(h or "").strip().lower() for h in rows[0]]
            return [dict(zip(header, ["" if v is None else v for v in row])) for row in rows[1:] if any(row)]
        content = uploaded.read()
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("missing header")
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]
    except Exception as exc:
        raise ValidationFailed("The visitor list could not be parsed: {}".format(exc), code="unparseable_list")


def _as_datetime(value):
    if isinstance(value, datetime.datetime):
        return value
    return parse_datetime(str(value)) if value else None


@transaction.atomic
def process_bulk_list(actor, data, rows, source_file=None):
    require_campus_admin(actor)
    kind = data.get("kind")
    current = now()
    if kind == BulkListKind.EVENT:
        event = VisitorEvent.objects.select_for_update(of=("self",)).filter(pk=data.get("event_id")).first()
        if event is None:
            raise ValidationFailed("Event context is required for an event list.", code="missing_event",
                                   details={"event_id": ["required"]})
        if event.status == EventStatus.CLOSED:
            raise Conflict("The event is closed.", code="event_closed")
        host, valid_from, valid_until = event.host, event.starts_at, event.ends_at
        zones = zones_from_codes(data["zones"], "zones") if data.get("zones") else list(event.venue_zones.all())
    elif kind == BulkListKind.RECURRING_VENDOR:
        event = None
        host = resolve_host(data.get("host_id"))
        valid_from, valid_until = data.get("valid_from"), data.get("valid_until")
        if not valid_from or not valid_until or valid_until <= valid_from:
            raise ValidationFailed("Vendor lists need a validity window.", details={"valid_until": ["invalid"]})
        zones = zones_from_codes(data.get("zones"), "zones")
    else:
        raise ValidationFailed("kind must be EVENT or RECURRING_VENDOR.", details={"kind": [kind]})
    if not rows:
        raise ValidationFailed("The visitor list is empty.", code="empty_list")
    snapshot = policy_snapshot()
    _host_zone_check(zones, snapshot)

    bulk = BulkVisitorList.objects.create(kind=kind, event=event, host=host, valid_from=valid_from,
                                          valid_until=valid_until, source_file=source_file, uploaded_by=actor,
                                          rows_total=len(rows))
    bulk.zones.set(zones)
    accepted, errors, seen_docs = 0, [], set()
    for index, raw in enumerate(rows, start=2):
        identity = {k: str(raw.get(k) or "").strip() for k in IDENTITY_FIELDS}
        identity["id_doc_type"] = identity["id_doc_type"].upper().replace(" ", "_").replace("'", "")
        try:
            _validate_identity(identity)
            doc_key = identity_keys(id_doc_number=identity["id_doc_number"])["id_doc_key"]
            if doc_key in seen_docs:
                raise ValidationFailed("Duplicate ID document in this list.", code="duplicate_row")
            seen_docs.add(doc_key)
            slot_start = _as_datetime(raw.get("slot_start")) or valid_from
            slot_end = _as_datetime(raw.get("slot_end")) or valid_until
            if not (valid_from <= slot_start < slot_end <= valid_until):
                raise ValidationFailed("Slot must fall inside the list validity.", code="bad_slot")
            result = registry_check(identity, Checkpoint.BULK, current)
            if result.disqualifying:
                raise_registry_alerts(result, Checkpoint.BULK, actor=actor, actor_role=VmsRole.ADMIN, identity=identity)
                raise ValidationFailed("Row matches the blacklist.", code="blacklist_match")
        except ValidationFailed as exc:
            errors.append({"row": index, "detail": exc.message, "code": exc.code, "errors": exc.details})
            continue
        visitor = Visitor(organization=str(raw.get("organization") or ""), **identity)
        visitor.save()
        visit = VisitRequest.objects.create(
            reference=generate_reference(), visitor=visitor, host=host,
            purpose="EVENT" if kind == BulkListKind.EVENT else "VENDOR",
            purpose_details=event.name if event else "Recurring vendor list", scheduled_start=slot_start,
            scheduled_end=slot_end, channel=Channel.BULK, status="", policy_snapshot=snapshot, submitted_at=current,
            event=event, bulk_list=bulk, registered_by=actor, watchlist_flag=bool(result.flags),
        )
        visit.requested_zones.set(zones)
        workflow.apply(visit, "BULK_ACCEPT", actor=actor, actor_role=VmsRole.ADMIN)
        token = issue_visitor_token(visitor)
        # AFR-155/156: generate and distribute event passes (BR-211: approved list -> PRE_REGISTERED)
        issue_pass(visit, PassType.PRE_REGISTERED, slot_start, slot_end, zones, issued_by=actor,
                   actor_role=VmsRole.ADMIN, visitor_token=token)
        accepted += 1
    bulk.rows_accepted, bulk.rows_rejected, bulk.row_errors = accepted, len(errors), errors
    bulk.save(update_fields=["rows_accepted", "rows_rejected", "row_errors"])
    if event is not None and accepted and event.status == EventStatus.DRAFT:
        event.status = EventStatus.PASSES_ACTIVE
        event.save(update_fields=["status", "updated_at"])
    audit.record(actor, VmsRole.ADMIN, "BULK_LIST_PROCESSED", bulk,
                 message="{} accepted, {} rejected".format(accepted, len(errors)))
    return bulk


@transaction.atomic
def configure_event_controls(actor, event_id, data):
    require_admin(actor)
    event = VisitorEvent.objects.select_for_update(of=("self",)).filter(pk=event_id).first()
    if event is None:
        raise NotFound("Event not found.")
    if event.status not in (EventStatus.PASSES_ACTIVE, EventStatus.CONTROLS_ACTIVE):
        raise Conflict("Event entry controls need active event passes first.", code="event_not_ready")
    overflow = bool(data.get("overflow_walk_in_enabled", event.overflow_walk_in_enabled))
    limit = data.get("walk_in_rate_limit_per_hour", event.walk_in_rate_limit_per_hour)
    if overflow and (not limit or int(limit) <= 0):
        raise ValidationFailed("An overflow walk-in lane needs a positive hourly rate limit.",
                               details={"walk_in_rate_limit_per_hour": ["required"]})
    event.fast_lane_enabled = bool(data.get("fast_lane_enabled", event.fast_lane_enabled))
    event.overflow_walk_in_enabled = overflow
    event.walk_in_rate_limit_per_hour = int(limit) if limit else None
    event.status = EventStatus.CONTROLS_ACTIVE
    event.save()
    audit.record(actor, VmsRole.ADMIN, "EVENT_CONTROLS_CONFIGURED", event,
                 metadata={"fast_lane": event.fast_lane_enabled, "overflow": overflow, "limit": limit})
    notify_role(VmsRole.SECURITY, NotificationEvent.REQUEST_APPROVED, "Event entry controls active",
                "{}: fast lane {}, overflow lane {}.".format(event.name, "on" if event.fast_lane_enabled else "off",
                                                             "on" if overflow else "off"))
    return event
