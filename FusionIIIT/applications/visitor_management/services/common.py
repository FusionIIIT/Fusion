"""Shared business-rule helpers used by every VMS service."""

import datetime
import hashlib
import secrets
import string
from collections import namedtuple

from django.db.models import Q

from .. import audit, conf
from ..constants import (
    AlertType,
    Checkpoint,
    NotificationEvent,
    RegistryEntryState,
    RegistryListType,
    SafeListScope,
    VmsRole,
    ZoneAccessLevel,
)
from ..errors import ValidationFailed
from ..matching import identity_keys, identity_q, keys_for, strong_identity_q
from ..models import (
    PreAuthorization,
    RegistryEntry,
    SecurityAlert,
    VipPermission,
    VisitPass,
    VisitRequest,
    Zone,
    ZoneElevation,
)
from ..notifications import notify_users, notify_visitor
from ..selectors import admins_covering, now, security_users

_ALPHABET = string.ascii_uppercase + string.digits


# --------------------------------------------------------------------------
# Identifiers and secrets
# --------------------------------------------------------------------------

def _random_code(length=6):
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_reference():
    stamp = now().strftime("%Y%m%d")
    while True:
        reference = "VMS-{}-{}".format(stamp, _random_code())
        if not VisitRequest.objects.filter(reference=reference).exists():
            return reference


def generate_pass_number():
    stamp = now().strftime("%y%m%d")
    while True:
        number = "VP{}{}".format(stamp, _random_code())
        if not VisitPass.objects.filter(pass_number=number).exists():
            return number


def new_qr_token():
    while True:
        token = secrets.token_urlsafe(24)
        if not VisitPass.objects.filter(qr_token=token).exists():
            return token


def new_otp():
    return "{:06d}".format(secrets.randbelow(10 ** 6))


def hash_secret(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def issue_visitor_token(visitor):
    """Secret for the visitor portal. Only the digest is persisted."""
    token = secrets.token_urlsafe(32)
    visitor.access_token_hash = hash_secret(token)
    visitor.save(update_fields=["access_token_hash"])
    return token


def mask(value, keep=4):
    value = value or ""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]


# --------------------------------------------------------------------------
# Zones and policy values
# --------------------------------------------------------------------------

def zones_from_codes(codes, field="zones"):
    codes = [c for c in (codes or []) if c]
    if not codes:
        return []
    zones = list(Zone.objects.filter(code__in=codes, is_active=True))
    missing = sorted(set(codes) - {z.code for z in zones})
    if missing:
        raise ValidationFailed("Unknown or inactive zone(s): {}".format(", ".join(missing)),
                               details={field: missing})
    return zones


def restricted_zone_ids(snapshot):
    return set(snapshot.get("restricted_zone_ids") or [])


def _parse_time(value):
    if not value:
        return None
    return datetime.datetime.strptime(value, "%H:%M").time()


def validate_schedule(snapshot, start, end, current=None, require_future=True):
    """VMS-BR-193 maximum duration and the configured visiting hours."""
    current = current or now()
    errors = {}
    if end <= start:
        errors["scheduled_end"] = ["Visit end must be after its start."]
    if require_future and end <= current:
        errors["scheduled_end"] = ["Visit end must be in the future."]
    max_minutes = snapshot["max_visit_duration_minutes"]
    if end > start and (end - start) > datetime.timedelta(minutes=max_minutes):
        errors["scheduled_end"] = [
            "Visit duration exceeds the policy maximum of {} minutes (VMS-BR-193).".format(max_minutes)
        ]
    hours_start = _parse_time(snapshot.get("visiting_hours_start"))
    hours_end = _parse_time(snapshot.get("visiting_hours_end"))
    if hours_start and hours_end:
        if start.date() != end.date() or start.time() < hours_start or end.time() > hours_end:
            errors["scheduled_start"] = ["Visit must fall within visiting hours {}-{}.".format(
                snapshot["visiting_hours_start"], snapshot["visiting_hours_end"])]
    if errors:
        raise ValidationFailed("Visit schedule is not allowed by the access policy.", details=errors)


def within_visiting_hours(snapshot, moment):
    hours_start = _parse_time(snapshot.get("visiting_hours_start"))
    hours_end = _parse_time(snapshot.get("visiting_hours_end"))
    if not (hours_start and hours_end):
        return True
    return hours_start <= moment.time() <= hours_end


def minutes(value):
    return datetime.timedelta(minutes=int(value))


# --------------------------------------------------------------------------
# Blacklist / watchlist / safe-list runtime checks (VMS-BR-051/112/116/117/118/119/120)
# --------------------------------------------------------------------------

RegistryResult = namedtuple("RegistryResult", "disqualifying flags exempted")


def _live_entries(at):
    return RegistryEntry.objects.filter(
        state=RegistryEntryState.PUBLISHED,  # VMS-BR-120: drafts never reach runtime
        is_active=True,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=at))


