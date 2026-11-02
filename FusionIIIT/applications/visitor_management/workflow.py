"""Visit lifecycle state machine.

The table below is a direct transcription of the authoritative State-Transition
Tables in VMS Workflow Specifications v1.3 (CW-VMS-01, 02, 03, 05, 07). Every
state change in the module goes through :func:`apply`, which refuses any move
the STT does not allow and records the STT row in ``VisitStateHistory``.

Rows marked "UC alt" are outcomes a use case states explicitly but no basis
workflow draws (e.g. an Admin rejecting a same-day exception); they reach only
states the STT already defines.
"""

from collections import namedtuple

from .constants import VisitStatus as S
from .constants import VmsRole
from .errors import Conflict
from .models import VisitStateHistory

Transition = namedtuple("Transition", "from_states to_state refs uc actor")

NEW = None  # "Not Submitted" / "Not Registered" / "Event Visitor List Draft"

TRANSITIONS = {
    # CW-VMS-01 Pre-registered Visit Lifecycle
    "SUBMIT_STANDARD": Transition({NEW}, S.PENDING_HOST_APPROVAL, "BW-VMS-01 R1 / BW-VMS-02 R1 / BW-VMS-03 R1", "VMS-UC-010", VmsRole.VISITOR),
    "SUBMIT_URGENT": Transition({NEW}, S.PENDING_ADMIN_EXCEPTION, "BW-VMS-22 R1", "VMS-UC-010", VmsRole.VISITOR),
    "SUBMIT_PREAUTHORIZED": Transition({NEW}, S.PASS_ACTIVE, "BW-VMS-04 R2", "VMS-UC-010", VmsRole.VISITOR),
    "SUBMIT_VIP": Transition({NEW}, S.PASS_ACTIVE, "BW-VMS-05 R2", "VMS-UC-010", VmsRole.VISITOR),
    "HOST_APPROVE": Transition({S.PENDING_HOST_APPROVAL}, S.PASS_ACTIVE, "BW-VMS-01 R2 / BW-VMS-22 R3 / BW-VMS-06 R2", "VMS-UC-013", VmsRole.HOST),
    "HOST_REJECT": Transition({S.PENDING_HOST_APPROVAL}, S.REJECTED, "BW-VMS-02 R2 / BW-VMS-08 R2", "VMS-UC-013", VmsRole.HOST),
    "EXPIRE": Transition({S.PENDING_HOST_APPROVAL}, S.EXPIRED, "BW-VMS-03 R2", "VMS-UC-037", VmsRole.SYSTEM),
    "EXCEPTION_APPROVE": Transition({S.PENDING_ADMIN_EXCEPTION}, S.PENDING_HOST_APPROVAL, "BW-VMS-22 R2", "VMS-UC-035", VmsRole.ADMIN),
    "EXCEPTION_REJECT": Transition({S.PENDING_ADMIN_EXCEPTION}, S.REJECTED, "VMS-UC-035 alt", "VMS-UC-035", VmsRole.ADMIN),
    # CW-VMS-02 Walk-in Visit Lifecycle
    "WALKIN_HOST_AVAILABLE": Transition({NEW}, S.PENDING_HOST_APPROVAL, "BW-VMS-06 R1 / BW-VMS-08 R1", "VMS-UC-017", VmsRole.SECURITY),
    "WALKIN_HOST_UNAVAILABLE": Transition({NEW}, S.PENDING_ADMIN_CONTINGENCY, "BW-VMS-07 R1", "VMS-UC-017", VmsRole.SECURITY),
    "CONTINGENCY_APPROVE": Transition({S.PENDING_ADMIN_CONTINGENCY}, S.PASS_ACTIVE, "BW-VMS-07 R2", "VMS-UC-033", VmsRole.ADMIN),
    "CONTINGENCY_REJECT": Transition({S.PENDING_ADMIN_CONTINGENCY}, S.REJECTED, "VMS-UC-033 main step 2", "VMS-UC-033", VmsRole.ADMIN),
    # CW-VMS-07 Bulk Event Visitor Handling
    "BULK_ACCEPT": Transition({NEW}, S.PASS_ACTIVE, "BW-VMS-21 R1", "VMS-UC-008", VmsRole.ADMIN),
    # Gate entry (lifecycle R3 rows) and CW-VMS-03 exception handling
    "GATE_CHECK_IN": Transition({S.PASS_ACTIVE}, S.ON_SITE, "BW-VMS-01 R3 / 04 R3 / 05 R3 / 06 R3 / 07 R3 / 21 R3 / 22 R4", "VMS-UC-018", VmsRole.SECURITY),
    "MANUAL_ENTRY": Transition({S.PASS_ACTIVE}, S.ON_SITE, "BW-VMS-10 R3", "VMS-UC-020", VmsRole.SECURITY),
    "OFFLINE_CHECK_IN": Transition({S.PASS_ACTIVE}, S.ON_SITE, "BW-VMS-11 R2", "VMS-UC-039", VmsRole.SYSTEM),
    # Checkout / completion (VMS-BR-105)
    "GATE_CHECK_OUT": Transition({S.ON_SITE, S.ON_SITE_PENDING_EXIT}, S.COMPLETED, "BW-VMS-01 R4 / 16 R2 / 18 R2 / 21 R4", "VMS-UC-021", VmsRole.SECURITY),
    "SELF_CHECK_OUT": Transition({S.ON_SITE, S.ON_SITE_PENDING_EXIT}, S.COMPLETED, "VMS-UC-031", "VMS-UC-031", VmsRole.VISITOR),
    "AUTO_CHECK_OUT": Transition({S.ON_SITE, S.ON_SITE_PENDING_EXIT}, S.COMPLETED, "VMS-UC-038", "VMS-UC-038", VmsRole.SYSTEM),
    "OFFLINE_CHECK_OUT": Transition({S.ON_SITE, S.ON_SITE_PENDING_EXIT}, S.COMPLETED, "BW-VMS-11 R2", "VMS-UC-039", VmsRole.SYSTEM),
    # CW-VMS-05 Early Termination and Extension
    "HOST_TERMINATE_BEFORE_CHECK_IN": Transition({S.PASS_ACTIVE}, S.TERMINATED, "BW-VMS-15 R1", "VMS-UC-016", VmsRole.HOST),
    "HOST_TERMINATE_ON_SITE": Transition({S.ON_SITE}, S.ON_SITE_PENDING_EXIT, "BW-VMS-16 R1", "VMS-UC-016", VmsRole.HOST),
    "ADMIN_TERMINATE_BEFORE_CHECK_IN": Transition({S.PASS_ACTIVE}, S.TERMINATED, "BW-VMS-17 R1", "VMS-UC-036", VmsRole.ADMIN),
    "ADMIN_TERMINATE_ON_SITE": Transition({S.ON_SITE}, S.ON_SITE_PENDING_EXIT, "BW-VMS-18 R1", "VMS-UC-036", VmsRole.ADMIN),
    "EXTENSION_APPROVED": Transition({S.PASS_ACTIVE, S.ON_SITE}, None, "BW-VMS-23 R1", "VMS-UC-034", VmsRole.ADMIN),
}


