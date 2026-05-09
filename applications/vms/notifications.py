"""
VMS Notifications — notification dispatch for the Visitor Management System.

Covers:
  BR-006  Host notification on visitor request
  BR-016  Approval notification (visitor + security)
  BR-024  Overstay notification
  BR-033  Security alert to checkpoints on blacklist action
  BR-039  Invalid pass alert during tracking
  BR-040  Unauthorized area alert
  BR-045  VIP arrival notification
  BR-051  Authority notification per escalation level
  BR-055  High-severity: police / lockdown notification
  BR-056  Low-severity: supervisor notification
  BR-062  User notification on config change
"""

import logging
from django.utils import timezone

logger = logging.getLogger("vms.notifications")


def _dispatch(channel: str, recipients: list[str], subject: str, body: str) -> bool:
    """
    Internal dispatcher — logs the notification and returns True.
    In production this would integrate with email/SMS/push services.
    """
    logger.info(
        "VMS NOTIFICATION [%s] to=%s subject='%s' body='%s'",
        channel, recipients, subject, body,
    )
    return True


# ---------------------------------------------------------------------------
# BR-006: Host notification on visitor request submission
# ---------------------------------------------------------------------------
def notify_host_visitor_request(visit) -> bool:
    """Send notification to the host when a visitor registers."""
    return _dispatch(
        channel="email",
        recipients=[visit.host_contact or visit.host_name],
        subject=f"New visitor request: {visit.visitor.full_name}",
        body=(
            f"Visitor {visit.visitor.full_name} (ID: {visit.visitor.id_number}) "
            f"has requested a visit for '{visit.purpose}'. "
            f"Expected duration: {visit.expected_duration_minutes} minutes."
        ),
    )


# ---------------------------------------------------------------------------
# BR-016: Approval notification — visitor and security
# ---------------------------------------------------------------------------
def notify_approval(visit, visitor_pass) -> bool:
    """Notify both visitor and security staff that a visit has been approved."""
    _dispatch(
        channel="email",
        recipients=[visit.visitor.contact_email or visit.visitor.contact_phone],
        subject=f"Visit approved — Pass {visitor_pass.pass_number}",
        body=(
            f"Your visit to {visit.host_department} has been approved. "
            f"Pass: {visitor_pass.pass_number}, "
            f"Valid until: {visitor_pass.valid_until.isoformat()}, "
            f"Zones: {visitor_pass.authorized_zones}."
        ),
    )
    _dispatch(
        channel="internal",
        recipients=["security_desk"],
        subject=f"Visitor arriving: {visit.visitor.full_name}",
        body=(
            f"Pass {visitor_pass.pass_number} issued for {visit.visitor.full_name}. "
            f"Host: {visit.host_name} ({visit.host_department}). "
            f"VIP: {'Yes' if visit.is_vip else 'No'}."
        ),
    )
    return True


# ---------------------------------------------------------------------------
# BR-024: Overstay alert
# ---------------------------------------------------------------------------
def notify_overstay(visit, visitor_pass) -> bool:
    """Alert host and security that a visitor has overstayed."""
    return _dispatch(
        channel="alert",
        recipients=["security_desk", visit.host_name],
        subject=f"OVERSTAY: Visit {visit.id} — {visit.visitor.full_name}",
        body=(
            f"Visitor {visit.visitor.full_name} (Pass {visitor_pass.pass_number}) "
            f"has exceeded the approved duration. "
            f"Pass expired at {visitor_pass.valid_until.isoformat()}."
        ),
    )


# ---------------------------------------------------------------------------
# BR-033: Checkpoint alert on blacklist action
# ---------------------------------------------------------------------------
def notify_checkpoints_blacklist(blacklist_entry, action: str) -> bool:
    """Broadcast immediate alert to all security checkpoints."""
    return _dispatch(
        channel="broadcast",
        recipients=["all_checkpoints"],
        subject=f"BLACKLIST {action.upper()}: {blacklist_entry.id_number}",
        body=(
            f"Visitor with ID {blacklist_entry.id_number} has been {action}. "
            f"Reason: {blacklist_entry.reason}. "
            "Update local access control lists immediately."
        ),
    )


# ---------------------------------------------------------------------------
# BR-039: Invalid pass alert during location tracking
# ---------------------------------------------------------------------------
def notify_invalid_pass_scan(visit, checkpoint_name: str) -> bool:
    """Security alert when an invalid/expired pass is scanned at a checkpoint."""
    return _dispatch(
        channel="alert",
        recipients=["security_desk", "control_room"],
        subject=f"INVALID PASS SCAN at {checkpoint_name}",
        body=(
            f"Visit {visit.id} ({visit.visitor.full_name}) presented an invalid or "
            f"expired pass at checkpoint '{checkpoint_name}'."
        ),
    )


