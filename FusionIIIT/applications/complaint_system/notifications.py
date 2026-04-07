from notification.views import complaint_system_notif

from applications.complaint_system.models import ComplaintStatus, Supervisor


STATUS_LABELS = {
    ComplaintStatus.PENDING: 'Pending',
    ComplaintStatus.IN_PROGRESS: 'In Progress',
    ComplaintStatus.RESOLVED: 'Resolved',
    ComplaintStatus.CLOSED: 'Closed',
    ComplaintStatus.ESCALATED: 'Escalated',
    ComplaintStatus.REOPENED: 'Reopened',
}


def _notify(sender_user, recipient_user, complaint, message, student_view=True):
    if recipient_user is None:
        return

    complaint_system_notif(
        sender_user,
        recipient_user,
        'complaint_update',
        complaint.id,
        1 if student_view else 0,
        message,
    )


def _assigned_caretaker_user(complaint):
    worker = complaint.assigned_to
    if worker is None or worker.secincharge_id is None or worker.secincharge_id.staff_id is None:
        return None
    return getattr(worker.secincharge_id.staff_id, 'user', None)


def _supervisor_users(complaint):
    recipients = []
    seen = set()
    queryset = Supervisor.objects.select_related('sup_id', 'sup_id__user').filter(type=complaint.complaint_type)
    for supervisor in queryset:
        user = getattr(supervisor.sup_id, 'user', None)
        if user is None or user.id in seen:
            continue
        recipients.append(user)
        seen.add(user.id)
    return recipients


def notify_complaint_created(complaint, actor=None):
    sender_user = getattr(actor, 'user', None) or getattr(complaint.complainer, 'user', None)
    complainer_user = getattr(complaint.complainer, 'user', None)
    caretaker_user = _assigned_caretaker_user(complaint)

    _notify(
        sender_user,
        complainer_user,
        complaint,
        f'Complaint {complaint.complaint_ref or complaint.id} created successfully. Current status: Pending.',
        student_view=True,
    )

    if caretaker_user:
        _notify(
            sender_user,
            caretaker_user,
            complaint,
            f'New complaint assigned: {complaint.complaint_ref or complaint.id} ({complaint.complaint_type} at {complaint.location}).',
            student_view=False,
        )


def notify_status_change(complaint, from_status, to_status, actor=None, remarks=''):
    sender_user = getattr(actor, 'user', None) or getattr(complaint.complainer, 'user', None)
    complainer_user = getattr(complaint.complainer, 'user', None)
    caretaker_user = _assigned_caretaker_user(complaint)

    from_label = STATUS_LABELS.get(from_status, str(from_status))
    to_label = STATUS_LABELS.get(to_status, str(to_status))
    suffix = f' Note: {remarks}' if str(remarks or '').strip() else ''
    message = f'Complaint {complaint.complaint_ref or complaint.id} moved from {from_label} to {to_label}.{suffix}'

    _notify(sender_user, complainer_user, complaint, message, student_view=True)
    if caretaker_user and caretaker_user.id != getattr(complainer_user, 'id', None):
        _notify(sender_user, caretaker_user, complaint, message, student_view=False)


def notify_reopen_requested(complaint, actor=None, reason=''):
    sender_user = getattr(actor, 'user', None) or getattr(complaint.complainer, 'user', None)
    message = (
        f'Reopen requested for complaint {complaint.complaint_ref or complaint.id}. '
        f'Reason: {reason or "No reason provided."}'
    )

    for recipient in _supervisor_users(complaint):
        _notify(sender_user, recipient, complaint, message, student_view=False)


def notify_reopen_approved(complaint, actor=None, reason=''):
    sender_user = getattr(actor, 'user', None) or getattr(complaint.complainer, 'user', None)
    complainer_user = getattr(complaint.complainer, 'user', None)
    caretaker_user = _assigned_caretaker_user(complaint)
    message = (
        f'Complaint {complaint.complaint_ref or complaint.id} has been reopened. '
        f'Reason: {reason or "No reason provided."}'
    )

    _notify(sender_user, complainer_user, complaint, message, student_view=True)
    if caretaker_user:
        _notify(sender_user, caretaker_user, complaint, message, student_view=False)


def notify_verification_result(complaint, actor=None, decision='approve', notes=''):
    sender_user = getattr(actor, 'user', None) or getattr(complaint.complainer, 'user', None)
    complainer_user = getattr(complaint.complainer, 'user', None)
    caretaker_user = _assigned_caretaker_user(complaint)

    if decision == 'approve':
        message = (
            f'Complaint {complaint.complaint_ref or complaint.id} was verified and closed.'
            f'{" Note: " + notes if str(notes or "").strip() else ""}'
        )
    else:
        message = (
            f'Complaint {complaint.complaint_ref or complaint.id} verification was rejected and reopened.'
            f'{" Note: " + notes if str(notes or "").strip() else ""}'
        )

    _notify(sender_user, complainer_user, complaint, message, student_view=True)

    if caretaker_user and caretaker_user.id != getattr(complainer_user, 'id', None):
        _notify(sender_user, caretaker_user, complaint, message, student_view=False)

    for supervisor_user in _supervisor_users(complaint):
        if supervisor_user.id in {
            getattr(complainer_user, 'id', None),
            getattr(caretaker_user, 'id', None),
        }:
            continue
        _notify(sender_user, supervisor_user, complaint, message, student_view=False)
