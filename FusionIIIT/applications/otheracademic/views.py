
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect,render

from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.core import serializers
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif,file_tracking_notif
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import LeaveFormTable,BonafideFormTableUpdated,GraduateSeminarFormTable,AssistantshipClaimFormStatusUpd,LeavePG,NoDues
from django.shortcuts import render, get_object_or_404
from datetime import date
from applications.filetracking.models import *
from applications.filetracking.sdk.methods import *

from notification.views import otheracademic_notif



@login_required
def otheracademic(request):
    """
    

    Description:
        This function checks the user's programme (B.Tech, M.Tech, or PhD) to determine whether they are an undergraduate or postgraduate student. It then renders the corresponding academic page accordingly.
        - If the user is an undergraduate student (B.Tech), the function renders the UG_page.html template.
        - If the user is a postgraduate student (M.Tech or PhD), the function renders the PG_page.html template.
    """
    if request.user.extrainfo.user_type != "student":
        return render(request, "otheracademic/othersPage.html")
    else :
        user = get_object_or_404(User, username=request.user.username)
        if user.extrainfo.student.programme == "B.Tech":
            return render(request, "otheracademic/UG_page.html")
        elif user.extrainfo.student.programme == "M.Tech" or user.extrainfo.student.programme == "PhD":
            return render(request, "otheracademic/PG_page.html")
        else:
            return HttpResponse(request,"NOt Available For you")

@login_required
def leaveform(request):
    """
    View function for accessing the leave form page.

    """
    return render(request, 'otheracademic/leaveform.html')


@csrf_exempt  # Exempt CSRF verification for this view
@login_required
def leave_form_submit(request):
    """
    View function for submitting a leave form.

    Description:
        This function handles form submission for leave requests, processes the data, and saves it to the database.
        It also notifies the relevant authority about the new leave application.
    """
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        
        # Create a new LeaveFormTable instance and save it to the database
        leave = LeaveFormTable.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            leave_type=data.get('leave_type'),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            date_of_application=date.today(),
            approved=False,  # Initially not approved
            rejected=False,  # Initially not rejected
            hod=data.get('hod_credential')
        )
        
        leave_hod = User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation

    
        
        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='ug_leave'
        )
       
        message = "A new leave application"
        otheracademic_notif(request.user, leave_hod, 'ug_leave_hod', leave.id, 'student', message)
        if leave:
            messages.success(request, "You successfully submitted your form")
            
        return HttpResponseRedirect('/otheracademic/leaveform')


def leaveApproveForm(request):
    """
    View function for accessing the leave approval form.

    Description:
        This function retrieves leave requests for approval by the designated authority (e.g., HOD) and displays them in a list.
    """
    user=get_object_or_404(User,username=request.user.username)
    design=request.session['currentDesignationSelected']
    if 'HOD' in design :
        inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
        leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'ug_leave']
    
        form_data = LeaveFormTable.objects.filter(id__in=leave_ids)
        return render(request, 'otheracademic/leaveformreciever.html', {'form_data': form_data})
    else:
        return HttpResponse("Not available for you or You are not a HOD.")


def leaveStatus(request):
    """
    View function for accessing the leave status page for the student.

    Description:
        This function retrieves and displays the leave status of the currently logged-in student.
    """
    form_data = LeaveFormTable.objects.filter(roll_no=request.user.extrainfo)
    roll_no = request.user.username
    return render(request, 'otheracademic/leaveStatus.html', {'form_data': form_data, 'roll_no' : roll_no})


def leaveStatus_Dip(request):
    """
    View function for track the record of leave applied.

    
    """
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'ug_leave']

    form_data = LeaveFormTable.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveStatus_Dip.html', {'form_data': form_data})

@login_required
def approve_leave(request, leave_id):
    """
    View function for approving a leave request.

    Parameters:
        leave_id (int): The ID of the leave request to be approved.

    Description:
        This function approves the leave request with the specified ID and updates its status accordingly.
    """
    leave_entry = LeaveFormTable.objects.get(id=leave_id)
    leave_entry.approved = True
    leave_entry.save()
    messages.success(request, "Successfully Approved")
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'ug_leave_hod_approve', leave_entry.id, 'student', message)
    
    

    return redirect('/otheracademic/leaveApproveForm')


def reject_leave(request, leave_id):
    """
    View function for rejecting a leave request.

    Parameters:
        leave_id (int): The ID of the leave request to be rejected.

    Description:
        This function rejects the leave request with the specified ID and updates its status accordingly.
    """
    leave_entry = LeaveFormTable.objects.get(id=leave_id)
    leave_entry.rejected = True
    leave_entry.save()
    messages.success(request, "Successfully Rejected")
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'ug_leave_hod_approve', leave_entry.id, 'student', message)
    
    return redirect('/otheracademic/leaveApproveForm')





# PG/MTECh
@login_required
def leavePG(request):
    """
    View function for accessing the leave page for postgraduate students.

    Description:
        This function checks if the logged-in user is a postgraduate student (M.Tech or PhD). If so, it renders the leavePG.html template, allowing them to apply for leave. 
        If the user is not a postgraduate student, it returns an "NOT AVAILABLE" message.
    """
    user = get_object_or_404(User, username=request.user.username)
    if user.extrainfo.student.programme == "M.Tech" or "PhD":
        return render(request, 'otheracademic/leavePG.html')
    else:
        return HttpResponse("NOT AVAILABLE")


