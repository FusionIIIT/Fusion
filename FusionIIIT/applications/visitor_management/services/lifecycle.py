"""Cross-cutting lifecycle services.

VMS-UC-016/036 early termination, VMS-UC-034 extension, and the event-triggered
services VMS-UC-037 (expiry), VMS-UC-038 (automatic checkout), VMS-UC-039
(offline reconciliation) and VMS-UC-040 (approval reminders).
"""

from django.db import transaction

from .. import audit, workflow
from ..constants import ExtensionStatus, LogMethod, NotificationEvent, VisitStatus, VmsRole
from ..errors import Conflict, NotAuthorized, NotFound, ValidationFailed
from ..models import ExtensionRequest, VisitRequest
from ..notifications import notify_role, notify_user, notify_visitor
from ..selectors import admin_covers, host_extrainfo, now
from .common import deactivate_pass, minutes, route_admin, visit_zone_set


# --------------------------------------------------------------------------
# VMS-UC-016 / VMS-UC-036 Terminate Visitor Visit Early (VMS-BR-073)
# --------------------------------------------------------------------------

@transaction.atomic
def terminate_visit(actor, reference, reason, as_role):
    visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").filter(
        reference=reference).first()
    if visit is None:
        raise NotFound("Visit not found.")
    if not (reason or "").strip():
        raise ValidationFailed("A policy-breach reason is required.", details={"reason": ["required"]})
    if as_role == VmsRole.HOST:
        host = host_extrainfo(actor)
        if host is None or host.pk != visit.host_id:
            raise NotAuthorized("Only the visit's Host can terminate it.")
        actions = ("HOST_TERMINATE_BEFORE_CHECK_IN", "HOST_TERMINATE_ON_SITE")
    else:
        if not admin_covers(actor, zones=visit_zone_set(visit), gate=visit.entry_gate or visit.registration_gate):
            raise NotAuthorized("You are not an authorised Admin for this visit.")
        actions = ("ADMIN_TERMINATE_BEFORE_CHECK_IN", "ADMIN_TERMINATE_ON_SITE")
    visit_pass = getattr(visit, "visit_pass", None)
    if visit_pass is None or not visit_pass.is_active:
        raise Conflict("The pass is already inactive.", code="already_inactive")
    if visit.status == VisitStatus.PASS_ACTIVE:
        action = actions[0]
    elif visit.status == VisitStatus.ON_SITE:
        action = actions[1]
    else:
        raise Conflict("Only an active pass or on-site visit can be terminated.", code="not_active")
    current = now()
    visit.terminated_at, visit.terminated_by, visit.termination_reason = current, actor, reason.strip()
    workflow.apply(visit, action, actor=actor, actor_role=as_role, note=reason.strip())
    deactivate_pass(visit_pass, actor, "TERMINATED: " + reason.strip())
    audit.record(actor, as_role, "VISIT_TERMINATED", visit, visitor=visit.visitor, message=reason.strip(),
                 metadata={"status": visit.status})
    notify_visitor(visit.visitor, NotificationEvent.VISIT_TERMINATED, "Visit authorisation ended",
                   "Your pass for visit {} has been deactivated.{}".format(
                       visit.reference, " Please proceed to the exit gate." if visit.status == VisitStatus.ON_SITE_PENDING_EXIT else ""),
                   visit=visit)
    notify_role(VmsRole.SECURITY, NotificationEvent.VISIT_TERMINATED, "Pass deactivated",
                "{} ({}) pass deactivated; {}.".format(
                    visit.visitor.full_name, visit.reference,
                    "visitor still on-site, record exit" if visit.status == VisitStatus.ON_SITE_PENDING_EXIT else "deny entry"),
                visit=visit)
    if as_role == VmsRole.ADMIN:
        notify_user(visit.host.user, NotificationEvent.VISIT_TERMINATED, "Visit terminated by Admin",
                    "{} ({}): {}".format(visit.visitor.full_name, visit.reference, reason.strip()), visit=visit)
    return visit


# --------------------------------------------------------------------------
# VMS-UC-034 Decide Visit Extension (VMS-BR-193/194)
# --------------------------------------------------------------------------

def _extendable(visit):
    visit_pass = getattr(visit, "visit_pass", None)
    if visit.status not in (VisitStatus.PASS_ACTIVE, VisitStatus.ON_SITE) or visit_pass is None or not visit_pass.is_active:
        raise Conflict("Only an active visit can be extended.", code="not_active")
    return visit_pass


def _apply_extension(visit, visit_pass, new_until):
    visit_pass.valid_until = new_until
    visit_pass.save(update_fields=["valid_until"])
    visit.scheduled_end = new_until
    visit.save(update_fields=["scheduled_end", "updated_at"])


