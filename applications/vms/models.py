import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from applications.globals.models import ExtraInfo


class Visitor(models.Model):
    ID_PASSPORT = "passport"
    ID_NATIONAL = "national_id"
    ID_DL = "driver_license"
    ID_AADHAAR = "aadhaar"

    ID_TYPES = (
        (ID_PASSPORT, "Passport"),
        (ID_NATIONAL, "National ID"),
        (ID_DL, "Driver License"),
        (ID_AADHAAR, "Aadhaar Card"),
    )

    full_name = models.CharField(max_length=120)
    id_number = models.CharField(max_length=64, unique=True)
    id_type = models.CharField(max_length=20, choices=ID_TYPES)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)
    photo_reference = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.id_number})"


class BlacklistEntry(models.Model):
    id_number = models.CharField(max_length=64, db_index=True)
    reason = models.CharField(max_length=200)
    evidence = models.TextField(blank=True)
    added_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="vms_blacklist_added"
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Blacklist Entry"
        verbose_name_plural = "Blacklist Entries"

    def __str__(self):
        state = "active" if self.active else "inactive"
        return f"{self.id_number} - {state}"


class Visit(models.Model):
    STATUS_REGISTERED = "registered"
    STATUS_VERIFIED = "id_verified"
    STATUS_PASS_ISSUED = "pass_issued"
    STATUS_INSIDE = "inside"
    STATUS_EXITED = "exited"
    STATUS_DENIED = "denied"

    STATUS_CHOICES = (
        (STATUS_REGISTERED, "Registered"),
        (STATUS_VERIFIED, "ID Verified"),
        (STATUS_PASS_ISSUED, "Pass Issued"),
        (STATUS_INSIDE, "Inside"),
        (STATUS_EXITED, "Exited"),
        (STATUS_DENIED, "Denied"),
    )

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="visits")
    purpose = models.CharField(max_length=200)
    host_name = models.CharField(max_length=120)
    host_department = models.CharField(max_length=120)
    host_contact = models.CharField(max_length=50, blank=True)
    expected_duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    pass_issued_at = models.DateTimeField(null=True, blank=True)
    entry_at = models.DateTimeField(null=True, blank=True)
    exit_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.CharField(max_length=200, blank=True)
    denial_remarks = models.TextField(blank=True)
    is_vip = models.BooleanField(default=False)
    # BR-046: VIP level drives escort-assignment eligibility.
    # 0 = not VIP, 1 = standard VIP, 2 = high, 3+ = escort-eligible by default.
    vip_level = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Visit {self.id} for {self.visitor.full_name}"


def _generate_pass_number() -> str:
    return f"VMS-{uuid.uuid4().hex[:10].upper()}"


class VisitorPass(models.Model):
    PASS_PENDING = "pending"
    PASS_ISSUED = "issued"
    PASS_RETURNED = "returned"
    PASS_LOST = "lost"

    PASS_STATUS = (
        (PASS_PENDING, "Pending"),
        (PASS_ISSUED, "Issued"),
        (PASS_RETURNED, "Returned"),
        (PASS_LOST, "Lost"),
    )

    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name="visitor_pass")
    pass_number = models.CharField(max_length=32, unique=True, default=_generate_pass_number)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    authorized_zones = models.CharField(max_length=200, default="public")
    status = models.CharField(max_length=20, choices=PASS_STATUS, default=PASS_PENDING)
    barcode_data = models.TextField(blank=True)
    is_vip_pass = models.BooleanField(default=False)

    def __str__(self):
        return f"Pass {self.pass_number}"


class VerificationLog(models.Model):
    METHOD_MANUAL = "manual"
    METHOD_BIOMETRIC = "biometric"

    METHODS = (
        (METHOD_MANUAL, "Manual"),
        (METHOD_BIOMETRIC, "Biometric"),
    )

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="verification_logs")
    verifier = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_verifications")
    method = models.CharField(max_length=20, choices=METHODS, default=METHOD_MANUAL)
    result = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "passed" if self.result else "failed"
        return f"Verification {self.id} ({status})"


class DenialLog(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="denials")
    reason = models.CharField(max_length=120)
    remarks = models.TextField(blank=True)
    escalated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Denial {self.id} - {self.reason}"


