import json
from django.shortcuts import render, get_object_or_404
from .models import *
from applications.globals.models import ExtraInfo
from applications.globals.models import *
from django.db.models import Q
from django.http import Http404
from .forms import EditDetailsForm, EditConfidentialDetailsForm, EditServiceBookForm, NewUserForm, AddExtraInfo
from django.contrib import messages
from applications.eis.models import *
from django.http import HttpResponse, HttpResponseRedirect
from applications.establishment.models import *
from applications.establishment.views import *
from applications.eis.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo, Designation

from html import escape
from io import BytesIO
import re
from rest_framework import status
from decimal import Decimal


from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import (get_object_or_404, redirect, render,
                              render)
from django.http import JsonResponse
from applications.filetracking.sdk.methods import *
from django.core.files.base import File as DjangoFile
from django.views.decorators.csrf import csrf_exempt


def edit_employee_details(request, id):
    """ Views for edit details"""
    template = 'hr2Module/editDetails.html'

    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Post does not exist")

    if request.method == "POST":
        for e in request.POST:
            print(e)
        print('--------------')
        form = EditDetailsForm(request.POST)
        conf_form = EditConfidentialDetailsForm(request.POST, request.FILES)
        print("f1", form.is_valid())
        print("f2", conf_form.is_valid())
        if form.is_valid() and conf_form.is_valid():
            form.save()
            conf_form.save()
            try:
                ee = ExtraInfo.objects.get(pk=id)
                ee.user_status = "PRESENT"
                ee.save()

            except:
                pass
            messages.success(request, "Employee details edited successfully")
        else:
            messages.warning(request, "Error in submitting form")
            pass
    else:
        print("Failed")

    form = EditDetailsForm(initial={'extra_info': employee.id})
    conf_form = EditConfidentialDetailsForm(initial={'extra_info': employee})
    context = {'form': form, 'confForm': conf_form, 'employee': employee}

    return render(request, template, context)


def hr_admin(request):
    """ Views for HR2 Admin page """

    user = request.user
    # extra_info = ExtraInfo.objects.select_related().get(user=user)
    designat = HoldsDesignation.objects.select_related().get(user=user)
    print(designat)
    if designat.designation.name == 'hradmin':
        template = 'hr2Module/hradmin.html'
        # searched employee
        query = request.GET.get('search')
        if(request.method == "GET"):
            if(query != None):
                emp = ExtraInfo.objects.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(id__icontains=query)
                ).distinct()
                emp = emp.filter(user_type="faculty")
            else:
                emp = ExtraInfo.objects.all()
                emp = emp.filter(user_type="faculty")
        else:
            emp = ExtraInfo.objects.all()
            emp = emp.filter(user_type="faculty")
        empPresent = emp.filter(user_status="PRESENT")
        empNew = emp.filter(user_status="NEW")
        context = {'emps': emp, "empPresent": empPresent, "empNew": empNew}
        print(context)
        return render(request, template, context)
    else:
        return HttpResponse('Unauthorized', status=401)