def registry_check(identity, checkpoint, at=None):
    """Return blacklist/watchlist hits for an identity at a checkpoint.

    ``identity`` is any object/dict with name, id document, phone and e-mail.
    A valid safe-list entry whose scope covers the checkpoint exempts the
    identity (VMS-BR-118); safe-list entries always carry an expiry (VMS-BR-119).
    """
    at = at or now()
    if isinstance(identity, dict):
        keys = identity if "id_doc_key" in identity else identity_keys(
            identity.get("full_name", ""), identity.get("id_doc_number", ""),
            identity.get("phone", ""), identity.get("email", ""))
    else:
        keys = keys_for(identity)
    hits = list(_live_entries(at).filter(identity_q(keys)).exclude(list_type=RegistryListType.SAFELIST))
    if not hits:
        return RegistryResult([], [], [])
    scope = SafeListScope.GATE if checkpoint == Checkpoint.GATE else SafeListScope.REGISTRATION
    safe = _live_entries(at).filter(
        list_type=RegistryListType.SAFELIST,
        expires_at__isnull=False,
        safelist_scope__in=[SafeListScope.ALL, scope],
    ).filter(strong_identity_q(keys)).exists()
    if safe:
        return RegistryResult([], [], hits)
    blacklist = [h for h in hits if h.list_type == RegistryListType.BLACKLIST]
    watchlist = [h for h in hits if h.list_type == RegistryListType.WATCHLIST]
    if conf.watchlist_rejects():
        return RegistryResult(blacklist + watchlist, [], [])
    return RegistryResult(blacklist, watchlist, [])


def raise_registry_alerts(result, checkpoint, actor=None, actor_role=VmsRole.SYSTEM, visitor=None, visit=None,
                          gate=None, identity=None, gate_attempt=None):
    """VMS-BR-117 / AFR-117 / AFR-173: alert security authorities and preserve the event."""
    alerts = []
    entries = [(e, AlertType.BLACKLIST_MATCH) for e in result.disqualifying]
    entries += [(e, AlertType.WATCHLIST_MATCH) for e in result.flags]
    if not entries:
        return alerts
    identity = identity or {}
    for entry, alert_type in entries:
        alert = SecurityAlert.objects.create(
            alert_type=alert_type,
            checkpoint=checkpoint,
            visit=visit,
            visitor=visitor,
            gate=gate,
            registry_entry=entry,
            gate_attempt=gate_attempt,
            message="{} match at {} (severity {}).".format(entry.get_list_type_display(), checkpoint, entry.severity),
            metadata={
                "identity": {k: identity.get(k, "") for k in ("full_name", "phone", "email")},
                "id_doc_hint": mask(identity.get("id_doc_number", "")),
                "severity": entry.severity,
                "rejected": alert_type == AlertType.BLACKLIST_MATCH or conf.watchlist_rejects(),
            },
        )
        alerts.append(alert)
        audit.record(actor, actor_role, "REGISTRY_MATCH", alert,
                     message=alert.message, metadata={"checkpoint": checkpoint, "entry": entry.pk},
                     visitor=visitor)
    recipients = admins_covering(gate=gate) + security_users(gate=gate)
    seen, unique = set(), []
    for user in recipients:
        if user.pk not in seen:
            seen.add(user.pk)
            unique.append(user)
    notify_users(unique, NotificationEvent.BLACKLIST_MATCH, "Blacklist/watchlist match",
                 "A {} match was detected at {}.".format(
                     "blacklist" if result.disqualifying else "watchlist", checkpoint.replace("_", " ").lower()),
                 visit=visit)
    return alerts


# --------------------------------------------------------------------------
# Approval bypasses (VMS-BR-195/196/197)
# --------------------------------------------------------------------------

def find_preauthorization(host, identity_keys, start, end, zones, purpose=None):
    candidates = PreAuthorization.objects.filter(
        host=host, is_active=True, revoked_at__isnull=True, valid_from__lte=start, valid_until__gte=end,
    ).filter(strong_identity_q(identity_keys)).prefetch_related("permitted_zones")
    wanted = {z.pk for z in zones}
    for preauth in candidates:
        if preauth.purpose and purpose and preauth.purpose != purpose:
            continue
        permitted = {z.pk for z in preauth.permitted_zones.all()}
        if wanted and not wanted.issubset(permitted):
            continue
        return preauth
    return None


def find_vip_permission(identity_keys, start, end):
    return VipPermission.objects.filter(
        visit__isnull=True, is_active=True, revoked_at__isnull=True, bypass_host_approval=True,
        valid_from__lte=start, valid_until__gte=end,
    ).filter(strong_identity_q(identity_keys)).order_by("-granted_at").first()


