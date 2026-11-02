"""Emergency muster services: VMS-UC-026/032 trigger, VMS-UC-027 roll-call (CW-VMS-06)."""

from django.db import transaction
from django.utils.dateparse import parse_datetime

from .. import audit
from ..constants import MusterStatus, NotificationEvent, RollCallStatus, RosterSource, VisitStatus, VmsRole
from ..errors import Conflict, NotAuthorized, NotFound, ValidationFailed
from ..models import EmergencyMuster, MusterRosterEntry, VisitRequest
from ..notifications import notify_user, notify_users, notify_visitor
from ..selectors import admins_covering, is_admin, is_security, now, security_users

DEFAULT_INSTRUCTIONS = "Please proceed calmly to the nearest assembly point and report to security staff."


def _host_name(visit):
    return visit.host.user.get_full_name() or visit.host.user.username


def _entry_for(muster, visit, live=True, cached=False, compare=False):
    return MusterRosterEntry.objects.create(
        muster=muster, visit=visit, visitor_name=visit.visitor.full_name, visitor_phone=visit.visitor.phone,
        visitor_email=visit.visitor.email, host_name=_host_name(visit),
        host_contact=visit.host.user.email or "",
        last_seen_zone=visit.last_seen_zone.name if visit.last_seen_zone_id else "",
        last_seen_at=visit.last_seen_at or visit.check_in_at, in_live_roster=live, in_cached_roster=cached,
        discrepancy=compare and live != cached,
    )


@transaction.atomic
def trigger_muster(actor, as_role, instructions="", cached_roster=None, offline_triggered_at=None):
    """VMS-BR-130: an authorised Admin (UC-026) or Security Personnel (UC-032) may trigger."""
    if as_role == VmsRole.ADMIN and not is_admin(actor):
        raise NotAuthorized("An active VMS Admin role is required.")
    if as_role == VmsRole.SECURITY and not is_security(actor):
        raise NotAuthorized("An active Security Personnel role is required.")
    if EmergencyMuster.objects.select_for_update(of=("self",)).filter(status=MusterStatus.ACTIVE).first() is not None:
        raise Conflict("An emergency muster is already active.", code="muster_active")
    current = now()
    muster = EmergencyMuster.objects.create(
        triggered_by=actor, triggered_by_role=as_role,
        triggered_at=parse_datetime(offline_triggered_at) if isinstance(offline_triggered_at, str) else (
            offline_triggered_at or current),
        assembly_instructions=(instructions or "").strip() or DEFAULT_INSTRUCTIONS,
        roster_source=RosterSource.CACHED if cached_roster is not None else RosterSource.LIVE,
    )
    live = {v.reference: v for v in VisitRequest.objects.filter(status__in=VisitStatus.ON_CAMPUS).select_related(
        "visitor", "host__user", "last_seen_zone")}
    cached_refs = set(cached_roster or [])
    unknown = sorted(r for r in cached_refs if r not in live and not VisitRequest.objects.filter(reference=r).exists())
    for reference, visit in live.items():
        _entry_for(muster, visit, live=True, cached=reference in cached_refs, compare=cached_roster is not None)
    # AFR-140/141: visitors only on the cached roster are kept and flagged, not dropped.
    for visit in VisitRequest.objects.filter(reference__in=cached_refs - set(live)).select_related(
            "visitor", "host__user", "last_seen_zone"):
        _entry_for(muster, visit, live=False, cached=True, compare=True)
    if unknown:
        muster.roster_incomplete = True
        muster.roster_note = "Cached roster referenced unknown visits: {}".format(", ".join(unknown))
        muster.save(update_fields=["roster_incomplete", "roster_note"])
    audit.record(actor, as_role, "EMERGENCY_MUSTER_TRIGGERED", muster,
                 metadata={"roster_size": muster.roster.count(), "source": muster.roster_source})
    # AFR-138/139: visitor alerts with assembly instructions (SMS where configured).
    for entry in muster.roster.select_related("visit", "visit__visitor", "visit__host__user"):
        notify_visitor(entry.visit.visitor, NotificationEvent.EMERGENCY_MUSTER, "EMERGENCY: campus muster",
                       muster.assembly_instructions, visit=entry.visit, sms=True)
        notify_user(entry.visit.host.user, NotificationEvent.EMERGENCY_MUSTER, "Emergency muster: your visitor",
                    "{} is on campus. {}".format(entry.visitor_name, muster.assembly_instructions), visit=entry.visit)
    responders = {u.pk: u for u in admins_covering() + security_users()}
    notify_users(list(responders.values()), NotificationEvent.EMERGENCY_MUSTER, "Emergency muster active",
                 "Muster triggered; {} visitor(s) on the roster.".format(muster.roster.count()))
    return muster


