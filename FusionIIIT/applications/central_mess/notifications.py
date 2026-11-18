from notifications.signals import notify


def central_mess_notif(sender, recipient, type, message=None, role=None):
    url = 'mess:mess'
    module = 'Central Mess'
    sender = sender
    recipient = recipient
    verb = ''

    if type == 'feedback_submitted':
        verb = 'Your feedback has been successfully submitted.'
    elif type == 'menu_change_accepted':
        verb = 'Menu request has been approved'
    elif type == 'leave_request':
        verb = message
    elif type == 'vacation_request':
        verb = 'Your vacation request has been' + message
    elif type == 'meeting_invitation':
        verb = message
    elif type == 'special_request':
        verb = "Your special food request has been " + message
    elif type == 'added_committee':
        verb = "You have been added to the mess committee. "

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb, role=role)
