# from django.shortcuts import render
# from django.contrib import messages
# from django.shortcuts import render, get_object_or_404, redirect
# # from .models import File, Tracking
# from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
# from django.template.defaulttags import csrf_token
# from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
# from django.contrib.auth.decorators import login_required
# from django.db import IntegrityError
# from django.core import serializers
# from django.contrib.auth.models import User
# from timeit import default_timer as time
# from notification.views import office_module_notif,file_tracking_notif
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import LeaveFormTable,BonafideFormTableUpdated,GraduateSeminarFormTable,AssistantshipClaimFormStatusUpd,NoDues
# from django.shortcuts import render, get_object_or_404
# from datetime import date 
# from applications.filetracking.models import *
# from applications.filetracking.sdk.methods import *
# from notification.views import otheracademic_notif
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect,render
# from .models import File, Tracking
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

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


#leave for UG

def otheracademic(request):
    
    user=get_object_or_404(User,username=request.user.username)
    if (user.extrainfo.student.programme == "B.Tech"):
        return  render(request, "otheracademic/UG_page.html")
    elif(user.extrainfo.student.programme == "M.Tech" or user.extrainfo.student.programme == "PhD"):
        return render(request, "otheracademic/PG_page.html")
    

def leaveform(request):
    return render(request, 'otheracademic/leaveform.html')



@csrf_exempt  # Exempt CSRF verification for this view
def leave_form_submit(request):
    if request.method == 'POST':
        # Extract data from the request
        current_user=get_object_or_404(User,username=request.user.username)
        y=ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        user_details=User.objects.filter(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        data = request.POST
        file = request.FILES.get('related_document')
        hodname=data.get('hod_credential')

        
            # Create a new LeaveFormTable instance and save it to the database
        leave=LeaveFormTable.objects.create(
                student_name=data.get('name'),
                roll_no=request.user.extrainfo,
                date_from=data.get('date_from'),
                date_to=data.get('date_to'),
                leave_type=data.get('leave_type'),
                upload_file=file,
                address=data.get('address'),
                purpose=data.get('purpose'),
                date_of_application=data.get('date_of_application'),
                approved=False,  # Initially not approved
                rejected=False, 
                hod=data.get('hod_credential') # Initially not rejected
            )
        
        leave_hod=User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation= HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj=lis[0].designation
        
        file_id= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value":2},
            attached_file=None,
            subject='ug_leave')
        # leave.save()
        # print(roll_no_id)
        message="A new leave application"
        otheracademic_notif(request.user,leave_hod,'alert',leave.id,'student',message)
        if(leave):
            messages.success(request,"you successfully submited your form")
            
        return HttpResponseRedirect('/otheracademic/leaveform')
    

def leaveApproveForm(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='ug_leave']
    
    form_data = LeaveFormTable.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveformreciever.html', {'form_data': form_data})

def leaveStatus(request):
     
    form_data = LeaveFormTable.objects.filter(roll_no=request.user.extrainfo)
    return render(request, 'otheracademic/leaveStatus.html',{'form_data' : form_data })

def leaveStatus_Dip(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='ug_leave']

    form_data = LeaveFormTable.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveStatus_Dip.html',{'form_data' : form_data })


def approve_leave(request, leave_id):
    leave_entry = LeaveFormTable.objects.get(id=leave_id)
    leave_entry.approved = True
    leave_entry.save()
    return redirect('/otheracademic/leaveApproveForm')  # Redirect to appropriate page after approval

def reject_leave(request, leave_id):
    leave_entry = LeaveFormTable.objects.get(id=leave_id)
    leave_entry.rejected = True
    leave_entry.save()
    return redirect('/otheracademic/leaveApproveForm')  # Redirect to appropriate page after rejection

# PG/MTECh
@login_required
def leavePG(request):
    user=get_object_or_404(User,username=request.user.username)
    if (user.extrainfo.student.programme == "M.Tech" or "PhD"):
        return render(request, 'otheracademic/leavePG.html')
    else:
        return HttpResponse("NOT AVAILABLE")



