"""Super Admin and Admin configuration services.

VMS-UC-001 roles, VMS-UC-002 integrations, VMS-UC-003 VIP permissions,
VMS-UC-005 access policies, VMS-UC-006 blacklist/watchlist/safe-list registry.
"""

import secrets

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Max, Q

from applications.globals.models import ExtraInfo

from .. import audit
from ..constants import (
    BASELINE_ADVANCE_REGISTRATION_MINUTES,
    BASELINE_APPROVAL_TIMEOUT_MINUTES,
    BASELINE_CONTINGENCY_SLA_MINUTES,
    BASELINE_MAX_VISIT_MINUTES,
    BASELINE_WALK_IN_PASS_MINUTES,
    AlertStatus,
    ExtensionStatus,
    GateAttemptStatus,
    IntegrationKey,
    IntegrationStatus,
    PolicyStatus,
    RegistryEntryState,
    RegistryListType,
    RoleScope,
    VisitStatus,
    VmsRole,
)
from ..errors import Conflict, NotAuthorized, NotFound, ValidationFailed
from ..matching import identity_keys, strong_identity_q
from ..models import (
    AccessPolicy,
    ExtensionRequest,
    Gate,
    GateAttempt,
    IntegrationConfig,
    RegistryEntry,
    RegistryPublication,
    SecurityAlert,
    VipPermission,
    VisitRequest,
    VmsRoleAssignment,
    Zone,
)
from ..selectors import is_admin, is_super_admin, active_assignments, now
from .common import hash_secret, zones_from_codes


# --------------------------------------------------------------------------
# Authorisation guards
# --------------------------------------------------------------------------

def require_super_admin(user):
    if not is_super_admin(user):
        raise NotAuthorized("Only the VMS Super Admin can perform this action.")


def require_campus_admin(user):
    """Campus-wide configuration (policies, registry, bulk lists) needs a campus-scoped Admin."""
    if not active_assignments(user, VmsRole.ADMIN).filter(scope_type=RoleScope.CAMPUS).exists():
        raise NotAuthorized("A campus-wide VMS Admin role is required for this action.")


def require_admin(user):
    if not is_admin(user):
        raise NotAuthorized("An active VMS Admin role is required for this action.")


# --------------------------------------------------------------------------
# VMS-UC-001 Configure VMS Roles (VMS-BR-181..184)
# --------------------------------------------------------------------------

def _resolve_directory_user(identifier):
    """UC-001 precondition: the role holder exists in the institutional directory."""
    user = None
    if identifier is not None:
        user = User.objects.filter(Q(username=str(identifier)) | Q(extrainfo__id=str(identifier))).first()
        if user is None and str(identifier).isdigit():
            user = User.objects.filter(pk=int(identifier)).first()
    if user is None or not user.is_active or not ExtraInfo.objects.filter(user=user).exists():
        raise NotFound("The user could not be resolved in the institutional directory.", code="directory_user_not_found")
    return user


def _validate_scope(role, scope_type, zone_code, gate_code):
    if role not in RoleScope.ALLOWED_FOR:
        raise ValidationFailed("Only Admin and Security Personnel roles are assigned through VMS.",
                               details={"role": [role]})
    if scope_type not in RoleScope.ALLOWED_FOR[role]:
        raise ValidationFailed(
            "{} roles cannot be scoped to {} (AFR-177/179).".format(role.title(), scope_type),
            code="hierarchy_conflict", details={"scope_type": [scope_type]})
    zone = gate = None
    if scope_type == RoleScope.ZONE:
        if not zone_code:
            raise ValidationFailed("A zone is required for a zone-scoped role.", details={"zone": ["required"]})
        zone = Zone.objects.filter(code=zone_code, is_active=True).first()
        if zone is None:
            raise ValidationFailed("Unknown zone.", details={"zone": [zone_code]})
    if scope_type == RoleScope.GATE:
        if not gate_code:
            raise ValidationFailed("A gate is required for a gate-scoped role.", details={"gate": ["required"]})
        gate = Gate.objects.filter(code=gate_code, is_active=True).first()
        if gate is None:
            raise ValidationFailed("Unknown gate.", details={"gate": [gate_code]})
    return zone, gate