class EntryExitLog(models.Model):
    ACTION_ENTRY = "entry"
    ACTION_EXIT = "exit"

    ACTIONS = (
        (ACTION_ENTRY, "Entry"),
        (ACTION_EXIT, "Exit"),
    )

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="movement_logs")
    action = models.CharField(max_length=10, choices=ACTIONS)
    gate_name = models.CharField(max_length=120)
    recorded_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_movements")
    items_declared = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action.title()} log for visit {self.visit_id}"


class SecurityIncident(models.Model):
    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"

    SEVERITIES = (
        (SEVERITY_CRITICAL, "Critical"),
        (SEVERITY_HIGH, "High"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_LOW, "Low"),
    )

    ISSUE_TYPES = (
        ("unauthorized_access", "Unauthorized Access"),
        ("policy_violation", "Policy Violation"),
        ("equipment_failure", "Equipment Failure"),
        ("suspicious_behavior", "Suspicious Behavior"),
        ("other", "Other"),
    )

    ESCALATION_LEVELS = (
        (0, "None"),
        (1, "Supervisor"),
        (2, "Security Head"),
        (3, "Administration"),
        (4, "Police / Lockdown"),
    )

    visitor = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    recorded_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_incidents")
    severity = models.CharField(max_length=10, choices=SEVERITIES)
    issue_type = models.CharField(max_length=40, choices=ISSUE_TYPES, default="other")
    description = models.TextField()
    status = models.CharField(max_length=20, default="open")
    tracking_number = models.CharField(max_length=32, unique=True, blank=True)
    escalation_level = models.IntegerField(choices=ESCALATION_LEVELS, default=0)
    containment_actions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Incident {self.tracking_number or self.id} ({self.severity})"

    @property
    def requires_escalation(self) -> bool:
        return self.severity in {self.SEVERITY_CRITICAL, self.SEVERITY_HIGH}

    def determine_escalation_level(self):
        """BR-050: Auto-determine escalation level based on severity."""
        mapping = {
            self.SEVERITY_LOW: 1,
            self.SEVERITY_MEDIUM: 2,
            self.SEVERITY_HIGH: 3,
            self.SEVERITY_CRITICAL: 4,
        }
        return mapping.get(self.severity, 0)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            ts = timezone.now().strftime("%Y%m%d")
            short = uuid.uuid4().hex[:8].upper()
            self.tracking_number = f"INC-{ts}-{short}"
        if not self.escalation_level:
            self.escalation_level = self.determine_escalation_level()
        super().save(*args, **kwargs)


def calculate_valid_until(start_time: timezone.datetime, duration_minutes: int, is_vip: bool = False) -> timezone.datetime:
    base_duration = duration_minutes
    extra = 60 if is_vip else 0
    return start_time + timedelta(minutes=base_duration + extra)


# ---------------------------------------------------------------------------
# BR-005: Unique request ID for every registration
# ---------------------------------------------------------------------------
class VisitorRequest(models.Model):
    """Tracks each registration request with a unique human-readable request ID."""
    request_id = models.CharField(max_length=32, unique=True, db_index=True)
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name="request")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.request_id

    @staticmethod
    def generate_request_id():
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        short = uuid.uuid4().hex[:6].upper()
        return f"VR-{ts}-{short}"


# ---------------------------------------------------------------------------
# BR-004 / BR-011: Host authority model
# ---------------------------------------------------------------------------
class HostAuthority(models.Model):
    LEVEL_BASIC = "basic"
    LEVEL_DEPARTMENT = "department"
    LEVEL_ADMIN = "admin"
    LEVEL_SUPER = "super_admin"

    LEVELS = (
        (LEVEL_BASIC, "Basic"),
        (LEVEL_DEPARTMENT, "Department"),
        (LEVEL_ADMIN, "Admin"),
        (LEVEL_SUPER, "Super Admin"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vms_host_authority"
    )
    authority_level = models.CharField(max_length=20, choices=LEVELS, default=LEVEL_BASIC)
    department = models.CharField(max_length=120, blank=True)
    can_approve_vip = models.BooleanField(default=False)
    max_daily_approvals = models.PositiveIntegerField(default=10)

    class Meta:
        verbose_name_plural = "Host Authorities"

    def __str__(self):
        return f"{self.user} ({self.authority_level})"


# ---------------------------------------------------------------------------
# BR-007: Daily registration quota per host
# ---------------------------------------------------------------------------
class RegistrationQuota(models.Model):
    host_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vms_quotas"
    )
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("host_user", "date")

    def __str__(self):
        return f"{self.host_user} on {self.date}: {self.count}"


