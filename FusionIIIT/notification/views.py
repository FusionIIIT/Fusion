from django.shortcuts import render
from notifications.signals import notify

# Create your views here.

def leave_module_notif(sender, recipient, type, date=None):
    url = 'leave:leave'
    module = 'Leave Module'
    sender=sender
    recipient=recipient
    verb=''
    if type=='leave_applied':
        verb="Your leave has been successfully submitted."
    elif type=='request_accepted':
        verb = "Your responsibility has been accepted "
    elif type=='request_declined':
        verb = "Your responsibility has been declined "
    elif type=='leave_accepted':
        verb = "You leave request has been accepted "
    elif type == 'leave_forwarded':
        verb = "You leave request has been forwarded "
    elif type=='leave_rejected':
        verb = "You leave request has been rejected "
    elif type=='offline_leave':
        verb = "Your offline leave has been updated "
    elif type=='replacement_request':
        verb = "You have a replacement request "
    elif type=='replacement_cancel':
        verb = "Your replacement has been cancelled for "+date

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def placement_cell_notif(sender, recipient, type):
    url = ''
    module = 'Placement Cell'
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def academics_module_notif(sender, recipient, type):
    url=''
    module="Academic's Module"
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def central_mess_notif(sender, recipient, type):
    url='mess:mess'
    module='Central Mess'
    sender = sender
    recipient = recipient
    verb = ''
    if type=='feedback_submitted':
        verb='Your feedback has been successfully submitted.'
    elif type=='menu_change_accepted':
        verb='Menu request has been approved'

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def visitors_hostel_notif(sender, recipient, type):
    url=''
    module="Visitor's Hostel"
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def healthcare_center_notif(sender, recipient, type):
    url=''
    module='Healthcare Center'
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def file_tracking_notif(sender, recipient, type):
    url=''
    module='File Tracking'
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def scholarship_portal_notif(sender, recipient, type):
    url='spacs:convener_view'
    module='Scholarship Portal'
    sender = sender
    recipient = recipient
    verb = ''

    if type.startswith('award'):
        s = type.split('-')
        verb = "Invitation to apply for " + s[1]
    elif type == 'Accept_mcm':
        verb = "Your Mcm form has been accepted "
    elif type == 'Reject_mcm':
        verb = "Your Mcm form has been rejected as you have not fulfiled the required criteria "
    elif type == 'Accept_gold':
        verb = "Your Covocation form for Director Gold Medal has been accepted "
    elif type == 'Reject_gold':
        verb = "Your Covocation form for Director Gold Medal has been rejected "
    elif type == 'Accept_silver':
        verb = "Your Covocation form for Director Silver Medal has been accepted "
    elif type == 'Reject_silver':
        verb = "Your Covocation form for Director Silver Medal has been rejected "
    elif type == 'Accept_dm':
        verb = "Your Covocation form for D&M Proficiency Gold Medal has been accepted "
    elif type == 'Reject_silver':
        verb = "Your Covocation form for D&M Proficiency Gold Medal has been rejected "

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def complaint_system_notif(sender, recipient, type):
    url='complaint:complaint'
    module='Complaint System'
    sender = sender
    recipient = recipient
    verb = ''
    if type=='lodge_comp_alert':
        verb="You have a new complaint "
    elif type=='assign_worker_alert':
        verb="Your worker has been a worker "
    elif type=='comp_redirect_alert':
        verb="Your complaint has been redirected to another caretaker "
    elif type=='comp_resolved_alert':
        verb="Your complaint has been resolved "
    elif type=='reassign_worker_alert':
        verb="Your complaint has been reassined a worker "

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)
