"""Read-side helpers: role resolution, scope checks and the runtime policy source."""

from django.db.models import Q
from django.utils import timezone

from applications.globals.models import ExtraInfo, HoldsDesignation

from . import conf
from .constants import (
    BASELINE_ADVANCE_REGISTRATION_MINUTES,
    BASELINE_APPROVAL_TIMEOUT_MINUTES,
    BASELINE_CONTINGENCY_SLA_MINUTES,
    BASELINE_MAX_VISIT_MINUTES,
    BASELINE_WALK_IN_PASS_MINUTES,
    PolicyStatus,
    RoleScope,
    VmsRole,
)
from .models import AccessPolicy, IntegrationConfig, VmsRoleAssignment

HOST_USER_TYPES = ("faculty", "staff")


def now():
    return timezone.now()


# --------------------------------------------------------------------------
# Roles (VMS-BR-181..185)
# --------------------------------------------------------------------------

def is_super_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return HoldsDesignation.objects.filter(
        working=user, designation__name__in=conf.super_admin_designations()
    ).exists()


def active_assignments(user, role, at=None):
    """VMS-BR-181: an assignment only counts inside its validity window."""
    if not user or not user.is_authenticated:
        return VmsRoleAssignment.objects.none()
    at = at or now()
    return VmsRoleAssignment.objects.filter(
        user=user, role=role, is_active=True, valid_from__lte=at, valid_until__gt=at,
    ).select_related("zone", "gate", "gate__zone")


def is_admin(user):
    return active_assignments(user, VmsRole.ADMIN).exists()


def is_security(user):
    return active_assignments(user, VmsRole.SECURITY).exists()


def host_extrainfo(user):
    """VMS-BR-185: Faculty/Staff from the institutional directory are Hosts."""
    if not user or not user.is_authenticated or not user.is_active:
        return None
    return ExtraInfo.objects.filter(user=user, user_type__in=HOST_USER_TYPES).select_related("user", "department").first()


def is_host(user):
    return host_extrainfo(user) is not None


def is_eligible_host(extra_info):
    return bool(extra_info and extra_info.user_type in HOST_USER_TYPES and extra_info.user.is_active)


def _zone_ids(zones):
    ids = set()
    for zone in zones or ():
        if zone is None:
            continue
        ids.add(zone if isinstance(zone, int) else zone.pk)
    return ids


def admin_covers(user, zones=(), gate=None):
    """True when the user holds an active Admin role whose scope covers the area.

    Campus-wide Admins cover everything. Zone Admins cover a case when one of its
    zones (or the gate's zone) is theirs ("Admin for the relevant area/zone").
    """
    wanted = _zone_ids(zones)
    if gate is not None and gate.zone_id:
        wanted.add(gate.zone_id)
    for assignment in active_assignments(user, VmsRole.ADMIN):
        if assignment.scope_type == RoleScope.CAMPUS:
            return True
        if assignment.scope_type == RoleScope.ZONE and assignment.zone_id in wanted:
            return True
    return False


def security_covers(user, gate=None, zone=None):
    """Security Personnel act at the gates/zones they are assigned to (AFR-179)."""
    assignments = list(active_assignments(user, VmsRole.SECURITY))
    if not assignments:
        return False
    if gate is None and zone is None:
        return True
    for assignment in assignments:
        if assignment.scope_type == RoleScope.GATE and gate is not None and assignment.gate_id == gate.pk:
            return True
        if assignment.scope_type == RoleScope.ZONE:
            if zone is not None and assignment.zone_id == zone.pk:
                return True
            if gate is not None and gate.zone_id and assignment.zone_id == gate.zone_id:
                return True
    return False


def admins_covering(zones=(), gate=None):
    """Routing order for Admin work: zone Admins first, then campus-wide Admins."""
    at = now()
    wanted = _zone_ids(zones)
    if gate is not None and gate.zone_id:
        wanted.add(gate.zone_id)
    base = VmsRoleAssignment.objects.filter(
        role=VmsRole.ADMIN, is_active=True, valid_from__lte=at, valid_until__gt=at,
    ).select_related("user").order_by("created_at")
    zoned = [a.user for a in base.filter(scope_type=RoleScope.ZONE, zone_id__in=wanted)] if wanted else []
    campus = [a.user for a in base.filter(scope_type=RoleScope.CAMPUS)]
    seen, ordered = set(), []
    for user in zoned + campus:
        if user.pk not in seen:
            seen.add(user.pk)
            ordered.append(user)
    return ordered