@transaction.atomic
def assign_role(actor, user_identifier, role, scope_type, valid_until, valid_from=None, zone_code=None, gate_code=None):
    require_super_admin(actor)  # VMS-BR-184
    user = _resolve_directory_user(user_identifier)
    zone, gate = _validate_scope(role, scope_type, zone_code, gate_code)
    valid_from = valid_from or now()
    if not valid_until:
        raise ValidationFailed("Role assignments are time-bound (VMS-BR-181).", details={"valid_until": ["required"]})
    if valid_until <= valid_from or valid_until <= now():
        raise ValidationFailed("valid_until must be after valid_from and in the future.",
                               details={"valid_until": ["invalid"]})
    duplicate = active_assignments(user, role).filter(scope_type=scope_type, zone=zone, gate=gate)
    if duplicate.exists():
        raise Conflict("The user already holds this active role assignment.", code="duplicate_assignment")
    assignment = VmsRoleAssignment.objects.create(
        user=user, role=role, scope_type=scope_type, zone=zone, gate=gate,
        valid_from=valid_from, valid_until=valid_until, assigned_by=actor,
    )
    audit.record(actor, VmsRole.SUPER_ADMIN, "ROLE_ASSIGNED", assignment,
                 message="{} assigned {} [{}]".format(user.username, role, scope_type),
                 metadata={"zone": zone_code, "gate": gate_code, "valid_until": valid_until})
    return assignment


def _handoff_pending_work(role, old_user, new_user):
    """VMS-BR-183: reroute pending work inside the reassigned scope."""
    moved = {}
    if role == VmsRole.ADMIN:
        moved["visit_requests"] = VisitRequest.objects.filter(
            assigned_admin=old_user, status__in=[VisitStatus.PENDING_ADMIN_EXCEPTION, VisitStatus.PENDING_ADMIN_CONTINGENCY],
        ).update(assigned_admin=new_user)
        moved["gate_overrides"] = GateAttempt.objects.filter(
            assigned_admin=old_user, status=GateAttemptStatus.BLOCKED,
        ).update(assigned_admin=new_user)
        moved["extensions"] = ExtensionRequest.objects.filter(
            assigned_admin=old_user, status=ExtensionStatus.PENDING,
        ).update(assigned_admin=new_user)
    moved["alerts"] = SecurityAlert.objects.filter(
        assigned_to=old_user, status__in=[AlertStatus.OPEN, AlertStatus.ESCALATED],
    ).update(assigned_to=new_user)
    return moved


@transaction.atomic
def reassign_role(actor, assignment_id, new_user_identifier, valid_until=None):
    require_super_admin(actor)
    old = VmsRoleAssignment.objects.select_for_update(of=("self",)).filter(pk=assignment_id, is_active=True).first()
    if old is None:
        raise NotFound("Active role assignment not found.")
    new_user = _resolve_directory_user(new_user_identifier)
    if new_user.pk == old.user_id:
        raise ValidationFailed("Reassignment needs a different user.", details={"user": ["same user"]})
    moment = now()
    valid_until = valid_until or old.valid_until
    if valid_until <= moment:
        raise ValidationFailed("valid_until must be in the future.", details={"valid_until": ["invalid"]})
    old.is_active = False
    old.ended_at = moment
    old.end_reason = "Reassigned to {}".format(new_user.username)
    old.save(update_fields=["is_active", "ended_at", "end_reason"])
    # VMS-BR-182: effective immediately, no handoff delay.
    new = VmsRoleAssignment.objects.create(
        user=new_user, role=old.role, scope_type=old.scope_type, zone=old.zone, gate=old.gate,
        valid_from=moment, valid_until=valid_until, assigned_by=actor, reassigned_from=old,
    )
    moved = _handoff_pending_work(old.role, old.user, new_user)
    audit.record(actor, VmsRole.SUPER_ADMIN, "ROLE_REASSIGNED", new,
                 message="{} {} reassigned from {} to {}".format(old.role, old.scope_type, old.user.username,
                                                                 new_user.username),
                 metadata={"previous_assignment": old.pk, "handoff": moved})
    return new, moved


