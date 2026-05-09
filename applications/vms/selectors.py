from django.db.models import Count, Q
from django.utils import timezone

from applications.globals.models import ExtraInfo

from .models import (
    AccessZone,
    BlacklistAuditLog,
    BlacklistEntry,
    ConfigChangeLog,
    DataOperationLog,
    EscortAssignment,
    SecurityIncident,
    SystemConfig,
    VIPActivityLog,
    Visit,
    Visitor,
    VisitorLocation,
    VisitorPass,
    VisitingHours,
)


def get_current_staff(user):
    """Return the ExtraInfo record for the given user, or None."""
    return ExtraInfo.objects.filter(user=user).first()


# ---------------------------------------------------------------------------
# Visit queries
# ---------------------------------------------------------------------------
def get_active_visitors():
    """Return visits that are currently inside or have a pass issued."""
    return Visit.objects.filter(
        status__in=[Visit.STATUS_INSIDE, Visit.STATUS_PASS_ISSUED],
    ).select_related("visitor").order_by("-registered_at")


def get_recent_visits(limit=5):
    """Return the most recent visits, ordered newest-first."""
    return Visit.objects.select_related("visitor").order_by("-registered_at")[:limit]


# ---------------------------------------------------------------------------
# Incident queries
# ---------------------------------------------------------------------------
def get_incidents(limit=20):
    """Return the most recent security incidents."""
    return SecurityIncident.objects.order_by("-created_at")[:limit]


def get_incidents_by_severity(severity: str, limit=50):
    """Filter incidents by severity level."""
    return SecurityIncident.objects.filter(severity=severity).order_by("-created_at")[:limit]


def get_open_incidents():
    """Return all incidents with status 'open'."""
    return SecurityIncident.objects.filter(status="open").order_by("-created_at")


# ---------------------------------------------------------------------------
# BR-030: Visitor history for blacklist evaluation
# ---------------------------------------------------------------------------
def get_visitor_full_history(id_number: str):
    """Return all visits, incidents, and blacklist records for a visitor."""
    visitor = Visitor.objects.filter(id_number=id_number).first()
    if visitor is None:
        return {"visitor": None, "visits": [], "incidents": [], "blacklist": []}

    return {
        "visitor": visitor,
        "visits": list(Visit.objects.filter(visitor=visitor).order_by("-registered_at")),
        "incidents": list(SecurityIncident.objects.filter(visitor=visitor).order_by("-created_at")),
        "blacklist": list(BlacklistEntry.objects.filter(id_number=id_number)),
    }


# ---------------------------------------------------------------------------
# BR-031: Incident history for blacklist decisions
# ---------------------------------------------------------------------------
def get_incident_history_for_visitor(id_number: str):
    """Return past incidents linked to a visitor by ID number."""
    visitor = Visitor.objects.filter(id_number=id_number).first()
    if visitor is None:
        return []
    return list(SecurityIncident.objects.filter(visitor=visitor).order_by("-created_at"))


# ---------------------------------------------------------------------------
# BR-036/037: Location tracking queries
# ---------------------------------------------------------------------------
def get_visitor_location_trail(visit_id: int):
    """Return chronological location trail for a visit."""
    return VisitorLocation.objects.filter(visit_id=visit_id).order_by("scanned_at")


def get_current_visitors_in_zone(zone_name: str):
    """Return visitors currently in a specific zone (latest scan)."""
    from django.db.models import Max, Subquery, OuterRef

    latest_scans = VisitorLocation.objects.filter(
        visit__status=Visit.STATUS_INSIDE
    ).values("visit_id").annotate(latest=Max("scanned_at"))

    return VisitorLocation.objects.filter(
        visit__status=Visit.STATUS_INSIDE,
        checkpoint_name__icontains=zone_name,
        scanned_at__in=[s["latest"] for s in latest_scans],
    ).select_related("visit__visitor")


# ---------------------------------------------------------------------------
# BR-024: Overstay detection query
# ---------------------------------------------------------------------------
def get_overstaying_visitors():
    """Return visits where the pass has expired but visitor is still inside."""
    now = timezone.now()
    return Visit.objects.filter(
        status=Visit.STATUS_INSIDE,
        visitor_pass__valid_until__lt=now,
    ).select_related("visitor", "visitor_pass")


# ---------------------------------------------------------------------------
# Blacklist queries
# ---------------------------------------------------------------------------
def get_active_blacklist():
    """Return all active blacklist entries."""
    return BlacklistEntry.objects.filter(active=True).order_by("-created_at")


def get_blacklist_audit_trail(id_number: str):
    """Return audit log for a specific blacklisted ID number."""
    return BlacklistAuditLog.objects.filter(id_number=id_number).order_by("-created_at")