def leavePgSubmit(request):
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user', 'department').filter(user=current_user).first()
        user_details = User.objects.filter(id=y.user_id)
        des = HoldsDesignation.objects.filter(user=user_details).all()
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        ta=data.get('ta_supervisor')
        
        leave = LeavePG.objects.create(
            student_name=data.get('student_name'),
            roll_no=request.user.extrainfo,
            programme=data.get('programme'),
            discipline=data.get('discipline'),
            Semester=data.get('Semester'),
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            date_of_application=data.get('date_of_application'),
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
            hod_approved=False,
            hod_rejected=False,
            
            hod=hodname
        )
        
        tasupervisor= User.objects.get(username=ta)
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
        otheracademic_notif(request.user,tasupervisor, 'alert', leave.id, 'student', message)
        if leave:
            messages.success(request, "You have successfully submitted your form")
            
        return HttpResponseRedirect('/otheracademic/leaveform')

    
def leaveApproveTA(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='pg_leave']
    
    form_data = LeavePG.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveApproveTA.html', {'form_data': form_data})

def approve_leave_ta(request, leave_id):

    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.ta_approved = True
    leave_entry.save()
    
    receiver_value = User.objects.get(username=request.user.username)
    receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
    lis = list(receiver_value_designation)
    obj = lis[0].designation
    leave_entry=get_object_or_404(LeavePG,id=leave_id)

        
    file_id_forward= create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_entry.hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave_id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='pg_leave')
    message = "A new leave application"
    hod_user=User.objects.get(username=leave_entry.hod)
    otheracademic_notif(request.user,hod_user, 'alert', leave_id, 'student', message)

    return redirect('/otheracademic/leaveApproveTA')  # Redirect to appropriate page after approval

def reject_leave_ta(request, leave_id):
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.ta_rejected = True
    leave_entry.save()
    return redirect('/otheracademic/leaveApproveTA')  # Redirect to appropriate page after rejection

def leaveApproveHOD(request):
    
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='pg_leave']
    
    form_data = LeavePG.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveApproveHOD.html', {'form_data': form_data})

def approve_leave_hod(request, leave_id):
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.hod_approved = True
    leave_entry.save()
    return redirect('/otheracademic/leaveApproveHOD')  # Redirect to appropriate page after approval

def reject_leave_hod(request, leave_id):
    leave_entry = LeavePG.objects.get(id=leave_id)
    leave_entry.hod_rejected = True
    leave_entry.save()
    return redirect('/otheracademic/leaveApproveHOD')  # Redirect to appropriate page after rejection


def leaveStatusPG(request):
    
    form_data = LeavePG.objects.all()
    roll_no = request.user.username
    print(roll_no)
    # form_data = LeavePG.objects.all()
    return render(request, 'otheracademic/leaveStatusPG.html', {'form_data': form_data, 'roll_no' : roll_no})



def leaveStatusPG_Dip(request):
    inbox=view_inbox(username=request.user.username,designation="student",src_module="otheracademic")
    leave_ids=[msg ['src_object_id'] for msg in inbox if  msg['subject']=='pg_leave']

    form_data = LeavePG.objects.filter(id__in=leave_ids)
    return render(request, 'otheracademic/leaveStatusPG_Dip.html', {'form_data': form_data})


def graduateseminar(request):
    user=get_object_or_404(User,username=request.user.username)
    if(request.user.username == "AG") :
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
    user=get_object_or_404(User,username=request.user.username)
    if(request.user.username == "AG") :
        form_data = GraduateSeminarFormTable.objects.all()
        return render(request, 'otheracademic/graduateSeminarStatus_Dip.html',{'form_data' : form_data })
    else :
        return HttpResponse("Not Available for You")

def bonafide(request):
    return render(request,'otheracademic/bonafideForm.html')





def bonafide_form_submit(request):
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')

        
            # Create a new LeaveFormTable instance and save it to the database
        bonafide=BonafideFormTableUpdated.objects.create(
                student_names=data.get('name'),
                roll_nos=request.user.extrainfo,
                branch_types = data.get('branch'),
                semester_types = data.get('semester'),
                purposes = data.get('purpose'),
                date_of_applications = data.get('date_of_application'),
                approve=False,  # Initially not approved
                reject=False,  # Initially not rejected
                download_file = None,
            )
        bonafide.save()
        return HttpResponseRedirect('/otheracademic/bonafide')