@transaction.atomic
def revoke_role(actor, assignment_id, reason=""):
    require_super_admin(actor)
    assignment = VmsRoleAssignment.objects.filter(pk=assignment_id, is_active=True).first()
    if assignment is None:
        raise NotFound("Active role assignment not found.")
    assignment.is_active = False
    assignment.ended_at = now()
    assignment.end_reason = reason or "Revoked"
    assignment.save(update_fields=["is_active", "ended_at", "end_reason"])
    audit.record(actor, VmsRole.SUPER_ADMIN, "ROLE_REVOKED", assignment, message=assignment.end_reason)
    return assignment


# --------------------------------------------------------------------------
# VMS-UC-002 Configure VMS Integration Boundaries
# --------------------------------------------------------------------------

def configure_integration(actor, key, data):
    require_super_admin(actor)
    valid_keys = {k for k, _ in IntegrationKey.CHOICES}
    errors = {}
    if key not in valid_keys:
        errors["key"] = ["Unsupported integration. VMS integrates only with {}.".format(", ".join(sorted(valid_keys)))]
    endpoint = data.get("endpoint_url", "")
    if endpoint:
        try:
            URLValidator(schemes=["http", "https"])(endpoint)
        except DjangoValidationError:
            errors["endpoint_url"] = ["Enter a valid http(s) URL."]
    settings_value = data.get("settings", {})
    if settings_value is not None and not isinstance(settings_value, dict):
        errors["settings"] = ["settings must be a JSON object."]
    status_value = data.get("status", IntegrationStatus.AVAILABLE)
    if status_value not in {s for s, _ in IntegrationStatus.CHOICES}:
        errors["status"] = ["Invalid status."]
    if errors:
        # UC-002 exception flow: invalid configuration is rejected and logged.
        audit.record(actor, VmsRole.SUPER_ADMIN, "INTEGRATION_CONFIG_REJECTED", None,
                     message="Rejected configuration for {}".format(key), metadata={"errors": errors})
        raise ValidationFailed("Invalid integration configuration.", details=errors)
    with transaction.atomic():
        return _save_integration(actor, key, endpoint, settings_value, status_value, data)


def _save_integration(actor, key, endpoint, settings_value, status_value, data):
    config, _ = IntegrationConfig.objects.get_or_create(key=key)
    config.endpoint_url = endpoint or ""
    config.settings = settings_value or {}
    config.status = status_value
    config.is_enabled = bool(data.get("is_enabled", True))
    config.updated_by = actor
    config.save()
    audit.record(actor, VmsRole.SUPER_ADMIN, "INTEGRATION_CONFIGURED", config,
                 message="{} configured ({})".format(key, config.status),
                 metadata={"enabled": config.is_enabled, "endpoint_url": config.endpoint_url})
    return config


@transaction.atomic
def rotate_integration_key(actor, key):
    require_super_admin(actor)
    if key not in IntegrationKey.KEYED:
        raise ValidationFailed("This integration does not call VMS and has no API key.", details={"key": [key]})
    config, _ = IntegrationConfig.objects.get_or_create(key=key)
    raw = secrets.token_urlsafe(32)
    config.api_key_hash = hash_secret(raw)
    config.updated_by = actor
    config.save(update_fields=["api_key_hash", "updated_by", "updated_at"])
    audit.record(actor, VmsRole.SUPER_ADMIN, "INTEGRATION_KEY_ROTATED", config, message=key)
    return config, raw


# --------------------------------------------------------------------------
# VMS-UC-003 Manage VIP Visitor Permissions (VMS-BR-196/197)
# --------------------------------------------------------------------------