# ---------------------------------------------------------------------------
# BR-013 / BR-064: Configurable access zones
# ---------------------------------------------------------------------------
class AccessZone(models.Model):
    name = models.CharField(max_length=60, unique=True)
    description = models.CharField(max_length=200, blank=True)
    requires_vip = models.BooleanField(default=False)
    requires_escort = models.BooleanField(default=False)
    is_restricted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# BR-036 / BR-037: Visitor location tracking
# ---------------------------------------------------------------------------
class VisitorLocation(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="locations")
    zone = models.ForeignKey(AccessZone, on_delete=models.SET_NULL, null=True, blank=True)
    checkpoint_name = models.CharField(max_length=120)
    scanned_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_location_scans"
    )

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"Visit {self.visit_id} at {self.checkpoint_name}"


# ---------------------------------------------------------------------------
# BR-034: Blacklist audit log
# ---------------------------------------------------------------------------
class BlacklistAuditLog(models.Model):
    ACTION_ADD = "add"
    ACTION_REMOVE = "remove"
    ACTION_UPDATE = "update"

    ACTIONS = (
        (ACTION_ADD, "Added"),
        (ACTION_REMOVE, "Removed"),
        (ACTION_UPDATE, "Updated"),
    )

    blacklist_entry = models.ForeignKey(
        BlacklistEntry, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=10, choices=ACTIONS)
    performed_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_blacklist_actions"
    )
    id_number = models.CharField(max_length=64)
    reason = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} blacklist for {self.id_number}"


# ---------------------------------------------------------------------------
# BR-046: VIP escort assignment
# ---------------------------------------------------------------------------
class EscortAssignment(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="escorts")
    escort = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_escort_duties"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Escort for visit {self.visit_id}"


# ---------------------------------------------------------------------------
# BR-047: VIP activity log (enhanced logging)
# ---------------------------------------------------------------------------
class VIPActivityLog(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="vip_logs")
    action = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_vip_actions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VIP log: {self.action} (visit {self.visit_id})"


# ---------------------------------------------------------------------------
# BR-054: Incident tracking number
# ---------------------------------------------------------------------------
class IncidentTrackingMixin:
    """Provides tracking_number generation for SecurityIncident."""

    @staticmethod
    def generate_tracking_number():
        ts = timezone.now().strftime("%Y%m%d")
        short = uuid.uuid4().hex[:8].upper()
        return f"INC-{ts}-{short}"


# ---------------------------------------------------------------------------
# BR-057–066: System configuration
# ---------------------------------------------------------------------------
class SystemConfig(models.Model):
    key = models.CharField(max_length=120, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=256, blank=True)
    updated_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_config_changes"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.key}={self.value[:40]}"


class ConfigChangeLog(models.Model):
    config = models.ForeignKey(SystemConfig, on_delete=models.CASCADE, related_name="change_logs")
    old_value = models.TextField()
    new_value = models.TextField()
    changed_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_config_audit"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Config '{self.config.key}' changed at {self.changed_at}"


# ---------------------------------------------------------------------------
# BR-063: Visiting hours
# ---------------------------------------------------------------------------
class VisitingHours(models.Model):
    DAY_CHOICES = (
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_holiday = models.BooleanField(default=False)
    holiday_name = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Visiting Hours"

    def __str__(self):
        return f"Day {self.day_of_week}: {self.start_time}-{self.end_time}"


# ---------------------------------------------------------------------------
# BR-067–074: Data operation logging
# ---------------------------------------------------------------------------
class DataOperationLog(models.Model):
    OP_EXPORT = "export"
    OP_IMPORT = "import"

    OP_TYPES = (
        (OP_EXPORT, "Export"),
        (OP_IMPORT, "Import"),
    )

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_ROLLED_BACK = "rolled_back"

    STATUSES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_ROLLED_BACK, "Rolled Back"),
    )

    operation_type = models.CharField(max_length=10, choices=OP_TYPES)
    status = models.CharField(max_length=16, choices=STATUSES, default=STATUS_PENDING)
    initiated_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, related_name="vms_data_ops"
    )
    parameters = models.JSONField(default=dict)
    result_summary = models.TextField(blank=True)
    records_processed = models.PositiveIntegerField(default=0)
    error_details = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.operation_type} ({self.status})"