# ---------------------------------------------------------------------------
# BR-040: Unauthorized area alert
# ---------------------------------------------------------------------------
def notify_unauthorized_area(visit, zone_name: str) -> bool:
    """Immediate alert when visitor detected in a restricted area."""
    return _dispatch(
        channel="alert",
        recipients=["security_desk", "control_room"],
        subject=f"UNAUTHORIZED AREA: {visit.visitor.full_name} in {zone_name}",
        body=(
            f"Visitor {visit.visitor.full_name} (Visit {visit.id}) detected in "
            f"restricted zone '{zone_name}'. Authorized zones: "
            f"{getattr(visit, 'visitor_pass', None) and visit.visitor_pass.authorized_zones or 'N/A'}."
        ),
    )


# ---------------------------------------------------------------------------
# BR-045: VIP arrival notification
# ---------------------------------------------------------------------------
def notify_vip_arrival(visit) -> bool:
    """Notify senior security and admin staff of a VIP visitor arrival."""
    return _dispatch(
        channel="priority",
        recipients=["senior_security", "administration"],
        subject=f"VIP ARRIVAL: {visit.visitor.full_name}",
        body=(
            f"VIP visitor {visit.visitor.full_name} has arrived on campus. "
            f"Host: {visit.host_name} ({visit.host_department}). "
            f"Purpose: {visit.purpose}."
        ),
    )


# ---------------------------------------------------------------------------
# BR-051: Authority notification per escalation level
# ---------------------------------------------------------------------------
ESCALATION_RECIPIENTS = {
    0: [],
    1: ["shift_supervisor"],
    2: ["security_head"],
    3: ["administration", "security_head"],
    4: ["police_liaison", "administration", "security_head"],
}


def notify_escalation(incident) -> bool:
    """Notify authorities according to incident escalation level."""
    recipients = ESCALATION_RECIPIENTS.get(incident.escalation_level, [])
    if not recipients:
        return False
    return _dispatch(
        channel="escalation",
        recipients=recipients,
        subject=f"INCIDENT ESCALATION (Level {incident.escalation_level}): {incident.tracking_number}",
        body=(
            f"Incident {incident.tracking_number} ({incident.severity}/{incident.issue_type}): "
            f"{incident.description[:200]}. "
            f"Escalation level: {incident.escalation_level}."
        ),
    )


# ---------------------------------------------------------------------------
# BR-055: High severity — police / lockdown
# ---------------------------------------------------------------------------
def notify_high_severity_response(incident) -> bool:
    """Trigger police notification and campus lockdown alert for critical incidents."""
    return _dispatch(
        channel="emergency",
        recipients=["police_liaison", "campus_security_all", "administration"],
        subject=f"EMERGENCY — {incident.tracking_number}: {incident.issue_type}",
        body=(
            f"HIGH-SEVERITY incident requiring immediate response. "
            f"Tracking: {incident.tracking_number}. "
            f"Severity: {incident.severity}. Type: {incident.issue_type}. "
            f"Description: {incident.description[:300]}. "
            "Initiate campus lockdown protocol if applicable."
        ),
    )


# ---------------------------------------------------------------------------
# BR-056: Low severity — supervisor only
# ---------------------------------------------------------------------------
def notify_low_severity(incident) -> bool:
    """Standard supervisor notification for low-severity incidents."""
    return _dispatch(
        channel="internal",
        recipients=["shift_supervisor"],
        subject=f"Low-priority incident: {incident.tracking_number}",
        body=(
            f"Incident {incident.tracking_number} ({incident.issue_type}): "
            f"{incident.description[:200]}. Handle via standard protocol."
        ),
    )


# ---------------------------------------------------------------------------
# BR-062: User notification on config change
# ---------------------------------------------------------------------------
def notify_config_change(config_entry, changed_by: str) -> bool:
    """Notify affected users when a system configuration changes."""
    return _dispatch(
        channel="internal",
        recipients=["all_vms_users"],
        subject=f"VMS Config Updated: {config_entry.key}",
        body=(
            f"Configuration '{config_entry.key}' has been updated "
            f"by {changed_by}. New value: {config_entry.value}. "
            f"Description: {config_entry.description}."
        ),
    )