def _vip_values(data, instance=None):
    errors = {}
    visit = None
    if data.get("visit_reference"):
        visit = VisitRequest.objects.filter(reference=data["visit_reference"]).select_related("visitor").first()
        if visit is None:
            errors["visit_reference"] = ["Unknown visit."]
    identity = {k: data.get(k, getattr(instance, k, "") if instance else "") or "" for k in
                ("full_name", "id_doc_type", "id_doc_number", "phone", "email")}
    if visit is None and not (identity["id_doc_number"] or identity["phone"]):
        errors["identity"] = ["Give the visitor's ID document number or phone, or a visit reference."]
    valid_from = data.get("valid_from") or (instance.valid_from if instance else now())
    valid_until = data.get("valid_until") or (instance.valid_until if instance else None)
    if not valid_until or valid_until <= valid_from:
        errors["valid_until"] = ["A validity end after valid_from is required."]
    elif valid_until <= now():
        errors["valid_until"] = ["An expired VIP permission cannot be granted."]
    zone_scope = data.get("zone_scope", instance.zone_scope if instance else VipPermission.ZONE_SCOPE_NONE)
    if zone_scope not in {c for c, _ in VipPermission.ZONE_SCOPE_CHOICES}:
        errors["zone_scope"] = ["Invalid zone scope."]
    zones = zones_from_codes(data.get("zones")) if data.get("zones") is not None else None
    if zone_scope == VipPermission.ZONE_SCOPE_LISTED and not (zones or (instance and instance.zones.exists())):
        errors["zones"] = ["List the zones the VIP override covers."]
    if errors:
        raise ValidationFailed("Invalid VIP permission.", details=errors)
    if visit is not None:
        for key in ("full_name", "id_doc_type", "id_doc_number", "phone", "email"):
            identity[key] = identity[key] or getattr(visit.visitor, key)
    return visit, identity, valid_from, valid_until, zone_scope, zones


@transaction.atomic
def grant_vip(actor, data):
    require_super_admin(actor)  # VMS-BR-196
    visit, identity, valid_from, valid_until, zone_scope, zones = _vip_values(data)
    permission = VipPermission(
        visit=visit, valid_from=valid_from, valid_until=valid_until, zone_scope=zone_scope,
        bypass_host_approval=bool(data.get("bypass_host_approval", True)), notes=data.get("notes", ""),
        granted_by=actor, **identity
    )
    permission.save()
    if zones is not None:
        permission.zones.set(zones)
    audit.record(actor, VmsRole.SUPER_ADMIN, "VIP_GRANTED", permission,
                 message="VIP permission granted", metadata={"zone_scope": zone_scope, "valid_until": valid_until,
                                                             "visit": visit.reference if visit else None})
    return permission


@transaction.atomic
def revise_vip(actor, permission_id, data):
    require_super_admin(actor)
    permission = VipPermission.objects.filter(pk=permission_id, is_active=True, revoked_at__isnull=True).first()
    if permission is None:
        raise NotFound("Active VIP permission not found.")
    visit, identity, valid_from, valid_until, zone_scope, zones = _vip_values(data, instance=permission)
    for key, value in identity.items():
        setattr(permission, key, value)
    permission.valid_from, permission.valid_until, permission.zone_scope = valid_from, valid_until, zone_scope
    if "bypass_host_approval" in data:
        permission.bypass_host_approval = bool(data["bypass_host_approval"])
    if "notes" in data:
        permission.notes = data["notes"]
    permission.save()
    if zones is not None:
        permission.zones.set(zones)
    audit.record(actor, VmsRole.SUPER_ADMIN, "VIP_REVISED", permission, message="VIP permission revised")
    return permission


@transaction.atomic
def revoke_vip(actor, permission_id):
    require_super_admin(actor)
    permission = VipPermission.objects.filter(pk=permission_id, is_active=True).first()
    if permission is None:
        raise NotFound("Active VIP permission not found.")
    permission.is_active = False
    permission.revoked_at = now()
    permission.revoked_by = actor
    permission.save(update_fields=["is_active", "revoked_at", "revoked_by"])
    audit.record(actor, VmsRole.SUPER_ADMIN, "VIP_REVOKED", permission, message="VIP permission revoked")
    return permission


# --------------------------------------------------------------------------
# VMS-UC-005 Manage Access Policies (VMS-BR-125..129)
# --------------------------------------------------------------------------

