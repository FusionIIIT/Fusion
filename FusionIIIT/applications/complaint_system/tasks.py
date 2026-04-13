import logging
from math import ceil

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from applications.complaint_system.escalation import AUTO_ESCALATION_NOTE, escalate_complaint_record
from applications.complaint_system.models import ComplaintEvent, ComplaintStatus, StudentComplain
from applications.complaint_system.notifications import notify_sla_deadline_reminder


logger = logging.getLogger(__name__)

SLA_REMINDER_WINDOW_HOURS = 4


@shared_task
def send_sla_deadline_reminders():
    now = timezone.now()
    reminder_deadline = now + timedelta(hours=SLA_REMINDER_WINDOW_HOURS)

    candidate_complaints = StudentComplain.objects.select_related(
        'complainer',
        'complainer__user',
        'assigned_to',
        'assigned_to__secincharge_id',
        'assigned_to__secincharge_id__staff_id',
        'assigned_to__secincharge_id__staff_id__user',
    ).filter(
        sla_deadline__isnull=False,
        sla_deadline__gt=now,
        sla_deadline__lte=reminder_deadline,
        is_escalated=0,
        status__in=(
            ComplaintStatus.PENDING,
            ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.REOPENED,
        ),
    )

    reminded_ids = []
    for complaint in candidate_complaints:
        sla_deadline_key = complaint.sla_deadline.isoformat()
        already_reminded = ComplaintEvent.objects.filter(
            complaint=complaint,
            action='sla_reminder_sent',
            metadata__sla_deadline=sla_deadline_key,
        ).exists()

        if already_reminded:
            continue

        hours_remaining = max(
            1,
            int(ceil((complaint.sla_deadline - now).total_seconds() / 3600)),
        )

        notify_sla_deadline_reminder(complaint, hours_remaining)
        ComplaintEvent.objects.create(
            complaint=complaint,
            actor=None,
            action='sla_reminder_sent',
            from_status=complaint.status,
            to_status=complaint.status,
            note='SLA deadline reminder sent',
            metadata={
                'sla_deadline': sla_deadline_key,
                'hours_remaining': hours_remaining,
                'source': 'automatic',
            },
        )
        reminded_ids.append(complaint.id)

    return {
        'reminder_count': len(reminded_ids),
        'reminder_ids': reminded_ids,
    }


@shared_task
def escalate_overdue_complaints():
    now = timezone.now()
    overdue_complaints = StudentComplain.objects.select_related('complainer', 'complainer__user').filter(
        sla_deadline__lt=now,
        is_escalated=0,
        status__in=(
            ComplaintStatus.PENDING,
            ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.REOPENED,
        ),
    )

    escalated_ids = []
    for complaint in overdue_complaints:
        try:
            escalate_complaint_record(
                complaint,
                AUTO_ESCALATION_NOTE,
                actor=None,
                automatic=True,
            )
            escalated_ids.append(complaint.id)
        except ValueError as exc:
            logger.info(
                'Skipping automatic complaint escalation',
                extra={'complaint_id': complaint.id, 'reason': str(exc)},
            )

    return {
        'escalated_count': len(escalated_ids),
        'escalated_ids': escalated_ids,
    }