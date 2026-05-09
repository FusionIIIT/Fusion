"""
VMS Validators — centralised validation logic for the Visitor Management System.

Covers:
  BR-002  Identity document format validation
  BR-003  Visit duration limits
  BR-007  Daily registration limits per host
  BR-008  Document upload validation
  BR-020  Pass expiry enforcement
  BR-025  Report parameter validation
  BR-026  Date range validation
  BR-058  Configuration value validation
  BR-068  Data format validation (export/import)
"""

import re
from datetime import date, timedelta

from django.utils import timezone

# ---------------------------------------------------------------------------
# BR-002: ID format patterns
# ---------------------------------------------------------------------------
ID_FORMAT_PATTERNS = {
    "passport": re.compile(r"^[A-Z]{1}[0-9]{7}$"),                # e.g. A1234567
    "national_id": re.compile(r"^[A-Z0-9]{6,20}$"),
    "driver_license": re.compile(r"^[A-Z]{2}-\d{2}-\d{4,8}$"),    # e.g. DL-09-12345
    "aadhaar": re.compile(r"^\d{12}$"),
}


def validate_id_format(id_type: str, id_number: str) -> tuple[bool, str]:
    """Return (is_valid, message) for a given identity document number."""
    pattern = ID_FORMAT_PATTERNS.get(id_type)
    if pattern is None:
        return True, "No format rule for this ID type; accepted."
    if pattern.match(id_number):
        return True, "ID format is valid."
    return False, f"ID number '{id_number}' does not match the expected format for {id_type}."


# ---------------------------------------------------------------------------
# BR-003: Duration limits per visitor category
# ---------------------------------------------------------------------------
DURATION_LIMITS = {
    "general": 480,       # 8 hours
    "vip": 1440,          # 24 hours
    "contractor": 600,    # 10 hours
    "interview": 240,     # 4 hours
}


def validate_duration(minutes: int, category: str = "general", is_vip: bool = False) -> tuple[bool, str]:
    """Enforce maximum visit duration based on visitor category."""
    key = "vip" if is_vip else category
    limit = DURATION_LIMITS.get(key, DURATION_LIMITS["general"])
    if minutes <= 0:
        return False, "Duration must be a positive number."
    if minutes > limit:
        return False, f"Duration {minutes}m exceeds the {limit}m limit for category '{key}'."
    return True, "Duration is within allowed limits."


# ---------------------------------------------------------------------------
# BR-007: Daily registration cap per host
# ---------------------------------------------------------------------------
DEFAULT_DAILY_LIMIT = 10


def validate_daily_registration_limit(host_user, limit: int | None = None) -> tuple[bool, str]:
    """Check if host has remaining registrations for today."""
    from .models import RegistrationQuota
    cap = limit if limit is not None else DEFAULT_DAILY_LIMIT
    today = date.today()
    quota, _ = RegistrationQuota.objects.get_or_create(host_user=host_user, date=today, defaults={"count": 0})
    if quota.count >= cap:
        return False, f"Host has reached the daily registration limit of {cap}."
    return True, "Within daily limit."


def increment_daily_count(host_user) -> None:
    from .models import RegistrationQuota
    today = date.today()
    quota, _ = RegistrationQuota.objects.get_or_create(host_user=host_user, date=today, defaults={"count": 0})
    quota.count += 1
    quota.save(update_fields=["count"])


# ---------------------------------------------------------------------------
# BR-008: Upload validation
# ---------------------------------------------------------------------------
ALLOWED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_upload(file) -> tuple[bool, str]:
    """Validate uploaded document file (format, size)."""
    if file is None:
        return False, "No file provided."

    name = getattr(file, "name", "")
    ext = ("." + name.rsplit(".", 1)[-1]).lower() if "." in name else ""
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Accepted: {ALLOWED_UPLOAD_EXTENSIONS}"

    size = getattr(file, "size", 0)
    if size > MAX_UPLOAD_SIZE_BYTES:
        return False, f"File size {size} bytes exceeds the {MAX_UPLOAD_SIZE_BYTES} byte limit."

    return True, "File is valid."


# ---------------------------------------------------------------------------
# BR-020: Pass expiry check
# ---------------------------------------------------------------------------
def validate_pass_expiry(visitor_pass) -> tuple[bool, str]:
    """Check whether a visitor pass is still valid (not expired)."""
    now = timezone.now()
    if visitor_pass.valid_until < now:
        return False, f"Pass {visitor_pass.pass_number} expired at {visitor_pass.valid_until.isoformat()}."
    if visitor_pass.status not in ("issued", "pending"):
        return False, f"Pass status is '{visitor_pass.status}'; not valid for entry."
    return True, "Pass is valid."


