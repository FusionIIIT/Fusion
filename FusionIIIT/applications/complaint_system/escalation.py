import logging

from django.db import transaction
from django.utils import timezone

from notification.views import complaint_system_notif

from applications.complaint_system.models import ComplaintEvent, ComplaintStatus, Supervisor


logger = logging.getLogger(__name__)

AUTO_ESCALATION_NOTE = 'Automatically escalated after SLA breach'


def _get_supervisor_recipients(complaint):
    recipients = []
    seen_ids = set()

    for supervisor in Supervisor.objects.select_related('sup_id', 'sup_id__user').filter(type=complaint.complaint_type):
        recipient = getattr(supervisor.sup_id, 'user', None)
        if recipient is None or recipient.id in seen_ids:
            continue
        seen_ids.add(recipient.id)
        recipients.append(recipient)

    return recipients


def notify_supervisors_about_escalation(complaint, reason, actor=None, automatic=False):
    sender = getattr(actor, 'user', None) or getattr(getattr(complaint, 'complainer', None), 'user', None)
    recipients = _get_supervisor_recipients(complaint)

    if not recipients:
        logger.warning(
            'No supervisors found for complaint escalation',
            extra={'complaint_id': complaint.id, 'complaint_type': complaint.complaint_type},
        )
        return 0

    message_prefix = 'Automatically escalated' if automatic else 'Escalated'
    message = f'{message_prefix} complaint {complaint.complaint_ref or complaint.id}: {reason}'

    for recipient in recipients:
        complaint_system_notif(
            sender,
            recipient,
            'complaint_escalation',
            complaint.id,
            0,
            message,
        )

    complainer_user = getattr(getattr(complaint, 'complainer', None), 'user', None)
    if complainer_user is not None:
        complaint_system_notif(
            sender,
            complainer_user,
            'complaint_escalation',
            complaint.id,
            1,
            message,
        )

    assigned = getattr(complaint, 'assigned_to', None)
    assigned_caretaker_user = None
    if assigned is not None and assigned.secincharge_id is not None and assigned.secincharge_id.staff_id is not None:
        assigned_caretaker_user = getattr(assigned.secincharge_id.staff_id, 'user', None)

    if assigned_caretaker_user is not None and assigned_caretaker_user.id != getattr(complainer_user, 'id', None):
        complaint_system_notif(
            sender,
            assigned_caretaker_user,
            'complaint_escalation',
            complaint.id,
            0,
            message,
        )

    return len(recipients)


@transaction.atomic
def escalate_complaint_record(complaint, reason, actor=None, automatic=False):
    escalation_reason = str(reason or '').strip()
    if not escalation_reason:
        raise ValueError('escalation_reason is required')

    if complaint.status == ComplaintStatus.ESCALATED:
        raise ValueError('Complaint is already escalated')

    before_status = complaint.status
    complaint.is_escalated = 1
    complaint.escalation_reason = escalation_reason
    complaint.escalated_date = timezone.now()
    complaint.status = ComplaintStatus.ESCALATED
    complaint.save(
        update_fields=['is_escalated', 'escalation_reason', 'escalated_date', 'status', 'updated_at'],
    )

    ComplaintEvent.objects.create(
        complaint=complaint,
        actor=actor,
        action='auto_escalated' if automatic else 'escalated',
        from_status=before_status,
        to_status=ComplaintStatus.ESCALATED,
        note=escalation_reason,
        metadata={
            'source': 'automatic' if automatic else 'manual',
        },
    )

    transaction.on_commit(
        lambda: notify_supervisors_about_escalation(
            complaint,
            escalation_reason,
            actor=actor,
            automatic=automatic,
        )
    )

    return complaint
