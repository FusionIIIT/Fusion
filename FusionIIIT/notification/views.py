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
    elif type=='leave_request':
        verb = "You have a leave request from "
    elif type=='leave_withdrawn':
        verb = "The leave has been withdrawn for " + date
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
    verb = type

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def office_module_notif(sender, recipient):
    url='office:officeOfRegistrar'
    module="Academic's Module"
    sender = sender
    recipient = recipient
    verb = "New file received"

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def central_mess_notif(sender, recipient, type, message=None):
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
    elif type =='special_request':
        verb = "Your special food request has been " + message
    elif type == 'added_committee':
        verb = "You have been added to the mess committee. "

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def visitors_hostel_notif(sender, recipient, type):
    url='visitorhostel:visitorhostel'
    module="Visitor's Hostel"
    sender = sender
    recipient = recipient
    verb = ''
    if type =='booking_confirmation':
        verb='Your booking has been confirmed '
    elif type =='booking_cancellation_request_accepted':
        verb='Your Booking Cancellation Request has been accepted '
    elif type =='booking_request':
        verb='New Booking Request '
    elif type =='cancellation_request_placed':
        verb='New Booking Cancellation Request '
    elif type =='booking_forwarded':
        verb='New Forwarded Booking Request '
    elif type =='booking_rejected':
        verb='Your Booking Request has been rejected '

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def healthcare_center_notif(sender, recipient, type):
    url='healthcenter:healthcenter'
    module='Healthcare Center'
    sender = sender
    recipient = recipient
    verb = ''
    if type == 'appoint':
        verb = "Your Appointment has been booked"
    if type == 'amb_request':
        verb = "Your Ambulance request has been placed"
    if type == 'Presc':
        verb = "You have been prescribed some medicine"
    if type == 'appoint_req':
        verb = "You have a new appointment request"
    if type == 'amb_req':
        verb = "You have a new ambulance request"



    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def file_tracking_notif(sender, recipient, type):
    url=''
    module='File Tracking'
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def scholarship_portal_notif(sender, recipient, type):
    url='spacs:spacs'
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
    url=''
    module='Complaint System'
    sender = sender
    recipient = recipient
    verb = ''

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def office_dean_PnD_notif(sender, recipient, type):
    url = 'office:officeOfDeanPnD'
    module = 'Office of Dean PnD Module'
    sender=sender
    recipient=recipient
    verb=''
    if type=='requisition_filed':
        verb = "Your requisition has been successfully submitted."
    elif type=='request_accepted':
        verb = "Your requisition has been accepted."
    elif type=='request_rejected':
        verb = "Your requisition has been rejected."
    elif type=='assignment_created':
        verb = "Assignment has been created."
    elif type=='assignment_received':
        verb = "You have received an assignment."
    elif type=='assignment_reverted':
        verb = "Assignment has been reverted."
    elif type=='assignment_approved':
        verb = "Assignment has been approved."
    elif type=='assignment_rejected':
        verb = "Assignment has been rejected."
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)
    
def office_module_DeanS_notif(sender, recipient, type):
    url='office:officeOfDeanStudents'
    module='Office Module'
    sender = sender
    recipient = recipient
    verb = ""

    if type == 'hostel_alloted':
        verb = "Hostel has been alloted successfully."
    elif type == 'insufficient_funds':
        verb = "Insufficient Funds! Please contact Junior Superintendent to allot funds."
    elif type == 'MOM_submitted':
        verb = "MOM of the meeting has been submitted successfully."
    elif type == 'budget_approved':
        verb = "Budget has been approved by Dean Students."
    elif type == 'budget_rejected':
        verb = "Budget has been rejected by Dean Students."
    elif type == 'club_approved':
        verb = "New Club has been approved by Dean Students."
    elif type == 'club_rejected':
        verb = "New Club has been rejected by Dean Students."
    elif type == 'meeting_booked':
        verb = "Meeting has been booked and members has been notified"
    elif type == 'session_approved':
        verb = "Club session has been approved"
    elif type == 'session_rejected':
        verb = "Club session has been rejected."
    elif type == 'budget_alloted':
        verb = "Budget has been alloted by Junior Superintendent"

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)