def leavePgSubmit(request):
    """
    View function for submitting a leave form by postgraduate students.

    Description:
        This function handles form submission for leave requests by postgraduate students.
        It processes the data, saves it to the database, notifies the TA supervisor about the new leave application,
        and redirects the user to the leave form page.

        -In this function  hod is charfield ,basically it ask the credential in charfied but by using user.get.object() it return the foreign key of hod and after that we can proceed furthur.
        this is used to  overcome the problem of database data
    """
    if request.method == 'POST':
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        ta = data.get('ta_supervisor')
        thesis = data.get('thesis_credential')
        
        leave = LeavePG.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            programme=request.user.extrainfo.student.programme,
            discipline=request.user.extrainfo.department,
            Semester=data.get('Semester'),
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            date_of_application=date.today(),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            leave_type=data.get('leave_type'),
            ta_supervisor=data.get('ta_supervisor'),
            mobile_no=data.get('mobile_no'),
            parent_mobile_no=data.get('parent_mobile_no'),
            alt_mobile_no=data.get('alt_mobile_no'),
            ta_approved=False,
            ta_rejected=False,
            thesis_approved=False,
            thesis_rejected=False,
            hod_approved=False,
            hod_rejected=False,
            hod=hodname,
            thesis_supervisor = thesis,
        )
    
        tasupervisor = User.objects.get(username=ta)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        
        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=tasupervisor,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='pg_leave'
        )
        
        message = "A new leave application"
        otheracademic_notif(request.user, tasupervisor,'pg_leave_ta', leave.id, 'student', message)
        if leave:
            messages.success(request, "You have successfully submitted your form")
            
        return HttpResponseRedirect('/otheracademic/leavePG')


def leaveApproveTA(request):
    """
    View function for accessing the leave approval page for TA supervisors.

    Description:
        This function retrieves leave requests for approval by the TA supervisor and displays them in a list.
    """
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'pg_leave']
    
    form_data = LeavePG.objects.filter(id__in=leave_ids)
    roll_no = request.user.username
    return render(request, 'otheracademic/leaveApproveTA.html', {'form_data': form_data,'roll_no' : roll_no})


def approve_leave_ta(request, leave_id):
    """
    View function for approving a leave request by TA supervisor.

    Description:
        This function approves the leave request with the specified ID by TA supervisor and updates its status accordingly and forwarded to hod.
    """
    leave_entry = get_object_or_404(LeavePG, id=leave_id)
    leave_entry.ta_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'pg_leave_ta_approve', leave_entry.id, 'student', message)

    
    
    receiver_value = User.objects.get(username=request.user.username)
    receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
    lis = list(receiver_value_designation)
    obj = lis[0].designation
    
        
    file_id_forward = create_file(
        uploader=request.user.username,
        uploader_designation=obj,
        receiver=leave_entry.thesis_supervisor,
        receiver_designation="student",
        src_module="otheracademic",
        src_object_id=leave_id,
        file_extra_JSON={"value": 2},
        attached_file=None,
        subject='pg_leave'
    )
   
    message = "A new leave application forwarded of PG student"
    thesis_user = User.objects.get(username=leave_entry.thesis_supervisor)
    otheracademic_notif(request.user, thesis_user, 'pg_leave_thesis', leave_id, 'student', message)
   

    return redirect('/otheracademic/leaveApproveTA')  # Redirect to appropriate page after approval


def reject_leave_ta(request, leave_id):
    """
    View function for rejecting a leave request by TA supervisor.

    Description:
        This function rejects the leave request with the specified ID by TA supervisor and updates its status accordingly.
    """
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.ta_rejected = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'pg_leave_ta_approve', leave_entry.id, 'student', message)
   

    return redirect('/otheracademic/leaveApproveTA')  # Redirect to appropriate page after rejection

def leaveApproveThesis(request):
    """
    View function for accessing the leave approval page for TA supervisors.

    Description:
        This function retrieves leave requests for approval by the TA supervisor and displays them in a list.
    """
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'pg_leave']
    
    form_data = LeavePG.objects.filter(id__in=leave_ids)
    roll_no = request.user.username
    return render(request, 'otheracademic/leaveApproveThesis.html', {'form_data': form_data, 'roll_no' : roll_no})


def approve_leave_thesis(request, leave_id):
    """
    View function for approving a leave request by TA supervisor.

    Description:
        This function approves the leave request with the specified ID by TA supervisor and updates its status accordingly and forwarded to hod.
    """
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.thesis_approved = True
    leave_entry.save()

    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'pg_leave_ta_approve', leave_entry.id, 'student', message)

    
    receiver_value = User.objects.get(username=request.user.username)
    receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
    lis = list(receiver_value_designation)
    obj = lis[0].designation
    leave_entry = get_object_or_404(LeavePG, id=leave_id)
        
    file_id_forward = create_file(
        uploader=request.user.username,
        uploader_designation=obj,
        receiver=leave_entry.hod,
        receiver_designation="student",
        src_module="otheracademic",
        src_object_id=leave_id,
        file_extra_JSON={"value": 2},
        attached_file=None,
        subject='pg_leave'
    )
    message = "A new leave application"
    hod_user = User.objects.get(username=leave_entry.hod)
    otheracademic_notif(request.user, hod_user, 'pg_leave_hod', leave_id, 'student', message)
   

    return redirect('/otheracademic/leaveApproveThesis')  # Redirect to appropriate page after approval


def reject_leave_thesis(request, leave_id):
    """
    View function for rejecting a leave request by TA supervisor.

    Description:
        This function rejects the leave request with the specified ID by TA supervisor and updates its status accordingly.
    """
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.thesis_rejected = True
    leave_entry.save()
   

    return redirect('/otheracademic/leaveApproveThesis')  # Redirect to appropriate page after rejection