def service_book(request):
    """
    Views for service book page
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)

    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')
    appraisal_form = EmpAppraisalForm.objects.filter(
        extra_info=extra_info).order_by('-year')
    pf = extra_info.id
    workAssignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    empprojects = emp_research_projects.objects.filter(
        pf_no=pf).order_by('-start_date')
    visits = emp_visits.objects.filter(pf_no=pf).order_by('-entry_date')
    conferences = emp_confrence_organised.objects.filter(
        pf_no=pf).order_by('-date_entry')
    template = 'hr2Module/servicebook.html'
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    thesis = emp_mtechphd_thesis.objects.filter(
        pf_no=pf).order_by('-date_entry')
    context = {'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book,
               'appraisalForm': appraisal_form,
               'empproject': empprojects,
               'visits': visits,
               'conferences': conferences,
               'awards': awards,
               'thesis': thesis,
               'extrainfo': extra_info,
               'workAssignment': workAssignemnt,
               'awards': awards
               }

    return HttpResponseRedirect("/eis/profile/")
    # return render(request, template, context)


def view_employee_details(request, id):
    """ Views for edit details"""
    extra_info = ExtraInfo.objects.get(user__id=id)
    context = {}
    try:
        emp = Employee.objects.get(extra_info=extra_info)
        context['emp'] = emp
    except:
        print("Personal details not found")
    # try:
        
    # except:
    #     extra_info = ExtraInfo.objects.get(pk=id)
        # print("caught error")
        # return
    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')
    appraisal_form = EmpAppraisalForm.objects.filter(
        extra_info=extra_info).order_by('-year')
    pf = extra_info.user.id
    print(pf)
    workAssignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    empprojects = emp_research_projects.objects.filter(
        pf_no=pf).order_by('-start_date')
    visits = emp_visits.objects.filter(pf_no=pf).order_by('-entry_date')
    conferences = emp_confrence_organised.objects.filter(
        pf_no=pf).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    thesis = emp_mtechphd_thesis.objects.filter(
        pf_no=pf).order_by('-date_entry')

    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        handle_appraisal(request)

    if is_eligible(request):
        response.update(generate_appraisal_lists(request))

    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))

    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    response.update({'cpda': False, 'ltc': False,
                     'appraisal': True, 'leave': False})
    # designat = HoldsDesignation.objects.get(user=request.user).designation
    template = 'hr2Module/viewdetails.html'
    context.update({'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book, 'user': extra_info.user, 'extrainfo': extra_info,
               'appraisalForm': appraisal_form,
               'empproject': empprojects,
               'visits': visits,
               'conferences': conferences,
               'awards': awards,
               'thesis': thesis,
               'workAssignment': workAssignemnt,
            #    'designat':designat,
                
               })
    context.update(response)

    return render(request, template, context)


def edit_employee_servicebook(request, id):
    """ Views for edit Service Book details"""
    template = 'hr2Module/editServiceBook.html'

    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Post does not exist")

    if request.method == "POST":
        form = EditServiceBookForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(
                request, "Employee Service Book details edited successfully")
        else:
            messages.warning(request, "Error in submitting form")
            pass

    form = EditServiceBookForm(initial={'extra_info': employee.id})
    context = {'form': form, 'employee': employee
               }

    return render(request, template, context)


def administrative_profile(request, username=None):
    user = get_object_or_404(
        User, username=username) if username else request.user
    extra_info = get_object_or_404(ExtraInfo, user=user)
    if extra_info.user_type != 'faculty' and extra_info.user_type != 'staff':
        return redirect('/')
    pf = extra_info.id

    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')

    response = {}

    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        handle_appraisal(request)

    if is_eligible(request):
        response.update(generate_appraisal_lists(request))

    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))

    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    response.update({'cpda': False, 'ltc': False,
                     'appraisal': True, 'leave': False})
    workAssignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    context = {'user': user,
               'pf': pf,
               'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book,
               'extrainfo': extra_info,
               'workAssignment': workAssignemnt
               }

    context.update(response)
    template = 'hr2Module/dashboard_hr.html'
    return render(request, template, context)

def chkValidity(password):
    flag = 0
    while True:  
        if (len(password)<8):
            flag = -1
            break
        elif not re.search("[a-z]", password):
            flag = -1
            break
        elif not re.search("[0-9]", password):
            flag = -1
            break
        elif not re.search("[_@$]", password):
            flag = -1
            break
        elif re.search("\s", password):
            flag = -1
            break
        else:
            return True
            break
    
    if flag ==-1:
        return False

def add_new_user(request):
    """ Views for edit Service Book details"""
    template = 'hr2Module/add_new_employee.html'

    if request.method == "POST":
        form = NewUserForm(request.POST)
        eform = AddExtraInfo(request.POST)
      
        if form.is_valid():
            user = form.save()
            messages.success(request, "New User added Successfully")
        else:
            t_pass = '0000'
            if 'password1' in request.POST:
                t_pass = request.POST['password1']
            # messages.error(request,str(type(t_pass)))
            if chkValidity(t_pass):
                messages.error(request,"User already exists")
            elif not t_pass == '0000':
                messages.error(request,"Use Stronger Password")
            else:
                messages.error(request,"User already exists")
                

        if eform.is_valid():
            eform.save()
            messages.success(request, "Extra info of user saved successfully")
        elif not eform.is_valid:
            messages.error(request,"Some error occured")

    form = NewUserForm
    eform = AddExtraInfo

    try:
        employee = ExtraInfo.objects.all().first()
    except:
        raise Http404("Post does not exist")

    
    context = {'employee': employee, "register_form": form, "eform": eform
               }

    return render(request, template, context)



def ltc_pre_processing(request):
    data = {}
    detailsOfFamilyMembersAlreadyDone = ""

    for memeber in request.POST.getlist('detailsOfFamilyMembersAlreadyDone'):
        if(memeber == ""):
            detailsOfFamilyMembersAlreadyDone  = detailsOfFamilyMembersAlreadyDone + 'None' + ','
        else:
            detailsOfFamilyMembersAlreadyDone  = detailsOfFamilyMembersAlreadyDone + memeber + ','

    data['detailsOfFamilyMembersAlreadyDone'] = detailsOfFamilyMembersAlreadyDone.rstrip(',')


    detailsOfFamilyMembersAboutToAvail = ""

    for i in range(1,4):
        for j in range(1,4):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                detailsOfFamilyMembersAboutToAvail = detailsOfFamilyMembersAboutToAvail + 'None' + ','
            else:
                detailsOfFamilyMembersAboutToAvail = detailsOfFamilyMembersAboutToAvail + request.POST.get(key_is) + ','
    
    data['detailsOfFamilyMembersAboutToAvail'] = detailsOfFamilyMembersAboutToAvail.rstrip(',')


    detailsOfDependents = ""
    
    for i in range(1,7):
        for j in range(1,5):
            key_is = f'd_info_{i}_{j}'
            if(request.POST.get(key_is) == ""):
                detailsOfDependents = detailsOfDependents + 'None' + ','
            else:
                detailsOfDependents = detailsOfDependents + request.POST.get(key_is) + ','
    
    data['detailsOfDependents'] = detailsOfDependents.rstrip(',')

    return data


def reverse_ltc_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'blockYear',
    'pfNo',
    'basicPaySalary',
    'name',
    'designation',
    'departmentInfo',
    'leaveRequired',
    'leaveStartDate',
    'leaveEndDate',
    'dateOfDepartureForFamily',
    'natureOfLeave',
    'purposeOfLeave',
    'hometownOrNot',
    'placeOfVisit',
    'addressDuringLeave',
    'amountOfAdvanceRequired',
    'certifiedThatFamilyDependents',
    'certifiedThatAdvanceTakenOn',
    'adjustedMonth',
    'submissionDate',
    'phoneNumberForContact'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    # Reversing array-like values
    reversed_data['detailsOfFamilyMembersAlreadyDone'] = getattr(data,'detailsOfFamilyMembersAlreadyDone').split(',')
    
    detailsOfFamilyMembersAboutToAvail = getattr(data,'detailsOfFamilyMembersAboutToAvail').split(',')
    for index, value in enumerate(detailsOfFamilyMembersAboutToAvail):
        detailsOfFamilyMembersAboutToAvail[index] = value if value != 'None' else ''
    
    reversed_data['info_1_1'] = detailsOfFamilyMembersAboutToAvail[0]
    reversed_data['info_1_2'] = detailsOfFamilyMembersAboutToAvail[1]
    reversed_data['info_1_3'] = detailsOfFamilyMembersAboutToAvail[2]
    reversed_data['info_2_1'] = detailsOfFamilyMembersAboutToAvail[3]
    reversed_data['info_2_2'] = detailsOfFamilyMembersAboutToAvail[4]
    reversed_data['info_2_3'] = detailsOfFamilyMembersAboutToAvail[5]
    reversed_data['info_3_1'] = detailsOfFamilyMembersAboutToAvail[6]
    reversed_data['info_3_2'] = detailsOfFamilyMembersAboutToAvail[7]
    reversed_data['info_3_3'] = detailsOfFamilyMembersAboutToAvail[8]

    # # Reversing details_of_dependents
    detailsOfDependents = getattr(data,'detailsOfDependents').split(',')
    for i in range(1, 7):
        for j in range(1, 5):
            key = f'd_info_{i}_{j}'
            value = detailsOfDependents.pop(0)
            reversed_data[key] = value if value != 'None' else ''

    return reversed_data

def get_designation_by_user_id(user_id):
    try:
        # Query HoldsDesignation model to get the user's designation
        designation_objs = HoldsDesignation.objects.filter(user=user_id)
        return designation_objs.first().designation
    except ExtraInfo.DoesNotExist:
        return None
    except HoldsDesignation.DoesNotExist:
        return None

def search_employee(request):
    search_text = request.GET.get('search', '')
    data = {'designation': 'Assistant Professor'}
    try:

        employee = User.objects.get(username = search_text)
  
    
        holds_designation = HoldsDesignation.objects.filter(user=employee)
        holds_designation = list(holds_designation)


        
        data['designation'] = str(holds_designation[0].designation)
    except ExtraInfo.DoesNotExist:
        data = {'error': "Employee doesn't exist"}

    return JsonResponse(data)

def ltc_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")
    user_id = id
    creator = User.objects.get(id = user_id)
    
    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student'):
        template = 'hr2Module/ltc_form.html'

        if request.method == "POST":
            try:

                data = ltc_pre_processing(request)
            

                form1 = {
                    'employeeId': id,
                    'name': request.POST.get('name'),
                    'blockYear': request.POST.get('blockYear'),
                    'basicPaySalary': request.POST.get('basicPaySalary'),
                    'designation': request.POST.get('designation'),
                    'pfNo': request.POST.get('pfNo'),
                    'departmentInfo': request.POST.get('departmentInfo'),
                    'leaveRequired': request.POST.get('leaveRequired'),
                    'leaveStartDate': request.POST.get('leaveStartDate'),
                    'leaveEndDate': request.POST.get('leaveEndDate'),
                    'dateOfDepartureForFamily': request.POST.get('dateOfDepartureForFamily'),
                    'natureOfLeave': request.POST.get('natureOfLeave'),
                    'purposeOfLeave': request.POST.get('purposeOfLeave'),
                    'hometownOrNot': request.POST.get('hometownOrNot'),
                    'placeOfVisit': request.POST.get('placeOfVisit'),
                    'addressDuringLeave': request.POST.get('addressDuringLeave'),
                    'detailsOfFamilyMembersAlreadyDone': data['detailsOfFamilyMembersAlreadyDone'],
                    'detailsOfFamilyMembersAboutToAvail': data['detailsOfFamilyMembersAboutToAvail'],
                    'detailsOfDependents': data['detailsOfDependents'],
                    'amountOfAdvanceRequired': request.POST.get('amountOfAdvanceRequired'),
                    'certifiedThatFamilyDependents': request.POST.get('certifiedThatFamilyDependents'),
                    'certifiedThatAdvanceTakenOn': request.POST.get('certifiedThatAdvanceTakenOn'),
                    'adjustedMonth': request.POST.get('adjustedMonth'),
                    'submissionDate': request.POST.get('submissionDate'),
                    'phoneNumberForContact': request.POST.get('phoneNumberForContact'),
                    'username_employee': request.POST.get('username_employee'),
                    'designation_employee': request.POST.get('designation_employee'),
                    'created_by' : creator,
                             }


                try:
                    ltc_form = LTCform.objects.create(
                        employeeId=id,
                        name=request.POST.get('name'),
                        blockYear=request.POST.get('blockYear'),
                        pfNo=request.POST.get('pfNo'),
                        basicPaySalary=request.POST.get('basicPaySalary'),
                        designation=request.POST.get('designation'),
                        departmentInfo=request.POST.get('departmentInfo'),
                        leaveRequired=request.POST.get('leaveAvailability'),
                        leaveStartDate=request.POST.get('leaveStartDate'),
                        leaveEndDate=request.POST.get('leaveEndDate'),
                        dateOfDepartureForFamily=request.POST.get('dateOfLeaveForFamily'),
                        natureOfLeave=request.POST.get('natureOfLeave'),
                        purposeOfLeave=request.POST.get('purposeOfLeave'),
                        hometownOrNot=request.POST.get('hometownOrNot'),
                        placeOfVisit=request.POST.get('placeOfVisit'),
                        addressDuringLeave=request.POST.get('addressDuringLeave'),
                        detailsOfFamilyMembersAlreadyDone=data['detailsOfFamilyMembersAlreadyDone'],
                        detailsOfFamilyMembersAboutToAvail=data['detailsOfFamilyMembersAboutToAvail'],
                        detailsOfDependents=data['detailsOfDependents'],
                        amountOfAdvanceRequired=request.POST.get('amountOfAdvanceRequired'),
                        certifiedThatFamilyDependents=request.POST.get('certifiedThatFamilyDependents'),
                        certifiedThatAdvanceTakenOn=request.POST.get('certifiedThatAdvanceTakenOn'),
                        adjustedMonth=request.POST.get('adjustedMonth'),
                        submissionDate=request.POST.get('submissionDate'),
                        phoneNumberForContact=request.POST.get('phoneNumberForContact'),
                        created_by=creator,
                    )
                    
                except Exception as e:
                   
                    print("An error occurred while creating the LTC form:", e)




                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(ltc_form.id)
                file_extra_JSON = {"type": "LTC"}


                # Create a file representing the LTC form and send it to HR admin
                file_id = create_file(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    receiver=receiver,
                    receiver_designation=receiver_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=None  # Attach any file if necessary
                )


                messages.success(request, "Ltc form filled successfully!")


                return redirect(request.path_info)

            except Exception as e:
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

         # Query all LTC requests
        ltc_requests = LTCform.objects.filter(employeeId=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

      
        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")
        archived_files = view_archived(username = username, designation = uploader_designation, src_module = "HR")
        filtered_inbox = []
        for i in inbox:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'LTC':
                filtered_inbox.append(i)

        filtered_archived_files = []
        for i in archived_files:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'LTC':
                filtered_archived_files.append(i)


       



        context = {'employee': employee, 'ltc_requests': ltc_requests, 'inbox': filtered_inbox , 'designation':designation, 'archived_files': filtered_archived_files , 'user_id': user_id}

        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    
def form_view_ltc(request , id):
    ltc_request = get_object_or_404(LTCform, id=id)

    user_id = ltc_request.created_by.id

    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    template = 'hr2Module/view_ltc_form.html'
    ltc_request = reverse_ltc_pre_processing(ltc_request)
    
    context = {'ltc_request' : ltc_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation ,"id" : id, "user_id" : user_id}

    return render(request , template , context)

def track_file(request, id):
    # Assuming file_history is a list of dictionaries
    template = 'hr2Module/ltc_form_trackfile.html'
    file_history = view_history(file_id=id)


    context = {'file_history': file_history}

    # Create a JSON response
    return render(request ,template , context)

def get_current_file_owner(file_id: int) -> User:
    '''
    This functions returns the current owner of the file.
    The current owner is the latest recipient of the file
    '''
    latest_tracking = Tracking.objects.filter(
        file_id=file_id).order_by('-receive_date').first()
    latest_recipient = latest_tracking.receiver_id
    return latest_recipient

def file_handle_leave(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        remark = form_data['remark_id']
       

        #database
        leave_form = LeaveForm.objects.get(id=form_id)
        
        leave_form.save()

        #database
        try:
            leave_form = LeaveForm.objects.get(id=form_id)
        except LeaveForm.DoesNotExist:
            return JsonResponse({"error": "LeaveForm object with the provided ID does not exist"}, status=404)
        


        current_owner =  get_current_file_owner(file_id)

         #  if action value is 0 then forward the file
        #  if action value is 1 then reject the file
        #  if action value is 3 then approve the file
        #  otherwise archive the file

        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            messages.success(request, "File rejected successfully")
        elif(action == '2'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            leave_form.approved = True
            leave_form.approvedDate = timezone.now()
            leave_form.approved_by = current_owner
            leave_form.save()
            messages.success(request, "File approved successfully")
        else:
            is_archived = archive_file(file_id=file_id)
            if( is_archived ):
                messages.error(request, "Error in file archived")
            else:
                messages.success(request, "Success in file archived")

        
        return HttpResponse("Success")
    else:
       
        return HttpResponse("Failure")
    

def file_handle_cpda(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        advanceAmountPDA = form_data['advanceAmountPDA']
        balanceAvailable = form_data['balanceAvailable']
        amountCheckedInPDA = form_data['amountCheckedInPDA']

        remark = form_data['remark_id']
        #change


        #database
        try:
            cpda_form = CPDAAdvanceform.objects.get(id=form_id)
        except CPDAAdvanceform.DoesNotExist:
            return JsonResponse({"error": "CPDAform object with the provided ID does not exist"}, status=404)
        

        if advanceAmountPDA == "":
           advanceAmountPDA = None 
        else:
          advanceAmountPDA = Decimal(advanceAmountPDA)

        if balanceAvailable == "":
          balanceAvailable = None  
        else:
           balanceAvailable = Decimal(balanceAvailable)

        if amountCheckedInPDA == "":
           amountCheckedInPDA = None       
        else:
         amountCheckedInPDA = Decimal(amountCheckedInPDA)
  


        
        # Update the attribute
        setattr(cpda_form, "advanceAmountPDA", advanceAmountPDA)
        setattr(cpda_form, "balanceAvailable", balanceAvailable)
        setattr(cpda_form, "amountCheckedInPDA", amountCheckedInPDA)
        cpda_form.save()

        #database
        try:
            cpda_form = CPDAAdvanceform.objects.get(id=form_id)
        except CPDAAdvanceform.DoesNotExist:
            return JsonResponse({"error": "CPDAform object with the provided ID does not exist"}, status=404)
        

        current_owner =  get_current_file_owner(file_id)
     
         #  if action value is 0 then forward the file
        #  if action value is 1 then reject the file
        #  if action value is 3 then approve the file
        #  otherwise archive the file

        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            messages.success(request, "File rejected successfully")
        elif(action == '2'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            cpda_form.approved = True
            cpda_form.approvedDate = timezone.now()
            cpda_form.approved_by = current_owner
            cpda_form.save()
            messages.success(request, "File approved successfully")
        else:
            is_archived = archive_file(file_id=file_id)
            if( is_archived ):
                messages.error(request, "Error in file archived")
            else:
                messages.success(request, "Success in file archived")

        
        return HttpResponse("Success")
    else:
       
        return HttpResponse("Failure")

    

def file_handle_cpda_reimbursement(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        advanceDueAdjustment = form_data['advanceDueAdjustment']
        balanceAvailable = form_data['balanceAvailable']
        amountCheckedInPDA = form_data['amountCheckedInPDA']

        remark = form_data['remark_id']
        #change


        #database
        try:
            cpda_form = CPDAReimbursementform.objects.get(id=form_id)
        except CPDAReimbursementform.DoesNotExist:
            return JsonResponse({"error": "CPDAReimbursementform object with the provided ID does not exist"}, status=404)
        

        if advanceDueAdjustment == "":
           advanceDueAdjustment = None 
        else:
          advanceDueAdjustment = Decimal(advanceDueAdjustment)

        if balanceAvailable == "":
          balanceAvailable = None  
        else:
           balanceAvailable = Decimal(balanceAvailable)

        if amountCheckedInPDA == "":
           amountCheckedInPDA = None       
        else:
         amountCheckedInPDA = Decimal(amountCheckedInPDA)
  

        # Update the attribute
        setattr(cpda_form, "advanceDueAdjustment", advanceDueAdjustment)
        setattr(cpda_form, "balanceAvailable", balanceAvailable)
        setattr(cpda_form, "amountCheckedInPDA", amountCheckedInPDA)
        cpda_form.save()

        #database
        try:
            cpda_form = CPDAReimbursementform.objects.get(id=form_id)
        except CPDAReimbursementform.DoesNotExist:
            return JsonResponse({"error": "CPDAReimbursementform object with the provided ID does not exist"}, status=404)
        

        current_owner =  get_current_file_owner(file_id)
      
        #  if action value is 0 then forward the file
        #  if action value is 1 then reject the file
        #  if action value is 3 then approve the file
        #  otherwise archive the file

        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            messages.success(request, "File rejected successfully")
        elif(action == '2'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            cpda_form.approved = True
            cpda_form.approvedDate = timezone.now()
            cpda_form.approved_by = current_owner
            cpda_form.save()
            messages.success(request, "File approved successfully")
        else:
            is_archived = archive_file(file_id=file_id)
            if( is_archived ):
                messages.error(request, "Error in file archived")
            else:
                messages.success(request, "Success in file archived")

        
        return HttpResponse("Success")
    else:
       
        return HttpResponse("Failure")
    



def file_handle_ltc(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        remark = form_data['remark_id']
        #change


        #database
        try:
            ltc_form = LTCform.objects.get(id=form_id)
        except LTCform.DoesNotExist:
            return JsonResponse({"error": "LTCform object with the provided ID does not exist"}, status=404)
        

        ltc_form.save()
        

        current_owner =  get_current_file_owner(file_id)


        #  if action value is 0 then forward the file
        #  if action value is 1 then reject the file
        #  if action value is 3 then approve the file
        #  otherwise archive the file

        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            messages.success(request, "File rejected successfully")
        elif(action == '2'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            ltc_form.approved = True
            ltc_form.approvedDate = timezone.now()
            ltc_form.approved_by = current_owner
            ltc_form.save()
            messages.success(request, "File approved successfully")
        else:
            is_archived = archive_file(file_id=file_id)
            if( is_archived ):
                messages.error(request, "Error in file archived")
            else:
                messages.success(request, "Success in file archived")

        
        return HttpResponse("Success")
    else:
       
        return HttpResponse("Failure")

def file_handle_appraisal(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']
               

        remark = form_data['remark_id']
        try:
            appraisal_form = Appraisalform.objects.get(id=form_id)
        except Appraisalform.DoesNotExist:
            return JsonResponse({"error": "Appraisalform object with the provided ID does not exist"}, status=404)      

        
        # Update the attribute
        setattr(appraisal_form, "form_id", form_id)   
       
        appraisal_form.save()

        current_owner =  get_current_file_owner(file_id)
        
        #database
        try:
            appraisal_form = Appraisalform.objects.get(id=form_id)
        except Appraisalform.DoesNotExist:
            return JsonResponse({"error": "Appraisalform object with the provided ID does not exist"}, status=404)
        
         
        #  if action value is 0 then forward the file
        #  if action value is 1 then reject the file
        #  if action value is 3 then approve the file
        #  otherwise archive the file

        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            messages.success(request, "File rejected successfully")
        elif(action == '2'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            appraisal_form.approved = True
            appraisal_form.approvedDate = timezone.now()
            appraisal_form.approved_by = current_owner
            appraisal_form.save()
            messages.success(request, "File approved successfully")
        else:
            is_archived = archive_file(file_id=file_id)
            if( is_archived ):
                messages.error(request, "Error in file archived")
            else:
                messages.success(request, "Success in file archived")

        
        return HttpResponse("Success")
    else:
       
        return HttpResponse("Failure")


def view_ltc_form(request, id):
    ltc_request = get_object_or_404(LTCform, id=id)
    
    ltc_request = reverse_ltc_pre_processing(ltc_request)


    context = {
        'ltc_request': ltc_request
    }
    return render(request,'hr2Module/view_ltc_form.html',context)

def form_mangement_ltc(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        
        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context= {
            'ltc_requests' : ltc_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/ltc_form.html',context)
    

def form_mangement_ltc_hr(request,id):
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS181"
    receiver_designation = "HOD"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the LTC form and send it to HR admin
    file_id = create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        attached_file=None  # Attach any file if necessary
    )


    messages.success(request, "Ltc form filled successfully")

    return HttpResponse("Sucess")

def form_mangement_ltc_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        
        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context= {
            'ltc_requests' : ltc_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/ltc_form.html',context)



@login_required(login_url='/accounts/login')
def dashboard(request):
    user = request.user

    user_id = ExtraInfo.objects.get(user=user).user_id
    context = {'user_id': user_id}
    return render(request, 'hr2Module/dashboard.html',context)


# cpda form -----------------------------------------------------------

def reverse_cpda_pre_processing(data):
    reversed_data = {}

    simple_keys = [
        'name', 'designation', 'pfNo', 'purpose', 'amountRequired', 'advanceDueAdjustment',
        'submissionDate',
        'balanceAvailable', 'advanceAmountPDA' ,'amountCheckedInPDA',
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    return reversed_data


def cpda_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")
    
    user_id = id
    creator = User.objects.get(id = user_id)
     
    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student' ):
        template = 'hr2Module/cpda_form.html'

        if request.method == "POST":
            try:
                advanceAmountPDA = request.POST.get('advanceAmountPDA')
                if advanceAmountPDA == "":
                   advanceAmountPDA = None 
                else:
                   advanceAmountPDA = Decimal(advanceAmountPDA)

                balanceAvailable = request.POST.get('balanceAvailable')
                if balanceAvailable == "":
                   balanceAvailable = None  
                else:
                    balanceAvailable = Decimal(balanceAvailable)

                amountCheckedInPDA = request.POST.get('amountCheckedInPDA')
                if amountCheckedInPDA == "":
                    amountCheckedInPDA = None       
                else:
                    amountCheckedInPDA = Decimal(amountCheckedInPDA)


                form_2 = {
                    'employeeId' : id,
                    'name' : request.POST.get('name'),
                    'designation' :  request.POST.get('designation'),
                    'pfNo' : request.POST.get('pfNo'),
                    'purpose' : request.POST.get('purpose'),
                    'amountRequired' : request.POST.get('amountRequired'),
                    'advanceDueAdjustment' : request.POST.get('advanceDueAdjustment'),
                    'submissionDate' : request.POST.get('submissionDate'),
                    'balanceAvailable' : request.POST.get('balanceAvailable'),
                    'advanceAmountPDA' : request.POST.get('advanceAmountPDA'),
                    'amountCheckedInPDA' : request.POST.get('amountCheckedInPDA'),
                    'created_by' : creator,
                }
                
                cpda_form = CPDAAdvanceform.objects.create(
                    employeeId = id, 
                    name = request.POST.get('name'),
                    designation = request.POST.get('designation'),
                    pfNo = request.POST.get('pfNo'), 
                    purpose = request.POST.get('purpose'),
                    amountRequired = request.POST.get('amountRequired'),  
                    advanceDueAdjustment = request.POST.get('advanceDueAdjustment'),  
                    submissionDate = request.POST.get('submissionDate'),  
                    balanceAvailable = request.POST.get('balanceAvailable'),  
                    advanceAmountPDA = request.POST.get('advanceAmountPDA'), 
                    amountCheckedInPDA = request.POST.get('amountCheckedInPDA'),  
                    created_by=creator,

                )


                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR" #dikkat 
                src_object_id = str(cpda_form.id)
                file_extra_JSON = {"type": "CPDAAdvance"}

                # Create a file representing the CPDA form 
                file_id = create_file(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    receiver=receiver,
                    receiver_designation=receiver_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=None  # Attach any file if necessary
                )

             

                messages.success(request, "CPDA form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

        cpda_requests = CPDAAdvanceform.objects.filter(employeeId=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'


        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        archived_files = view_archived(username = username, designation = uploader_designation, src_module = "HR")

        filtered_inbox = []
        for i in inbox:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'CPDAAdvance':
                filtered_inbox.append(i)

        filtered_archived_files = []
        for i in archived_files:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'CPDAAdvance':
                filtered_archived_files.append(i)

        context = {'employee': employee, 'cpda_requests': cpda_requests, 'inbox': filtered_inbox , 'designation':designation, 'archived_files': filtered_archived_files,'user_id':user_id}


        messages.success(request, "CPDA form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    

def form_view_cpda(request , id):
    cpda_request = get_object_or_404(CPDAAdvanceform, id=id)
    user_id = cpda_request.created_by.id
    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')



    template = 'hr2Module/view_cpda_form.html'
    cpda_request = reverse_cpda_pre_processing(cpda_request)
    
    context = {'cpda_request' : cpda_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation,"id":id,"user_id":user_id}

    return render(request , template , context)


def view_cpda_form(request, id):
    cpda_request = get_object_or_404(CPDAAdvanceform, id=id)
   
    cpda_request = reverse_cpda_pre_processing(cpda_request)


    context = {
        'cpda_request': cpda_request
    }
    return render(request,'hr2Module/view_cpda_form.html',context)


def form_mangement_cpda(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        
        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAAdvanceform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context= {
            'cpda_requests' : cpda_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/cpda_form.html',context)
    
def form_mangement_cpda_hr(request,id):
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS181"
    receiver_designation = "HOD"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the CPDA form and send it to HR admin
    file_id = create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        attached_file=None  # Attach any file if necessary
    )


    messages.success(request, "CPda form filled successfully")


    return HttpResponse("Success")


def form_mangement_cpda_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        
        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAAdvanceform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context= {
            'cpda_requests' : cpda_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/cpda_form.html',context)
    

#  Leave form -------------------------------------------------------------
    
def reverse_leave_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'name', 'designation', 'submissionDate', 'pfNo', 'departmentInfo', 'natureOfLeave',
        'leaveStartDate', 'leaveEndDate', 'purposeOfLeave', 'addressDuringLeave', 'academicResponsibility',
        'addministrativeResponsibiltyAssigned'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    return reversed_data

    
def leave_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    user_id = id
    creator = User.objects.get(id = user_id)
    
    if(employee.user_type == 'faculty' or employee.user_type == 'student' or employee.user_type == 'staff'):
        template = 'hr2Module/leave_form.html'

        if request.method == "POST":
            try:


                form_3 = {
                    'employeeId' : id,
                    'name' : request.POST.get('name'),
                    'designation' :  request.POST.get('designation'),
                    'submissionDate' : request.POST.get('submissionDate'),
                    'pfNo' : request.POST.get('pfNo'),
                    'departmentInfo' : request.POST.get('departmentInfo'),
                    'natureOfLeave' : request.POST.get('natureOfLeave'),
                    'leaveStartDate' : request.POST.get('leaveStartDate'),
                    'leaveEndDate' : request.POST.get('leaveEndDate'),
                    'purposeOfLeave' : request.POST.get('purposeOfLeave'),
                    'addressDuringLeave' : request.POST.get('addressDuringLeave'),
                    'academicResponsibility' : request.POST.get('academicResponsibility'),
                    'addministrativeResponsibiltyAssigned' : request.POST.get('addministrativeResponsibiltyAssigned'),
                    'created_by' : creator,
                }
                
                leave_form = LeaveForm.objects.create(
                    employeeId = id,
                    name = request.POST.get('name'),
                    designation =  request.POST.get('designation'),
                    submissionDate = request.POST.get('submissionDate'),
                    pfNo = request.POST.get('pfNo'),
                    departmentInfo = request.POST.get('departmentInfo'),
                    leaveStartDate = request.POST.get('leaveStartDate'),
                    leaveEndDate = request.POST.get('leaveEndDate'),
                    natureOfLeave = request.POST.get('natureOfLeave'),
                    purposeOfLeave = request.POST.get('purposeOfLeave'),
                    addressDuringLeave = request.POST.get('addressDuringLeave'),
                    academicResponsibility = request.POST.get('academicResponsibility'),
                    addministrativeResponsibiltyAssigned = request.POST.get('addministrativeResponsibiltyAssigned'),
                    created_by=creator,
                )
            

                uploader = employee.user
                uploader_designation = 'Assistant Professor'


                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(leave_form.id)
                file_extra_JSON = {"type": "Leave"}


                # Create a file representing the CPDA form 
                file_id = create_file(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    receiver=receiver,
                    receiver_designation=receiver_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=None  # Attach any file if necessary
                )


                messages.success(request, "Leave form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

         # Query all Leave requests
        leave_requests = LeaveForm.objects.filter(employeeId=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        archived_files = view_archived(username = username, designation = uploader_designation, src_module = "HR")

        filtered_inbox = []
        for i in inbox:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'Leave':
                filtered_inbox.append(i)

        filtered_archived_files = []
        for i in archived_files:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'Leave':
                filtered_archived_files.append(i)



        context = {'employee': employee, 'leave_requests': leave_requests, 'inbox': filtered_inbox , 'designation':designation, 'archived_files': filtered_archived_files,'user_id':user_id}

        messages.success(request, "Leave form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')



def form_view_leave(request , id):

    leave_request = get_object_or_404(LeaveForm, id=id)
    user_id = leave_request.created_by.id
    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')


    template = 'hr2Module/view_leave_form.html'
    leave_request = reverse_leave_pre_processing(leave_request)
    
    context = {'leave_request' : leave_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation, "id" : id,"user_id":user_id}

    return render(request , template , context)

# ek or bna lena
def view_leave_form(request, id):
    leave_request = get_object_or_404(LeaveForm, id=id)

    
    
    leave_request = reverse_leave_pre_processing(leave_request)


    context = {
        'leave_request': leave_request
    }
    return render(request,'hr2Module/view_leave_form.html',context)


def form_mangement_leave(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        leave_requests = []

        for src_object_id in src_object_ids:
            leave_request = get_object_or_404(LeaveForm, id=src_object_id)
            leave_requests.append(leave_request)

        context= {
            'leave_requests' : leave_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/leave_form.html',context)
    

def form_mangement_leave_hr(request,id):
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS181"
    receiver_designation = "HOD"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the Leave form and send it to HR admin
    file_id = create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        attached_file=None  # Attach any file if necessary
    )


    messages.success(request, "Leave form filled successfully")

    return HttpResponse("Sucess")

def form_mangement_leave_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        
        leave_requests = []

        for src_object_id in src_object_ids:
            leave_request = get_object_or_404(LeaveForm, id=src_object_id)
            leave_requests.append(leave_request)

        context= {
            'leave_requests' : leave_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/leave_form.html',context)
    

    
def appraisal_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    user_id = id
    creator = User.objects.get(id = user_id)
    
    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student'):
        template = 'hr2Module/appraisal_form.html'

        if request.method == "POST":
            try:

                data = appraisal_pre_processing(request)
               

                form_4 = {
                    'employeeId': id,
                    'name': request.POST.get('name'),
                    'designation': request.POST.get('designation'),
                    'disciplineInfo': request.POST.get('disciplineInfo'),
                    'specificFieldOfKnowledge': request.POST.get('specificFieldOfKnowledge'),
                    'currentResearchInterests': request.POST.get('currentResearchInterests'),
                    'coursesTaught': data['coursesTaught'],
                    'newCoursesIntroduced': data['newCoursesIntroduced'],
                    'newCoursesDeveloped': data['newCoursesDeveloped'],
                    'otherInstructionalTasks': request.POST.get('otherInstructionalTasks'),
                    'thesisSupervision': data['thesisSupervision'],
                    'sponsoredReseachProjects': data['sponsoredReseachProjects'],
                    'otherResearchElement': request.POST.get('otherResearchElement'),
                    'publication': request.POST.get('publication'),
                    'referredConference': request.POST.get('referredConference'),
                    'conferenceOrganised': request.POST.get('conferenceOrganised'),
                    'membership': request.POST.get('membership'),
                    'honours ' :   request.POST.get('honours'),
                    'editorOfPublications':  request.POST.get('editorOfPublications'),
                    'expertLectureDelivered': request.POST.get('expertLectureDelivered'),
                    'membershipOfBOS': request.POST.get('membershipOfBOS'),
                    'otherExtensionTasks': request.POST.get('otherExtensionTasks'),
                    'administrativeAssignment': request.POST.get('administrativeAssignment'),
                    'serviceToInstitute': request.POST.get('serviceToInstitute'),
                    'otherContribution': request.POST.get('otherContribution'),
                    'performanceComments' : request.POST.get('performanceComments'),
                    'submissionDate' : request.POST.get('submissionDate'),
                    'approved' : request.POST.get('approved'),
                    'approvedDate' : request.POST.get('approvedDate'),
                    'created_by' : creator,
                    
                }


                appraisal_form = Appraisalform.objects.create(
                    employeeId= id,
                    name= request.POST.get('name'),
                    designation= request.POST.get('designation'),
                    disciplineInfo= request.POST.get('disciplineInfo'),
                    specificFieldOfKnowledge= request.POST.get('specificFieldOfKnowledge'),
                    currentResearchInterests= request.POST.get('currentResearchInterests'),
                    coursesTaught= data['coursesTaught'],
                    newCoursesIntroduced= data['newCoursesIntroduced'],
                    newCoursesDeveloped= data['newCoursesDeveloped'],
                    otherInstructionalTasks= request.POST.get('otherInstructionalTasks'),
                    thesisSupervision= data['thesisSupervision'],
                    sponsoredReseachProjects= data['sponsoredReseachProjects'],
                    otherResearchElement= request.POST.get('otherResearchElement'),
                    publication= request.POST.get('publication'),
                    referredConference= request.POST.get('referredConference'),
                    conferenceOrganised= request.POST.get('conferenceOrganised'),
                    membership= request.POST.get('membership'),
                    honours  = request.POST.get('honours'),
                    editorOfPublications= request.POST.get('editorOfPublications'),
                    expertLectureDelivered= request.POST.get('expertLectureDelivered'),
                    membershipOfBOS= request.POST.get('membershipOfBOS'),
                    otherExtensionTasks= request.POST.get('otherExtensionTasks'),
                    administrativeAssignment= request.POST.get('administrativeAssignment'),
                    serviceToInstitute= request.POST.get('serviceToInstitute'),
                    otherContribution= request.POST.get('otherContribution'),
                    performanceComments = request.POST.get('performanceComments'),
                    submissionDate = request.POST.get('submissionDate'),
                    approved = request.POST.get('approved'),
                    approvedDate = request.POST.get('approvedDate'),
                    created_by=creator,
                      
                
                )

                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(appraisal_form.id)
                file_extra_JSON = {"type": "Appraisal"}

               
                # Create a file representing the AppraisL form and send it to HR admin
                file_id = create_file(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    receiver=receiver,
                    receiver_designation=receiver_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=None  # Attach any file if necessary
                )


                messages.success(request, "Appraisal form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

        appraisal_requests = Appraisalform.objects.filter(employeeId=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

       

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        archived_files = view_archived(username = username, designation = uploader_designation, src_module = "HR")

        filtered_inbox = []
        for i in inbox:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'Appraisal':
                filtered_inbox.append(i)

        filtered_archived_files = []
        for i in archived_files:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'Appraisal':
                filtered_archived_files.append(i)


        context = {'employee': employee, 'appraisal_requests': appraisal_requests, 'inbox': filtered_inbox , 'designation':designation, 'archived_files': filtered_archived_files,'user_id':user_id}

        messages.success(request, "Appraisal form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    

   
def form_view_appraisal(request , id):
    appraisal_request = get_object_or_404(Appraisalform, id=id)
    user_id = appraisal_request.created_by.id
    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')


    template = 'hr2Module/view_appraisal_form.html'
    appraisal_request = reverse_appraisal_pre_processing(appraisal_request)
    
    context = {'appraisal_request' : appraisal_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation,"id":id,"user_id":user_id}

    return render(request , template , context)


def view_appraisal_form(request, id):
    appraisal_request = get_object_or_404(Appraisalform, id=id)
    
   
    appraisal_request = reverse_appraisal_pre_processing(appraisal_request)

    context = {
        'appraisal_request': appraisal_request
    }
    return render(request,'hr2Module/view_appraisal_form.html',context)



def form_mangement_appraisal(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

       
        src_object_ids = [item['src_object_id'] for item in inbox]
        
        appraisal_requests = []

        for src_object_id in src_object_ids:
            appraisal_request = get_object_or_404(Appraisalform, id=src_object_id)
            appraisal_requests.append(appraisal_request)

        context= {
            'appraisal_requests' : appraisal_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/appraisal_form.html',context)


def form_mangement_appraisal_hr(request,id):
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS181"
    receiver_designation = "HOD"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the Appraisal form and send it to HR admin
    file_id = create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        attached_file=None  # Attach any file if necessary
    )


    messages.success(request, "Appraisal form filled successfully")

    return HttpResponse("Sucess")    


    
def appraisal_pre_processing(request):
    data = {}
    

    coursesTaught = ""

    for i in range(1,3):
        for j in range(1,8):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                coursesTaught = coursesTaught + 'None' + ','
            else:
                coursesTaught = coursesTaught + request.POST.get(key_is) + ','
    
    data['coursesTaught'] = coursesTaught.rstrip(',')

    newCoursesIntroduced = ""

    for i in range(3,5):
        for j in range(1,4):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                newCoursesIntroduced = newCoursesIntroduced + 'None' + ','
            else:
                newCoursesIntroduced = newCoursesIntroduced + request.POST.get(key_is) + ','
    
    data['newCoursesIntroduced'] = newCoursesIntroduced.rstrip(',')


    newCoursesDeveloped = ""

    for i in range(5,7):
        for j in range(1,5):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                newCoursesDeveloped = newCoursesDeveloped + 'None' + ','
            else:
                newCoursesDeveloped = newCoursesDeveloped + request.POST.get(key_is) + ','
    
    data['newCoursesDeveloped'] = newCoursesDeveloped.rstrip(',')

    thesisSupervision = ""

    for i in range(7,9):
        for j in range(1,6):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                thesisSupervision = thesisSupervision + 'None' + ','
            else:
                thesisSupervision = thesisSupervision + request.POST.get(key_is) + ','
    
    data['thesisSupervision'] = thesisSupervision.rstrip(',')



    sponsoredReseachProjects = ""

    for i in range(9,10):
        for j in range(1,8):
            key_is = f'info_{i}_{j}'
            
            if(request.POST.get(key_is) == ""):
                sponsoredReseachProjects = sponsoredReseachProjects + 'None' + ','
            else:
                sponsoredReseachProjects = sponsoredReseachProjects + request.POST.get(key_is) + ','
    
    data['sponsoredReseachProjects'] = sponsoredReseachProjects.rstrip(',')


    return data




def reverse_appraisal_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'name', 'designation', 'disciplineInfo', 'specificFieldOfKnowledge', 'designation', 'currentResearchInterests',
        'otherInstructionalTasks', 'otherResearchElement', 'publication', 'referredConference',
        'conferenceOrganised', 'membership', 'honours', 'editorOfPublications', 
        'expertLectureDelivered', 'membershipOfBOS', 'otherExtensionTasks',
        'administrativeAssignment', 'serviceToInstitute', 'otherContribution', 'performanceComments',
        'submissionDate'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''
    
    courses_taught = getattr(data,'coursesTaught').split(',')
    for index, value in enumerate(courses_taught):
        courses_taught[index] = value if value != 'None' else ''
    
    reversed_data['info_1_1'] = courses_taught[0]
    reversed_data['info_1_2'] = courses_taught[1]
    reversed_data['info_1_3'] = courses_taught[2]
    reversed_data['info_1_4'] = courses_taught[3]
    reversed_data['info_1_5'] = courses_taught[4]
    reversed_data['info_1_6'] = courses_taught[5]
    reversed_data['info_1_7'] = courses_taught[6]
    reversed_data['info_2_1'] = courses_taught[7]
    reversed_data['info_2_2'] = courses_taught[8]
    reversed_data['info_2_3'] = courses_taught[9]
    reversed_data['info_2_4'] = courses_taught[10]
    reversed_data['info_2_5'] = courses_taught[11]
    reversed_data['info_2_6'] = courses_taught[12]
    reversed_data['info_2_7'] = courses_taught[13]

    # # Reversing details_of_dependents
    new_courses_introduced = getattr(data,'newCoursesIntroduced').split(',')
    for i in range(3, 5):
        for j in range(1, 4):
            key = f'info_{i}_{j}'
            value = new_courses_introduced.pop(0)
            reversed_data[key] = value if value != 'None' else ''
        

        
    newCoursesDeveloped = getattr(data,'newCoursesDeveloped').split(',')
    for i in range(5, 7):
        for j in range(1, 5):
            key = f'info_{i}_{j}'
            value = newCoursesDeveloped.pop(0)
            reversed_data[key] = value if value != 'None' else ''



    thesis_reasearch = getattr(data,'otherResearchElement').split(',')
    for i in range(7, 9):
        for j in range(1, 6):
            key = f'info_{i}_{j}'
            if thesis_reasearch:
               value = thesis_reasearch.pop()
            else:
    # Handle the case where the list is empty
                print("The list is empty, cannot pop from it.")
            # value = thesis_reasearch.pop(0)
            reversed_data[key] = value if value != 'None' else ''



    sponsored_research = getattr(data,'sponsoredReseachProjects').split(',')
    for i in range(9, 10):
        for j in range(1, 8):
            key = f'info_{i}_{j}'
            value = sponsored_research.pop(0)
            reversed_data[key] = value if value != 'None' else ''

    return reversed_data



def reverse_cpda_reimbursement_pre_processing(data):
    reversed_data = {}

    simple_keys = [
        'name', 'designation', 'pfNo', 'purpose', 'advanceTaken', 'adjustmentSubmitted',
        'submissionDate',
        'balanceAvailable', 'advanceDueAdjustment', 'amountCheckedInPDA', 
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    return reversed_data


def cpda_reimbursement_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")
    
    user_id = id
    creator = User.objects.get(id = user_id)

    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student' ):
        template = 'hr2Module/cpda_reimbursement_form.html'

        if request.method == "POST":
            try:

                form_2 = {
                    'employeeId' : id,
                    'name' : request.POST.get('name'),
                    'designation' :  request.POST.get('designation'),
                    'pfNo' : request.POST.get('pfNo'),
                    'purpose' : request.POST.get('purpose'),
                    'advanceTaken' : request.POST.get('advanceTaken'),
                    'advanceDueAdjustment' : request.POST.get('advanceDueAdjustment'),
                    'submissionDate' : request.POST.get('submissionDate'),
                    'balanceAvailable' : request.POST.get('balanceAvailable'),
                    'adjustmentSubmitted' : request.POST.get('adjustmentSubmitted'),
                    'amountCheckedInPDA' : request.POST.get('amountCheckedInPDA'),
                    'created_by' : creator,
                }
                
                cpda_form = CPDAReimbursementform.objects.create(
                    employeeId = id, 
                    name = request.POST.get('name'),
                    designation = request.POST.get('designation'),
                    pfNo = request.POST.get('pfNo'), 
                    purpose = request.POST.get('purpose'),
                    advanceTaken = request.POST.get('advanceTaken'),  
                    advanceDueAdjustment = request.POST.get('advanceDueAdjustment'),  
                    submissionDate = request.POST.get('submissionDate'),  
                    balanceAvailable = request.POST.get('balanceAvailable'),  
                    adjustmentSubmitted = request.POST.get('adjustmentSubmitted'), 
                    amountCheckedInPDA = request.POST.get('amountCheckedInPDA'),  
                    created_by=creator,

                )


                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR" 
                src_object_id = str(cpda_form.id)
                file_extra_JSON = {"type": "CPDAReimbursement"}

                # Create a file representing the CPDA form 
                file_id = create_file(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    receiver=receiver,
                    receiver_designation=receiver_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=None  # Attach any file if necessary
                )

                messages.success(request, "cpdareimbursement form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

        cpda_reimbursement_requests = CPDAReimbursementform.objects.filter(employeeId=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'


        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        archived_files = view_archived(username = username, designation = uploader_designation, src_module = "HR")

        filtered_inbox = []
        for i in inbox:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'CPDAReimbursement':
                filtered_inbox.append(i)

        filtered_archived_files = []
        for i in archived_files:
            item = i.get('file_extra_JSON', {})  
            if item.get('type') == 'CPDAReimbursement':
                filtered_archived_files.append(i)


        context = {'employee': employee, 'cpda_reimbursement_requests': cpda_reimbursement_requests, 'inbox': filtered_inbox , 'designation':designation, 'archived_files': filtered_archived_files,'user_id':user_id}


        messages.success(request, "cpdareimbursement form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    



def form_view_cpda_reimbursement(request , id):
    cpda_reimbursement_request = get_object_or_404(CPDAReimbursementform, id=id)
    user_id = cpda_reimbursement_request.created_by.id
    # isko recheck krna h
    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    template = 'hr2Module/view_cpda_reimbursement_form.html'
    cpda_reimbursement_request = reverse_cpda_reimbursement_pre_processing(cpda_reimbursement_request)
    
    context = {'cpda_reimbursement_request' : cpda_reimbursement_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation,"id":id,"user_id":user_id}

    return render(request , template , context)


def view_cpda_reimbursement_form(request, id):
    cpda_reimbursement_request = get_object_or_404(CPDAReimbursementform, id=id)
   
    cpda_reimbursement_request = reverse_cpda_reimbursement_pre_processing(cpda_reimbursement_request)

    context = {
        'cpda_reimbursement_request': cpda_reimbursement_request
    }
    return render(request,'hr2Module/view_cpda_reimbursement_form.html',context)



def form_mangement_cpda_reimbursement(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        
        cpda_reimbursement_requests = []

        for src_object_id in src_object_ids:
            cpda_reimbursement_request = get_object_or_404(CPDAReimbursementform, id=src_object_id)
            cpda_reimbursement_requests.append(cpda_reimbursement_request)

        context= {
            'cpda_reimbursement_requests' : cpda_reimbursement_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/cpda_reimbursement_form.html',context)
    
def form_mangement_cpda_reimbursement_hr(request,id):
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS181"
    receiver_designation = "HOD"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the CPDA form and send it to HR admin
    file_id = create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        attached_file=None  # Attach any file if necessary
    )


    messages.success(request, "CPda form filled successfully")


    return HttpResponse("Success")


def form_mangement_cpda_reimbursement_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")


        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]

        
        cpda_reimbursement_requests = []

        for src_object_id in src_object_ids:
            cpda_reimbursement_request = get_object_or_404(CPDAReimbursementform, id=src_object_id)
            cpda_reimbursement_requests.append(cpda_reimbursement_request)

        context= {
            'cpda_reimbursement_requests' : cpda_reimbursement_requests,
            'hr' : "1",
        }


        return render(request, 'hr2Module/cpda_reimbursement_form.html',context)
    

def getform(request):
    form_type = request.GET.get("type")
    id = request.GET.get("id")

    if form_type == "LTC":
        try:
            forms = LTCform.objects.filter(created_by=id)
            
            form_data = []
            for form in forms:
                form_data.append({
                    'id': form.id,
                    'name': form.name,
                    'designation': form.designation,
                    'submissionDate': form.submissionDate.strftime("%Y-%m-%d") if form.submissionDate else None,
                    'is_approved' : form.approved,
                    
                })

            return JsonResponse(form_data, safe=False)  # Return JSON response
        except LTCform.DoesNotExist:
            return JsonResponse({"message": "No LTC forms found."}, status=404)
        
def getformcpdaAdvance(request):
    form_type = request.GET.get("type")
    id = request.GET.get("id")

    if form_type == "CPDAAdvance":
        try:
            forms = CPDAAdvanceform.objects.filter(created_by=id)
            form_data = []
            for form in forms:
                form_data.append({
                    'id': form.id,
                    'name': form.name,
                    'designation': form.designation,
                    'submissionDate': form.submissionDate.strftime("%Y-%m-%d") if form.submissionDate else None,
                    'is_approved' : form.approved,
                })

            return JsonResponse(form_data, safe=False)  # Return JSON response
        except CPDAAdvanceform.DoesNotExist:
            return JsonResponse({"message": "No CPDAAdvance forms found."}, status=404)        
        

def getformLeave(request):
    form_type = request.GET.get("type")
    id = request.GET.get("id")

    if form_type == "Leave":
        try:
            forms = LeaveForm.objects.filter(created_by=id)
            form_data = []
            for form in forms:
                form_data.append({
                    'id': form.id,
                    'name': form.name,
                    'designation': form.designation,
                    'submissionDate': form.submissionDate.strftime("%Y-%m-%d") if form.submissionDate else None,
                    'is_approved' : form.approved,
                    # Add other fields as needed
                })

            return JsonResponse(form_data, safe=False)  # Return JSON response
        except LeaveForm.DoesNotExist:
            return JsonResponse({"message": "No Leave forms found."}, status=404)    


def getformAppraisal(request):
    form_type = request.GET.get("type")
    id = request.GET.get("id")

    if form_type == "Appraisal":
        try:
            forms = Appraisalform.objects.filter(created_by=id)
            form_data = []
            for form in forms:
                form_data.append({
                    'id': form.id,
                    'name': form.name,
                    'designation': form.designation,
                    'submissionDate': form.submissionDate.strftime("%Y-%m-%d") if form.submissionDate else None,
                    'is_approved' : form.approved,
                })

            return JsonResponse(form_data, safe=False)  # Return JSON response
        except Appraisalform.DoesNotExist:
            return JsonResponse({"message": "No Appraisal forms found."}, status=404)        
        


def getformcpdaReimbursement(request):
    form_type = request.GET.get("type")
    id = request.GET.get("id")

    if form_type == "CPDAReimbursement":
        try:
            forms = CPDAReimbursementform.objects.filter(created_by=id)
            form_data = []
            for form in forms:
                form_data.append({
                    'id': form.id,
                    'name': form.name,
                    'designation': form.designation,
                    'submissionDate': form.submissionDate.strftime("%Y-%m-%d") if form.submissionDate else None,
                    'is_approved' : form.approved,
                    # Add other fields as needed
                })

            return JsonResponse(form_data, safe=False)  # Return JSON response
        except CPDAReimbursementform.DoesNotExist:
            return JsonResponse({"message": "No CPDAReimbursement forms found."}, status=404)        