def allowed(action, status):
    return status in TRANSITIONS[action].from_states


def apply(visit, action, actor=None, actor_role=None, note="", save=True):
    """Move ``visit`` along ``action`` or raise Conflict. Returns the history row."""
    transition = TRANSITIONS[action]
    current = visit.status or None
    if current not in transition.from_states:
        raise Conflict(
            "Visit {} cannot perform {} from state {}.".format(visit.reference, action, current or "NEW"),
            code="invalid_transition",
            details={"status": current, "action": action},
        )
    to_state = transition.to_state or current
    visit.status = to_state
    if save:
        visit.save()
    return VisitStateHistory.objects.create(
        visit=visit,
        from_status=current or "",
        to_status=to_state,
        transition_ref=transition.refs,
        uc_ref=transition.uc,
        actor=actor if (actor is not None and getattr(actor, "is_authenticated", False)) else None,
        actor_role=actor_role or transition.actor,
        note=note or "",
    )


# --------------------------------------------------------------------------
# STT traceability: every basis-workflow row -> what implements it.
# ("visit", ACTION) rows go through TRANSITIONS above; the others change the
# state of a different record (gate attempt, alert, muster, event, ...).
# tests/test_workflows.py checks this map against specs/workflows.yaml.
# --------------------------------------------------------------------------

