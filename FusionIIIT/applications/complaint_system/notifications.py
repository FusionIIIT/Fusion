from notifications.signals import notify


def complaint_system_notif(sender, recipient, type, complaint_id, student, message, role=None):
    if (student == 0):
        url = ('complaint:detail')
    else:
        url = ('complaint:detail2')
    module = 'Complaint System'
    sender = sender
    recipient = recipient
    verb = message
    description = complaint_id

    notify.send(sender=sender, recipient=recipient, url=url,
                module=module, verb=verb, description=description, role=role)
