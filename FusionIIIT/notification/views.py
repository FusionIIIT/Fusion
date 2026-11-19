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


    
# Pages of the Programme and Curriculum module in the React app; the dashboard
# opens a notification's url as an app path.
PC_INWARD_FILES = '/programme_curriculum/faculty_inward_files'
PC_COURSE_PROPOSALS = '/programme_curriculum/faculty_view_course_proposal'


def prog_and_curr_notif(sender, recipient, title, url=PC_INWARD_FILES, role=None):
    """role: the recipient's designation the notification is for; the
    dashboard switches to it before opening url."""
    module = 'Programme and Curriculum'
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=title, role=role)