def security_users(gate=None, zone=None):
    at = now()
    base = VmsRoleAssignment.objects.filter(
        role=VmsRole.SECURITY, is_active=True, valid_from__lte=at, valid_until__gt=at,
    ).select_related("user")
    if gate is not None or zone is not None:
        query = Q(pk__in=[])
        if gate is not None:
            query |= Q(scope_type=RoleScope.GATE, gate=gate)
            if gate.zone_id:
                query |= Q(scope_type=RoleScope.ZONE, zone_id=gate.zone_id)
        if zone is not None:
            query |= Q(scope_type=RoleScope.ZONE, zone=zone)
        base = base.filter(query)
    users, seen = [], set()
    for assignment in base:
        if assignment.user_id not in seen:
            seen.add(assignment.user_id)
            users.append(assignment.user)
    return users


def actor_role(user):
    """Most specific VMS role label used in audit/history records."""
    if is_super_admin(user):
        return VmsRole.SUPER_ADMIN
    if is_admin(user):
        return VmsRole.ADMIN
    if is_security(user):
        return VmsRole.SECURITY
    if is_host(user):
        return VmsRole.HOST
    return VmsRole.SYSTEM


def roles_for(user):
    def describe(assignment):
        return {
            "id": assignment.pk,
            "scope_type": assignment.scope_type,
            "zone": assignment.zone.code if assignment.zone_id else None,
            "gate": assignment.gate.code if assignment.gate_id else None,
            "valid_until": assignment.valid_until,
        }

    return {
        "super_admin": is_super_admin(user),
        "admin": [describe(a) for a in active_assignments(user, VmsRole.ADMIN)],
        "security": [describe(a) for a in active_assignments(user, VmsRole.SECURITY)],
        "host": is_host(user),
    }


# --------------------------------------------------------------------------
# Runtime access policy (VMS-BR-126/127/129)
# --------------------------------------------------------------------------

def get_published_policy():
    return AccessPolicy.objects.filter(status=PolicyStatus.PUBLISHED).order_by("-version").first()


def policy_snapshot(policy=None):
    """Values a new visit is governed by. Stored on the visit for non-retroactivity.

    Until an Admin publishes a policy, the frozen-PS baseline defaults apply.
    """
    if policy is None:
        policy = get_published_policy()
    if policy is None:
        return {
            "version": None,
            "source": "BASELINE",
            "visiting_hours_start": None,
            "visiting_hours_end": None,
            "max_visit_duration_minutes": BASELINE_MAX_VISIT_MINUTES,
            "walk_in_pass_duration_minutes": BASELINE_WALK_IN_PASS_MINUTES,
            "approval_timeout_minutes": BASELINE_APPROVAL_TIMEOUT_MINUTES,
            "advance_registration_minutes": BASELINE_ADVANCE_REGISTRATION_MINUTES,
            "contingency_sla_minutes": BASELINE_CONTINGENCY_SLA_MINUTES,
            "reminder_offsets_minutes": [],
            "restricted_zone_ids": [],
        }
    return {
        "version": policy.version,
        "source": "PUBLISHED",
        "visiting_hours_start": policy.visiting_hours_start.strftime("%H:%M") if policy.visiting_hours_start else None,
        "visiting_hours_end": policy.visiting_hours_end.strftime("%H:%M") if policy.visiting_hours_end else None,
        "max_visit_duration_minutes": policy.max_visit_duration_minutes,
        "walk_in_pass_duration_minutes": policy.walk_in_pass_duration_minutes,
        "approval_timeout_minutes": policy.approval_timeout_minutes,
        "advance_registration_minutes": policy.advance_registration_minutes,
        "contingency_sla_minutes": policy.contingency_sla_minutes,
        "reminder_offsets_minutes": sorted(int(m) for m in (policy.reminder_offsets_minutes or [])),
        "restricted_zone_ids": sorted(policy.restricted_zones.values_list("pk", flat=True)),
    }


# --------------------------------------------------------------------------
# Integrations (VMS-UC-002, VMS-BR-174)
# --------------------------------------------------------------------------

def integration(key):
    return IntegrationConfig.objects.filter(key=key).first()


def integration_usable(key, default=True):
    """A missing config row means "not configured": ``default`` decides."""
    config = integration(key)
    if config is None:
        return default
    return config.is_usable
