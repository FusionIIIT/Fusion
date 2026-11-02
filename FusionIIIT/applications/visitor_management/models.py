"""Visitor Management System (VMS) data model.

Data obligations come from Problem Statement v1.2 section 3.14 and AFR-206..216.
Host, Admin, Security Personnel and Super Admin are Fusion users
(``auth.User`` / ``globals.ExtraInfo``); Visitors are external people and live in
``Visitor`` only. Nothing here duplicates institutional master data
(Fusion-README sync guideline: reference production tables, never copy them).
"""

from django.contrib.auth.models import User
from django.db import models

from applications.globals.models import ExtraInfo

from .constants import (
    AlertStatus,
    AlertType,
    BulkListKind,
    Channel,
    Checkpoint,
    CredentialType,
    EventStatus,
    ExtensionStatus,
    GateAttemptStatus,
    IdDocumentType,
    IntegrationKey,
    IntegrationStatus,
    LogMethod,
    LogType,
    MusterStatus,
    NotificationEvent,
    OfflineEventStatus,
    PassType,
    PolicyStatus,
    Purpose,
    RegistryEntryState,
    RegistryListType,
    RoleScope,
    RollCallStatus,
    RosterSource,
    SafeListScope,
    Severity,
    VisitStatus,
    VmsRole,
    ZoneAccessLevel,
)


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# --------------------------------------------------------------------------
# Campus topology
# --------------------------------------------------------------------------

class Zone(TimeStamped):
    """AFR-213: campus zone with name, description and access level."""

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    access_level = models.CharField(max_length=20, choices=ZoneAccessLevel.CHOICES,
                                    default=ZoneAccessLevel.CONTROLLED)
    # VMS-UC-020 step 4 / AFR-225: logs in hostel areas are shared with Hostel Management.
    is_hostel_area = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vms_zone"
        ordering = ["code"]

    def __str__(self):
        return "{} ({})".format(self.name, self.code)


class Gate(TimeStamped):
    """Gate checkpoint. ``zone`` is set when the gate guards a controlled zone (AFR-080)."""

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="gates")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vms_gate"
        ordering = ["code"]

    def __str__(self):
        return "{} ({})".format(self.name, self.code)


# --------------------------------------------------------------------------
# Configuration owned by Super Admin / Admin
# --------------------------------------------------------------------------

class AccessPolicy(TimeStamped):
    """VMS-UC-005, VMS-BR-125..129, AFR-215.

    Published versions are immutable: a modification is a new version
    (VMS-BR-128). Runtime reads only the latest PUBLISHED version (VMS-BR-127).
    """

    version = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=12, choices=PolicyStatus.CHOICES, default=PolicyStatus.DRAFT)
    based_on = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="revisions")
    visiting_hours_start = models.TimeField(null=True, blank=True)
    visiting_hours_end = models.TimeField(null=True, blank=True)
    max_visit_duration_minutes = models.PositiveIntegerField()
    walk_in_pass_duration_minutes = models.PositiveIntegerField()
    approval_timeout_minutes = models.PositiveIntegerField()
    advance_registration_minutes = models.PositiveIntegerField()
    contingency_sla_minutes = models.PositiveIntegerField()
    # VMS-UC-040 / ISS-VMS-018: reminder instants are configuration, never hard-coded.
    reminder_offsets_minutes = models.JSONField(default=list, blank=True)
    restricted_zones = models.ManyToManyField(Zone, blank=True, related_name="restricting_policies")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "vms_access_policy"
        ordering = ["-version"]

    def __str__(self):
        return "Policy v{} ({})".format(self.version, self.status)