POLICY_FIELDS = (
    "visiting_hours_start", "visiting_hours_end", "max_visit_duration_minutes", "walk_in_pass_duration_minutes",
    "approval_timeout_minutes", "advance_registration_minutes", "contingency_sla_minutes",
    "reminder_offsets_minutes", "notes",
)

BASELINE_POLICY = {
    "visiting_hours_start": None,
    "visiting_hours_end": None,
    "max_visit_duration_minutes": BASELINE_MAX_VISIT_MINUTES,
    "walk_in_pass_duration_minutes": BASELINE_WALK_IN_PASS_MINUTES,
    "approval_timeout_minutes": BASELINE_APPROVAL_TIMEOUT_MINUTES,
    "advance_registration_minutes": BASELINE_ADVANCE_REGISTRATION_MINUTES,
    "contingency_sla_minutes": BASELINE_CONTINGENCY_SLA_MINUTES,
    "reminder_offsets_minutes": [],
    "notes": "",
}


def _validate_policy(values):
    errors = {}
    for field in ("max_visit_duration_minutes", "walk_in_pass_duration_minutes", "approval_timeout_minutes",
                  "contingency_sla_minutes"):
        if not values.get(field) or int(values[field]) <= 0:
            errors[field] = ["Must be a positive number of minutes."]
    if values.get("advance_registration_minutes") is None or int(values["advance_registration_minutes"]) < 0:
        errors["advance_registration_minutes"] = ["Must be zero or more minutes."]
    if not errors and values["walk_in_pass_duration_minutes"] > values["max_visit_duration_minutes"]:
        errors["walk_in_pass_duration_minutes"] = ["Cannot exceed the maximum visit duration."]
    start, end = values.get("visiting_hours_start"), values.get("visiting_hours_end")
    if bool(start) != bool(end):
        errors["visiting_hours"] = ["Give both visiting-hours start and end, or neither."]
    elif start and end and start >= end:
        errors["visiting_hours"] = ["Visiting hours must start before they end."]
    offsets = values.get("reminder_offsets_minutes") or []
    if not isinstance(offsets, list) or not all(isinstance(o, int) for o in offsets):
        errors["reminder_offsets_minutes"] = ["Give a list of whole minutes."]
    elif not errors.get("approval_timeout_minutes") and any(o <= 0 or o >= values["approval_timeout_minutes"] for o in offsets):
        errors["reminder_offsets_minutes"] = ["Each reminder must fall inside the approval window."]
    if errors:
        raise ValidationFailed("Invalid access policy values.", details=errors)


@transaction.atomic
def create_policy_version(actor, data, based_on_version=None):
    require_campus_admin(actor)
    base = None
    if based_on_version:
        base = AccessPolicy.objects.filter(version=based_on_version).first()
        if base is None:
            raise NotFound("Policy version {} not found.".format(based_on_version))
    values = {f: getattr(base, f) for f in POLICY_FIELDS} if base else dict(BASELINE_POLICY)
    values.update({k: v for k, v in data.items() if k in POLICY_FIELDS})
    _validate_policy(values)
    zone_codes = data.get("restricted_zones")
    zones = zones_from_codes(zone_codes, "restricted_zones") if zone_codes is not None else (
        list(base.restricted_zones.all()) if base else [])
    version = (AccessPolicy.objects.aggregate(v=Max("version"))["v"] or 0) + 1
    policy = AccessPolicy.objects.create(version=version, status=PolicyStatus.DRAFT, based_on=base,
                                         created_by=actor, **values)
    policy.restricted_zones.set(zones)
    audit.record(actor, VmsRole.ADMIN, "POLICY_DRAFT_CREATED", policy, message="Policy v{} drafted".format(version))
    return policy