def bonafideApproveForm(request):
    if(request.user.username == "acadadmin"):
        form_data = BonafideFormTableUpdated.objects.all()
        return render(request, 'otheracademic/bonafideApprove.html', {'form_data': form_data})
    else:
        return HttpResponse("Not available For You")

def approve_bonafide(request, leave_id):
    file = request.FILES.get('related_document')
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.approve = True
    leave_entry.save()
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after approval

def reject_bonafide(request, leave_id):
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.reject = True
    leave_entry.save()
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after rejection

def bonafideStatus(request):

    form_data = BonafideFormTableUpdated.objects.all()
    roll_no = request.user.username
    return render(request, 'otheracademic/bonafideStatus.html',{'form_data' : form_data, 'roll_no' : roll_no })


# views.py




def upload_file(request, entry_id):
    if request.method == 'POST' and request.FILES.get('related_document'):
        related_document = request.FILES['related_document']
        
        # Assuming you want to update the 'download_file' field of your model
        bonafide_entry = BonafideFormTableUpdated.objects.get(id=entry_id)
        bonafide_entry.download_file = related_document
        bonafide_entry.save()
        
        return JsonResponse({'message': 'File uploaded successfully'}, status=200)
    else:
        return JsonResponse({'error': 'No file provided'}, status=400)


# def assistantship(request):
#     return render(request,'otheracademic/assistantshipclaimform.html')

# def assistantship_form_submission(request):
#     if request.method == 'POST':
#         # Retrieve form data

#         student_name = request.POST.get('student_name')
#         roll_no = request.POST.get('roll_no')
#         discipline = request.POST.get('discipline')
#         date_from = request.POST.get('date_from')
#         date_to = request.POST.get('date_to')
#         bank_account_no = request.POST.get('bank_account_no')
#         signature = request.FILES.get('signature')
#         applicability = request.POST.get('applicability')
#         ta_supervisor = request.POST.get('ta_supervisor')
#         thesis_supervisor = request.POST.get('thesis_supervisor')
#         date_applied = request.POST.get('date_of_application')

#         current_date = date.today()
        
#         # Save form data to the database
#         assistantship_claim = AssistantshipClaimFormStatusUpd(
#             student_name=student_name,
#             roll_no=request.user.extrainfo,
#             discipline=discipline,
#             dateFrom=date_from,
#             dateTo=date_to,
#             bank_account=bank_account_no,
#             student_signature=signature,
#             dateApplied= current_date ,
#             ta_supervisor=ta_supervisor,
#             thesis_supervisor=thesis_supervisor,
#             applicability=applicability,
#             TA_approved=False,
#             TA_rejected=False,
#             Ths_approved=False,
#             Ths_rejected=False,
#             HOD_approved=False,
#             HOD_rejected=False,
#             Acad_approved=False,
#             Acad_rejected=False
#         )
#         assistantship_claim.save()
        
#         # Redirect to a success page or return a success message
#         return HttpResponseRedirect('/otheracademic/assistantship')  # Replace '/otheracademic/assistantship' with the actual URL you want to redirect to

#     else:
#         # Return an error response for invalid request method
#         return HttpResponse('Invalid request method')


# def assistantship_form_approval(request):
#     # Retrieve data from the database
#     form_data =AssistantshipClaimForm.objects.all()
#     return render(request, 'otheracademic/assistantship_approval.html', {'form_data': form_data})




#No Dues Status







def nodues(request):
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


# @csrf_exempt  # Exempt CSRF verification for this view
# def submit_nodues_form(request):
#     if request.method == 'POST':
#         roll_no = request.POST.get('roll_no')
#         student_name = request.POST.get('student_name')