def _active_muster(muster_id):
    muster = EmergencyMuster.objects.select_for_update(of=("self",)).filter(pk=muster_id).first()
    if muster is None:
        raise NotFound("Muster not found.")
    if muster.status != MusterStatus.ACTIVE:
        raise Conflict("This muster is already completed.", code="muster_completed")
    return muster


@transaction.atomic
def update_roll_call(actor, muster_id, updates, source="live"):
    """VMS-UC-027 roll-call; ``source='cached'`` replays offline updates without overwriting newer ones."""
    if not is_security(actor):
        raise NotAuthorized("Only Security Personnel perform roll-call.")
    muster = _active_muster(muster_id)
    valid = {s for s, _ in RollCallStatus.CHOICES}
    applied, skipped = [], []
    for item in updates or []:
        status = item.get("status")
        if status not in valid:
            raise ValidationFailed("Invalid roll-call status.", details={"status": [status]})
        entry = muster.roster.filter(pk=item.get("entry_id")).first() if item.get("entry_id") else \
            muster.roster.filter(visit__reference=item.get("reference")).first()
        if entry is None:
            skipped.append({"item": item, "detail": "Not on this muster roster."})
            continue
        recorded_at = parse_datetime(item["recorded_at"]) if isinstance(item.get("recorded_at"), str) else item.get(
            "recorded_at")
        recorded_at = recorded_at or now()
        if source == "cached" and entry.updated_at and entry.updated_at >= recorded_at:
            skipped.append({"item": item, "detail": "A newer roll-call update already exists."})
            continue
        entry.status = status
        entry.note = item.get("note", entry.note)
        entry.updated_by, entry.updated_at = actor, recorded_at
        if source == "cached":
            entry.in_cached_roster = True
        entry.save()
        applied.append(entry.pk)
    audit.record(actor, VmsRole.SECURITY, "ROLL_CALL_UPDATED", muster,
                 metadata={"applied": applied, "skipped": len(skipped), "source": source})
    return applied, skipped


def build_report(muster):
    roster = list(muster.roster.all())
    counts = {s: sum(1 for e in roster if e.status == s) for s, _ in RollCallStatus.CHOICES}
    return {
        "muster_id": muster.pk,
        "triggered_at": muster.triggered_at.isoformat(),
        "triggered_by_role": muster.triggered_by_role,
        "finalized_at": muster.finalized_at.isoformat() if muster.finalized_at else None,
        "roster_source": muster.roster_source,
        "roster_incomplete": muster.roster_incomplete,
        "roster_note": muster.roster_note,
        "total": len(roster),
        "counts": counts,
        "unresolved": [{"reference": e.visit.reference, "visitor": e.visitor_name, "phone": e.visitor_phone,
                        "host": e.host_name, "last_seen_zone": e.last_seen_zone,
                        "last_seen_at": e.last_seen_at.isoformat() if e.last_seen_at else None}
                       for e in roster if e.status == RollCallStatus.PENDING],
        "discrepancies": [e.visit.reference for e in roster if e.discrepancy],
    }


@transaction.atomic
def finalize_muster(actor, muster_id):
    if not (is_security(actor) or is_admin(actor)):
        raise NotAuthorized("Only Security Personnel or Admin can finalise the muster.")
    muster = _active_muster(muster_id)
    muster.status = MusterStatus.COMPLETED
    muster.finalized_at, muster.finalized_by = now(), actor
    # Unaccounted visitors stay PENDING in the report; nobody is silently marked safe.
    muster.report = build_report(muster)
    muster.save()
    audit.record(actor, VmsRole.SECURITY if is_security(actor) else VmsRole.ADMIN, "EMERGENCY_MUSTER_COMPLETED",
                 muster, metadata=muster.report["counts"])
    return muster