@transaction.atomic
def update_policy_draft(actor, version, data):
    require_campus_admin(actor)
    policy = AccessPolicy.objects.select_for_update(of=("self",)).filter(version=version).first()
    if policy is None:
        raise NotFound("Policy version not found.")
    if policy.status != PolicyStatus.DRAFT:
        # VMS-BR-128: a published version is never mutated; modifications are new versions.
        raise Conflict("Published policy versions are immutable. Create a new version to modify it.",
                       code="policy_immutable")
    values = {f: getattr(policy, f) for f in POLICY_FIELDS}
    values.update({k: v for k, v in data.items() if k in POLICY_FIELDS})
    _validate_policy(values)
    for key, value in values.items():
        setattr(policy, key, value)
    policy.save()
    if data.get("restricted_zones") is not None:
        policy.restricted_zones.set(zones_from_codes(data["restricted_zones"], "restricted_zones"))
    audit.record(actor, VmsRole.ADMIN, "POLICY_DRAFT_UPDATED", policy, message="Policy v{} draft updated".format(version))
    return policy


@transaction.atomic
def publish_policy(actor, version):
    require_campus_admin(actor)
    policy = AccessPolicy.objects.select_for_update(of=("self",)).filter(version=version).first()
    if policy is None:
        raise NotFound("Policy version not found.")
    if policy.status != PolicyStatus.DRAFT:
        raise Conflict("Only a draft policy version can be published.", code="policy_not_draft")
    _validate_policy({f: getattr(policy, f) for f in POLICY_FIELDS})
    previous = list(AccessPolicy.objects.select_for_update(of=("self",)).filter(status=PolicyStatus.PUBLISHED))
    AccessPolicy.objects.filter(pk__in=[p.pk for p in previous]).update(status=PolicyStatus.SUPERSEDED)
    policy.status = PolicyStatus.PUBLISHED
    policy.published_at = now()
    policy.published_by = actor
    policy.save(update_fields=["status", "published_at", "published_by", "updated_at"])
    audit.record(actor, VmsRole.ADMIN, "POLICY_PUBLISHED", policy,
                 message="Policy v{} published".format(version),
                 metadata={"superseded": [p.version for p in previous]})
    return policy


# --------------------------------------------------------------------------
# VMS-UC-006 Manage Blacklist/Watchlist and Safe-list Registry (VMS-BR-118..120)
# --------------------------------------------------------------------------

REGISTRY_FIELDS = ("list_type", "full_name", "id_doc_type", "id_doc_number", "phone", "email", "reason",
                   "severity", "expires_at", "is_active", "safelist_scope")


def _validate_registry_values(values, exclude_ids=()):
    errors = {}
    list_type = values.get("list_type")
    if list_type not in {c for c, _ in RegistryListType.CHOICES}:
        errors["list_type"] = ["Invalid list type."]
    if not any(values.get(k) for k in ("full_name", "id_doc_number", "phone", "email")):
        errors["identity"] = ["Give at least a name, ID number, phone or e-mail."]
    if list_type in (RegistryListType.BLACKLIST, RegistryListType.WATCHLIST) and not values.get("reason"):
        errors["reason"] = ["A reason is required (AFR-109)."]
    if list_type == RegistryListType.SAFELIST:
        if not (values.get("id_doc_number") or values.get("phone")):
            errors["identity"] = ["A safe-list entry needs an ID number or phone to match on."]
        if not values.get("expires_at"):
            errors["expires_at"] = ["Every temporary safe-list entry must have an expiry (VMS-BR-119)."]
    if values.get("expires_at") and values["expires_at"] <= now():
        errors["expires_at"] = ["Expiry must be in the future."]
    if errors:
        raise ValidationFailed("Invalid registry record.", details=errors)
    keys = identity_keys(values.get("full_name"), values.get("id_doc_number"), values.get("phone"), values.get("email"))
    if keys["id_doc_key"] or keys["phone_key"]:
        duplicate = RegistryEntry.objects.filter(
            list_type=list_type, state__in=[RegistryEntryState.DRAFT, RegistryEntryState.PUBLISHED],
        ).filter(strong_identity_q(keys)).exclude(pk__in=list(exclude_ids))
        if duplicate.exists():
            raise Conflict("A {} record for this identity already exists.".format(list_type.lower()),
                           code="duplicate_registry_entry")