@transaction.atomic
def request_extension(actor, reference, requested_valid_until, reason):
    visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").filter(
        reference=reference).first()
    if visit is None:
        raise NotFound("Visit not found.")
    host = host_extrainfo(actor)
    is_visit_host = host is not None and host.pk == visit.host_id
    admin = admin_covers(actor, zones=visit_zone_set(visit))
    if not (is_visit_host or admin):
        raise NotAuthorized("Only the visit's Host or an authorised Admin can request an extension.")
    visit_pass = _extendable(visit)
    if not requested_valid_until or requested_valid_until <= visit_pass.valid_until:
        raise ValidationFailed("The new end must be later than the current validity.",
                               details={"requested_valid_until": ["invalid"]})
    max_minutes = visit.policy_snapshot["max_visit_duration_minutes"]
    within_max = (requested_valid_until - visit_pass.valid_from) <= minutes(max_minutes)
    role = VmsRole.HOST if is_visit_host else VmsRole.ADMIN
    if within_max:
        # UC-034 alt flow: within the maximum no Admin exception is needed.
        old_until = visit_pass.valid_until
        _apply_extension(visit, visit_pass, requested_valid_until)
        audit.record(actor, role, "VISIT_EXTENDED_WITHIN_MAX", visit, visitor=visit.visitor,
                     metadata={"from": old_until, "to": requested_valid_until})
        notify_visitor(visit.visitor, NotificationEvent.VISIT_EXTENDED, "Visit extended",
                       "Visit {} now ends at {}.".format(visit.reference, requested_valid_until.strftime("%d %b %H:%M")),
                       visit=visit)
        return None, visit
    if ExtensionRequest.objects.filter(visit=visit, status=ExtensionStatus.PENDING).exists():
        raise Conflict("An extension request is already pending for this visit.", code="extension_pending")
    if not (reason or "").strip():
        raise ValidationFailed("A reason is required for an extension beyond the maximum.", details={"reason": ["required"]})
    extension = ExtensionRequest.objects.create(
        visit=visit, requested_by=actor, requested_by_role=role, current_valid_until=visit_pass.valid_until,
        requested_valid_until=requested_valid_until, reason=reason.strip(),
        assigned_admin=route_admin(visit_zone_set(visit)),
    )
    audit.record(actor, role, "EXTENSION_REQUESTED", extension, visitor=visit.visitor,
                 metadata={"requested_valid_until": requested_valid_until})
    if extension.assigned_admin and extension.assigned_admin != actor:
        notify_user(extension.assigned_admin, NotificationEvent.REQUEST_PENDING_FOR_ADMIN, "Visit extension request",
                    "{} ({}) requests validity until {}.".format(visit.visitor.full_name, visit.reference,
                                                               requested_valid_until.strftime("%d %b %H:%M")),
                    visit=visit)
    return extension, visit


@transaction.atomic
def decide_extension(actor, extension_id, decision, note=""):
    extension = ExtensionRequest.objects.select_for_update(of=("self",)).select_related("visit", "visit__visitor").filter(
        pk=extension_id).first()
    if extension is None:
        raise NotFound("Extension request not found.")
    visit = VisitRequest.objects.select_for_update(of=("self",)).get(pk=extension.visit_id)
    if not admin_covers(actor, zones=visit_zone_set(visit)):
        raise NotAuthorized("Only an authorised Admin can decide extensions beyond the maximum (VMS-BR-194).")
    if extension.status != ExtensionStatus.PENDING:
        raise Conflict("This extension request is already decided.", code="not_pending")
    extension.decided_by, extension.decided_at, extension.decision_note = actor, now(), note
    if decision == "APPROVE":
        visit_pass = _extendable(visit)
        _apply_extension(visit, visit_pass, extension.requested_valid_until)
        workflow.apply(visit, "EXTENSION_APPROVED", actor=actor, actor_role=VmsRole.ADMIN,
                       note="Validity extended to {}".format(extension.requested_valid_until))
        extension.status = ExtensionStatus.APPROVED
        notify_visitor(visit.visitor, NotificationEvent.VISIT_EXTENDED, "Visit extension approved",
                       "Visit {} now ends at {}.".format(visit.reference,
                                                        extension.requested_valid_until.strftime("%d %b %H:%M")),
                       visit=visit)
    elif decision == "REJECT":
        extension.status = ExtensionStatus.REJECTED
    else:
        raise ValidationFailed("decision must be APPROVE or REJECT.", details={"decision": [decision]})
    extension.save()
    audit.record(actor, VmsRole.ADMIN, "EXTENSION_" + decision, extension, visitor=visit.visitor, message=note)
    if extension.requested_by and extension.requested_by != actor:
        notify_user(extension.requested_by, NotificationEvent.VISIT_EXTENDED,
                    "Extension {}".format(extension.status.lower()),
                    "Extension for {} was {}.".format(visit.reference, extension.status.lower()), visit=visit,
                    email=False)
    return extension


