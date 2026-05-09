"""
VMS Background Tasks — periodic and event-driven tasks.

Covers:
  BR-024  Overstay detection and alerting
  BR-036  Location tracking activation on pass scan
  BR-038  Real-time dashboard push (placeholder)
  BR-052  Containment action requirements
  BR-053  Visitor status update on incident
  BR-060  Configuration cache refresh
"""

import logging
from django.utils import timezone

from .models import SecurityIncident, Visit, VisitorPass

logger = logging.getLogger("vms.tasks")


# ---------------------------------------------------------------------------
# BR-024: Overstay detection
# ---------------------------------------------------------------------------
def detect_overstays():
    """
    Scan all active visits with issued passes and flag those whose
    pass has expired while the visitor is still inside.
    Returns list of (visit, visitor_pass) tuples that are overstaying.
    """
    from .notifications import notify_overstay

    now = timezone.now()
    overstaying = []

    active_visits = Visit.objects.filter(status=Visit.STATUS_INSIDE).select_related("visitor_pass", "visitor")

    for visit in active_visits:
        vpass = getattr(visit, "visitor_pass", None)
        if vpass and vpass.valid_until < now:
            overstaying.append((visit, vpass))
            notify_overstay(visit, vpass)
            logger.warning(
                "Overstay detected: Visit %s (%s), pass expired at %s",
                visit.id, visit.visitor.full_name, vpass.valid_until,
            )

    return overstaying


# ---------------------------------------------------------------------------
# BR-036: Location tracking activation
# ---------------------------------------------------------------------------
def activate_location_tracking(visit, checkpoint_name: str, recorded_by=None):
    """
    Record a location scan event. Called when a visitor pass is scanned
    at any checkpoint. Creates a VisitorLocation entry.
    """
    from .models import AccessZone, VisitorLocation

    zone = AccessZone.objects.filter(name__icontains=checkpoint_name).first()

    location = VisitorLocation.objects.create(
        visit=visit,
        zone=zone,
        checkpoint_name=checkpoint_name,
        recorded_by=recorded_by,
    )
    logger.info("Location recorded: Visit %s at %s", visit.id, checkpoint_name)
    return location


# ---------------------------------------------------------------------------
# BR-038: Real-time dashboard push (placeholder)
# ---------------------------------------------------------------------------
def push_dashboard_update(event_type: str, payload: dict):
    """
    Placeholder for WebSocket/SSE push to the tracking dashboard.
    In production, integrate with Django Channels or similar.
    """
    logger.info("Dashboard push [%s]: %s", event_type, payload)
    return True


# ---------------------------------------------------------------------------
# BR-052: Containment actions
# ---------------------------------------------------------------------------
CONTAINMENT_ACTIONS = {
    "critical": [
        "Initiate campus lockdown",
        "Notify police liaison",
        "Secure all entry/exit points",
        "Activate CCTV monitoring for all zones",
    ],
    "high": [
        "Restrict visitor movement to current zone",
        "Deploy patrol officers to area",
        "Notify security head",
    ],
    "medium": [
        "Monitor visitor via CCTV",
        "Alert nearest patrol officer",
    ],
    "low": [
        "Log for supervisor review",
    ],
}


def determine_containment_actions(incident: SecurityIncident) -> list[str]:
    """
    Return required containment actions based on incident severity.
    Also persists them on the incident record.
    """
    actions = CONTAINMENT_ACTIONS.get(incident.severity, [])
    incident.containment_actions = "\n".join(actions)
    incident.save(update_fields=["containment_actions"])
    logger.info(
        "Containment actions for %s: %s",
        incident.tracking_number, actions,
    )
    return actions


# ---------------------------------------------------------------------------
# BR-053: Visitor status update on incident
# ---------------------------------------------------------------------------
def update_visitor_status_on_incident(incident: SecurityIncident):
    """
    Update a visitor's current visit status when they are involved
    in a security incident.
    """
    visit = incident.visit
    if visit is None:
        return None

    if incident.severity in (SecurityIncident.SEVERITY_CRITICAL, SecurityIncident.SEVERITY_HIGH):
        visit.status = Visit.STATUS_DENIED
        visit.denial_reason = f"security_incident_{incident.tracking_number}"
        visit.denial_remarks = incident.description[:200]
        visit.save(update_fields=["status", "denial_reason", "denial_remarks"])
        logger.info("Visit %s denied due to incident %s", visit.id, incident.tracking_number)
    return visit


# ---------------------------------------------------------------------------
# BR-060: Configuration cache refresh
# ---------------------------------------------------------------------------
_config_cache: dict[str, str] = {}


def refresh_config_cache():
    """Reload all system configuration values into the in-memory cache."""
    from .models import SystemConfig
    global _config_cache
    _config_cache = {c.key: c.value for c in SystemConfig.objects.all()}
    logger.info("VMS config cache refreshed: %d entries", len(_config_cache))
    return _config_cache


def get_cached_config(key: str, default: str = "") -> str:
    """Retrieve a config value from cache, refreshing if empty."""
    if not _config_cache:
        refresh_config_cache()
    return _config_cache.get(key, default)