def active_vip_for_visit(visit, at=None):
    at = at or now()
    keys = keys_for(visit.visitor)
    query = VipPermission.objects.filter(
        is_active=True, revoked_at__isnull=True, valid_from__lte=at, valid_until__gte=at,
    ).filter(Q(visit=visit) | (Q(visit__isnull=True) & strong_identity_q(keys)))
    if visit.vip_permission_id:
        query = query | VipPermission.objects.filter(
            pk=visit.vip_permission_id, is_active=True, revoked_at__isnull=True,
            valid_from__lte=at, valid_until__gte=at)
    return query.distinct().order_by("-granted_at")


# --------------------------------------------------------------------------
# Zone permission (VMS-BR-191, 096, 127/129, 197)
# --------------------------------------------------------------------------

def zone_permission(visit, zone, at=None):
    """Decide whether ``visit`` may enter ``zone``. Returns (allowed, basis)."""
    at = at or now()
    restricted = restricted_zone_ids(visit.policy_snapshot)
    if zone.access_level == ZoneAccessLevel.PUBLIC and zone.pk not in restricted:
        return True, "PUBLIC_ZONE"
    if ZoneElevation.objects.filter(visit=visit, zones=zone, valid_from__lte=at, valid_until__gt=at).exists():
        return True, "TEMPORARY_ELEVATION"
    for vip in active_vip_for_visit(visit, at):
        if vip.zone_scope == VipPermission.ZONE_SCOPE_ALL:
            return True, "VIP_OVERRIDE"
        if vip.zone_scope == VipPermission.ZONE_SCOPE_LISTED and vip.zones.filter(pk=zone.pk).exists():
            return True, "VIP_OVERRIDE"
    if zone.pk in restricted:
        return False, "RESTRICTED_ZONE"
    visit_pass = getattr(visit, "visit_pass", None)
    if visit_pass is not None and visit_pass.permitted_zones.filter(pk=zone.pk).exists():
        return True, "PASS_PERMISSION"
    return False, "ZONE_NOT_PERMITTED"


# --------------------------------------------------------------------------
# Pass issuance (VMS-CFR-020, VMS-BR-211)
# --------------------------------------------------------------------------

def pass_message(visit_pass, visitor_token=None):
    zones = ", ".join(visit_pass.permitted_zones.values_list("name", flat=True)) or "general campus areas"
    lines = [
        "Your visitor pass {} ({}) is ready.".format(visit_pass.pass_number, visit_pass.get_pass_type_display()),
        "Valid {} to {}.".format(visit_pass.valid_from.strftime("%d %b %Y %H:%M"),
                                 visit_pass.valid_until.strftime("%d %b %Y %H:%M")),
        "Permitted zones: {}.".format(zones),
        "QR code value: {}".format(visit_pass.qr_token),
        "One-time OTP for manual verification: {}".format(visit_pass.otp),
    ]
    if visitor_token:
        lines.append("Visitor portal access token: {}".format(visitor_token))
    return "\n".join(lines)


def issue_pass(visit, pass_type, valid_from, valid_until, zones, issued_by=None, actor_role=VmsRole.SYSTEM,
               visitor_token=None):
    visit_pass = VisitPass.objects.create(
        visit=visit,
        pass_number=generate_pass_number(),
        qr_token=new_qr_token(),
        otp=new_otp(),
        pass_type=pass_type,
        valid_from=valid_from,
        valid_until=valid_until,
        issued_by=issued_by if (issued_by is not None and issued_by.is_authenticated) else None,
    )
    visit_pass.permitted_zones.set(zones)
    audit.record(issued_by, actor_role, "PASS_ISSUED", visit_pass,
                 message="{} pass issued for {}".format(pass_type, visit.reference),
                 metadata={"visit": visit.reference, "valid_from": valid_from, "valid_until": valid_until,
                           "zones": [z.code for z in zones]}, visitor=visit.visitor)
    # AFR-043 / AFR-167 / AFR-221: pass delivery is a critical notification.
    notify_visitor(visit.visitor, NotificationEvent.PASS_ISSUED, "Visitor pass issued",
                   pass_message(visit_pass, visitor_token), visit=visit, sms=True)
    return visit_pass


def deactivate_pass(visit_pass, actor, reason):
    if visit_pass is None or not visit_pass.is_active:
        return
    visit_pass.is_active = False
    visit_pass.deactivated_at = now()
    visit_pass.deactivated_by = actor if (actor is not None and actor.is_authenticated) else None
    visit_pass.deactivation_reason = reason[:200]
    visit_pass.save(update_fields=["is_active", "deactivated_at", "deactivated_by", "deactivation_reason"])


def route_admin(zones=(), gate=None):
    admins = admins_covering(zones=zones, gate=gate)
    return admins[0] if admins else None


def visit_zone_set(visit):
    zones = list(visit.requested_zones.all())
    visit_pass = getattr(visit, "visit_pass", None)
    if visit_pass is not None:
        zones += list(visit_pass.permitted_zones.all())
    return zones
