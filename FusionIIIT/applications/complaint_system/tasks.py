import logging

from celery import shared_task
from django.utils import timezone

from applications.complaint_system.escalation import AUTO_ESCALATION_NOTE, escalate_complaint_record
from applications.complaint_system.models import ComplaintStatus, StudentComplain


logger = logging.getLogger(__name__)


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