#         # Create a new NoDues instance and save it to the database
#         nodues_entry = NoDues.objects.create(
#             roll_no=roll_no,
#             student_name=student_name,
#             library_clear=False,
#             library_notclear=True,
#             hostel_clear=False,
#             hostel_notclear=True,
#             mess_clear=False,
#             mess_notclear=True,
#             ece_clear=False,
#             ece_notclear=True,
#             physics_lab_clear=False,
#             physics_lab_notclear=True,
#             mechatronics_lab_clear=False,
#             mechatronics_lab_notclear=True,
#             cc_clear=False,
#             cc_notclear=True,
#             workshop_clear=False,
#             workshop_notclear=True,
#             signal_processing_lab_clear=False,
#             signal_processing_lab_notclear=True,
#             vlsi_clear=False,
#             vlsi_notclear=True,
#             design_studio_clear=False,
#             design_studio_notclear=True,
#             design_project_clear=False,
#             design_project_notclear=True,
#             bank_clear=False,
#             bank_notclear=True,
#             icard_dsa_clear=False,
#             icard_dsa_notclear=True,
#             account_clear=False,
#             account_notclear=True,
#             btp_supervisor_clear=False,
#             btp_supervisor_notclear=True,
#             discipline_office_clear=False,
#             discipline_office_notclear=True,
#             student_gymkhana_clear=False,
#             student_gymkhana_notclear=True,
#             discipline_office_dsa_clear=False,
#             discipline_office_dsa_notclear=True,
#             alumni_clear=False,
#             alumni_notclear=True,
#             placement_cell_clear=False,
#             placement_cell_notclear=True,
   
#      )
#         # Optionally, you can redirect to a success page or render a template
#         nodues_entry.save()
#         # print(roll_no_id)
#         return redirect('no_dues_form.html')
#     else:
#         return render(request, 'no_dues_form.html')
    

@csrf_exempt  # Exempt CSRF verification for this view
def submit_nodues_form(request):
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
        
            # Create a new LeaveFormTable instance and save it to the database
        nodues=NoDues.objects.create(
            roll_no=data.get('roll_no'),
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
            discipline_office_dsa_clear=False,
            discipline_office_dsa_notclear=False,
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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,hostel_receiver, 'alert', nodues.id, 'student', message)


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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,bank_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,btp_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,cse_receiver, 'alert', nodues.id, 'student', message)
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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,design_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,acad_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,ece_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,library_receiver, 'alert', nodues.id, 'student', message)
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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,me_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,mess_receiver, 'alert', nodues.id, 'student', message)

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
        
        message = "A new leave application of no dues"
        otheracademic_notif(request.user,physics_receiver, 'alert', nodues.id, 'student', message)
        messages.success(request,'You successfully applied for no_dues')
        

        
        # print(roll_no_id)
        return HttpResponseRedirect('/otheracademic/nodues_apply')
    