@transaction.atomic
def create_registry_entry(actor, data):
    require_campus_admin(actor)
    values = {k: data.get(k) for k in REGISTRY_FIELDS if k in data}
    values.setdefault("is_active", True)
    _validate_registry_values(values)
    entry = RegistryEntry(created_by=actor, state=RegistryEntryState.DRAFT,
                          **{k: (v if v is not None else "") if k not in ("expires_at", "is_active") else v
                             for k, v in values.items()})
    entry.save()
    audit.record(actor, VmsRole.ADMIN, "REGISTRY_DRAFT_CREATED", entry, message=str(entry))
    return entry


@transaction.atomic
def revise_registry_entry(actor, entry_id, data):
    """Drafts change in place; a published entry gets a draft revision (VMS-BR-120)."""
    require_campus_admin(actor)
    entry = RegistryEntry.objects.select_for_update(of=("self",)).filter(pk=entry_id).first()
    if entry is None:
        raise NotFound("Registry entry not found.")
    if entry.state not in (RegistryEntryState.DRAFT, RegistryEntryState.PUBLISHED):
        raise Conflict("Only draft or published entries can be revised.", code="registry_entry_closed")
    values = {k: getattr(entry, k) for k in REGISTRY_FIELDS}
    values.update({k: data[k] for k in REGISTRY_FIELDS if k in data})
    values["list_type"] = entry.list_type
    if entry.state == RegistryEntryState.DRAFT:
        _validate_registry_values(values, exclude_ids=[entry.pk, entry.revision_of_id or 0])
        for key, value in values.items():
            setattr(entry, key, value if value is not None or key in ("expires_at",) else "")
        entry.save()
        audit.record(actor, VmsRole.ADMIN, "REGISTRY_DRAFT_UPDATED", entry, message=str(entry))
        return entry
    if entry.revisions.filter(state=RegistryEntryState.DRAFT).exists():
        raise Conflict("A draft revision of this entry is already pending publication.", code="revision_pending")
    _validate_registry_values(values, exclude_ids=[entry.pk])
    draft = RegistryEntry(created_by=actor, state=RegistryEntryState.DRAFT, revision_of=entry,
                          **{k: (v if v is not None else "") if k not in ("expires_at", "is_active") else v
                             for k, v in values.items()})
    draft.save()
    audit.record(actor, VmsRole.ADMIN, "REGISTRY_REVISION_DRAFTED", draft, message="Revision of entry {}".format(entry.pk))
    return draft


@transaction.atomic
def discard_registry_draft(actor, entry_id):
    require_campus_admin(actor)
    entry = RegistryEntry.objects.filter(pk=entry_id, state=RegistryEntryState.DRAFT).first()
    if entry is None:
        raise NotFound("Draft registry entry not found.")
    entry.state = RegistryEntryState.DISCARDED
    entry.save(update_fields=["state"])
    audit.record(actor, VmsRole.ADMIN, "REGISTRY_DRAFT_DISCARDED", entry, message=str(entry))
    return entry


@transaction.atomic
def publish_registry(actor, notes=""):
    require_campus_admin(actor)
    drafts = list(RegistryEntry.objects.select_for_update(of=("self",)).filter(state=RegistryEntryState.DRAFT))
    if not drafts:
        raise Conflict("There are no draft registry changes to publish.", code="nothing_to_publish")
    version = (RegistryPublication.objects.aggregate(v=Max("version"))["v"] or 0) + 1
    publication = RegistryPublication.objects.create(version=version, published_by=actor,
                                                     entries_changed=len(drafts), notes=notes)
    superseded_ids = [d.revision_of_id for d in drafts if d.revision_of_id]
    RegistryEntry.objects.filter(pk__in=superseded_ids, state=RegistryEntryState.PUBLISHED).update(
        state=RegistryEntryState.SUPERSEDED)
    RegistryEntry.objects.filter(pk__in=[d.pk for d in drafts]).update(
        state=RegistryEntryState.PUBLISHED, publication=publication)
    audit.record(actor, VmsRole.ADMIN, "REGISTRY_PUBLISHED", publication,
                 message="Registry v{} published with {} change(s)".format(version, len(drafts)))
    return publication