def leaveApproveHOD(request):
    """
    View function for accessing the leave approval page for HOD.

    Description:
        This function retrieves leave requests for approval by the HOD and displays them in a list.
    """
    user=get_object_or_404(User,username=request.user.username)
    design=request.session['currentDesignationSelected']
    if 'HOD' in design :
        inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
        leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'pg_leave']
        form_data = LeavePG.objects.filter(id__in=leave_ids)
        roll_no = request.user.username
        return render(request, 'otheracademic/leaveApproveHOD.html', {'form_data': form_data, 'roll_no' : roll_no})
    else:
        return HttpResponse("Not Avaible For You...OR You are not the HOD")

def approve_leave_hod(request, leave_id):
    """
    View function for approving a leave request by HOD.

    Description:
        This function approves the leave request with the specified ID by HOD and updates its status accordingly.
    """
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.hod_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Leave Application Status approve/rejected'
    otheracademic_notif(request.user,leave_receive, 'pg_leave_ta_approve', leave_entry.id, 'student', message)

   
    return redirect('/otheracademic/leaveApproveHOD')  # Redirect to appropriate page after approval


def reject_leave_hod(request, leave_id):
    """
    View function for rejecting a leave request by HOD.

    Description:
        This function rejects the leave request with the specified ID by HOD and updates its status accordingly.
    """
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.hod_rejected = True
   
    leave_entry.save()
    
    return redirect('/otheracademic/leaveApproveHOD')  # Redirect to appropriate page after rejection


def leaveStatusPG(request):
    """
    View function for accessing the leave status page for postgraduate students.

    Description:
        This function retrieves and displays the leave status of postgraduate students.
    """
    form_data = LeavePG.objects.all()
    roll_no = request.user.username
    return render(request, 'otheracademic/leaveStatusPG.html', {'form_data': form_data, 'roll_no': roll_no})


def leaveStatusPG_Dip(request):
    """
    View function for accessing the leave  logged data of PG .

    Description:
        This function retrieves and displays the leave logged data of PG leave for future reference.
    """
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    leave_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'pg_leave']

    form_data = LeavePG.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveStatusPG_Dip.html', {'form_data': form_data})








def graduateseminar(request):
    """
    This function is used to log the graduate seminar form and show the status.
    
    """
    user=get_object_or_404(User,username=request.user.username)
    design=request.session['currentDesignationSelected']
    if 'deptadmin' in design :
        return render(request,'otheracademic/graduateseminarForm.html')
    else :
        return HttpResponse("Not Available for You")

def graduate_form_submit(request):
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        # file = request.FILES.get('related_document')

        
            # Create a new LeaveFormTable instance and save it to the database
        graduate=GraduateSeminarFormTable.objects.create(
                
                roll_no=data.get('roll_no'),
                semester=data.get('semester'),
                date_of_seminar=data.get('date_of_seminar'),
               
            )
        graduate.save()
        return redirect('/otheracademic/graduateseminar')

def graduate_status(request):

    form_data = GraduateSeminarFormTable.objects.all()
    roll_no = request.user.username
    return render(request, 'otheracademic/graduateSeminarStatus.html',{'form_data' : form_data, 'roll_no' : roll_no })

def graduateSeminarStatus_Dip(request):
    receiver_value = User.objects.get(username=request.user.username)
    receiver_value_designation= HoldsDesignation.objects.filter(user=receiver_value)
    lis = list(receiver_value_designation)
    obj=lis[0].designation
    
    
    if  obj :
        form_data = GraduateSeminarFormTable.objects.all()
        return render(request, 'otheracademic/graduateSeminarStatus_Dip.html',{'form_data' : form_data })
    else :
        return HttpResponse("Not Available")










def bonafide(request):
    """
    This function is used for solve the problem of Bonafied.In this Student apply for the bonafide .
    
    
    
    
    
    """
    return render(request,'otheracademic/bonafideForm.html')





def bonafide_form_submit(request):
    """
    Bonafide form submitted to acadadmin
    """
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')

        
            # Create a new LeaveFormTable instance and save it to the database
        bonafide=BonafideFormTableUpdated.objects.create(
                student_names=request.user.first_name+request.user.last_name,
                roll_nos=request.user.extrainfo,
                branch_types = data.get('branch'),
                semester_types = data.get('semester'),
                purposes = data.get('purpose'),
                date_of_applications = data.get('date_of_application'),
                approve=False,  # Initially not approved
                reject=False,  # Initially not rejected
                download_file = "not available",
            )
        messages.success(request,'form submitted successfully')
        bonafide.save()
        acad_admin_des_id = Designation.objects.get(name="acadadmin")        
        user_ids = HoldsDesignation.objects.filter(designation_id=acad_admin_des_id.id).values_list('user_id', flat=True) 
        # print(user_ids)  
        # print(user_ids[0]) 
        # acad_admins = ExtraInfo.objects.get(user_id=user_ids[0])
        # # print(acad_admins)
        # user=ExtraInfo.objects.get(pk=acad_admins.id)
        bonafide_receiver = User.objects.get(id=user_ids[0])
        message='A Bonafide applicationn received'
        otheracademic_notif(request.user,bonafide_receiver, 'bonafide', 1, 'student', message)
        return HttpResponseRedirect('/otheracademic/bonafide')


def bonafideApproveForm(request):

    """
    Bonafide form approveform where it got option to accept and reject the application 
    """
    user=get_object_or_404(User,username=request.user.username)
    design=request.session['currentDesignationSelected']
    
    if 'acadadmin' in design :
        form_data = BonafideFormTableUpdated.objects.all()
        return render(request, 'otheracademic/bonafideApprove.html', {'form_data': form_data})
    else:
        return HttpResponse("Not available For You")