def approve_BTP(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.btp_supervisor_clear= True
    leave_entry.btp_supervisor_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/BTP_nodues')  # Red    
    




def approve_bank(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.bank_clear= True
    leave_entry.bank_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red    

def approve_CSE(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.cc_clear= True
    leave_entry.cc_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/CSE_nodues')  # Red  

def approve_design_project(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_project_clear= True
    leave_entry.design_project_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red      

def approve_design_studio(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.design_studio_clear= True
    leave_entry.design_studio_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Design_nodues')  # Red    
    
 

def approve_icard(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.icard_dsa_clear= True
    leave_entry.icard_dsa_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_placement(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.placement_cell_clear= True
    leave_entry.placement_cell_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_account(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.account_clear= True
    leave_entry.account_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Bank_nodues')  # Red    

def approve_alumni(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.alumni_clear= True
    leave_entry.alumni_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red   

def approve_gym(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.student_gymkhana_clear= True
    leave_entry.student_gymkhana_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red     

def approve_discipline(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= True
    leave_entry.discipline_office_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red   

def approve_discipline_not(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= True
    leave_entry.discipline_office_notclear = False
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues_not')  # Red   
    


def reject_discipline(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.discipline_office_clear= False
    leave_entry.discipline_office_notclear = True
    leave_entry.save()
    return redirect('/otheracademic/dsa_nodues')  # Red    

def approve_signal(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.signal_processing_lab_clear= True
    leave_entry.signal_processing_lab_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  


def approve_vlsi(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.vlsi_clear= True
    leave_entry.vlsi_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  

def approve_ece(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.ece_clear= True
    leave_entry.ece_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/Ece_nodues')  # Red  


def approve_hostel(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.hostel_clear= True
    leave_entry.hostel_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/hostel_nodues')  # Red  



def approve_library(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.library_clear= True
    leave_entry.library_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/library_nodues')  # Red  


def approve_workshop(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.workshop_clear= True
    leave_entry.workshop_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Red  


def approve_mecha(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mechatronics_lab_clear= True
    leave_entry.mechatronics_lab_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/ME_nodues')  # Red  


def approve_mess(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.mess_clear= True
    leave_entry.mess_notclear = False
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
    leave_entry.save()
    return redirect('/otheracademic/mess_nodues')  # Red  

def approve_physics(request, no_dues_id):
    leave_entry = NoDues.objects.get(id=no_dues_id)
    leave_entry.physics_lab_clear= True
    leave_entry.physics_lab_notclear = False
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



# def nodues_status(request):
#     form_data = NoDues.objects.all()
#     roll_no = request.user.username
#     print(roll_no)
#     return render(request, 'otheracademic/nodues_status.html',{'form_data' : form_data, 'roll_no' : roll_no })

# def nodues_status(request):
#     roll_no = request.user.username
#     form_data = NoDues.objects.filter(roll_no=roll_no)
#     print(form_data)
#     return render(request, 'otheracademic/nodues_status.html', {'form_data': form_data, 'roll_no': roll_no})



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
     user = get_object_or_404(User, username=request.user.username)
     if user.extrainfo.student.programme == 'M.Tech':
        return render(request, 'otheracademic/assistantshipclaimform.html')
     else:
        return HttpResponse("NOt available")

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
        
        
        
        assistant = AssistantshipClaimFormStatusUpd.objects.create(student_name=student_name,roll_no=request.user.extrainfo,
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
            # amount =0
            # rate = 0
            # half_day_leave = models.IntegerField(default=0)
            # full_day_leave = models.IntegerField(default=0)


        )
        # print(assistant.id)
        # assistant.save()
        current_user=get_object_or_404(User,username=request.user.username)
        ta_supervisor_id=User.objects.get(username=ta_supervisor)
        ts=User.objects.get(username=thesis_supervisor)
        # y=ExtraInfo.object.all().select_related('user','department').filter(user=current_user).first()
        # thesis_supervisor_name=HoldsDesignation.objects.select_related('user','working','designation').get(designation__name=thesis_supervisor)
        user_details=User.objects.get(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        file_id = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =ta_supervisor, receiver_designation = "student", src_module = "otheracademic", src_object_id = assistant.id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
        print(request.user)
        print(file_id)
        message="A new assistantship application raised"
        otheracademic_notif(request.user,ta_supervisor_id ,'alert',assistant.id,"student",message)
        # Redirect to a success page or return a success message
        return HttpResponseRedirect('/otheracademic/assistantship')  # Replace '/otheracademic/assistantship' with the actual URL you want to redirect to

    else:
        # Return an error response for invalid request method
        return HttpResponse('Invalid request method')


# def assistantship_form_approval(request):
#     # Retrieve data from the database
#     inbox = view_inbox(username = request.user.username, designation = "student", src_module = "otheracademic")
#     print(inbox)
#     print(request.user.username)
#     form_data = AssistantshipClaimFormStatusUpd.objects.all()
#     return render(request, 'otheracademic/assistantship_approval.html', {'form_data': form_data})



def assistantship_form_approval(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    # print(inbox)
    # print(request.user.username)
    
    # Find the src_object_id where subject is 'assistantship'
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    
    return render(request, 'otheracademic/assistantship_approval.html', {'form_data': form_data})
     
def assistantship_thesis(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
  
    assistantship_ids = [msg['src_object_id' ] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    
    return render(request, 'otheracademic/thesis_supervisor_approve.html', {'form_data': form_data})


def assistantship_hod(request):
    # Retrieve data from the database
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    print(inbox)
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    
    return render(request, 'otheracademic/hod_approval.html', {'form_data': form_data})



     
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
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    forwarded_file_id = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =leave_entry.thesis_supervisor, receiver_designation = "student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    message = "Assistantship status received"
    otheracademic_notif(request.user, thesis_supervisor_user, 'alert', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/approveform')



def assistanship_ta_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.TA_rejected = True
    leave_entry.save()
    messages.success(request, "Successfully rejected.")
    return redirect('/otheracademic/approveform')

def assistanship_thesis_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    csehod_user = User.objects.get(username=leave_entry.hod)

    # Update TA_approved field to True
    leave_entry.Ths_approved = True
    leave_entry.save()
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
   
    
    forwarded_hod = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver =leave_entry.hod, receiver_designation ="student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
    # Forward the file to the thesis supervisor
    # forwarded_file_id = forward_file(
    #     file_id=ass_id_from_inbox,
    #     receiver=leave_entry.thesis_supervisor,
    #     receiver_designation="thesis_supervisor",
    #     file_extra_JSON={"key": "value"},
    #     remarks="Forwarding to thesis supervisor",
    #     attached_file=None,
    # ) 

    # Get the thesis supervisor's User object
     

    # Send notification to the thesis  supervisor
    if(forwarded_hod):
        message = "Assistantship status received"
        otheracademic_notif(request.user,csehod_user , 'alert', ass_id, "student", message)

    # Display success message
        messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
        return redirect('/otheracademic/assitantship/thesis_approveform')



def assistanship_thesis_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.Ths_rejected = True
    leave_entry.save()
    messages.success(request, "Successfully rejected.")
    return redirect('/otheracademic/assitantship/thesis_approveform')


def assistanship_hod_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    acadadmin = User.objects.get(username='acadadmin')

    # Update TA_approved field to True
    leave_entry.HOD_approved = True
    leave_entry.save()
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    
    forwarded_acad = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver ='acadadmin', receiver_designation ="student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    message = "Assistantship status received"
    otheracademic_notif(request.user,acadadmin , 'alert', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/hod_approveform')



def assistanship_hod_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.HOD_rejected = True
    leave_entry.save()
    messages.success(request, "Successfully rejected.")
    
    return redirect('/otheracademic/assitantship/hod_approveform')


def assistantship_acad_approveform(request):
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")
    print(inbox)
    assistantship_ids = [msg['src_object_id'] for msg in inbox if msg['subject'] == 'assistantship']
    
    # Filter form_data queryset based on the ids found
    form_data = AssistantshipClaimFormStatusUpd.objects.filter(id__in=assistantship_ids)
    
    return render(request, 'otheracademic/acadadmin_approval.html', {'form_data': form_data})

def assistanship_acad_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    acadadmin = User.objects.get(username='acadadmin')

    # Update TA_approved field to True
    leave_entry.HOD_approved = True
    leave_entry.save()
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    
    
  
    message = "Assistantship status received"
    otheracademic_notif(request.user,acadadmin , 'alert', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/acad_approveform')



def assistanship_acad_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.Acad_rejected = True
    leave_entry.save()
    messages.success(request, "Successfully rejected.")
    
    return redirect('/otheracademic/assitantship/acad_approveform')


def assistanship_acad_approve(request, ass_id):
    # Obtain inbox data
    inbox = view_inbox(username=request.user.username, designation="student", src_module="otheracademic")

    # Find the object with the given ID from the AssistantshipClaimFormStatusUpd model
    leave_entry = get_object_or_404(AssistantshipClaimFormStatusUpd, id=ass_id)

    # Access the thesis_supervisor attribute of leave_entry
    print(leave_entry.thesis_supervisor)
    acadadmin = User.objects.get(username='acadadmin')

    # Update TA_approved field to True
    leave_entry.Acad_approved = True
    leave_entry.save()
    ass_id_from_inbox = find_id_from_inbox(inbox, ass_id)
    print(ass_id_from_inbox)
    a=get_object_or_404(User,username=request.user.username)
    y=ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    user_details=User.objects.get(id=y.user_id)
    des=HoldsDesignation.objects.filter(user=user_details).all()
    
    
    # forwarded_acad = create_file(uploader = request.user.username, uploader_designation=des[0].designation, receiver ='acadadmin', receiver_designation ="student", src_module = "otheracademic", src_object_id =ass_id, file_extra_JSON = {"value": 2}, attached_file = None,subject="assistantship")
  
    message = "Assistantship status received"
    otheracademic_notif(request.user,acadadmin , 'alert', ass_id, "student", message)

    # Display success message
    messages.success(request, "Successfully approved and forwarded.")

    # Redirect to the approveform page
    return redirect('/otheracademic/assitantship/hod_approveform')



def assistanship_acad_reject(request, ass_id):
    leave_entry = AssistantshipClaimFormStatusUpd.objects.get(id = ass_id)
    leave_entry.Acad_rejected = True
    leave_entry.save()
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


























    