# ---------------------------------------------------------------------------
# VIP queries
# ---------------------------------------------------------------------------
def get_active_vip_visits():
    """Return all active VIP visits."""
    return Visit.objects.filter(
        is_vip=True,
        status__in=[Visit.STATUS_INSIDE, Visit.STATUS_PASS_ISSUED, Visit.STATUS_VERIFIED],
    ).select_related("visitor").order_by("-registered_at")


def get_vip_activity_log(visit_id: int):
    """Return enhanced activity log for a VIP visit."""
    return VIPActivityLog.objects.filter(visit_id=visit_id).order_by("-created_at")


def get_active_escorts():
    """Return all currently active escort assignments."""
    return EscortAssignment.objects.filter(released_at__isnull=True).select_related("visit__visitor")


def get_busy_escort_ids():
    """BR-046: ExtraInfo IDs of personnel currently on an unreleased escort duty."""
    return set(
        EscortAssignment.objects.filter(
            released_at__isnull=True, escort__isnull=False
        ).values_list("escort_id", flat=True)
    )


def is_escort_available(escort_id):
    """BR-046: True when the staff member has no unreleased escort assignment."""
    if not escort_id:
        return False
    return not EscortAssignment.objects.filter(
        escort_id=escort_id, released_at__isnull=True
    ).exists()


def get_available_escorts():
    """BR-046: Qualified security personnel free to take a new escort duty.

    'Qualified' here means any ExtraInfo tagged under the security department
    (department name contains 'security'). Deployments without that taxonomy
    still surface every staff member that is not already busy, so the UI is
    never empty on a fresh install.
    """
    busy = get_busy_escort_ids()
    qs = ExtraInfo.objects.filter(user__is_active=True).exclude(id__in=busy)
    qualified = qs.filter(department__name__icontains="security")
    if qualified.exists():
        return qualified
    return qs


# ---------------------------------------------------------------------------
# Report-oriented queries (BR-025–029)
# ---------------------------------------------------------------------------
def get_visit_statistics(start_date, end_date):
    """Aggregate visit statistics over a date range."""
    visits = Visit.objects.filter(
        registered_at__date__gte=start_date,
        registered_at__date__lte=end_date,
    )
    return {
        "total": visits.count(),
        "by_status": dict(visits.values_list("status").annotate(c=Count("id"))),
        "vip_count": visits.filter(is_vip=True).count(),
        "avg_duration": visits.exclude(exit_at__isnull=True).extra(
            select={"dur": "EXTRACT(EPOCH FROM (exit_at - entry_at)) / 60"}
        ).values_list("dur", flat=True),
    }


def get_incident_statistics(start_date, end_date):
    """Aggregate incident statistics over a date range."""
    incidents = SecurityIncident.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    return {
        "total": incidents.count(),
        "by_severity": dict(incidents.values_list("severity").annotate(c=Count("id"))),
        "by_type": dict(incidents.values_list("issue_type").annotate(c=Count("id"))),
        "open_count": incidents.filter(status="open").count(),
    }


# ---------------------------------------------------------------------------
# System config queries (BR-057–066)
# ---------------------------------------------------------------------------
def get_all_config():
    """Return all system configuration entries."""
    return SystemConfig.objects.all().order_by("key")


def get_config_value(key: str, default: str = "") -> str:
    """Return a single config value by key."""
    config = SystemConfig.objects.filter(key=key).first()
    return config.value if config else default


def get_config_change_history(key: str = None, limit=50):
    """Return configuration change history, optionally filtered by key."""
    qs = ConfigChangeLog.objects.select_related("config")
    if key:
        qs = qs.filter(config__key=key)
    return qs.order_by("-changed_at")[:limit]


# ---------------------------------------------------------------------------
# Visiting hours queries (BR-063)
# ---------------------------------------------------------------------------
def get_visiting_hours():
    """Return all configured visiting hours."""
    return VisitingHours.objects.filter(active=True).order_by("day_of_week")


# ---------------------------------------------------------------------------
# Access zone queries (BR-064)
# ---------------------------------------------------------------------------
def get_all_zones():
    """Return all configured access zones."""
    return AccessZone.objects.all().order_by("name")


def get_restricted_zones():
    """Return only restricted zones."""
    return AccessZone.objects.filter(is_restricted=True, active=True)


# ---------------------------------------------------------------------------
# Data operation queries (BR-072)
# ---------------------------------------------------------------------------
def get_data_operations(limit=20):
    """Return recent data export/import operations."""
    return DataOperationLog.objects.order_by("-started_at")[:limit]