def approve_bonafide(request, leave_id):

    """
    Approve Bonafide form
    """
    file = request.FILES.get('related_document')
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.approve = True
    leave_entry.save()
    bonafide_aceptor = User.objects.get(username=leave_entry.roll_nos_id)
    message='A Bonafide uploaded'
    otheracademic_notif(request.user,bonafide_aceptor, 'bonafide_accept', 1, 'student', message)
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after approval

def reject_bonafide(request, leave_id):
    """
    Reject Bonafide Form
    """
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.reject = True
    leave_entry.save()
    bonafide_aceptor = User.objects.get(username=leave_entry.roll_no_id)
    message='A Bonafide rejected'
    otheracademic_notif(request.user,bonafide_aceptor, 'bonafide_accept', 1, 'student', message)
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after rejection

def bonafideStatus(request):
    """
    Bonafide Status shown to student with option of download
    """

    form_data = BonafideFormTableUpdated.objects.all()
    roll_no = request.user.username
    return render(request, 'otheracademic/bonafideStatus.html',{'form_data' : form_data, 'roll_no' : roll_no })


# views.py




def upload_file(request, entry_id):

    """
    Bonafide uploaded by acadadmin
    """
    if request.method == 'POST' and request.FILES.get('related_document'):
        related_document = request.FILES['related_document']
        
        # Assuming you want to update the 'download_file' field of your model
        bonafide_entry = BonafideFormTableUpdated.objects.get(id=entry_id)
        bonafide_entry.download_file = related_document
        bonafide_entry.save()
        
        return HttpResponse("File Uploaded Successfuly")
    else:
        return HttpResponse("No File Attached")





def nodues(request):
    """
    No Dues Form where student can apply for no dues
    """
    return render(request,'otheracademic/noduesverification.html')


def PG_page(request):
    return render(request,'otheracademic/PG_page.html')


def nodues_status(request):
    form_data = NoDues.objects.all()
    roll_no = request.user.username
    print(form_data)
    return render(request, 'otheracademic/nodues_status.html',{'form_data' : form_data, 'roll_no' : roll_no })


def noduesStatus_acad(request):
    form_data = NoDues.objects.all()
    return render(request, 'otheracademic/noduesStatus_acad.html',{'form_data' : form_data })


def nodues_apply(request):
    form_data = NoDues.objects.all()
    roll_no = request.user.username
    return render(request,'otheracademic/nodues_apply.html', {'form_data' : form_data, 'roll_no' : roll_no})



def update_dues_status(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        clear = request.POST.get('clear')  # 'true' if clear, 'false' if not clear
        # Convert clear to boolean
        clear = clear.lower() == 'true'

        # Update clearance status in the database
        try:
            student = NoDues.objects.get(roll_no=roll_no)
            if clear:
                student.clear_status = True
                student.not_clear_status = False
            else:
                student.clear_status = False
                student.not_clear_status = True
            student.save()
            return JsonResponse({'message': 'Clearance status updated successfully'}, status=200)
        except NoDues.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)