# ---------------------------------------------------------------------------
# BR-025 / BR-026: Report parameter & date range validation
# ---------------------------------------------------------------------------
MAX_REPORT_RANGE_DAYS = 365


def validate_report_params(params: dict) -> tuple[bool, str]:
    """Validate report generation request parameters."""
    report_type = params.get("report_type", "")
    if report_type not in ("visitor_summary", "incident_summary", "access_log", "vip_report", "full_audit"):
        return False, f"Unknown report type: '{report_type}'."
    return validate_date_range(params.get("start_date"), params.get("end_date"))


def validate_date_range(start_date, end_date) -> tuple[bool, str]:
    """Ensure date range is valid and within the allowed historical boundary."""
    if start_date is None or end_date is None:
        return False, "Both start_date and end_date are required."
    if start_date > end_date:
        return False, "start_date must not be after end_date."
    if end_date > date.today():
        return False, "end_date cannot be in the future."
    delta = (end_date - start_date).days
    if delta > MAX_REPORT_RANGE_DAYS:
        return False, f"Date range ({delta} days) exceeds maximum of {MAX_REPORT_RANGE_DAYS} days."
    return True, "Date range is valid."


# ---------------------------------------------------------------------------
# BR-058: Configuration value validation
# ---------------------------------------------------------------------------
CONFIG_VALIDATORS = {
    "max_daily_visitors": lambda v: v.isdigit() and int(v) > 0,
    "default_visit_duration": lambda v: v.isdigit() and 5 <= int(v) <= 1440,
    "vip_extra_minutes": lambda v: v.isdigit() and 0 <= int(v) <= 480,
    "enable_location_tracking": lambda v: v.lower() in ("true", "false"),
    "enable_notifications": lambda v: v.lower() in ("true", "false"),
    # BR-046: minimum vip_level that triggers mandatory escort assignment.
    "escort_threshold": lambda v: v.isdigit() and 1 <= int(v) <= 10,
}


def validate_config_value(key: str, value: str) -> tuple[bool, str]:
    """Validate a system configuration value before it is applied."""
    validator = CONFIG_VALIDATORS.get(key)
    if validator is None:
        return True, "No specific validation rule for this key."
    if validator(value):
        return True, "Configuration value is valid."
    return False, f"Invalid value '{value}' for configuration key '{key}'."


# ---------------------------------------------------------------------------
# BR-059: Configuration conflict detection
# ---------------------------------------------------------------------------
CONFLICTING_KEYS = [
    {"enable_location_tracking", "disable_all_tracking"},
]


def detect_config_conflicts(pending_changes: dict, current_config: dict) -> list[str]:
    """Return list of conflict descriptions between pending changes and current config."""
    merged = {**current_config, **pending_changes}
    conflicts = []
    for group in CONFLICTING_KEYS:
        active = [k for k in group if merged.get(k, "").lower() == "true"]
        if len(active) > 1:
            conflicts.append(f"Conflicting keys active simultaneously: {active}")
    return conflicts


# ---------------------------------------------------------------------------
# BR-068: Data format validation for export/import
# ---------------------------------------------------------------------------
ALLOWED_DATA_FORMATS = {"csv", "json", "xlsx"}


def validate_data_format(fmt: str) -> tuple[bool, str]:
    """Check that the requested data format is supported."""
    if fmt.lower() in ALLOWED_DATA_FORMATS:
        return True, "Data format is supported."
    return False, f"Unsupported data format '{fmt}'. Allowed: {ALLOWED_DATA_FORMATS}"


# ---------------------------------------------------------------------------
# BR-063: Visiting hours validation
# ---------------------------------------------------------------------------
def validate_visiting_hours(now=None) -> tuple[bool, str]:
    """Check if the current time falls within configured visiting hours."""
    from .models import VisitingHours
    if now is None:
        from django.conf import settings
        now = timezone.localtime(timezone.now()) if settings.USE_TZ else timezone.now()
    current_day = now.weekday()
    current_time = now.time()

    hours = VisitingHours.objects.filter(day_of_week=current_day, active=True)
    if not hours.exists():
        return True, "No visiting hours configured for today; access allowed."

    for slot in hours:
        if slot.is_holiday:
            return False, f"Today is a holiday ({slot.holiday_name}); visiting not allowed."
        if slot.start_time <= current_time <= slot.end_time:
            return True, "Within visiting hours."

    return False, "Current time is outside configured visiting hours."
