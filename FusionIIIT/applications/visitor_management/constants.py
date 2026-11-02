"""Value domains for the Visitor Management System (VMS).

Every enumeration here comes from the frozen VMS specification bundle
(Problem Statement v1.2, CFR/AFR registry v1.3, UC/BR/WF specifications v1.3).
The spec reference that defines each domain is noted beside it.
"""


class VisitStatus:
    """Visit lifecycle states.

    Taken from the authoritative State-Transition Tables (STT) of the composite
    workflows CW-VMS-01, 02 and 05 (the STT is the binding behavioural spec, see
    Workflow Specification section 1). The AFR-209 historical names map as:
    PENDING -> PENDING_ADMIN_EXCEPTION / PENDING_ADMIN_CONTINGENCY,
    APPROVED -> PASS_ACTIVE.
    """

    PENDING_ADMIN_EXCEPTION = "PENDING_ADMIN_EXCEPTION"      # BW-VMS-22 "Pending Admin Exception"
    PENDING_HOST_APPROVAL = "PENDING_HOST_APPROVAL"          # "Pending Host Approval"
    PENDING_ADMIN_CONTINGENCY = "PENDING_ADMIN_CONTINGENCY"  # BW-VMS-07 "Pending Admin Contingency"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"                                      # BW-VMS-03, VMS-BR-200
    PASS_ACTIVE = "PASS_ACTIVE"                              # "Pass Active (<type>)"
    ON_SITE = "ON_SITE"
    ON_SITE_PENDING_EXIT = "ON_SITE_PENDING_EXIT"            # BW-VMS-16/18 "Pass Deactivated / On-site Pending Exit"
    TERMINATED = "TERMINATED"                                # BW-VMS-15/17 "Terminated / Pass Deactivated"
    COMPLETED = "COMPLETED"
    # Reserved by AFR-209 only. ISS-VMS-019: no actor goal or transition reaches
    # CANCELLED in the frozen baseline, so no API produces it.
    CANCELLED = "CANCELLED"

    CHOICES = [
        (PENDING_ADMIN_EXCEPTION, "Pending Admin Exception"),
        (PENDING_HOST_APPROVAL, "Pending Host Approval"),
        (PENDING_ADMIN_CONTINGENCY, "Pending Admin Contingency"),
        (REJECTED, "Rejected"),
        (EXPIRED, "Expired"),
        (PASS_ACTIVE, "Pass Active"),
        (ON_SITE, "On-site"),
        (ON_SITE_PENDING_EXIT, "Pass Deactivated / On-site Pending Exit"),
        (TERMINATED, "Terminated / Pass Deactivated"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled (reserved, ISS-VMS-019)"),
    ]

    PENDING = {PENDING_ADMIN_EXCEPTION, PENDING_HOST_APPROVAL, PENDING_ADMIN_CONTINGENCY}
    OPEN = PENDING | {PASS_ACTIVE, ON_SITE, ON_SITE_PENDING_EXIT}
    ON_CAMPUS = {ON_SITE, ON_SITE_PENDING_EXIT}
    FINAL = {REJECTED, EXPIRED, TERMINATED, COMPLETED, CANCELLED}


class PassType:
    """VMS-BR-211 / AFR-211: exactly these three pass types."""

    PRE_REGISTERED = "PRE_REGISTERED"
    WALK_IN = "WALK_IN"
    VIP = "VIP"
    CHOICES = [(PRE_REGISTERED, "Pre-registered"), (WALK_IN, "Walk-in"), (VIP, "VIP")]


class Channel:
    ONLINE = "ONLINE"
    WALK_IN = "WALK_IN"
    BULK = "BULK"
    CHOICES = [(ONLINE, "Online pre-registration"), (WALK_IN, "Walk-in at gate"), (BULK, "Bulk list")]


class IdDocumentType:
    """VMS-BR-187 / AFR-187."""

    PASSPORT = "PASSPORT"
    NATIONAL_ID = "NATIONAL_ID"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    OTHER = "OTHER"
    CHOICES = [
        (PASSPORT, "Passport"),
        (NATIONAL_ID, "National ID"),
        (DRIVERS_LICENSE, "Driver's License"),
        (OTHER, "Other"),
    ]


class Purpose:
    OFFICIAL = "OFFICIAL"
    PERSONAL = "PERSONAL"
    VENDOR = "VENDOR"
    INTERVIEW = "INTERVIEW"
    EVENT = "EVENT"
    PARENT = "PARENT"
    OTHER = "OTHER"
    CHOICES = [
        (OFFICIAL, "Official"),
        (PERSONAL, "Personal"),
        (VENDOR, "Vendor"),
        (INTERVIEW, "Interview"),
        (EVENT, "Event"),
        (PARENT, "Parent/Guardian"),
        (OTHER, "Other"),
    ]


class LogType:
    """AFR-212: visit-log event domain."""

    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"
    ZONE_ACCESS = "ZONE_ACCESS"
    ACCESS_DENIED = "ACCESS_DENIED"
    CHOICES = [
        (CHECK_IN, "Check-in"),
        (CHECK_OUT, "Check-out"),
        (ZONE_ACCESS, "Zone access"),
        (ACCESS_DENIED, "Access denied"),
    ]


class LogMethod:
    QR = "QR"
    OTP = "OTP"
    BADGE = "BADGE"
    MANUAL = "MANUAL"
    KIOSK = "KIOSK"
    APP = "APP"
    AUTO = "AUTO"
    OFFLINE = "OFFLINE"
    ACS = "ACS"
    CHOICES = [(m, m.title()) for m in (QR, OTP, BADGE, MANUAL, KIOSK, APP, AUTO, OFFLINE, ACS)]


class CredentialType:
    QR = "QR"
    BARCODE = "BARCODE"
    OTP = "OTP"
    BADGE = "BADGE"
    CHOICES = [(QR, "QR code"), (BARCODE, "Barcode"), (OTP, "OTP"), (BADGE, "Badge")]


class GateFailure:
    """Failure reasons recorded for blocked gate attempts (VMS-BR-082)."""

    UNKNOWN_CREDENTIAL = "UNKNOWN_CREDENTIAL"
    PASS_INACTIVE = "PASS_INACTIVE"                    # VMS-BR-077
    VISIT_NOT_ENTERABLE = "VISIT_NOT_ENTERABLE"        # visit already on-site / completed / not approved
    OUTSIDE_VALIDITY_WINDOW = "OUTSIDE_VALIDITY_WINDOW"  # VMS-BR-190
    BLACKLIST_MATCH = "BLACKLIST_MATCH"                # VMS-BR-116
    GATE_ZONE_NOT_PERMITTED = "GATE_ZONE_NOT_PERMITTED"  # AFR-080 / VMS-BR-191
    OTP_ALREADY_USED = "OTP_ALREADY_USED"              # AFR-067 one-time OTP
    CHOICES = [(c, c.replace("_", " ").title()) for c in (
        UNKNOWN_CREDENTIAL, PASS_INACTIVE, VISIT_NOT_ENTERABLE, OUTSIDE_VALIDITY_WINDOW,
        BLACKLIST_MATCH, GATE_ZONE_NOT_PERMITTED, OTP_ALREADY_USED,
    )]


class GateAttemptStatus:
    """BW-VMS-09/10 gate-attempt progression."""

    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"                          # "Entry Blocked"
    OVERRIDE_AUTHORIZED = "OVERRIDE_AUTHORIZED"  # "Override Authorized"
    OVERRIDE_DENIED = "OVERRIDE_DENIED"
    MANUAL_ENTRY_RECORDED = "MANUAL_ENTRY_RECORDED"
    CHOICES = [(s, s.replace("_", " ").title()) for s in (
        ALLOWED, BLOCKED, OVERRIDE_AUTHORIZED, OVERRIDE_DENIED, MANUAL_ENTRY_RECORDED,
    )]


class RegistryListType:
    """VMS-UC-006 registry record kinds."""

    BLACKLIST = "BLACKLIST"
    WATCHLIST = "WATCHLIST"
    SAFELIST = "SAFELIST"
    CHOICES = [(BLACKLIST, "Blacklist"), (WATCHLIST, "Watchlist"), (SAFELIST, "Temporary safe-list")]


class RegistryEntryState:
    """VMS-BR-120 / AFR-205: drafts never reach runtime checks."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    DISCARDED = "DISCARDED"
    CHOICES = [(s, s.title()) for s in (DRAFT, PUBLISHED, SUPERSEDED, DISCARDED)]


class Severity:
    """AFR-110."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    CHOICES = [(s, s.title()) for s in (LOW, MEDIUM, HIGH, CRITICAL)]


class SafeListScope:
    """VMS-BR-118: the safe-list exception applies only within its recorded scope."""

    ALL = "ALL"
    REGISTRATION = "REGISTRATION"
    GATE = "GATE"
    CHOICES = [(ALL, "All checkpoints"), (REGISTRATION, "Registration only"), (GATE, "Gate check-in only")]


class Checkpoint:
    """VMS-BR-112 runtime blacklist checkpoints."""

    PRE_REGISTRATION = "PRE_REGISTRATION"
    WALK_IN = "WALK_IN"
    GATE = "GATE"
    BULK = "BULK"
    CHOICES = [(c, c.replace("_", " ").title()) for c in (PRE_REGISTRATION, WALK_IN, GATE, BULK)]


class PolicyStatus:
    """VMS-BR-125/126/128."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    CHOICES = [(s, s.title()) for s in (DRAFT, PUBLISHED, SUPERSEDED)]


class ZoneAccessLevel:
    """AFR-213 access-level information."""

    PUBLIC = "PUBLIC"          # common areas, open to any on-site visitor
    CONTROLLED = "CONTROLLED"  # needs the zone on the pass
    CHOICES = [(PUBLIC, "Public / common area"), (CONTROLLED, "Controlled")]


class VmsRole:
    """VMS-BR-184: Super Admin > Admin > Security Personnel. Host is implicit (VMS-BR-185)."""

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    SECURITY = "SECURITY"
    HOST = "HOST"
    VISITOR = "VISITOR"
    SYSTEM = "SYSTEM"
    ASSIGNABLE = [(ADMIN, "Admin"), (SECURITY, "Security Personnel")]
    CHOICES = [
        (SUPER_ADMIN, "Super Admin"), (ADMIN, "Admin"), (SECURITY, "Security Personnel"),
        (HOST, "Host"), (VISITOR, "Visitor"), (SYSTEM, "System"),
    ]


class RoleScope:
    """AFR-177/179: Admin is zone or campus scoped, Security is gate or zone scoped."""

    CAMPUS = "CAMPUS"
    ZONE = "ZONE"
    GATE = "GATE"
    CHOICES = [(CAMPUS, "Campus-wide"), (ZONE, "Zone"), (GATE, "Gate")]
    ALLOWED_FOR = {
        VmsRole.ADMIN: {CAMPUS, ZONE},
        VmsRole.SECURITY: {GATE, ZONE},
    }


class AlertType:
    ZONE_VIOLATION = "ZONE_VIOLATION"
    BLACKLIST_MATCH = "BLACKLIST_MATCH"
    WATCHLIST_MATCH = "WATCHLIST_MATCH"
    FLAGGED_GATE_ATTEMPT = "FLAGGED_GATE_ATTEMPT"
    SUSPICIOUS_CASE = "SUSPICIOUS_CASE"
    CHOICES = [(a, a.replace("_", " ").title()) for a in (
        ZONE_VIOLATION, BLACKLIST_MATCH, WATCHLIST_MATCH, FLAGGED_GATE_ATTEMPT, SUSPICIOUS_CASE,
    )]


class AlertStatus:
    OPEN = "OPEN"
    HANDLED = "HANDLED"
    ESCALATED = "ESCALATED"
    FALSE_ALARM = "FALSE_ALARM"
    CHOICES = [(s, s.replace("_", " ").title()) for s in (OPEN, HANDLED, ESCALATED, FALSE_ALARM)]


class MusterStatus:
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CHOICES = [(ACTIVE, "Muster Active"), (COMPLETED, "Muster Completed")]


class RollCallStatus:
    """VMS-UC-027: unknown visitors stay PENDING, never silently ACCOUNTED."""

    PENDING = "PENDING"
    ACCOUNTED = "ACCOUNTED"
    EXITED = "EXITED"
    CHOICES = [(PENDING, "Pending / unaccounted"), (ACCOUNTED, "Accounted at assembly"), (EXITED, "Already left campus")]


class RosterSource:
    LIVE = "LIVE"
    CACHED = "CACHED"
    CHOICES = [(LIVE, "Live roster"), (CACHED, "Cached roster (offline)")]


class OfflineEventStatus:
    """BW-VMS-11 / VMS-UC-039."""

    PENDING = "PENDING_RECONCILIATION"
    RECONCILED = "RECONCILED"
    CONFLICT = "CONFLICT"
    REVIEWED = "REVIEWED"
    CHOICES = [(PENDING, "Pending reconciliation"), (RECONCILED, "Reconciled"),
               (CONFLICT, "Conflict flagged for review"), (REVIEWED, "Conflict reviewed")]


class ExtensionStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHOICES = [(PENDING, "Pending Admin decision"), (APPROVED, "Approved"), (REJECTED, "Rejected")]


class EventStatus:
    """CW-VMS-07 states."""

    DRAFT = "DRAFT"                       # "Event Visitor List Draft"
    PASSES_ACTIVE = "PASSES_ACTIVE"       # "Event Passes Active"
    CONTROLS_ACTIVE = "CONTROLS_ACTIVE"   # "Event Entry Controls Active"
    CLOSED = "CLOSED"
    CHOICES = [(DRAFT, "Visitor list draft"), (PASSES_ACTIVE, "Event passes active"),
               (CONTROLS_ACTIVE, "Event entry controls active"), (CLOSED, "Closed")]


class BulkListKind:
    EVENT = "EVENT"
    RECURRING_VENDOR = "RECURRING_VENDOR"
    CHOICES = [(EVENT, "Event attendees"), (RECURRING_VENDOR, "Recurring vendors")]


class IntegrationKey:
    """VMS-UC-002 / VMS-CFR-003: the only integrations VMS may configure (AFR-226)."""

    CAMPUS_ID = "CAMPUS_ID"
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    EVENT_MANAGEMENT = "EVENT_MANAGEMENT"
    HOSTEL_MANAGEMENT = "HOSTEL_MANAGEMENT"
    CHOICES = [
        (CAMPUS_ID, "Campus ID system / user directory"),
        (EMAIL, "Institutional email"),
        (SMS, "SMS gateway"),
        (IN_APP, "In-app push"),
        (ACCESS_CONTROL, "Access control (door readers / turnstiles)"),
        (EVENT_MANAGEMENT, "Event Management"),
        (HOSTEL_MANAGEMENT, "Hostel Management"),
    ]
    NOTIFICATION_CHANNELS = (EMAIL, SMS, IN_APP)
    KEYED = (ACCESS_CONTROL, EVENT_MANAGEMENT, HOSTEL_MANAGEMENT)


class IntegrationStatus:
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    CHOICES = [(AVAILABLE, "Available"), (UNAVAILABLE, "Temporarily unavailable")]


class NotificationEvent:
    """VMS-CFR-028 / AFR-164..173 notification triggers."""

    REQUEST_SUBMITTED = "REQUEST_SUBMITTED"
    REQUEST_PENDING_FOR_HOST = "REQUEST_PENDING_FOR_HOST"
    REQUEST_PENDING_FOR_ADMIN = "REQUEST_PENDING_FOR_ADMIN"
    REQUEST_APPROVED = "REQUEST_APPROVED"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    PASS_ISSUED = "PASS_ISSUED"
    VISITOR_CHECKED_IN = "VISITOR_CHECKED_IN"
    VISITOR_CHECKED_OUT = "VISITOR_CHECKED_OUT"
    APPROVAL_REMINDER = "APPROVAL_REMINDER"
    REQUEST_EXPIRED = "REQUEST_EXPIRED"
    VISIT_TERMINATED = "VISIT_TERMINATED"
    VISIT_EXTENDED = "VISIT_EXTENDED"
    EMERGENCY_MUSTER = "EMERGENCY_MUSTER"
    ZONE_VIOLATION = "ZONE_VIOLATION"
    BLACKLIST_MATCH = "BLACKLIST_MATCH"
    ALERT_ESCALATED = "ALERT_ESCALATED"
    OVERRIDE_REQUESTED = "OVERRIDE_REQUESTED"
    CHOICES = [(e, e.replace("_", " ").title()) for e in (
        REQUEST_SUBMITTED, REQUEST_PENDING_FOR_HOST, REQUEST_PENDING_FOR_ADMIN, REQUEST_APPROVED,
        REQUEST_REJECTED, PASS_ISSUED, VISITOR_CHECKED_IN, VISITOR_CHECKED_OUT, APPROVAL_REMINDER,
        REQUEST_EXPIRED, VISIT_TERMINATED, VISIT_EXTENDED, EMERGENCY_MUSTER, ZONE_VIOLATION,
        BLACKLIST_MATCH, ALERT_ESCALATED, OVERRIDE_REQUESTED,
    )]


class DeliveryStatus:
    SENT = "SENT"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    SKIPPED = "SKIPPED"


# Frozen-PS baseline defaults (Problem Statement 3.1, 3.2, 3.8). They apply
# until an Admin publishes an access policy; a published policy replaces them.
BASELINE_MAX_VISIT_MINUTES = 8 * 60
BASELINE_WALK_IN_PASS_MINUTES = 4 * 60
BASELINE_APPROVAL_TIMEOUT_MINUTES = 24 * 60
BASELINE_ADVANCE_REGISTRATION_MINUTES = 2 * 60
# The frozen PS leaves the contingency SLA to configuration (VMS-BR-050).
BASELINE_CONTINGENCY_SLA_MINUTES = 30