# --------------------------------------------------------------------------
# VMS-UC-037 Expire Pending Visit Request (VMS-BR-062/200)
# --------------------------------------------------------------------------

def expire_visit(visit, current=None):
    current = current or now()
    if visit.status != VisitStatus.PENDING_HOST_APPROVAL:
        return False  # UC-037 exception flow: already decided, no expiry applied
    workflow.apply(visit, "EXPIRE", actor_role=VmsRole.SYSTEM, note="Approval timeout elapsed")
    audit.record(None, VmsRole.SYSTEM, "VISIT_EXPIRED", visit, visitor=visit.visitor,
                 metadata={"deadline": visit.approval_deadline})
    notify_visitor(visit.visitor, NotificationEvent.REQUEST_EXPIRED, "Visit request expired",
                   "Your visit request {} expired because the host did not respond in time.".format(visit.reference),
                   visit=visit)  # AFR-201
    if visit.registered_by:
        notify_user(visit.registered_by, NotificationEvent.REQUEST_EXPIRED, "Walk-in request expired",
                    "{} ({}) expired without a host decision.".format(visit.visitor.full_name, visit.reference),
                    visit=visit, email=False)
    return True


def expire_pending_requests(current=None):
    current = current or now()
    count = 0
    due = VisitRequest.objects.filter(status=VisitStatus.PENDING_HOST_APPROVAL, approval_deadline__lte=current)
    for pk in due.values_list("pk", flat=True):
        with transaction.atomic():
            visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor").get(pk=pk)
            if visit.approval_deadline and visit.approval_deadline <= current and expire_visit(visit, current):
                count += 1
    return count


# --------------------------------------------------------------------------
# VMS-UC-040 Send Pending Approval Reminder (ISS-VMS-018: configured instants)
# --------------------------------------------------------------------------

def send_pending_reminders(current=None):
    current = current or now()
    sent = 0
    pending = VisitRequest.objects.filter(status=VisitStatus.PENDING_HOST_APPROVAL, approval_deadline__gt=current)
    for pk in pending.values_list("pk", flat=True):
        with transaction.atomic():
            visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").get(pk=pk)
            if visit.status != VisitStatus.PENDING_HOST_APPROVAL:
                continue  # suppressed: no longer pending
            snapshot = visit.policy_snapshot
            offsets = snapshot.get("reminder_offsets_minutes") or []
            window_start = visit.approval_deadline - minutes(snapshot["approval_timeout_minutes"])
            done = set(visit.reminders_sent or [])
            due = [o for o in offsets if o not in done and window_start + minutes(o) <= current]
            if not due:
                continue
            remaining = visit.approval_deadline - current
            notify_user(visit.host.user, NotificationEvent.APPROVAL_REMINDER, "Reminder: visit request pending",
                        "{} ({}) is still awaiting your decision; it expires in {} minutes.".format(
                            visit.visitor.full_name, visit.reference, int(remaining.total_seconds() // 60)),
                        visit=visit)
            visit.reminders_sent = sorted(done | set(due))
            visit.save(update_fields=["reminders_sent", "updated_at"])
            sent += 1
    return sent


# --------------------------------------------------------------------------
# VMS-UC-038 Automatically Check Out Visit (VMS-BR-101/105)
# --------------------------------------------------------------------------

def auto_check_out(current=None):
    from .gate import complete_visit
    current = current or now()
    count = 0
    due = VisitRequest.objects.filter(status__in=VisitStatus.ON_CAMPUS, visit_pass__valid_until__lte=current)
    for pk in due.values_list("pk", flat=True):
        with transaction.atomic():
            visit = VisitRequest.objects.select_for_update(of=("self",)).select_related("visitor", "host__user").get(pk=pk)
            visit_pass = getattr(visit, "visit_pass", None)
            if visit.status not in VisitStatus.ON_CAMPUS or visit.check_out_at or visit_pass is None:
                continue  # never a second checkout
            if visit_pass.valid_until > current:
                continue
            complete_visit(visit, LogMethod.AUTO, actor_role=VmsRole.SYSTEM, at=visit_pass.valid_until)
            count += 1
    return count


def run_scheduled_tasks(current=None):
    """Entry point for cron / Celery beat (``manage.py vms_run_scheduled_tasks``)."""
    from .gate import reconcile_offline_events
    current = current or now()
    return {
        "expired": expire_pending_requests(current),
        "reminders": send_pending_reminders(current),
        "auto_checked_out": auto_check_out(current),
        "offline_reconciled": len(reconcile_offline_events()),
    }
