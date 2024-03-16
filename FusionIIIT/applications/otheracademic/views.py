from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
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
from .models import LeaveFormTable,BonafideFormTableUpdated,GraduateSeminarFormTable,AssistantshipClaimFormStatusUpd
from django.shortcuts import render, get_object_or_404
from datetime import date 

def otheracademic(request):
    return  render(request, "otheracademic/leaveform.html")



@csrf_exempt  # Exempt CSRF verification for this view
def leave_form_submit(request):
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')

        
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
                rejected=False,  # Initially not rejected
            )
        leave.save()
        # print(roll_no_id)
        return HttpResponseRedirect('/otheracademic')
    

def leaveApproveForm(request):
    
    form_data = LeaveFormTable.objects.all()
    return render(request, 'otheracademic/leaveformreciever.html', {'form_data': form_data})

def leaveStatus(request):
    
    form_data = LeaveFormTable.objects.all()
    return render(request, 'otheracademic/leaveStatus.html',{'form_data' : form_data })



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

def graduateseminar(request):
    return render(request,'otheracademic/graduateseminarForm.html')

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
    return render(request, 'otheracademic/graduateSeminarStatus.html',{'form_data' : form_data })

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
    
    form_data = BonafideFormTableUpdated.objects.all()
    return render(request, 'otheracademic/bonafideApprove.html', {'form_data': form_data})

def approve_bonafide(request, leave_id):
    file = request.FILES.get('related_document')
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.approve = True
    leave_entry.download_file = file
    leave_entry.save()
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after approval

def reject_bonafide(request, leave_id):
    leave_entry = BonafideFormTableUpdated.objects.get(id=leave_id)
    leave_entry.reject = True
    leave_entry.save()
    return redirect('/otheracademic/bonafideApproveForm')  # Redirect to appropriate page after rejection

def bonafideStatus(request):

    form_data = BonafideFormTableUpdated.objects.all()
    return render(request, 'otheracademic/bonafideStatus.html',{'form_data' : form_data })


# views.py




def upload_file(request, entry_id):
    if request.method == 'POST' and request.FILES.get('related_document'):
        related_document = request.FILES['related_document']
        
        # Assuming you want to update the 'download_file' field of your model
        bonafide_entry = get_object_or_404(BonafideFormTableUpdated, pk=entry_id)
        bonafide_entry.download_file = related_document
        bonafide_entry.save()
        
        return JsonResponse({'message': 'File uploaded successfully'}, status=200)
    else:
        return JsonResponse({'error': 'No file provided'}, status=400)


def assistantship(request):
    return render(request,'otheracademic/assistantshipclaimform.html')

def assistantship_form_submission(request):
    if request.method == 'POST':
        # Retrieve form data
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
        date_applied = request.POST.get('date_of_application')

        current_date = date.today()
        
        # Save form data to the database
        assistantship_claim = AssistantshipClaimFormStatusUpd(
            student_name=student_name,
            roll_no=request.user.extrainfo,
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
            Acad_rejected=False
        )
        assistantship_claim.save()
        
        # Redirect to a success page or return a success message
        return HttpResponseRedirect('/otheracademic/assistantship')  # Replace '/otheracademic/assistantship' with the actual URL you want to redirect to
    else:
        # Return an error response for invalid request method
        return HttpResponse('Invalid request method')


def assistantship_form_approval(request):
    # Retrieve data from the database
    form_data =AssistantshipClaimForm.objects.all()
    return render(request, 'otheracademic/assistantship_approval.html', {'form_data': form_data})


def nodues(request):
    return render(request,'otheracademic/noduesverification.html')
