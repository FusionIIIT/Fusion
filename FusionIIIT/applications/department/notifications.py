from notifications.signals import notify


def department_notif(sender, recipient, type):
    url = 'dep:dep'
    module = 'department'
    sender = sender
    recipient = recipient
    verb = type
    flag = "announcement"

    notify.send(sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                flag=flag)