@csrf_exempt  # Exempt CSRF verification for this view
def submit_nodues_form(request):

    """
    Submit the No Dues form for a student
    description:-

    There are many actors in this problem like authory of:-
    library,
    mess,
    hostel,
    Physics Lab,
    ECE Lab,
    Computer Centre,
    mechatronics_lab,
    Vlsi,
    Design,
    Bank,
    BTP,
    Placement cell etc.......

    Students apply this form and this forwarded to all this actor to approve/reject


    There is also example Bank_nodues_not for those student whose in first time application is rejected and when they go to second time it will be approved by them.


    """
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        hostel_credential = data.get('hostel_credential'),
        bank_credential = data.get('bank_credential'),
        btp_credential = data.get('btp_credential'),
        cse_credential = data.get('cse_credential'),
        design_credential = data.get('design_credential'),
        acad_credential = data.get('acad_credential'),
        ece_credential = data.get('ece_credential'),
        library_credential = data.get('library_credential'),
        me_credential = data.get('me_credential'),
        mess_credential = data.get('mess_credential'),
        physics_credential = data.get('physics_credential'),
        discipline_credential = data.get('discipline_credential'),

        
            
        nodues=NoDues.objects.create(
            roll_no=request.user.extrainfo,
            name=data.get('name'),
            library_clear=False,
            library_notclear=False,
            hostel_clear=False,
            hostel_notclear=False,
            mess_clear=False,
            mess_notclear=False,
            ece_clear=False,
            ece_notclear=False,
            physics_lab_clear=False,
            physics_lab_notclear=False,
            mechatronics_lab_clear=False,
            mechatronics_lab_notclear=False,
            cc_clear=False,
            cc_notclear=False,
            workshop_clear=False,
            workshop_notclear=False,
            signal_processing_lab_clear=False,
            signal_processing_lab_notclear=False,
            vlsi_clear=False,
            vlsi_notclear=False,
            design_studio_clear=False,
            design_studio_notclear=False,
            design_project_clear=False,
            design_project_notclear=False,
            bank_clear=False,
            bank_notclear=False,
            icard_dsa_clear=False,
            icard_dsa_notclear=False,
            account_clear=False,
            account_notclear=False,
            btp_supervisor_clear=False,
            btp_supervisor_notclear=False,
            discipline_office_clear=False,
            discipline_office_notclear=False,
            student_gymkhana_clear=False,
            student_gymkhana_notclear=False,
            # discipline_office_dsa_clear=False,
            # discipline_office_dsa_notclear=False,
            alumni_clear=False,
            alumni_notclear=False,
            placement_cell_clear=False,
            placement_cell_notclear=False,

            hostel_credential = data.get('hostel_credential'),
            bank_credential = data.get('bank_credential'),
            btp_credential = data.get('btp_credential'),
            cse_credential = data.get('cse_credential'),
            design_credential = data.get('design_credential'),
            acad_credential = data.get('acad_credential'),
            ece_credential = data.get('ece_credential'),
            library_credential = data.get('library_credential'),
            me_credential = data.get('me_credential'),
            mess_credential = data.get('mess_credential'),
            physics_credential = data.get('physics_credential'),
            discipline_credential = data.get('discipline_credential'),

            acad_admin_float = False,
   
            )
        hostel_receiver=User.objects.get(username=data.get('hostel_credential'))

        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        file_hostel = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=hostel_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new hostel application of no dues"
        otheracademic_notif(request.user,hostel_receiver, 'hostel_nodues', nodues.id, 'student', message)


        #bnk_receiver
        bank_receiver=User.objects.get(username=data.get('bank_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=bank_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new bank application of no dues"
        otheracademic_notif(request.user,bank_receiver, 'bank_nodues', nodues.id, 'student', message)

        #btp_receiver
        btp_receiver=User.objects.get(username=data.get('btp_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=btp_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new btp application of no dues"
        otheracademic_notif(request.user,btp_receiver, 'btp_nodues', nodues.id, 'student', message)

        #cse_receiver
        cse_receiver=User.objects.get(username=data.get('cse_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=bank_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new cse application of no dues"
        otheracademic_notif(request.user,cse_receiver, 'cse_nodues', nodues.id, 'student', message)
        #design_receiver
        design_receiver=User.objects.get(username=data.get('design_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=design_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new design application of no dues"
        otheracademic_notif(request.user,design_receiver, 'design_nodues', nodues.id, 'student', message)

        #acad_receiver
        acad_receiver=User.objects.get(username=data.get('acad_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=acad_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new acad application of no dues"
        otheracademic_notif(request.user,acad_receiver, 'acad_nodues', nodues.id, 'student', message)

        #ece_receiver
        ece_receiver=User.objects.get(username=data.get('ece_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=ece_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new ece application of no dues"
        otheracademic_notif(request.user,ece_receiver, 'ece_nodues', nodues.id, 'student', message)

        #library_receiver
        library_receiver=User.objects.get(username=data.get('library_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=library_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new library application of no dues"
        otheracademic_notif(request.user,library_receiver, 'library_nodues', nodues.id, 'student', message)
        #  me_receiver
        me_receiver=User.objects.get(username=data.get('me_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=me_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new ME application of no dues"
        otheracademic_notif(request.user,me_receiver, 'me_nodues', nodues.id, 'student', message)

        #mess_receiver
        mess_receiver=User.objects.get(username=data.get('mess_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=mess_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new mess application of no dues"
        otheracademic_notif(request.user,mess_receiver, 'mess_nodues', nodues.id, 'student', message)

        #physics_receiver
        physics_receiver=User.objects.get(username=data.get('physics_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=physics_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new physics application of no dues"
        otheracademic_notif(request.user,physics_receiver, 'physics_nodues', nodues.id, 'student', message)
        

        #discipline_receiver
        discipline_receiver=User.objects.get(username=data.get('discipline_credential'))
        file_bank= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=discipline_receiver,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=nodues.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='no_dues'
        )
        
        message = "A new discipline application of no dues"
        otheracademic_notif(request.user,discipline_receiver, 'discipline_nodues', nodues.id, 'student', message)
        messages.success(request,'You successfully applied for no_dues')
        

        
        # print(roll_no_id)
        return HttpResponseRedirect('/otheracademic/nodues_apply')
    



def approve_BTP(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.btp_supervisor_clear= True
    leave_entry.btp_supervisor_notclear = False
    btp_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Btp nodues approved"
    otheracademic_notif(request.user,btp_receiver , 'nodues_approve', leave_entry.id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")
            
    leave_entry.save()
    return redirect('/otheracademic/BTP_nodues')  # Red 

def approve_BTP_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.btp_supervisor_clear= True
    leave_entry.btp_supervisor_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/BTP_nodues_not')  # Red     
    


def reject_BTP(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.btp_supervisor_clear= False
    leave_entry.btp_supervisor_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Btp nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/BTP_nodues')  # Red    
    




def approve_bank(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.bank_clear= True
    leave_entry.bank_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "bank nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red   

def approve_bank_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.bank_clear= True
    leave_entry.bank_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues_not')  # Red    
    


def reject_bank(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.bank_clear= False
    leave_entry.bank_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "bank nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
  
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red    

def approve_CSE(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.cc_clear= True
    leave_entry.cc_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Cse nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/CSE_nodues')  # Red    

def approve_CSE_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.cc_clear= True
    leave_entry.cc_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/CSE_nodues_not')  # Red  
    


def reject_CSE(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.cc_clear= False
    leave_entry.cc_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Cse nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/CSE_nodues')  # Red  

def approve_design_project(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_project_clear= True
    leave_entry.design_project_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Design project nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red    

def approve_design_project_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_project_clear= True
    leave_entry.design_project_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues_not')  # Red 
    


def reject_design_project(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_project_clear= False
    leave_entry.design_project_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Design project nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red      

def approve_design_studio(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_studio_clear= True
    leave_entry.design_studio_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Design studio nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red  

def approve_design_studio_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_studio_clear= True
    leave_entry.design_studio_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues_not')  # Red  

def reject_design_studio(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_studio_clear= False
    leave_entry.design_studio_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Design studio nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red    
    
 

def approve_icard(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.icard_dsa_clear= True
    leave_entry.icard_dsa_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "icard nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red   

def approve_icard_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.icard_dsa_clear= True
    leave_entry.icard_dsa_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues_not')  # Red 
    


def reject_icard(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.icard_dsa_clear= False
    leave_entry.icard_dsa_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "icard nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_placement(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.placement_cell_clear= True
    leave_entry.placement_cell_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "placement nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red  

def approve_placement_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.placement_cell_clear= True
    leave_entry.placement_cell_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues_not')  # Red     
    


def reject_placement(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.placement_cell_clear= False
    leave_entry.placement_cell_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "placement nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_account(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.account_clear= True
    leave_entry.account_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "account nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red 

def approve_account_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.account_clear= True
    leave_entry.account_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues_not')  # Red    
    


def reject_account(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.account_clear= False
    leave_entry.account_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "account nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red    

def approve_alumni(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.alumni_clear= True
    leave_entry.alumni_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "alumni nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Realumni

def approve_alumni_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.alumni_clear= True
    leave_entry.alumni_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues_not')  # Realumni
    


def reject_alumni(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.alumni_clear= False
    leave_entry.alumni_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "alumni nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red   

def approve_gym(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.student_gymkhana_clear= True
    leave_entry.student_gymkhana_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "gym nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red   

def approve_gym_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.student_gymkhana_clear= True
    leave_entry.student_gymkhana_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues_not')  # Red  
    


def reject_gym(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.student_gymkhana_clear= False
    leave_entry.student_gymkhana_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "gym nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red     

def approve_discipline(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= True
    leave_entry.discipline_office_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Discipline office nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/discipline_nodues')  # Red   

def approve_discipline_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= True
    leave_entry.discipline_office_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/discipline_nodues_not')  # Red   
    


def reject_discipline(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= False
    leave_entry.discipline_office_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Discipline office nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_signal(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.signal_processing_lab_clear= True
    leave_entry.signal_processing_lab_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "signal nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Realumni

def approve_signal_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.signal_processing_lab_clear= True
    leave_entry.signal_processing_lab_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues_not')  # Realumni
    


def reject_signal(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.signal_processing_lab_clear= False
    leave_entry.signal_processing_lab_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "signal nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  


def approve_vlsi(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.vlsi_clear= True
    leave_entry.vlsi_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "vlsi nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Realumni

def approve_vlsi_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.vlsi_clear= True
    leave_entry.vlsi_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues_not')  # Realumni
    


def reject_vlsi(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.vlsi_clear= False
    leave_entry.vlsi_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Vlsi nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  

def approve_ece(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.ece_clear= True
    leave_entry.ece_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Ece nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Realumni

def approve_ece_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.ece_clear= True
    leave_entry.ece_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues_not')  # Realumni
    


def reject_ece(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.ece_clear= False
    leave_entry.ece_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "Ece nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  


def approve_hostel(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.hostel_clear= True
    leave_entry.hostel_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "hostel nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/hostel_nodues')  # Realumni

def approve_hostel_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.hostel_clear= True
    leave_entry.hostel_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/hostel_nodues_not')  # Realumni
    


def reject_hostel(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.hostel_clear= False
    leave_entry.hostel_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "hostel nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/hostel_nodues')  # Red  



def approve_library(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.library_clear= True
    leave_entry.library_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "library nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/library_nodues')  # Realumni

def approve_library_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.library_clear= True
    leave_entry.library_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/library_nodues_not')  # Realumni
    


def reject_library(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.library_clear= False
    leave_entry.library_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "library nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/library_nodues')  # Red  


def approve_workshop(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.workshop_clear= True
    leave_entry.workshop_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "workshop nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Realumni

def approve_workshop_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.workshop_clear= True
    leave_entry.workshop_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues_not')  # Realumni
    


def reject_workshop(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.workshop_clear= False
    leave_entry.workshop_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "workshop nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Red  


def approve_mecha(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mechatronics_lab_clear= True
    leave_entry.mechatronics_lab_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "mecha nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Realumni

def approve_mecha_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mechatronics_lab_clear= True
    leave_entry.mechatronics_lab_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues_not')  # Realumni
    


def reject_mecha(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mechatronics_lab_clear= False
    leave_entry.mechatronics_lab_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "mecha nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Red  


def approve_mess(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mess_clear= True
    leave_entry.mess_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "mess nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/mess_nodues')  # Realumni

def approve_mess_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mess_clear= True
    leave_entry.mess_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/mess_nodues_not')  # Realumni
    


def reject_mess(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mess_clear= False
    leave_entry.mess_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "mess nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/mess_nodues')  # Red  

def approve_physics(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.physics_lab_clear= True
    leave_entry.physics_lab_notclear = False
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "physics nodues approved"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Physics_nodues')  # Realumni

def approve_physics_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.physics_lab_clear= True
    leave_entry.physics_lab_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/Physics_nodues_not')  # Realumni
    


def reject_physics(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.physics_lab_clear= False
    leave_entry.physics_lab_notclear = True
    nodues_receiver=User.objects.get(username=leave_entry.roll_no_id)
    message = "physics nodues rejected"
    otheracademic_notif(request.user,nodues_receiver , 'nodues_status', leave_entry.id, "student", message)
    leave_entry.save()
    return redirect('/otheracademic/Physics_nodues')  # Red  


def Bank_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    # form_data=NoDues.objects.all()
    return render(request,'otheracademic/Bank_nodues.html',{'form_data': form_data})

def Bank_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Bank_nodues_not.html',{'form_data': form_data})

def BTP_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/BTP_nodues.html',{'form_data': form_data})

def BTP_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/BTP_nodues_not.html',{'form_data': form_data})

def CSE_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/CSE_nodues.html',{'form_data': form_data})

def CSE_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/CSE_nodues_not.html',{'form_data': form_data})


def Design_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Design_nodues.html',{'form_data': form_data})

def Design_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Design_nodues_not.html',{'form_data': form_data})


def dsa_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/dsa_nodues.html',{'form_data': form_data})

def dsa_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/dsa_nodues_not.html',{'form_data': form_data})


def Ece_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Ece_nodues.html',{'form_data': form_data})

def Ece_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Ece_nodues_not.html',{'form_data': form_data})


def hostel_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/hostel_nodues.html',{'form_data': form_data})

def hostel_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/hostel_nodues_not.html',{'form_data': form_data})


def ME_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/ME_nodues.html',{'form_data': form_data})

def ME_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/ME_nodues_not.html',{'form_data': form_data})


def mess_nodues(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/mess_nodues.html',{'form_data': form_data})

def mess_nodues_not(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/mess_nodues_not.html',{'form_data': form_data})


def Physics_nodues(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Physics_nodues.html',{'form_data': form_data})

def Physics_nodues_not(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Physics_nodues_not.html',{'form_data': form_data})

def discipline_nodues(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Discipline_nodues.html',{'form_data': form_data})

def discipline_nodues_not(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/Discipline_nodues_not.html',{'form_data': form_data})

def library_nodues(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/library_nodues.html',{'form_data': form_data})

def library_nodues_not(request): 
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='no_dues']
    
    form_data = NoDues.objects.filter(id__in=leave_ids)
    return render(request,'otheracademic/library_nodues_not.html',{'form_data': form_data})







def noduesStatus_acad(request):
    if(request.user.username == "acadadmin"):
        form_data = NoDues.objects.all()
        return render(request, 'otheracademic/noduesStatus_acad.html',{'form_data' : form_data })
    else :
        return HttpResponse("Not Available for you.")

def nodues_apply(request):
    return render(request,'otheracademic/nodues_apply.html')



def update_dues_status(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        clear = request.POST.get('clear')  # 'true' if clear, 'false' if not clear
        # Convert clear to boolean
        clear = clear.lower() == 'true'

        # Update clearance status in the database
        try:
            student = NoDues.objects.get(roll_no=roll_no)
            if clear:
                student.clear_status = True
                student.not_clear_status = False
            else:
                student.clear_status = False
                student.not_clear_status = True
            student.save()
            return JsonResponse({'message': 'Clearance status updated successfully'}, status=200)
        except NoDues.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
#assistantship



@login_required
def assistantship(request):
     
     """
     This function solve the problem of assistantship apply by mtech and phd students for thhe monthly stipend.
     The form firstly approved by TA_supervisor ---->then it forwarded to---->Thesis_Supervisor------>HOD------>acadadmin
     After approval status is shown to the student
     
     
     
     
     """
     user = get_object_or_404(User, username=request.user.username)
     if user.extrainfo.student.programme == 'M.Tech' or 'PhD':
        return render(request, 'otheracademic/assistantshipclaimform.html')
     else:
        return HttpResponse("NOt available")
@login_required
def assistantship_form_submission(request):
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    # num=1
    # comp_id=y.id
    if request.method == 'POST':
        # Retrieve form data
        print(request.POST)
        student_name = request.POST.get('student_name')
        roll_no = request.POST.get('roll_no')
        discipline = request.POST.get('discipline')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        bank_account_no = request.POST.get('bank_account_no')
        signature = request.FILES.get('signature')
        applicability = request.POST.get('applicability')
        ta_supervisor = request.POST.get('ta_supervisor')
        thesis_supervisor = request.POST.get('thesis_supervisor')
        date_applied = request.POST.get('date_of_application'),
        hod=request.POST.get('hod_credential')
        

        current_date = date.today()
        
        
        
        assistant = AssistantshipClaimFormStatusUpd.objects.create(student_name=request.user.first_name+request.user.last_name,roll_no=request.user.extrainfo,
            discipline=discipline,
            dateFrom=date_from,
            dateTo=date_to,
            bank_account=bank_account_no,
            student_signature=signature,
            dateApplied= current_date ,
            ta_supervisor=ta_supervisor,
            thesis_supervisor=thesis_supervisor,
            applicability=applicability,
            TA_approved=False,
            TA_rejected=False,
            Ths_approved=False,
            Ths_rejected=False,
            HOD_approved=False,
            HOD_rejected=False,
            Acad_approved=False,
            Acad_rejected=False,
            hod=hod
           


        )
       
        current_user=get_object_or_404(User,username=request.user.username)
        ta_supervisor_id=User.objects.get(username=ta_supervisor)
        ts=User.objects.get(username=thesis_supervisor)
        
        user_details=User.objects.get(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        file_id = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =ta_supervisor, receiver_designation = "student", src_module = "otheracademic", src_object_id = assistant.id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
        print(request.user)
        print(file_id)
        message="A new assistantship application raised"
        otheracademic_notif(request.user,ta_supervisor_id ,'ast_ta',assistant.id,"student",message)
        # if date_from>=date_to:
        #     messages.warning(request,"enter")
        #     return HttpResponseRedirect('/otheracademic/assistantship')
        # Redirect to a success page or return a success message
        messages.success(request,"Your form is successfully submitted")
        return HttpResponseRedirect('/otheracademic/assistantship')  # Replace '/otheracademic/assistantship' with the actual URL you want to redirect to

    else:
        # Return an error response for invalid request method
        return HttpResponse('Invalid request method')






def assistantship_form_approval(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    # print(inbox)
    # print(request.user.username)
    
    # Find the src_object_id where subject is 'assistantship'
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    roll_no = request.user.username
    return render(request, 'otheracademic/assistantship_approval.html', {'form_data': form_data, 'roll_no' : roll_no})
     
def assistantship_thesis(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
  
    assistantship_ids = [msg['src_object_id' ] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    roll_no = request.user.username
    return render(request, 'otheracademic/thesis_supervisor_approve.html', {'form_data': form_data, 'roll_no' : roll_no})


def assistantship_hod(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    print(inbox)
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    roll_no = request.user.username
    return render(request, 'otheracademic/hod_approval.html', {'form_data': form_data, 'roll_no' : roll_no})



     
def assistantship_status(request):
    form_data = AssistantshipClaimFormStatusUpd.objects.all()
    roll_no = request.user.username
    return render(request, 'otheracademic/assistantship_status.html', { 'form_data' : form_data, 'roll_no' : roll_no})


def assistantship_log(request):
    user=get_object_or_404(User,username=request.user.username)
    if(user.extrainfo.department.name == 'Academics'):
        form_data = AssistantshipClaimFormStatusUpd.objects.all()
        return render(request, 'otheracademic/assistantship_log.html', { 'form_data' : form_data})
    else:
        return HttpResponse("Not Avalable For You.")

def find_id_from_inbox(inbox_data, src_obj_id):
    for item in inbox_data:
        if item.get('src_object_id') == src_obj_id:
            return item.get('id')
    return None  # Return None if src_obj_id is not found in the inbox



def assistanship_ta_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    thesis_supervisor_user = User.objects.get(username=leave_entry.thesis_supervisor)

    # Update TA_approved field to True
    leave_entry.TA_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    forwarded_file_id = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =leave_entry.thesis_supervisor, receiver_designation = "student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    message = "Assistantship status form forwarded"
    otheracademic_notif(request.user, thesis_supervisor_user, 'ast_thesis', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/approveform')



def assistanship_ta_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.TA_rejected = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    messages.success(request, "Successfully rejected.")
    return redirect('/otheracademic/approveform')

def assistanship_thesis_approve(request, ass_id):
   
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    csehod_user = User.objects.get(username=leave_entry.hod)

    # Update TA_approved field to True
    leave_entry.Ths_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    # ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    # print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
   
    forwarded_hod = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =leave_entry.hod, receiver_designation = "student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
    
   
    
    message = "Assistantship status received"
    otheracademic_notif(request.user,csehod_user , 'ast_hod', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/thesis_approveform')



def assistanship_thesis_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.Ths_rejected = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    messages.success(request, "Successfully rejected.")
    return redirect('/otheracademic/assitantship/thesis_approveform')


def assistanship_hod_approve(request, ass_id):
    
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)
    leave_entry.HOD_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()

    acad_admin_des_id = Designation.objects.get(name="acadadmin")        
    user_ids = HoldsDesignation.objects.filter(designation_id=acad_admin_des_id.id).values_list('user_id', flat=True) 
        
    acadadmin_receiver = User.objects.get(id=user_ids[0])
    
    
    forwarded_acad = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =acadadmin_receiver, receiver_designation ="student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    message = "Assistantship status received"
    otheracademic_notif(request.user,acadadmin_receiver , 'ast_acadadmin', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/hod_approveform')



def assistanship_hod_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.HOD_rejected = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    messages.success(request, "Successfully rejected.")
    
    return redirect('/otheracademic/assitantship/hod_approveform')


def assistantship_acad_approveform(request):
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    print(inbox)
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    user=get_object_or_404(User,username=request.user.username)
    if(user.extrainfo.department.name == 'Academics'):
        form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
        return render(request, 'otheracademic/acadadmin_approval.html', { 'form_data' : form_data})
    else:
        return HttpResponse("Not Avalable For You.")


def assistanship_acad_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    # print(leave_entry.thesis_supervisor)
    # acadadmin = User.objects.get(username='acadadmin')

    # Update TA_approved field to True
    leave_entry.Acad_approved = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    
    # forwarded_acad = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver ='acadadmin', receiver_designation ="student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    # message = "Assistantship status received"
    # otheracademic_notif(request.user,acadadmin , 'alert', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/hod_approveform')



def assistanship_acad_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.Acad_rejected = True
    leave_entry.save()
    leave_receive = User.objects.get(username=leave_entry.roll_no_id)
    message='Assistanstship Claim form status'
    otheracademic_notif(request.user,leave_receive, 'ast_ta_accept', leave_entry.id, 'student', message)
    messages.success(request, "Successfully rejected.")
    
    return redirect('/otheracademic/assitantship/hod_approveform')



def othersPage(request):
    return render(request, 'otheracademic/othersPage.html')

def othersLeave(request):
    return render(request, 'otheracademic/othersLeave.html')

def othersNoDues(request):
    return render(request, 'otheracademic/othersNoDues.html')

def othersAssistantship(request):
    return render(request, 'otheracademic/othersAssistantship.html')

def othersGraduate(request):
    return render(request, 'otheracademic/othersGraduate.html')


























    
