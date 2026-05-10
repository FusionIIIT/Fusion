from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from applications.audit_account.models import (
    ActionDecision,
    ActionLog,
    AuditObservation,
    Request,
    RequestStatus,
    TARequestStatus,
    TravelAllowance,
    WorkflowType,
)
from django.contrib.auth.models import User
from notification.views import audit_account_notif


REQUEST_ESCALATION_HOURS = int(getattr(settings, "AUDIT_ACCOUNT_REQUEST_ESCALATION_HOURS", 24))
TA_ESCALATION_HOURS = int(getattr(settings, "AUDIT_ACCOUNT_TA_ESCALATION_HOURS", 24))


def _next_role(role):
    if role == "hod":
        return "dean"
    if role == "dean":
        return "director"
    return "director"


def _notify_role(role, sender, message):
    if not role:
        return
    for user in User.objects.filter(current_designation__designation__name=role).distinct():
        audit_account_notif(sender, user, "request_escalated", message)


@shared_task
def run_audit_account_escalations():
    now = timezone.now()
    request_cutoff = now - timedelta(hours=REQUEST_ESCALATION_HOURS)
    ta_cutoff = now - timedelta(hours=TA_ESCALATION_HOURS)

    for req in Request.objects.filter(
        status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED],
        assigned_at__lte=request_cutoff,
    ).exclude(current_approver_role=""):
        next_role = _next_role(req.current_approver_role)
        req.status = RequestStatus.ESCALATED
        req.current_approver_role = next_role
        req.escalated_at = now
        req.assigned_at = now
        req.anomaly_reason = "Approval timed out and was auto-escalated."
        req.save(update_fields=["status", "current_approver_role", "escalated_at", "assigned_at", "anomaly_reason", "updated_at"])
        AuditObservation.objects.create(
            target_workflow=WorkflowType.EXPENSE,
            request=req,
            title="Approval timeout escalation",
            details=req.anomaly_reason,
        )
        ActionLog.objects.create(
            workflow=WorkflowType.EXPENSE,
            decision=ActionDecision.ESCALATED,
            from_status=RequestStatus.FINANCE_VALIDATED,
            to_status=req.status,
            remarks=req.anomaly_reason,
            request=req,
        )
        _notify_role(next_role, req.created_by_user, f"Request #{req.id} was auto-escalated to {next_role.upper()}.")

    for ta in TravelAllowance.objects.filter(status=TARequestStatus.SUBMITTED, assigned_at__lte=ta_cutoff):
        ta.escalated_at = now
        ta.assigned_at = now
        ta.save(update_fields=["escalated_at", "assigned_at", "updated_at"])
        AuditObservation.objects.create(
            target_workflow=WorkflowType.TA,
            travel_allowance=ta,
            title="TA verification timeout",
            details="TA verification is overdue.",
        )
        ActionLog.objects.create(
            workflow=WorkflowType.TA,
            decision=ActionDecision.ESCALATED,
            from_status=TARequestStatus.SUBMITTED,
            to_status=TARequestStatus.SUBMITTED,
            remarks="TA verification is overdue.",
            travel_allowance=ta,
        )

    for ta in TravelAllowance.objects.filter(
        status=TARequestStatus.VERIFIED,
        high_value=True,
        assigned_at__lte=ta_cutoff,
    ).exclude(current_approver_role=""):
        next_role = _next_role(ta.current_approver_role)
        ta.current_approver_role = next_role
        ta.escalated_at = now
        ta.assigned_at = now
        ta.save(update_fields=["current_approver_role", "escalated_at", "assigned_at", "updated_at"])
        AuditObservation.objects.create(
            target_workflow=WorkflowType.TA,
            travel_allowance=ta,
            title="TA approval timeout escalation",
            details="High-value TA approval timed out and was auto-escalated.",
        )
        ActionLog.objects.create(
            workflow=WorkflowType.TA,
            decision=ActionDecision.ESCALATED,
            from_status=TARequestStatus.VERIFIED,
            to_status=TARequestStatus.VERIFIED,
            remarks="High-value TA approval timed out and was auto-escalated.",
            travel_allowance=ta,
        )
        _notify_role(next_role, ta.employee, f"High-value TA #{ta.id} was auto-escalated to {next_role.upper()}.")