class IntegrationConfig(TimeStamped):
    """VMS-UC-002: VMS-facing settings for an external collaborator (AFR-226)."""

    key = models.CharField(max_length=30, choices=IntegrationKey.CHOICES, unique=True)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=12, choices=IntegrationStatus.CHOICES, default=IntegrationStatus.AVAILABLE)
    endpoint_url = models.URLField(blank=True)
    settings = models.JSONField(default=dict, blank=True)
    # Integration callers (ACS, Event/Hostel Management) authenticate with a key;
    # only its SHA-256 digest is stored.
    api_key_hash = models.CharField(max_length=64, blank=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "vms_integration_config"

    @property
    def is_usable(self):
        return self.is_enabled and self.status == IntegrationStatus.AVAILABLE


class VmsRoleAssignment(models.Model):
    """VMS-UC-001, VMS-BR-181..184: time-bound Admin / Security Personnel roles."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vms_role_assignments")
    role = models.CharField(max_length=12, choices=VmsRole.ASSIGNABLE)
    scope_type = models.CharField(max_length=10, choices=RoleScope.CHOICES)
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    reassigned_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_role_assignment"
        ordering = ["-created_at"]

    def __str__(self):
        return "{} {} [{}]".format(self.user.username, self.role, self.scope_type)


class HostProfile(models.Model):
    """AFR-207: Host data linked to the institutional account (Host role is implicit, VMS-BR-185)."""

    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, related_name="vms_host_profile")
    is_available = models.BooleanField(default=True)
    unavailable_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vms_host_profile"


# --------------------------------------------------------------------------
# Visitors and the blacklist/watchlist/safe-list registry
# --------------------------------------------------------------------------

def visitor_document_path(instance, filename):
    return "vms/id_documents/{}".format(filename)


def visitor_photo_path(instance, filename):
    return "vms/photos/{}".format(filename)


class IdentityFields(models.Model):
    """Identity/contact columns shared by Visitor, registry entries, pre-authorisations and VIP grants."""

    full_name = models.CharField(max_length=200, blank=True)
    id_doc_type = models.CharField(max_length=20, choices=IdDocumentType.CHOICES, blank=True)
    id_doc_number = models.CharField(max_length=60, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    # Normalised forms used by blacklist / pre-authorisation matching.
    name_key = models.CharField(max_length=200, blank=True, db_index=True)
    id_doc_key = models.CharField(max_length=60, blank=True, db_index=True)
    phone_key = models.CharField(max_length=20, blank=True, db_index=True)
    email_key = models.CharField(max_length=254, blank=True, db_index=True)

    class Meta:
        abstract = True

    def refresh_identity_keys(self):
        from .matching import normalise_doc, normalise_email, normalise_name, normalise_phone
        self.name_key = normalise_name(self.full_name)
        self.id_doc_key = normalise_doc(self.id_doc_number)
        self.phone_key = normalise_phone(self.phone)
        self.email_key = normalise_email(self.email)

    def save(self, *args, **kwargs):
        self.refresh_identity_keys()
        super().save(*args, **kwargs)


class Visitor(IdentityFields):
    """AFR-206: visitor identity, contact, document, photo and organisation."""

    organization = models.CharField(max_length=200, blank=True)
    id_document = models.FileField(upload_to=visitor_document_path, null=True, blank=True)
    photo = models.ImageField(upload_to=visitor_photo_path, null=True, blank=True)
    # Visitors have no Fusion account. The portal (UC-011/012/030/031) is
    # reached with a secret token handed out at registration; only its digest is kept.
    access_token_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_visitor"
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name


class RegistryPublication(models.Model):
    """One publication of the blacklist/watchlist/safe-list registry (VMS-BR-120)."""

    version = models.PositiveIntegerField(unique=True)
    published_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    published_at = models.DateTimeField(auto_now_add=True)
    entries_changed = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "vms_registry_publication"
        ordering = ["-version"]


class RegistryEntry(IdentityFields):
    """VMS-UC-006, AFR-106..111, 118, 119, 214.

    A DRAFT never affects runtime checks. Editing a PUBLISHED entry creates a
    DRAFT whose ``revision_of`` points at it; publishing the registry promotes
    drafts and supersedes what they replace.
    """

    list_type = models.CharField(max_length=12, choices=RegistryListType.CHOICES)
    state = models.CharField(max_length=12, choices=RegistryEntryState.CHOICES, default=RegistryEntryState.DRAFT)
    revision_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="revisions")
    reason = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=Severity.CHOICES, default=Severity.MEDIUM)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    safelist_scope = models.CharField(max_length=15, choices=SafeListScope.CHOICES, default=SafeListScope.ALL)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    publication = models.ForeignKey(RegistryPublication, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="entries")

    class Meta:
        db_table = "vms_registry_entry"
        ordering = ["-created_at"]

    def __str__(self):
        return "{} {} [{}]".format(self.list_type, self.full_name or self.id_doc_number, self.state)


class PreAuthorization(IdentityFields):
    """VMS-UC-014, VMS-BR-195: Host-scoped approval bypass for a recurring visitor."""

    host = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name="vms_preauthorizations")
    purpose = models.CharField(max_length=20, choices=Purpose.CHOICES, blank=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    permitted_zones = models.ManyToManyField(Zone, blank=True, related_name="+")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_preauthorization"
        ordering = ["-created_at"]


class VipPermission(IdentityFields):
    """VMS-UC-003, VMS-BR-196/197: Super Admin scoped VIP override."""

    ZONE_SCOPE_NONE = "NONE"
    ZONE_SCOPE_LISTED = "LISTED"
    ZONE_SCOPE_ALL = "ALL"
    ZONE_SCOPE_CHOICES = [(ZONE_SCOPE_NONE, "No zone bypass"), (ZONE_SCOPE_LISTED, "Listed zones"),
                          (ZONE_SCOPE_ALL, "All zones")]

    visit = models.ForeignKey("VisitRequest", null=True, blank=True, on_delete=models.CASCADE,
                              related_name="vip_permissions")
    bypass_host_approval = models.BooleanField(default=True)
    zone_scope = models.CharField(max_length=10, choices=ZONE_SCOPE_CHOICES, default=ZONE_SCOPE_NONE)
    zones = models.ManyToManyField(Zone, blank=True, related_name="+")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    notes = models.TextField(blank=True)
    granted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "vms_vip_permission"
        ordering = ["-granted_at"]


# --------------------------------------------------------------------------
# Bulk / special events (VMS-UC-008, VMS-UC-009, CW-VMS-07)
# --------------------------------------------------------------------------

class VisitorEvent(TimeStamped):
    name = models.CharField(max_length=200)
    external_event_ref = models.CharField(max_length=100, blank=True, db_index=True)
    host = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name="vms_events")
    venue_zones = models.ManyToManyField(Zone, blank=True, related_name="+")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=EventStatus.CHOICES, default=EventStatus.DRAFT)
    fast_lane_enabled = models.BooleanField(default=False)
    overflow_walk_in_enabled = models.BooleanField(default=False)
    walk_in_rate_limit_per_hour = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "vms_event"
        ordering = ["-starts_at"]

    def __str__(self):
        return self.name


def bulk_list_path(instance, filename):
    return "vms/bulk_lists/{}".format(filename)


class BulkVisitorList(models.Model):
    kind = models.CharField(max_length=20, choices=BulkListKind.CHOICES)
    event = models.ForeignKey(VisitorEvent, null=True, blank=True, on_delete=models.CASCADE, related_name="bulk_lists")
    host = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name="+")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    zones = models.ManyToManyField(Zone, blank=True, related_name="+")
    source_file = models.FileField(upload_to=bulk_list_path, null=True, blank=True)
    rows_total = models.PositiveIntegerField(default=0)
    rows_accepted = models.PositiveIntegerField(default=0)
    rows_rejected = models.PositiveIntegerField(default=0)
    row_errors = models.JSONField(default=list, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_bulk_list"
        ordering = ["-uploaded_at"]


# --------------------------------------------------------------------------
# Visits, passes and their state
# --------------------------------------------------------------------------

class VisitRequest(TimeStamped):
    """AFR-208: the visit request and its lifecycle state."""

    LANE_NORMAL = "NORMAL"
    LANE_FAST = "FAST"
    LANE_OVERFLOW = "OVERFLOW"
    LANE_CHOICES = [(LANE_NORMAL, "Normal"), (LANE_FAST, "Fast lane"), (LANE_OVERFLOW, "Overflow walk-in lane")]

    reference = models.CharField(max_length=30, unique=True)
    visitor = models.ForeignKey(Visitor, on_delete=models.PROTECT, related_name="visits")
    host = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name="vms_hosted_visits")
    purpose = models.CharField(max_length=20, choices=Purpose.CHOICES)
    purpose_details = models.TextField(blank=True)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    requested_zones = models.ManyToManyField(Zone, blank=True, related_name="requested_in_visits")
    channel = models.CharField(max_length=10, choices=Channel.CHOICES)
    lane = models.CharField(max_length=10, choices=LANE_CHOICES, default=LANE_NORMAL)
    status = models.CharField(max_length=30, choices=VisitStatus.CHOICES, db_index=True)
    is_urgent = models.BooleanField(default=False)

    # VMS-BR-129: the policy in force when the visit was created keeps governing it.
    policy = models.ForeignKey(AccessPolicy, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    policy_snapshot = models.JSONField(default=dict)

    submitted_at = models.DateTimeField()
    approval_deadline = models.DateTimeField(null=True, blank=True)
    contingency_deadline = models.DateTimeField(null=True, blank=True)
    reminders_sent = models.JSONField(default=list, blank=True)

    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    decision_notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    exception_decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    exception_decided_at = models.DateTimeField(null=True, blank=True)
    exception_note = models.TextField(blank=True)

    preauthorization = models.ForeignKey(PreAuthorization, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="visits")
    vip_permission = models.ForeignKey(VipPermission, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="applied_visits")
    event = models.ForeignKey(VisitorEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name="visits")
    bulk_list = models.ForeignKey(BulkVisitorList, null=True, blank=True, on_delete=models.SET_NULL, related_name="visits")

    registered_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    registration_gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    host_unavailable = models.BooleanField(default=False)
    assigned_admin = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    watchlist_flag = models.BooleanField(default=False)

    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    checkout_method = models.CharField(max_length=10, choices=LogMethod.CHOICES, blank=True)
    entry_gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    entry_reconciled = models.BooleanField(default=True)
    last_seen_zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    last_seen_at = models.DateTimeField(null=True, blank=True)

    terminated_at = models.DateTimeField(null=True, blank=True)
    terminated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    termination_reason = models.TextField(blank=True)

    class Meta:
        db_table = "vms_visit_request"
        ordering = ["-submitted_at"]
        indexes = [models.Index(fields=["status", "approval_deadline"])]

    def __str__(self):
        return "{} {} [{}]".format(self.reference, self.visitor.full_name, self.status)


class VisitStateHistory(models.Model):
    """Every lifecycle transition with the STT row that authorised it."""

    visit = models.ForeignKey(VisitRequest, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    transition_ref = models.CharField(max_length=120)
    uc_ref = models.CharField(max_length=20, blank=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    actor_role = models.CharField(max_length=12, choices=VmsRole.CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_visit_state_history"
        ordering = ["created_at", "id"]


class VisitPass(models.Model):
    """AFR-066..072, AFR-210: credentials, validity, zones, type and issuer."""

    visit = models.OneToOneField(VisitRequest, on_delete=models.CASCADE, related_name="visit_pass")
    pass_number = models.CharField(max_length=30, unique=True)  # printed badge / barcode value
    qr_token = models.CharField(max_length=64, unique=True)
    otp = models.CharField(max_length=6)
    otp_used_at = models.DateTimeField(null=True, blank=True)
    pass_type = models.CharField(max_length=20, choices=PassType.CHOICES)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    permitted_zones = models.ManyToManyField(Zone, blank=True, related_name="+")
    is_active = models.BooleanField(default=True)
    issued_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    issued_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deactivation_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "vms_visit_pass"

    def __str__(self):
        return "{} {}".format(self.pass_number, self.pass_type)


class GateAttempt(models.Model):
    """VMS-UC-018/019, BW-VMS-09/10: one credential presentation at a gate."""

    visit = models.ForeignKey(VisitRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="gate_attempts")
    gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    device_id = models.CharField(max_length=100, blank=True)
    credential_type = models.CharField(max_length=10, choices=CredentialType.CHOICES)
    credential_hint = models.CharField(max_length=40, blank=True)
    lane = models.CharField(max_length=10, choices=VisitRequest.LANE_CHOICES, default=VisitRequest.LANE_NORMAL)
    status = models.CharField(max_length=25, choices=GateAttemptStatus.CHOICES)
    failure_reasons = models.JSONField(default=list, blank=True)
    override_eligible = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)
    attempted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    attempted_at = models.DateTimeField()
    assigned_admin = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    override_requested_at = models.DateTimeField(null=True, blank=True)
    escalation_note = models.TextField(blank=True)
    override_decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    override_decided_at = models.DateTimeField(null=True, blank=True)
    override_justification = models.TextField(blank=True)

    class Meta:
        db_table = "vms_gate_attempt"
        ordering = ["-attempted_at"]


class OfflineGateEvent(models.Model):
    """VMS-UC-028 cached gate event awaiting VMS-UC-039 reconciliation."""

    EVENT_CHECK_IN = "CHECK_IN"
    EVENT_CHECK_OUT = "CHECK_OUT"
    EVENT_CHOICES = [(EVENT_CHECK_IN, "Check-in"), (EVENT_CHECK_OUT, "Check-out")]

    client_event_id = models.CharField(max_length=64, unique=True)
    gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    device_id = models.CharField(max_length=100, blank=True)
    credential_type = models.CharField(max_length=10, choices=CredentialType.CHOICES)
    credential_value = models.CharField(max_length=64)
    otp = models.CharField(max_length=6, blank=True)
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    occurred_at = models.DateTimeField()
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=OfflineEventStatus.CHOICES, default=OfflineEventStatus.PENDING)
    conflict_reason = models.TextField(blank=True)
    visit = models.ForeignKey(VisitRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="offline_events")
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        db_table = "vms_offline_gate_event"
        ordering = ["occurred_at", "id"]


class VisitLog(models.Model):
    """AFR-081, AFR-212: CHECK_IN, CHECK_OUT, ZONE_ACCESS and ACCESS_DENIED events."""

    visit = models.ForeignKey(VisitRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="logs")
    log_type = models.CharField(max_length=15, choices=LogType.CHOICES)
    method = models.CharField(max_length=10, choices=LogMethod.CHOICES)
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    device_id = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    detail = models.TextField(blank=True)
    is_manual = models.BooleanField(default=False)
    is_offline = models.BooleanField(default=False)
    hostel_area = models.BooleanField(default=False)
    gate_attempt = models.ForeignKey(GateAttempt, null=True, blank=True, on_delete=models.SET_NULL, related_name="logs")
    offline_event = models.ForeignKey(OfflineGateEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name="logs")

    class Meta:
        db_table = "vms_visit_log"
        ordering = ["-occurred_at", "-id"]


class ZoneElevation(models.Model):
    """VMS-UC-024, VMS-BR-096: always time-boxed."""

    visit = models.ForeignKey(VisitRequest, on_delete=models.CASCADE, related_name="zone_elevations")
    zones = models.ManyToManyField(Zone, related_name="+")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    reason = models.TextField()
    granted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_zone_elevation"
        ordering = ["-created_at"]


class SecurityAlert(models.Model):
    """Zone-violation, blacklist/watchlist and flagged-gate alerts (AFR-084, 094, 117, 172, 173)."""

    alert_type = models.CharField(max_length=25, choices=AlertType.CHOICES)
    status = models.CharField(max_length=15, choices=AlertStatus.CHOICES, default=AlertStatus.OPEN)
    checkpoint = models.CharField(max_length=20, choices=Checkpoint.CHOICES, blank=True)
    visit = models.ForeignKey(VisitRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="alerts")
    visitor = models.ForeignKey(Visitor, null=True, blank=True, on_delete=models.CASCADE, related_name="alerts")
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    gate = models.ForeignKey(Gate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    registry_entry = models.ForeignKey(RegistryEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="hits")
    visit_log = models.ForeignKey(VisitLog, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    gate_attempt = models.ForeignKey(GateAttempt, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts")
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    handled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    handled_at = models.DateTimeField(null=True, blank=True)
    handling_note = models.TextField(blank=True)
    escalated_to_admin = models.BooleanField(default=False)

    class Meta:
        db_table = "vms_security_alert"
        ordering = ["-created_at"]


class ExtensionRequest(models.Model):
    """VMS-UC-034, VMS-BR-193/194: extension beyond the policy maximum."""

    visit = models.ForeignKey(VisitRequest, on_delete=models.CASCADE, related_name="extension_requests")
    requested_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    requested_by_role = models.CharField(max_length=12, choices=VmsRole.CHOICES)
    current_valid_until = models.DateTimeField()
    requested_valid_until = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=ExtensionStatus.CHOICES, default=ExtensionStatus.PENDING)
    assigned_admin = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vms_extension_request"
        ordering = ["-created_at"]


class EmergencyMuster(models.Model):
    """VMS-UC-026/027/032, CW-VMS-06."""

    status = models.CharField(max_length=10, choices=MusterStatus.CHOICES, default=MusterStatus.ACTIVE)
    triggered_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    triggered_by_role = models.CharField(max_length=12, choices=VmsRole.CHOICES)
    triggered_at = models.DateTimeField()
    assembly_instructions = models.TextField()
    roster_source = models.CharField(max_length=10, choices=RosterSource.CHOICES, default=RosterSource.LIVE)
    roster_incomplete = models.BooleanField(default=False)
    roster_note = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "vms_emergency_muster"
        ordering = ["-triggered_at"]


class MusterRosterEntry(models.Model):
    """AFR-132..136: on-site visitor snapshot with roll-call status."""

    muster = models.ForeignKey(EmergencyMuster, on_delete=models.CASCADE, related_name="roster")
    visit = models.ForeignKey(VisitRequest, on_delete=models.CASCADE, related_name="+")
    visitor_name = models.CharField(max_length=200)
    visitor_phone = models.CharField(max_length=20, blank=True)
    visitor_email = models.EmailField(blank=True)
    host_name = models.CharField(max_length=200, blank=True)
    host_contact = models.CharField(max_length=100, blank=True)
    last_seen_zone = models.CharField(max_length=120, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=RollCallStatus.CHOICES, default=RollCallStatus.PENDING)
    in_live_roster = models.BooleanField(default=True)
    in_cached_roster = models.BooleanField(default=False)
    discrepancy = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vms_muster_roster_entry"
        unique_together = [["muster", "visit"]]
        ordering = ["visitor_name"]


class VmsNotification(models.Model):
    """Notification event record (VMS-BR-174: kept even if delivery fails)."""

    event_type = models.CharField(max_length=30, choices=NotificationEvent.CHOICES)
    recipient_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="vms_notifications")
    recipient_visitor = models.ForeignKey(Visitor, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    recipient_role = models.CharField(max_length=12, choices=VmsRole.CHOICES, blank=True)
    visit = models.ForeignKey(VisitRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    delivery = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vms_notification"
        ordering = ["-created_at", "-id"]


class AuditLog(models.Model):
    """AFR-216: actor, action, message, metadata and timestamp. Append-only."""

    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    actor_role = models.CharField(max_length=12, choices=VmsRole.CHOICES)
    action = models.CharField(max_length=60, db_index=True)
    entity_type = models.CharField(max_length=40)
    entity_id = models.CharField(max_length=40, blank=True)
    visitor = models.ForeignKey(Visitor, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "vms_audit_log"
        ordering = ["-created_at", "-id"]
