from django.shortcuts import render
from requests import Response
from notifications.signals import notify
# Create your views here.


def academics_module_notif(sender, recipient, type):
    url = ''
    module = "Academic's Module"
    sender = sender
    recipient = recipient
    verb = type

    notify.send(sender=sender, recipient=recipient,
                url=url, module=module, verb=verb)


    
def prog_and_curr_notif(sender, recipient,title):
    url='programme_curriculum:inward_files'
    module='Programme and Curriculum'
    sender = sender
    recipient = recipient
    verb = title
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

