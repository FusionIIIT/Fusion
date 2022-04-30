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
    url = 'placement:placement'
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
    url='office_module:officeOfRegistrar'
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


def file_tracking_notif(sender, recipient,title):
    url='filetracking:inward'
    module='File Tracking'
    sender = sender
    recipient = recipient
    verb = title

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)

def scholarship_portal_notif(sender, recipient, type):
    url='spacs:spacs'
    module='Scholarship Portal'
    sender = sender
    recipient = recipient
    verb = ''

    if type.startswith('award'):
        s = type.split('_')
        verb = "Invitation to apply for " + s[1]
    elif type == 'Accept_MCM':
        verb = "Your Mcm form has been accepted "
    elif type == 'Reject_MCM':
        verb = "Your Mcm form has been rejected as you have not fulfilled the required criteria "
    elif type == 'Accept_Gold':
        verb = "Your Convocation form for Director's Gold Medal has been accepted "
    elif type == 'Reject_Gold':
        verb = "Your Convocation form for Director's Gold Medal has been rejected "
    elif type == 'Accept_Silver':
        verb = "Your Convocation form for Director's Silver Medal has been accepted "
    elif type == 'Reject_Silver':
        verb = "Your Convocation form for Director's Silver Medal has been rejected "
    elif type == 'Accept_DM':
        verb = "Your Convocation form for D&M Proficiency Gold Medal has been accepted "
    elif type == 'Reject_Silver':
        verb = "Your Convocation form for D&M Proficiency Gold Medal has been rejected "
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)




def complaint_system_notif(sender, recipient, type, complaint_id,student,message):
    if(student==0):
        url = ('complaint:detail')
    else:
        url=('complaint:detail2')
    module='Complaint System'
    sender = sender
    recipient = recipient
    verb = message
    description = complaint_id

    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb,description=description)

def office_dean_PnD_notif(sender, recipient, type):
    url = 'office_module:officeOfDeanPnD'
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
    url='office_module:officeOfDeanStudents'
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


def gymkhana_voting(sender, recipient, type, title, desc):
    url = 'gymkhana:gymkhana'
    module = 'Gymkhana Module'
    sender = sender
    recipient = recipient
    title = title
    desc = desc
    verb = ""

    if type == 'voting_open':
        verb = "Voting is open for {}".format(title)

    notify.send(sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                description=desc
                )


def gymkhana_session(sender, recipient, type, club, desc, venue):
    url = 'gymkhana:gymkhana'
    module = 'Gymkhana Module'
    sender = sender
    recipient = recipient
    desc = desc
    verb = ""

    if type == 'new_session':
        verb = "A session by {} Club will be organised in {}".format(club, venue)

    notify.send(sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                description=desc
                )


def gymkhana_event(sender, recipient, type, club, event_name, desc, venue):
    url = 'gymkhana:gymkhana'
    module = 'Gymkhana Module'
    sender = sender
    recipient = recipient
    desc = desc
    verb = ""

    if type == 'new_event':
        verb = "{} event by {} Club will be organised in {}".format(event_name, club, venue)

    notify.send(sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                description=desc
                )

def AssistantshipClaim_notify(sender,recipient,month,year):
    
    message="Your Assistantshipclaim of {} month year {} is approved ".format(month,year)
    url = 'academic-procedures:academic_procedures'
    module = 'Assistantship Request'
    notify.send(sender=sender,recipient= recipient, url=url, module=module, verb=message)



def AssistantshipClaim_faculty_notify(sender,recipient):
    
    message=" Assistantshipclaim is requested "
    url = 'academic-procedures:academic_procedures'
    module = 'Assistantship Request'
    notify.send(sender=sender,recipient= recipient, url=url, module=module, verb=message)


def AssistantshipClaim_acad_notify(sender,recipient):
    message = "AssistantshipClaim is requested " 
    url = 'academic-procedures:academic_procedures'
    module = 'Assistantship Request'
    notify.send(sender=sender,recipient= recipient, url=url, module=module, verb=message)


def AssistantshipClaim_account_notify(sender,stu, recipient):
    message = "Assistantship claim of{} is forwaded ".format(stu)
    url = 'academic-procedures:academic_procedures'
    module = 'Assistantship Request'
    notify.send(sender=sender,recipient= recipient, url=url, module=module, verb=message)

def department_notif(sender, recipient, type):
    url='dep:dep'
    module='department'
    sender = sender
    recipient = recipient
    verb = type
    flag = "department"

    notify.send(sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                flag=flag)




def office_module_DeanRSPC_notif(sender, recipient, type):
    url='office:officeOfDeanRSPC'
    module='Office Module'
    sender = sender
    recipient = recipient
    verb = ""

    if type == 'Approve':
        verb = "Your Project request has been accepted"
    elif type == 'Disapprove':
        verb = "Your project request got rejected ."
    elif type == 'Pending':
        verb = "Kindly wait for the response"


    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)


def research_procedures_notif(sender,recipient,type):
    url = 'research_procedures:patent_registration'
    module = 'Research Procedures'
    sender = sender
    recipient = recipient
    verb = ""

    if type == "Approved":
        verb = "Your Patent has been Approved"
    elif type == "Disapproved":
        verb = "Your Patent has been Rejected"
    elif type == "Pending":
        verb = "Your Patent has been Pending, wait for the response"
    elif type == "submitted":
        verb = "Your Patent has been Submitted, wait for the response"
    elif type == "created":
        verb = "A new Patent has been Created"

    notify.send(sender=sender,recipient=recipient,url=url,module=module,verb=verb)