STT_TRACE = {
    "BW-VMS-01 R1": ("visit", "SUBMIT_STANDARD"),
    "BW-VMS-01 R2": ("visit", "HOST_APPROVE"),
    "BW-VMS-01 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-01 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-02 R1": ("visit", "SUBMIT_STANDARD"),
    "BW-VMS-02 R2": ("visit", "HOST_REJECT"),
    "BW-VMS-03 R1": ("visit", "SUBMIT_STANDARD"),
    "BW-VMS-03 R2": ("visit", "EXPIRE"),
    "BW-VMS-04 R1": ("preauthorization", "PreAuthorization.is_active"),
    "BW-VMS-04 R2": ("visit", "SUBMIT_PREAUTHORIZED"),
    "BW-VMS-04 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-04 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-05 R1": ("vip_permission", "VipPermission.is_active"),
    "BW-VMS-05 R2": ("visit", "SUBMIT_VIP"),
    "BW-VMS-05 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-05 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-06 R1": ("visit", "WALKIN_HOST_AVAILABLE"),
    "BW-VMS-06 R2": ("visit", "HOST_APPROVE"),
    "BW-VMS-06 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-06 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-07 R1": ("visit", "WALKIN_HOST_UNAVAILABLE"),
    "BW-VMS-07 R2": ("visit", "CONTINGENCY_APPROVE"),
    "BW-VMS-07 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-07 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-08 R1": ("visit", "WALKIN_HOST_AVAILABLE"),
    "BW-VMS-08 R2": ("visit", "HOST_REJECT"),
    "BW-VMS-09 R1": ("gate_attempt", "GateAttempt.status=BLOCKED"),
    "BW-VMS-10 R1": ("gate_attempt", "GateAttempt.status=BLOCKED (override_eligible)"),
    "BW-VMS-10 R2": ("gate_attempt", "GateAttempt.status=OVERRIDE_AUTHORIZED"),
    "BW-VMS-10 R3": ("visit", "MANUAL_ENTRY"),
    "BW-VMS-11 R1": ("offline_event", "OfflineGateEvent.status=PENDING_RECONCILIATION"),
    "BW-VMS-11 R2": ("visit", "OFFLINE_CHECK_IN"),
    "BW-VMS-12 R1": ("visit_log", "VisitLog.log_type=ZONE_ACCESS"),
    "BW-VMS-13 R1": ("security_alert", "VisitLog ACCESS_DENIED + SecurityAlert.status=OPEN"),
    "BW-VMS-13 R2": ("security_alert", "SecurityAlert.status=HANDLED"),
    "BW-VMS-14 R1": ("security_alert", "VisitLog ACCESS_DENIED + SecurityAlert.status=OPEN"),
    "BW-VMS-14 R2": ("zone_elevation", "ZoneElevation (time-boxed)"),
    "BW-VMS-14 R3": ("visit_log", "VisitLog.log_type=ZONE_ACCESS (TEMPORARY_ELEVATION)"),
    "BW-VMS-15 R1": ("visit", "HOST_TERMINATE_BEFORE_CHECK_IN"),
    "BW-VMS-16 R1": ("visit", "HOST_TERMINATE_ON_SITE"),
    "BW-VMS-16 R2": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-17 R1": ("visit", "ADMIN_TERMINATE_BEFORE_CHECK_IN"),
    "BW-VMS-18 R1": ("visit", "ADMIN_TERMINATE_ON_SITE"),
    "BW-VMS-18 R2": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-19 R1": ("muster", "EmergencyMuster.status=ACTIVE (Admin)"),
    "BW-VMS-19 R2": ("muster", "EmergencyMuster.status=COMPLETED"),
    "BW-VMS-20 R1": ("muster", "EmergencyMuster.status=ACTIVE (Security)"),
    "BW-VMS-20 R2": ("muster", "EmergencyMuster.status=COMPLETED"),
    "BW-VMS-21 R1": ("visit", "BULK_ACCEPT"),
    "BW-VMS-21 R2": ("event", "VisitorEvent.status=CONTROLS_ACTIVE"),
    "BW-VMS-21 R3": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-21 R4": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-22 R1": ("visit", "SUBMIT_URGENT"),
    "BW-VMS-22 R2": ("visit", "EXCEPTION_APPROVE"),
    "BW-VMS-22 R3": ("visit", "HOST_APPROVE"),
    "BW-VMS-22 R4": ("visit", "GATE_CHECK_IN"),
    "BW-VMS-22 R5": ("visit", "GATE_CHECK_OUT"),
    "BW-VMS-23 R1": ("visit", "EXTENSION_APPROVED"),
}
