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
from applications.filetracking.models import Tracking
from html import escape
from io import BytesIO
import re
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
        # t_pass = request.POST['password1']
        # t_user = request.POST['username']

        if form.is_valid():
            user = form.save()
            messages.success(request, "New User added Successfully")
        else:
            print(form.errors)
            # print(request.POST['password1'])
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
            print(eform.errors)
            messages.error(request,"Some error occured")

    form = NewUserForm
    eform = AddExtraInfo

    try:
        employee = ExtraInfo.objects.all().first()
    except:
        raise Http404("Post does not exist")

    # if request.method == "POST":
    #     form = EditServiceBookForm(request.POST, request.FILES)

    #     if form.is_valid():
    #         form.save()
    #         messages.success(
    #             request, "Employee Service Book details edited successfully")
    #     else:
    #         messages.warning(request, "Error in submitting form")
    #         pass

    # form = EditServiceBookForm(initial={'extra_info': employee.id})
    context = {'employee': employee, "register_form": form, "eform": eform
               }

    return render(request, template, context)

# def ltc_form(request, id):
#     """ Views for edit details"""
#     try:
#         employee = ExtraInfo.objects.get(user__id=id)
#     except:
#         raise Http404("Post does not exist! id doesnt exist")

#     print(employee.user_type)

    
#     if(employee.user_type == 'faculty'):
#         template = 'hr2Module/ltc_form.html'

#         if request.method == "POST":
#             family_mem_a = request.POST.get('id_family_mem_a', '')
#             family_mem_b = request.POST.get('id_family_mem_b', '')
#             family_mem_c = request.POST.get('id_family_mem_c', '')

        
#             details_of_family_members = ', '.join(filter(None, [family_mem_a, family_mem_b, family_mem_c]))

        
#             request.POST = request.POST.copy()
#             request.POST['details_of_family_members_already_done'] = details_of_family_members

    
#             family_members = []
#             for i in range(1, 7):  # Loop through input fields for each family member
#                 name = request.POST.get(f'info_{i}_2', '')  # Get the name
#                 age = request.POST.get(f'info_{i}_3', '')   # Get the age
#                 if name and age:  # Check if both name and age are provided
#                     family_members.append(f"{name} ({age} years)")  # Concatenate name and age

#             family_members_str = ', '.join(family_members)

#             # Populate the form with concatenated family member details
#             request.POST['family_members_about_to_avail'] = family_members_str

#             dependents = []
#             for i in range(1, 7):  # Loop through input fields for each dependent
#                 name = request.POST.get(f'd_info_{i}_2', '')  # Get the name
#                 age = request.POST.get(f'd_info_{i}_3', '')   # Get the age
#                 why_dependent = request.POST.get(f'd_info_{i}_4', '')  # Get the reason for dependency
#                 if name and age:  # Check if both name and age are provided
#                     dependents.append(f"{name} ({age} years), {why_dependent}")  # Concatenate name, age, and reason
            

#             # Concatenate all dependent strings into a single string
#             dependents_str = ', '.join(dependents)

#             # Populate the form with concatenated dependent details
#             request.POST['details_of_dependents'] = dependents_str

#             # print("first",request.POST['family_members_about_to_avail'])
#             pf_no = int(request.POST.get('pf_no')) if request.POST.get('pf_no') else None
#             basic_pay_salary = int(request.POST.get('basic_pay_salary')) if request.POST.get('basic_pay_salary') else None
#             amount_of_advance_required = int(request.POST.get('amount_of_advance_required')) if request.POST.get('amount_of_advance_required') else None
#             phone_number_for_contact = int(request.POST.get('phone_number_for_contact')) if request.POST.get('phone_number_for_contact') else None


#             try:
#                 ltc_request = LTCform.objects.create(
#                     employee_id = id,
#                     details_of_family_members_already_done=request.POST.get('details_of_family_members_already_done', ''),
#                     family_members_about_to_avail=request.POST.get('family_members_about_to_avail', ''),
#                     details_of_dependents=request.POST.get('details_of_dependents', ''),
#                     name=request.POST.get('name', ''),
#                     block_year=request.POST.get('block_year', ''),
#                     pf_no=request.POST.get('pf_no', ''),
#                     basic_pay_salary=request.POST.get('basic_pay_salary', ''),
#                     designation=request.POST.get('designation', ''),
#                     department_info=request.POST.get('department_info', ''),
#                     leave_availability=request.POST.get('leave_availability', ''),
#                     leave_start_date=request.POST.get('leave_start_date', ''),
#                     leave_end_date=request.POST.get('leave_end_date', ''),
#                     date_of_leave_for_family=request.POST.get('date_of_leave_for_family', ''),
#                     nature_of_leave=request.POST.get('nature_of_leave', ''),
#                     purpose_of_leave=request.POST.get('purpose_of_leave', ''),
#                     hometown_or_not=request.POST.get('hometown_or_not', ''),
#                     place_of_visit=request.POST.get('place_of_visit', ''),
#                     address_during_leave=request.POST.get('address_during_leave', ''),
#                     mode_for_vacation=request.POST.get('mode_for_vacation', ''),
#                     details_of_family_members=request.POST.get('details_of_family_members', ''),
#                     amount_of_advance_required=request.POST.get('amount_of_advance_required', ''),
#                     certified_family_dependents=request.POST.get('certified_family_dependents', ''),
#                     certified_advance=request.POST.get('certified_advance', ''),
#                     adjusted_month=request.POST.get('adjusted_month', ''),
#                     date=request.POST.get('date', ''),
#                     phone_number_for_contact=request.POST.get('phone_number_for_contact', '')
#                 )
#                 print("done")
#                 messages.success(request, "Ltc form filled successfully")
#             except Exception as e:
#                 print("error" , e)
#                 messages.warning(request, "Fill not correctly")
#                 context = {'employee': employee}
#                 return render(request, template, context)

            
#          # Query all LTC requests
#         ltc_requests = LTCform.objects.filter(employee_id=id)

#         context = {'employee': employee, 'ltc_requests': ltc_requests}

#         return render(request, template, context)
#     else:
#         return render(request, 'hr2Module/edit.html')

# def reverse_ltc_pre_processing(ltc_form_data):
#     reversed_data = {}

#     # Reverse general information
#     reversed_data['name'] = [ltc_form_data.name]
#     reversed_data['block_year'] = [str(ltc_form_data.block_year)]
#     reversed_data['pf_no'] = [str(ltc_form_data.pf_no)]
#     reversed_data['basic_pay_salary'] = [str(ltc_form_data.basic_pay_salary)]
#     reversed_data['designation'] = [ltc_form_data.designation]
#     reversed_data['department_info'] = [ltc_form_data.department_info]
#     reversed_data['leave_availability'] = ['True'] if ltc_form_data.leave_availability else ['False']
#     reversed_data['leave_start_date'] = [ltc_form_data.leave_start_date]
#     reversed_data['leave_end_date'] = [ltc_form_data.leave_end_date]
#     reversed_data['date_of_leave_for_family'] = [ltc_form_data.date_of_leave_for_family]
#     reversed_data['nature_of_leave'] = [ltc_form_data.nature_of_leave]
#     reversed_data['purpose_of_leave'] = [ltc_form_data.purpose_of_leave]
#     reversed_data['hometown_or_not'] = ['True'] if ltc_form_data.hometown_or_not else ['False']
#     reversed_data['place_of_visit'] = [ltc_form_data.place_of_visit]
#     reversed_data['address_during_leave'] = [ltc_form_data.address_during_leave]

#     # Reverse details of family members
#     family_members = ltc_form_data.details_of_family_members_already_done.split(',')
    
#     count = 0

#     for i in range(1, 7):
#         if(len(family_members) > count+3):
#             reversed_data[f'info_{i}_1'] = [family_members[count]]
#             reversed_data[f'info_{i}_2'] = [family_members[count+1]]
#             reversed_data[f'info_{i}_3'] = [family_members[count+2]]
#             count+=3
#         else:
#             reversed_data[f'info_{i}_1'] = ['']
#             reversed_data[f'info_{i}_2'] = ['']
#             reversed_data[f'info_{i}_3'] = ['']
#             count+=3

#     # for i, member in enumerate(family_members, start=1):
#     #     if member:
#     #         reversed_data[f'info_{i}_1'] = [member.split(',')[0]]
#     #         reversed_data[f'info_{i}_2'] = [member.split(',')[1]]
#     #         reversed_data[f'info_{i}_3'] = [member.split(',')[2]]
#     #     else:
#     #         # If family member information is not provided, use empty strings
#     #         reversed_data[f'info_{i}_1'] = ['']
#     #         reversed_data[f'info_{i}_2'] = ['']
#     #         reversed_data[f'info_{i}_3'] = ['']

#     # Reverse details of dependents
#     dependents = ltc_form_data.details_of_dependents.split(',')

#     count=0

#     for i in range(1, 7):
#         if(len(dependents) > count+4):
#             reversed_data[f'd_info_{i}_1'] = [dependents[count]]
#             reversed_data[f'd_info_{i}_2'] = [dependents[count+1]]
#             reversed_data[f'd_info_{i}_3'] = [dependents[count+2]]
#             reversed_data[f'd_info_{i}_4'] = [dependents[count+3]]
#             count+=4
#         else:
#             reversed_data[f'd_info_{i}_1'] = ['']
#             reversed_data[f'd_info_{i}_2'] = ['']
#             reversed_data[f'd_info_{i}_3'] = ['']
#             reversed_data[f'd_info_{i}_4'] = ['']
#             count+=4


#     # for i, dependent in enumerate(dependents, start=1):
#     #     if dependent:
#     #         reversed_data[f'd_info_{i}_1'] = [dependent.split(',')[0]]
#     #         reversed_data[f'd_info_{i}_2'] = [dependent.split(',')[1]]
#     #         reversed_data[f'd_info_{i}_3'] = [dependent.split(',')[2]]
#     #         reversed_data[f'd_info_{i}_4'] = [dependent.split(',')[3]]
#     #     else:
#     #         # If dependent information is not provided, use empty strings
#     #         reversed_data[f'd_info_{i}_1'] = ['']
#     #         reversed_data[f'd_info_{i}_2'] = ['']
#     #         reversed_data[f'd_info_{i}_3'] = ['']
#     #         reversed_data[f'd_info_{i}_4'] = ['']

#     # Reverse remaining fields
#     reversed_data['amount_of_advance_required'] = [str(ltc_form_data.amount_of_advance_required)]
#     reversed_data['certified_family_dependents'] = [ltc_form_data.certified_family_dependents]
#     reversed_data['certified_advance'] = [str(ltc_form_data.certified_advance)]
#     reversed_data['adjusted_month'] = [ltc_form_data.adjusted_month]
#     reversed_data['date'] = [ltc_form_data.date]
#     reversed_data['phone_number_for_contact'] = [str(ltc_form_data.phone_number_for_contact)]

#     return reversed_data




# def ltc_pre_processing(request):
#     ltc_form_data = {}

#     # Extract general information
#     ltc_form_data['name'] = request.POST.get('name')
#     ltc_form_data['block_year'] = int(request.POST.get('block_year'))
#     ltc_form_data['pf_no'] = int(request.POST.get('pf_no'))
#     ltc_form_data['basic_pay_salary'] = int(request.POST.get('basic_pay_salary'))
#     ltc_form_data['designation'] = request.POST.get('designation')
#     ltc_form_data['department_info'] = request.POST.get('department_info')
#     ltc_form_data['leave_availability'] = request.POST.getlist('leave_availability') == ['True', 'True']
#     ltc_form_data['leave_start_date'] = request.POST.get('leave_start_date')
#     ltc_form_data['leave_end_date'] = request.POST.get('leave_end_date')
#     ltc_form_data['date_of_leave_for_family'] = request.POST.get('date_of_leave_for_family')
#     ltc_form_data['nature_of_leave'] = request.POST.get('nature_of_leave')
#     ltc_form_data['purpose_of_leave'] = request.POST.get('purpose_of_leave')
#     ltc_form_data['hometown_or_not'] = request.POST.get('hometown_or_not') == 'True'
#     ltc_form_data['place_of_visit'] = request.POST.get('place_of_visit')
#     ltc_form_data['address_during_leave'] = request.POST.get('address_during_leave')

#     # Extract details of family members
#     family_members = []
#     for i in range(1, 7):
#         if request.POST.get(f'info_{i}_1'):
#             family_member = ','.join(request.POST.getlist(f'info_{i}_{j}')[0] for j in range(1, 4))
#             family_members.append(family_member)
#     ltc_form_data['details_of_family_members_already_done'] = ','.join(family_members)

#     # Extract details of dependents
#     dependents = []
#     for i in range(1, 7):
#         if request.POST.get(f'd_info_{i}_1'):
#             dependent = ','.join(request.POST.getlist(f'd_info_{i}_{j}')[0] for j in range(1, 5))
#             dependents.append(dependent)
#     ltc_form_data['details_of_dependents'] = ','.join(dependents)

#     # Extract remaining fields
#     ltc_form_data['amount_of_advance_required'] = int(request.POST.get('amount_of_advance_required'))
#     ltc_form_data['certified_family_dependents'] = request.POST.get('certified_family_dependents')
#     ltc_form_data['certified_advance'] = int(request.POST.get('certified_advance'))
#     ltc_form_data['adjusted_month'] = request.POST.get('adjusted_month')
#     ltc_form_data['date'] = request.POST.get('date')
#     ltc_form_data['phone_number_for_contact'] = int(request.POST.get('phone_number_for_contact'))

#     return ltc_form_data

def ltc_pre_processing(request):
    data = {}
    details_of_family_members_already_done = ""

    for memeber in request.POST.getlist('details_of_family_members_already_done'):
        if(memeber == ""):
            details_of_family_members_already_done  = details_of_family_members_already_done + 'None' + ','
        else:
            details_of_family_members_already_done  = details_of_family_members_already_done + memeber + ','

    data['details_of_family_members_already_done'] = details_of_family_members_already_done.rstrip(',')


    family_members_about_to_avail = ""

    for i in range(1,4):
        for j in range(1,4):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                family_members_about_to_avail = family_members_about_to_avail + 'None' + ','
            else:
                family_members_about_to_avail = family_members_about_to_avail + request.POST.get(key_is) + ','
    
    data['family_members_about_to_avail'] = family_members_about_to_avail.rstrip(',')


    details_of_dependents = ""
    
    for i in range(1,7):
        for j in range(1,5):
            key_is = f'd_info_{i}_{j}'
            if(request.POST.get(key_is) == ""):
                details_of_dependents = details_of_dependents + 'None' + ','
            else:
                details_of_dependents = details_of_dependents + request.POST.get(key_is) + ','
    
    data['details_of_dependents'] = details_of_dependents.rstrip(',')

    return data


def reverse_ltc_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'block_year', 'pf_no', 'basic_pay_salary', 'name', 'designation', 'department_info',
        'leave_availability', 'leave_start_date', 'leave_end_date', 'date_of_leave_for_family',
        'nature_of_leave', 'purpose_of_leave', 'hometown_or_not', 'place_of_visit',
        'address_during_leave', 'amount_of_advance_required', 'certified_family_dependents',
        'certified_advance', 'adjusted_month', 'date', 'phone_number_for_contact'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    # Reversing array-like values
    reversed_data['details_of_family_members_already_done'] = getattr(data,'details_of_family_members_already_done').split(',')
    
    family_members_about_to_avail = getattr(data,'family_members_about_to_avail').split(',')
    for index, value in enumerate(family_members_about_to_avail):
        family_members_about_to_avail[index] = value if value != 'None' else ''
    
    reversed_data['info_1_1'] = family_members_about_to_avail[0]
    reversed_data['info_1_2'] = family_members_about_to_avail[1]
    reversed_data['info_1_3'] = family_members_about_to_avail[2]
    reversed_data['info_2_1'] = family_members_about_to_avail[3]
    reversed_data['info_2_2'] = family_members_about_to_avail[4]
    reversed_data['info_2_3'] = family_members_about_to_avail[5]
    reversed_data['info_3_1'] = family_members_about_to_avail[6]
    reversed_data['info_3_2'] = family_members_about_to_avail[7]
    reversed_data['info_3_3'] = family_members_about_to_avail[8]

    # # Reversing details_of_dependents
    details_of_dependents = getattr(data,'details_of_dependents').split(',')
    for i in range(1, 7):
        for j in range(1, 5):
            key = f'd_info_{i}_{j}'
            value = details_of_dependents.pop(0)
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
        # employee = ExtraInfo.objects.filter(user__username__icontains=search_text)

        employee = User.objects.get(username = search_text)
  
        print(employee)
    
        holds_designation = HoldsDesignation.objects.filter(user=employee)
        holds_designation = list(holds_designation)

        print(holds_designation[0].designation)

        
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

    print(employee.user_type)

    
    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student'):
        template = 'hr2Module/ltc_form.html'

        if request.method == "POST":
            try:
                print("Creating ltc object!")

                data = ltc_pre_processing(request)
                # print(request.POST.getlist('details_of_family_members_already_done'))
                # print(request.POST.get('d1'))

                # print(request.POST)
                # print(data)

                form_1 = {
                    'employee_id': id,
                    'name': request.POST.get('name'),
                    'block_year': request.POST.get('block_year'),
                    'basic_pay_salary': request.POST.get('basic_pay_salary'),
                    'designation': request.POST.get('designation'),
                    'pf_no': request.POST.get('pf_no'),
                    'department_info': request.POST.get('department_info'),
                    'leave_availability': request.POST.get('leave_availability'),
                    'leave_start_date': request.POST.get('leave_start_date'),
                    'leave_end_date': request.POST.get('leave_end_date'),
                    'date_of_leave_for_family': request.POST.get('date_of_leave_for_family'),
                    'nature_of_leave': request.POST.get('nature_of_leave'),
                    'purpose_of_leave': request.POST.get('purpose_of_leave'),
                    'hometown_or_not': request.POST.get('hometown_or_not'),
                    'place_of_visit': request.POST.get('place_of_visit'),
                    'address_during_leave': request.POST.get('address_during_leave'),
                    'details_of_family_members_already_done': data['details_of_family_members_already_done'],
                    'family_members_about_to_avail ' : data['family_members_about_to_avail'],
                    'details_of_dependents': data['details_of_dependents'],
                    'amount_of_advance_required': request.POST.get('amount_of_advance_required'),
                    'certified_family_dependents': request.POST.get('certified_family_dependents'),
                    'certified_advance': request.POST.get('certified_advance'),
                    'adjusted_month': request.POST.get('adjusted_month'),
                    'date': request.POST.get('date'),
                    'phone_number_for_contact': request.POST.get('phone_number_for_contact'),
                    'username_employee' : request.POST.get('username_employee'),
                    'designation_employee' : request.POST.get('designation_employee')
                }

                # attached_file = None

                # print(request.FILES.get('file_attachment'))

                # if(request.FILES.get('file_attachment') != ""):
                #     attached_file = open(request.FILES.get('file_attachment'), "rb")
                #     attached_file = DjangoFile(attached_file)
                

                # print(attached_file)



                

                ltc_form = LTCform.objects.create(
                    employee_id=id,
                    name=request.POST.get('name'),
                    block_year = request.POST.get('block_year'),
                    pf_no = request.POST.get('pf_no'),
                    basic_pay_salary=request.POST.get('basic_pay_salary'),
                    designation=request.POST.get('designation'),
                    department_info=request.POST.get('department_info'),
                    leave_availability=request.POST.get('leave_availability'),
                    leave_start_date=request.POST.get('leave_start_date'),
                    leave_end_date=request.POST.get('leave_end_date'),
                    date_of_leave_for_family=request.POST.get('date_of_leave_for_family'),
                    nature_of_leave=request.POST.get('nature_of_leave'),
                    purpose_of_leave=request.POST.get('purpose_of_leave'),
                    hometown_or_not=request.POST.get('hometown_or_not'),
                    place_of_visit=request.POST.get('place_of_visit'),
                    address_during_leave=request.POST.get('address_during_leave'),
                    details_of_family_members_already_done=data['details_of_family_members_already_done'],
                    family_members_about_to_avail=data['family_members_about_to_avail'],
                    details_of_dependents=data['details_of_dependents'],
                    amount_of_advance_required=request.POST.get('amount_of_advance_required'),
                    certified_family_dependents=request.POST.get('certified_family_dependents'),
                    certified_advance=request.POST.get('certified_advance'),
                    adjusted_month=request.POST.get('adjusted_month'),
                    date=request.POST.get('date'),
                    phone_number_for_contact=request.POST.get('phone_number_for_contact')
                )

                print("Created Ltc Object!")

                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(ltc_form.id)
                file_extra_JSON = {"key": "value"}

                print("uploader",uploader)
                print("uploader_designation",uploader_designation)
                print("receiver",receiver)
                print("receiver_designation",receiver_designation)

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

                print("Sent the file to Hradmin!")

                messages.success(request, "Ltc form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

         # Query all LTC requests
        ltc_requests = LTCform.objects.filter(employee_id=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

        # designation = get_designation_by_user_id(employee.user)
        # if(designation):
        #     uploader_designation = designation

        # print("username",username)
        # print("uploader_designation",uploader_designation)
        
        # inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        # print(inbox)


        # context = {'employee': employee, 'ltc_requests': ltc_requests, 'inbox': inbox, }

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        print("username",username)
        print("uploader_designation",uploader_designation)
        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        context = {'employee': employee, 'ltc_requests': ltc_requests, 'inbox': inbox , 'designation':designation}

        messages.success(request, "Ltc form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    
def form_view_ltc(request , id):
    ltc_request = get_object_or_404(LTCform, id=id)

    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    print(file_id)
    print(from_user)
    print(from_designation)



    template = 'hr2Module/view_ltc_form.html'
    print(ltc_request)
    ltc_request = reverse_ltc_pre_processing(ltc_request)
    print(ltc_request)
    
    context = {'ltc_request' : ltc_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation ,"id" : id}

    return render(request , template , context)

def track_file(request, id):
    # Assuming file_history is a list of dictionaries
    template = 'hr2Module/ltc_form_trackfile.html'
    file_history = view_history(file_id=id)


    print(file_history)

    print(file_history[0]['current_id'])

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
        print(request.POST.get('context'))
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        print(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        remark = form_data['remark_id']
        id_info_1_1 = form_data['id_info_1_1']
        id_info_1_2 = form_data['id_info_1_2']
        id_info_1_3 = form_data['id_info_1_3']
        id_info_1_4 = form_data['id_info_1_4']
        id_info_1_5 = form_data['id_info_1_5']
        id_info_1_6 = form_data['id_info_1_6']
        id_info_2_1 = form_data['id_info_2_1']
        id_info_2_2 = form_data['id_info_2_2']
        id_info_2_3 = form_data['id_info_2_3']
        id_info_2_4 = form_data['id_info_2_4']
        id_info_2_5 = form_data['id_info_2_5']
        id_info_2_6 = form_data['id_info_2_6']
        id_info_3_1 = form_data['id_info_3_1']
        id_info_3_2 = form_data['id_info_3_2']
        id_info_3_3 = form_data['id_info_3_3']
        id_info_3_4 = form_data['id_info_3_4']
        id_info_3_5 = form_data['id_info_3_5']
        id_info_3_6 = form_data['id_info_3_6']
        dealing_assistant = form_data['dealing_assistant']
        deputy_registrar = form_data['deputy_registrar']
        sanction_status = form_data['sanction_status']
        r_name = form_data['r_name']
        r_desgination = form_data['r_desgination']

        office_use = None

        if(office_use == ""):
            office_use = None
        else:
            office_use = f"{id_info_1_1},{id_info_1_2},{id_info_1_3},{id_info_1_4},{id_info_1_5},{id_info_1_6},{id_info_2_1},{id_info_2_2},{id_info_2_3},{id_info_2_4},{id_info_2_5},{id_info_2_6},{id_info_3_1},{id_info_3_2},{id_info_3_3},{id_info_3_4},{id_info_3_5},{id_info_3_6}"

        #change


        #database
        leave_form = LeaveForm.objects.get(id=form_id)

        # Update the attribute
        setattr(leave_form, "office_use", office_use)
        setattr(leave_form, "dealing_assistant", dealing_assistant)
        setattr(leave_form, "deputy_registrar", deputy_registrar)
        setattr(leave_form, "sanction_status", sanction_status)
        setattr(leave_form, "r_name", r_name)
        setattr(leave_form, "r_desgination", r_desgination)
        leave_form.save()

        #database
        try:
            leave_form = LeaveForm.objects.get(id=form_id)
        except LeaveForm.DoesNotExist:
            return JsonResponse({"error": "LeaveForm object with the provided ID does not exist"}, status=404)
        

        print(remark)

        current_owner =  get_current_file_owner(file_id)

        print(current_owner)
    
        


        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee} . Reason : {remark}", file_extra_JSON = "None")
            print("done1",track_id)
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done2")
            messages.success(request, "File rejected successfully")
        else:
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = leave_form.name, receiver_designation = leave_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done3")
            messages.success(request, "File approved successfully")

        
        return HttpResponse("Success")
    else:
        # Handle other HTTP methods if needed
        return HttpResponse("Failure")




def file_handle_cpda(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        print(request.POST.get('context'))
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        print(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']

        recomm_hod_confirm = form_data['recomm_hod_confirm']
        date_rspc_confirm = form_data['date_rspc_confirm']
        advance_amount_pda = form_data['advance_amount_pda']
        dealing_asstt_name = form_data['dealing_asstt_name']
        balance_available = form_data['balance_available']
        sanction_status = form_data['sanction_status']
        id_ar_dr_name = form_data['id_ar_dr_name']
        id_ar_dr_ia_name = form_data['id_ar_dr_ia_name']
        id_check_amount = form_data['id_check_amount']
        dealing_asstt_ia_name = form_data['dealing_asstt_ia_name']
        copy_to = form_data['copy_to']
        remark = form_data['remark_id']
        #change


        #database
        try:
            cpda_form = CPDAform.objects.get(id=form_id)
        except CPDAform.DoesNotExist:
            return JsonResponse({"error": "CPDAform object with the provided ID does not exist"}, status=404)
        
        if(copy_to == ""):
            copy_to = None

        if(recomm_hod_confirm == ""):
            recomm_hod_confirm = None

        if(advance_amount_pda == ""):
            advance_amount_pda = None 

        if(balance_available == ""):
            balance_available = None        


        
        # Update the attribute
        setattr(cpda_form, "recomm_hod_confirm", recomm_hod_confirm)
        setattr(cpda_form, "date_rspc_confirm", date_rspc_confirm)
        setattr(cpda_form, "advance_amount_pda", advance_amount_pda)
        setattr(cpda_form, "dealing_asstt_name", dealing_asstt_name)
        setattr(cpda_form, "id_ar_dr_name", id_ar_dr_name)
        setattr(cpda_form, "sanction_status", sanction_status)
        setattr(cpda_form, "id_ar_dr_ia_name", id_ar_dr_ia_name)
        setattr(cpda_form, "id_check_amount", id_check_amount)
        setattr(cpda_form, "balance_available", balance_available)
        setattr(cpda_form, "dealing_asstt_ia_name", dealing_asstt_ia_name)
        setattr(cpda_form, "copy_to", copy_to)
        cpda_form.save()

        #database
        try:
            cpda_form = CPDAform.objects.get(id=form_id)
        except CPDAform.DoesNotExist:
            return JsonResponse({"error": "CPDAform object with the provided ID does not exist"}, status=404)
        
        print(cpda_form)

        current_owner =  get_current_file_owner(file_id)
        print(current_owner)

        print("form_id" , form_id)
        print("file_id",file_id)
        print("from_user",from_user)
        print("from_designation",from_designation)
        print("action",action)
        print("username_employee",username_employee)
        print("designation_employee",designation_employee)
        print("recomm_hod_confirm",recomm_hod_confirm)
        print("date_rspc_confirm",date_rspc_confirm)
        print("advance_amount_pda",advance_amount_pda)
        print("dealing_asstt_name",dealing_asstt_name)
        print("id_ar_dr_ia_name",id_ar_dr_ia_name)
        print("sanction_status",sanction_status)
        print("copy_to",copy_to)


        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            print("done1",track_id)
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done2")
            messages.success(request, "File rejected successfully")
        else:
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done3")
            messages.success(request, "File approved successfully")

        
        return HttpResponse("Success")
    else:
        # Handle other HTTP methods if needed
        return HttpResponse("Failure")
    

def file_handle_ltc(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        print(request.POST.get('context'))
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        print(form_data)
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
        print(current_owner)


        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            print("done1",track_id)
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done2")
            messages.success(request, "File rejected successfully")
        else:
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = ltc_form.name, receiver_designation = ltc_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done3")
            messages.success(request, "File approved successfully")

        
        return HttpResponse("Success")
    else:
        # Handle other HTTP methods if needed
        return HttpResponse("Failure")   


def file_handle_appraisal(request):
    if request.method == 'POST':
        form_data2 = request.POST
        form_data=request.POST.get('context')
        print(request.POST.get('context'))
        action = form_data2.get('action')
        
        form_data=json.loads(form_data)
        print(form_data)
        form_id = form_data['form_id']
        file_id = form_data['file_id']
        from_user = form_data['from_user']
        from_designation = form_data['from_designation']
        username_employee = form_data['username_employee']
        designation_employee = form_data['designation_employee']
        remarks = form_data['remarks']
        sign_hod = form_data['sign_hod']
        sign_director = form_data['sign_director']
        

        remark = form_data['remark_id']
        try:
            appraisal_form = Appraisalform.objects.get(id=form_id)
        except Appraisalform.DoesNotExist:
            return JsonResponse({"error": "Appraisalform object with the provided ID does not exist"}, status=404)      


        
        # Update the attribute
        setattr(appraisal_form, "form_id", form_id)
        setattr(appraisal_form, "sign_hod", sign_hod)
        setattr(appraisal_form, "remarks", remarks)
        setattr(appraisal_form, "sign_director", sign_director)
       
        appraisal_form.save()

        current_owner =  get_current_file_owner(file_id)
        print(current_owner)
        
        #database
        try:
            appraisal_form = Appraisalform.objects.get(id=form_id)
        except Appraisalform.DoesNotExist:
            return JsonResponse({"error": "Appraisalform object with the provided ID does not exist"}, status=404)
        


        if(action == '0'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee,remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
            print("done1",track_id)
            messages.success(request, "File forwarded successfully")
        elif(action == '1'):
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done2")
            messages.success(request, "File rejected successfully")
        else:
            if(remark == ""):
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
            else:
                track_id = forward_file(file_id = file_id, receiver = appraisal_form.name, receiver_designation = appraisal_form.designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
            print("done3")
            messages.success(request, "File approved successfully")

        
        return HttpResponse("Success")
    else:
        # Handle other HTTP methods if needed
        return HttpResponse("Failure") 

# def file_handle(request):
#     if request.method == 'POST':
#         form_data2 = request.POST
#         form_data=request.POST.get('context')
#         print(request.POST.get('context'))
#         action = form_data2.get('action')
        
#         form_data=json.loads(form_data)
#         print(form_data)
#         form_id = form_data['form_id']
#         file_id = form_data['file_id']
#         from_user = form_data['from_user']
#         from_designation = form_data['from_designation']
#         username_employee = form_data['username_employee']
#         designation_employee = form_data['designation_employee']

#         remark = form_data['remark_id']


#         print("form_id" , form_id)
#         print("file_id",file_id)
#         print("from_user",from_user)
#         print("from_designation",from_designation)
#         print("action",action)
#         print("username_employee",username_employee)
#         print("designation_employee",designation_employee)

#         print(remark)

#         current_owner =  get_current_file_owner(file_id)  

#         print(current_owner)

#         if(action == '0'):
#             if(remark == ""):
#                 track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee, remarks = f"Forwarded by {current_owner} to {username_employee}", file_extra_JSON = "None")
#             else:
#                 track_id = forward_file(file_id = file_id, receiver = username_employee, receiver_designation = designation_employee, remarks = f"Forwarded by {current_owner} to {username_employee}, Reason : {remark}", file_extra_JSON = "None")               
#             print("done1",track_id)
#             messages.success(request, "File forwarded successfully")
#         elif(action == '1'):
#             if(remark == ""):
#                 track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}", file_extra_JSON = "None")
#             else:
#                 track_id = forward_file(file_id = file_id, receiver = cpda_form.name, receiver_designation = cpda_form.designation, remarks = f"Rejected by {current_owner}, Reason : {remark}", file_extra_JSON = "None")
#             print("done2")
#             messages.success(request, "File rejected successfully")
#         else:
#             if(remark == ""):
#                 track_id = forward_file(file_id = file_id, receiver = from_user, receiver_designation = from_designation, remarks = f"Approved by {current_owner}", file_extra_JSON = "None")
#             else:
#                 track_id = forward_file(file_id = file_id, receiver = from_user, receiver_designation = from_designation, remarks = f"Approved by {current_owner}, Reason : {remark}", file_extra_JSON = "None")   
#             print("done3")
#             messages.success(request, "File approved successfully")

        
#         return HttpResponse("Success")
#     else:
#         # Handle other HTTP methods if needed
#         return HttpResponse("Failure")

def view_ltc_form(request, id):
    ltc_request = get_object_or_404(LTCform, id=id)
    # print("ltc object: ", ltc_request)
    # print("ltc object: ", reverse_ltc_pre_processing(ltc_request))
    print(ltc_request)
    ltc_request = reverse_ltc_pre_processing(ltc_request)

    print(ltc_request)

    context = {
        'ltc_request': ltc_request
    }
    return render(request,'hr2Module/view_ltc_form.html',context)

def form_mangement_ltc(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)
        
        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context= {
            'ltc_requests' : ltc_requests,
            'hr' : "1",
        }

        print(ltc_requests[0].name)

        return render(request, 'hr2Module/ltc_form.html',context)
    

def form_mangement_ltc_hr(request,id):
    print("Request of forward!")
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

    print("Sent the file to Hod!")

    messages.success(request, "Ltc form filled successfully")

    return HttpResponse("Sucess")

def form_mangement_ltc_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15]
        
        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context= {
            'ltc_requests' : ltc_requests,
            'hr' : "1",
        }

        print(ltc_requests[0].name)

        return render(request, 'hr2Module/ltc_form.html',context)


# def form_mangement_ltc(request):
#     if(request.method == "GET"):
#         username = "21BCS185"
#         designation = "hradmin"
#         inbox = view_inbox(username = username, designation = designation, src_module = "HR")

#         # print(inbox)

#         # Extract src_object_id values
#         src_object_ids = [item['src_object_id'] for item in inbox]
#         # print(src_object_ids)

#         src_object_ids = [14,15]
        
#         ltc_requests = []

#         for src_object_id in src_object_ids:
#             ltc_request = get_object_or_404(LTCform, id=src_object_id)
#             ltc_requests.append(ltc_request)

#         context= {
#             'ltc_requests' : ltc_requests,
#             'hr' : "1",
#         }

#         print(ltc_requests[0].name)

#         return render(request, 'hr2Module/ltc_form.html',context)
    
    # elif(request.method == "POST"):
    #     # username = request.data['receiver']
    #     username = request.POST.get['receiver']
    #     receiver_value = User.objects.get(username=username)
    #     receiver_value_designation= HoldsDesignation.objects.filter(user=receiver_value)
    #     lis = list(receiver_value_designation)
    #     obj=lis[0].designation
    #     forward_file(file_id = request.data['file_id'], receiver = request.data['receiver'], 
    #         receiver_designation = obj.name, remarks = request.data['remarks'], 
    #         file_extra_JSON = request.data['file_extra_JSON']
    #     )
    #     messages.success(request, "forwarded succesfully")

@login_required(login_url='/accounts/login')
def dashboard(request):
    user = request.user
    print(request.user)

    user_id = ExtraInfo.objects.get(user=user).user_id
    print(user_id)
    context = {'user_id': user_id}
    print("context",user_id)
    return render(request, 'hr2Module/dashboard.html',context)


# cpda form -----------------------------------------------------------


def reverse_cpda_pre_processing(data):
    reversed_data = {}

    simple_keys = [
        'name', 'designation', 'pf_no', 'purpose', 'amount_required', 'adjusted_pda',
        'achievements_uploaded_date', 'submission_date', 'recomm_hod_confirm', 'date_rspc_confirm',
        'balance_available', 'advance_amount_pda', 'dealing_asstt_name', 'ar_dr_name',
        'check_amount', 'dealing_asstt_ia_name', 'ar_dr_ia_name',
        'sanction_status', 'copy_to'
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

    print(employee.user_type)

    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student' ):
        template = 'hr2Module/cpda_form.html'

        if request.method == "POST":
            try:
                print("Creating cpda object!")

                # data = ltc_pre_processing(request) #isko dekhege

                form_2 = {
                    'employee_id' : id,
                    'name' : request.POST.get('name'),
                    'designation' :  request.POST.get('designation'),
                    'pf_no' : request.POST.get('pf_no'),
                    'purpose' : request.POST.get('purpose'),
                    'amount_required' : request.POST.get('amount_required'),
                    'adjusted_pda' : request.POST.get('adjusted_pda'),
                    'achievements_uploaded_date' : request.POST.get('achievements_uploaded_date'),
                    'submission_date' : request.POST.get('submission_date'),
                    'recomm_hod_confirm' : request.POST.get('recomm_hod_confirm'),
                    'date_rspc_confirm' : request.POST.get('date_rspc_confirm'),
                    'balance_available' : request.POST.get('balance_available'),
                    'advance_amount_pda' : request.POST.get('advance_amount_pda'),
                    'dealing_asstt_name' : request.POST.get('dealing_asstt_name'),
                    'ar_dr_name' : request.POST.get('ar_dr_name'),
                    'check_amount' : request.POST.get('check_amount'),
                    'dealing_asstt_ia_name' : request.POST.get('dealing_asstt_ia_name'),
                    'ar_dr_ia_name' : request.POST.get('ar_dr_ia_name'),
                    'sanction_status' : request.POST.get('sanction_status'),
                    'copy_to' : request.POST.get('copy_to')

                }
                
                cpda_form = CPDAform.objects.create(
                    employee_id = id,
                    name = request.POST.get('name'),
                    designation =  request.POST.get('designation'),
                    pf_no = request.POST.get('pf_no'),
                    purpose = request.POST.get('purpose'),
                    amount_required = request.POST.get('amount_required'),
                    adjusted_pda = request.POST.get('adjusted_pda'),
                    achievements_uploaded_date = request.POST.get('achievements_uploaded_date'),
                    submission_date = request.POST.get('submission_date'),
                    recomm_hod_confirm = request.POST.get('recomm_hod_confirm'),
                    date_rspc_confirm = request.POST.get('date_rspc_confirm'),
                    balance_available = request.POST.get('balance_available'),
                    advance_amount_pda = request.POST.get('advance_amount_pda'),
                    dealing_asstt_name = request.POST.get('dealing_asstt_name'),
                    ar_dr_name = request.POST.get('ar_dr_name'),
                    check_amount = request.POST.get('check_amount'),
                    dealing_asstt_ia_name = request.POST.get('dealing_asstt_ia_name'),
                    ar_dr_ia_name = request.POST.get('ar_dr_ia_name'),
                    sanction_status = request.POST.get('sanction_status'),
                    copy_to = request.POST.get('copy_to')
                )

                print("Created CPDA Object!")

                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR" #dikkat 
                src_object_id = str(cpda_form.id)
                file_extra_JSON = {"key": "value"}

                print("uploader",uploader)
                print("uploader_designation",uploader_designation)
                print("receiver",receiver)
                print("receiver_designation",receiver_designation)

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

                print("Sent the file to Hradmin!") #isko dekhege
                print(file_id)

                messages.success(request, "CPDA form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

        cpda_requests = CPDAform.objects.filter(employee_id=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

        # designation = get_designation_by_user_id(employee.user)
        # if(designation):
        #     uploader_designation = designation

        # # print("username",username)
        # # print("uploader_designation",uploader_designation)
        
        # inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        # print(inbox)

        # context = {'employee': employee, 'cpda_requests': cpda_requests, 'inbox': inbox}

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        # print("username",username)
        # print("uploader_designation",uploader_designation)
        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        context = {'employee': employee, 'cpda_requests': cpda_requests, 'inbox': inbox , 'designation':designation}


        

        messages.success(request, "CPDA form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    

def form_view_cpda(request , id):
    print(id)
    cpda_request = get_object_or_404(CPDAform, id=id)

    # isko recheck krna h
    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    print(file_id)
    print(from_user)
    print(from_designation)

    template = 'hr2Module/view_cpda_form.html'
    cpda_request = reverse_cpda_pre_processing(cpda_request)#isko bnana h
    print(cpda_request)
    
    context = {'cpda_request' : cpda_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation,"id":id}

    return render(request , template , context)

def view_cpda_form(request, id):
    cpda_request = get_object_or_404(CPDAform, id=id)
   
    print(cpda_request)
    cpda_request = reverse_cpda_pre_processing(cpda_request)

    print(cpda_request)

    context = {
        'cpda_request': cpda_request
    }
    return render(request,'hr2Module/view_cpda_form.html',context)

def form_mangement_cpda(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        
        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context= {
            'cpda_requests' : cpda_requests,
            'hr' : "1",
        }

        print(cpda_requests[0].name)

        return render(request, 'hr2Module/cpda_form.html',context)
    
def form_mangement_cpda_hr(request,id):
    print("Request of forward!")
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

    print("Sent the file to Hod!")
    print(file_id)

    messages.success(request, "CPda form filled successfully")


    return HttpResponse("Sucess")


def form_mangement_cpda_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15]
        
        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context= {
            'cpda_requests' : cpda_requests,
            'hr' : "1",
        }

        print(cpda_requests[0].name)

        return render(request, 'hr2Module/cpda_form.html',context)
    

#  Leave form -------------------------------------------------------------
    
def leave_pre_processing(request):
    data = {}

    office_use = ""
    
    for i in range(1,4):
        for j in range(1,7):
            key_is = f'info_{i}_{j}'
            if(request.POST.get(key_is) == ""):
                office_use = office_use + ','
            else:
                office_use = office_use + request.POST.get(key_is) + ','
    
    data['office_use'] = office_use.rstrip(',')

    print(data['office_use'])

    return data

def reverse_leave_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    # dalna h
    simple_keys = [
        'name', 'designation', 'application_date', 'application_pf_no', 'discipline', 'nature_of_leave',
        'nature_leave_start_date', 'nature_leave_end_date', 'station_leave', 'station_leave_start_date',
        'station_leave_end_date', 'purpose', 'leave_address', 'academic_responsibility',
        'addministrative_responsibilty_assigned', 'sign_dir_reg_r_name', 'sign_dir_reg_r_desgination',
        'dealing_assistant', 'deputy_registrar', 'sanction_status', 'r_name', 'r_desgination'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    # # Reversing details_of_dependents
    # office_use = getattr(data,'office_use').split(',')
    # for i in range(1, 4):
    #     for j in range(1, 7):
    #         key = f'info_{i}_{j}'
    #         value = office_use.pop(0)
    #         reversed_data[key] = value if value != 'None' else ''
        

    office_use = getattr(data, 'office_use')
    print(office_use)
    print(data.dealing_assistant)

    if office_use is not None:
        office_use = office_use.split(',')
    else:
        office_use = []

    for i in range(1, 4):
        for j in range(1, 7):
            key = f'info_{i}_{j}'
            if office_use:
                value = office_use.pop(0)
                reversed_data[key] = value if value != 'None' else ''
            else:
                reversed_data[key] = ''


    return reversed_data

    
def leave_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    print(employee.user_type)

    
    if(employee.user_type == 'faculty' or employee.user_type == 'student' or employee.user_type == 'staff'):
        template = 'hr2Module/leave_form.html'

        if request.method == "POST":
            try:
                print("Creating leave object!")


                form_3 = {
                    'employee_id' : id,
                    'name' : request.POST.get('name'),
                    'designation' :  request.POST.get('designation'),
                    'application_date' : request.POST.get('application_date'),
                    'application_pf_no' : request.POST.get('application_pf_no'),
                    'discipline' : request.POST.get('discipline'),
                    'nature_of_leave' : request.POST.get('nature_of_leave'),
                    'nature_leave_start_date' : request.POST.get('nature_leave_start_date'),
                    'nature_leave_end_date' : request.POST.get('nature_leave_end_date'),
                    'station_leave' : request.POST.get('station_leave'),
                    'station_leave_start_date' : request.POST.get('station_leave_start_date'),
                    'station_leave_end_date' : request.POST.get('station_leave_end_date'),
                    'purpose' : request.POST.get('purpose'),
                    'leave_address' : request.POST.get('leave_address'),
                    'academic_responsibility' : request.POST.get('academic_responsibility'),
                    'addministrative_responsibilty_assigned' : request.POST.get('addministrative_responsibilty_assigned'),
                    'sign_dir_reg_r_name' : request.POST.get('sign_dir_reg_r_name'),
                    'sign_dir_reg_r_desgination' : request.POST.get('sign_dir_reg_r_desgination'),
                    'dealing_assistant' : request.POST.get('dealing_assistant'),
                    'deputy_registrar' : request.POST.get('deputy_registrar'),
                    'sanction_status' : request.POST.get('sanction_status'),
                    'r_name' : request.POST.get('r_name'),
                    'r_desgination' : request.POST.get('r_desgination')

                }
                
                leave_form = LeaveForm.objects.create(
                    employee_id = id,
                    name = request.POST.get('name'),
                    designation =  request.POST.get('designation'),
                    application_date = request.POST.get('application_date'),
                    application_pf_no = request.POST.get('application_pf_no'),
                    discipline = request.POST.get('discipline'),
                    nature_of_leave = request.POST.get('nature_of_leave'),
                    nature_leave_start_date = request.POST.get('nature_leave_start_date'),
                    nature_leave_end_date = request.POST.get('nature_leave_end_date'),
                    station_leave = request.POST.get('station_leave'),
                    station_leave_start_date = request.POST.get('station_leave_start_date'),
                    station_leave_end_date = request.POST.get('station_leave_end_date'),
                    purpose = request.POST.get('purpose'),
                    leave_address = request.POST.get('leave_address'),
                    academic_responsibility = request.POST.get('academic_responsibility'),
                    addministrative_responsibilty_assigned = request.POST.get('addministrative_responsibilty_assigned'),
                    sign_dir_reg_r_name = request.POST.get('sign_dir_reg_r_name'),
                    sign_dir_reg_r_desgination = request.POST.get('sign_dir_reg_r_desgination'),
                    office_use = "",
                    dealing_assistant = request.POST.get('dealing_assistant'),
                    deputy_registrar = request.POST.get('deputy_registrar'),
                    sanction_status = request.POST.get('sanction_status'),
                    r_name = request.POST.get('r_name'),
                    r_desgination = request.POST.get('r_desgination')

                )

                print("Created Leave Object!")

                uploader = employee.user
                uploader_designation = 'Assistant Professor'


                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(leave_form.id)
                file_extra_JSON = {"key": "value"}

                print("uploader",uploader)
                print("uploader_designation",uploader_designation)
                print("receiver",receiver)
                print("receiver_designation",receiver_designation)

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

                print("Sent the file to Hradmin!")

                messages.success(request, "Leave form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

         # Query all Leave requests
        leave_requests = LeaveForm.objects.filter(employee_id=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        print("username",username)
        print("uploader_designation",uploader_designation)
        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        context = {'employee': employee, 'leave_requests': leave_requests, 'inbox': inbox , 'designation':designation}

        messages.success(request, "Leave form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    

def form_view_leave(request , id):

    leave_request = get_object_or_404(LeaveForm, id=id)

    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    print(file_id)
    print(from_user)
    print(from_designation)

    template = 'hr2Module/view_leave_form.html'
    print(leave_request)
    leave_request = reverse_leave_pre_processing(leave_request)
    print(leave_request)
    
    context = {'leave_request' : leave_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation, "id" : id}

    return render(request , template , context)

# ek or bna lena
def view_leave_form(request, id):
    leave_request = get_object_or_404(LeaveForm, id=id)

    
    print("1",leave_request.dealing_assistant)
    leave_request = reverse_leave_pre_processing(leave_request)

    print(leave_request)

    context = {
        'leave_request': leave_request
    }
    return render(request,'hr2Module/view_leave_form.html',context)


def form_mangement_leave(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        src_object_ids = [14,15,19]
        
        leave_requests = []

        for src_object_id in src_object_ids:
            leave_request = get_object_or_404(LeaveForm, id=src_object_id)
            leave_requests.append(leave_request)

        context= {
            'leave_requests' : leave_requests,
            'hr' : "1",
        }

        print(leave_requests[0].name)

        return render(request, 'hr2Module/leave_form.html',context)
    

def form_mangement_leave_hr(request,id):
    print("Request of forward!")
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

    print("Sent the file to Hod!")

    messages.success(request, "Leave form filled successfully")

    return HttpResponse("Sucess")

def form_mangement_leave_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15]
        
        leave_requests = []

        for src_object_id in src_object_ids:
            leave_request = get_object_or_404(LeaveForm, id=src_object_id)
            leave_requests.append(leave_request)

        context= {
            'leave_requests' : leave_requests,
            'hr' : "1",
        }

        print(leave_requests[0].name)

        return render(request, 'hr2Module/leave_form.html',context)
    



def appraisal_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    print(employee.user_type)

    
    if(employee.user_type == 'faculty' or employee.user_type == 'staff' or employee.user_type == 'student'):
        template = 'hr2Module/appraisal_form.html'

        if request.method == "POST":
            try:
                print("Creating appraisal object!")

                data = appraisal_pre_processing(request)
                # print(request.POST.getlist('details_of_family_members_already_done'))
                # print(request.POST.get('d1'))

                # print(request.POST)
                # print(data)

                form_4 = {
                    'employee_id': id,
                    'name': request.POST.get('name'),
                    'designation': request.POST.get('designation'),
                    'discipline': request.POST.get('discipline'),
                    'field_knowledge': request.POST.get('field_knowledge'),
                    'current_res_int': request.POST.get('current_res_int'),
                    'courses_taught': data['courses_taught'],
                    'new_courses_introduced': data['new_courses_introduced'],
                    'new_courses_developed': data['new_courses_developed'],
                    'instructional_tasks': request.POST.get('instructional_tasks'),
                    'thesis_reasearch': data['thesis_reasearch'],
                    'sponsored_research': data['sponsored_research'],
                    'research_element': request.POST.get('research_element'),
                    'publication': request.POST.get('publication'),
                    'referred_conf': request.POST.get('referred_conf'),
                    'conf_organised': request.POST.get('conf_organised'),
                    'memberships': request.POST.get('memberships'),
                    'honours ' :   request.POST.get('honours'),
                    'edt_of_rep_pub':  request.POST.get('edt_of_rep_pub'),
                    'expert_lec_del': request.POST.get('expert_lec_del'),
                    'mem_of_bos': request.POST.get('mem_of_bos'),
                    'extention_tasks': request.POST.get('extention_tasks'),
                    'add_assign': request.POST.get('add_assign'),
                    'service_inst_community': request.POST.get('service_inst_community'),
                    'other_contri': request.POST.get('other_contri'),
                    'your_comments' : request.POST.get('your_comments'),
                    'date' : request.POST.get('date'),
                    'sign_faculty' : request.POST.get('sign_faculty'),
                    'remarks' : request.POST.get('remarks'),
                    'sign_hod' : request.POST.get('sign_hod'),
                    'sign_director' : request.POST.get('sign_director')
                }

                # attached_file = None

                # print(request.FILES.get('file_attachment'))

                # if(request.FILES.get('file_attachment') != ""):
                #     attached_file = open(request.FILES.get('file_attachment'), "rb")
                #     attached_file = DjangoFile(attached_file)
                

                # print(attached_file)

                appraisal_form = Appraisalform.objects.create(
                    employee_id= id,
                    name= request.POST.get('name'),
                    designation= request.POST.get('designation'),
                    discipline= request.POST.get('discipline'),
                    field_knowledge= request.POST.get('field_knowledge'),
                    current_res_int= request.POST.get('current_res_int'),
                    courses_taught= data['courses_taught'],
                    new_courses_introduced= data['new_courses_introduced'],
                    new_courses_developed= data['new_courses_developed'],
                    instructional_tasks= request.POST.get('instructional_tasks'),
                    thesis_reasearch= data['thesis_reasearch'],
                    sponsored_research= data['sponsored_research'],
                    research_element= request.POST.get('research_element'),
                    publication= request.POST.get('publication'),
                    referred_conf= request.POST.get('referred_conf'),
                    conf_organised= request.POST.get('conf_organised'),
                    memberships= request.POST.get('memberships'),
                    honours  = request.POST.get('honours'),
                    edt_of_rep_pub= request.POST.get('edt_of_rep_pub'),
                    expert_lec_del= request.POST.get('expert_lec_del'),
                    mem_of_bos= request.POST.get('mem_of_bos'),
                    extention_tasks= request.POST.get('extention_tasks'),
                    add_assign= request.POST.get('add_assign'),
                    service_inst_community= request.POST.get('service_inst_community'),
                    other_contri= request.POST.get('other_contri'),
                    your_comments = request.POST.get('your_comments'),
                    date = request.POST.get('date'),
                    sign_faculty = request.POST.get('sign_faculty'),
                    remarks = request.POST.get('remarks'),
                    sign_hod = request.POST.get('sign_hod'),
                    sign_director = request.POST.get('sign_director')   
                
                )
                print("Created Appraisal Object!")

                uploader = employee.user
                uploader_designation = 'Assistant Professor'

                get_designation = get_designation_by_user_id(employee.user)
                if(get_designation):
                    uploader_designation = get_designation

                receiver = request.POST.get('username_employee')
                receiver_designation = request.POST.get('designation_employee')
                src_module = "HR"
                src_object_id = str(appraisal_form.id)
                file_extra_JSON = {"key": "value"}

                print("uploader",uploader)
                print("uploader_designation",uploader_designation)
                print("receiver",receiver)
                print("receiver_designation",receiver_designation)

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

                print("Sent the file to Hradmin!")

                messages.success(request, "Appraisal form filled successfully")

                return redirect(request.path_info)

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

        appraisal_requests = Appraisalform.objects.filter(employee_id=id)

        username = employee.user
        uploader_designation = 'Assistant Professor'

        # designation = get_designation_by_user_id(employee.user)
        # if(designation):
        #     uploader_designation = designation

        # print("username",username)
        # print("uploader_designation",uploader_designation)
        
        # inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        # print(inbox)

        # context = {'employee': employee, 'appraisal_requests': appraisal_requests, 'inbox': inbox}

        designation = get_designation_by_user_id(employee.user)
        if(designation):
            uploader_designation = designation

        print("username",username)
        print("uploader_designation",uploader_designation)
        
        inbox = view_inbox(username = username, designation = uploader_designation, src_module = "HR")

        context = {'employee': employee, 'appraisal_requests': appraisal_requests, 'inbox': inbox , 'designation':designation}

        messages.success(request, "Appraisal form filled successfully!")
        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')
    

   
def form_view_appraisal(request , id):
    appraisal_request = get_object_or_404(Appraisalform, id=id)

    from_user = request.GET.get('param1')
    from_designation = request.GET.get('param2')
    file_id = request.GET.get('param3')

    print(file_id)
    print(from_user)
    print(from_designation)



    template = 'hr2Module/view_appraisal_form.html'
    print(appraisal_request)
    appraisal_request = reverse_appraisal_pre_processing(appraisal_request)
    print(appraisal_request)
    
    context = {'appraisal_request' : appraisal_request , "button" : 1 , "file_id" : file_id, "from_user" :from_user , "from_designation" : from_designation,"id":id}

    return render(request , template , context)


def view_appraisal_form(request, id):
    appraisal_request = get_object_or_404(Appraisalform, id=id)
    # print("ltc object: ", ltc_request)
    # print("ltc object: ", reverse_ltc_pre_processing(ltc_request))
    print(appraisal_request)
    appraisal_request = reverse_appraisal_pre_processing(appraisal_request)

    print(appraisal_request)

    context = {
        'appraisal_request': appraisal_request
    }
    return render(request,'hr2Module/view_appraisal_form.html',context)



def form_mangement_appraisal(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        src_object_ids = [14,15,19]
        
        appraisal_requests = []

        for src_object_id in src_object_ids:
            appraisal_request = get_object_or_404(Appraisalform, id=src_object_id)
            appraisal_requests.append(appraisal_request)

        context= {
            'appraisal_requests' : appraisal_requests,
            'hr' : "1",
        }

        print(appraisal_requests[0].name)

        return render(request, 'hr2Module/appraisal_form.html',context)


def form_mangement_appraisal_hr(request,id):
    print("Request of forward!")
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

    print("Sent the file to Hod!")

    messages.success(request, "Appraisal form filled successfully")

    return HttpResponse("Sucess")    

def form_mangement_appraisal_hod(request):
    if(request.method == "GET"):
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15]
        
        appraisal_requests = []

        for src_object_id in src_object_ids:
            appraisal_request = get_object_or_404(Appraisalform, id=src_object_id)
            appraisal_requests.append(appraisal_request)

        context= {
            'appraisal_requests' : appraisal_requests,
            'hr' : "1",
        }

        print(appraisal_requests[0].name)

        return render(request, 'hr2Module/appraisal_form.html',context)
    
def appraisal_pre_processing(request):
    data = {}
    

    courses_taught = ""

    for i in range(1,3):
        for j in range(1,8):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                courses_taught = courses_taught + 'None' + ','
            else:
                courses_taught = courses_taught + request.POST.get(key_is) + ','
    
    data['courses_taught'] = courses_taught.rstrip(',')

    new_courses_introduced = ""

    for i in range(3,5):
        for j in range(1,4):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                new_courses_introduced = new_courses_introduced + 'None' + ','
            else:
                new_courses_introduced = new_courses_introduced + request.POST.get(key_is) + ','
    
    data['new_courses_introduced'] = new_courses_introduced.rstrip(',')


    new_courses_developed = ""

    for i in range(5,7):
        for j in range(1,5):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                new_courses_developed = new_courses_developed + 'None' + ','
            else:
                new_courses_developed = new_courses_developed + request.POST.get(key_is) + ','
    
    data['new_courses_developed'] = new_courses_developed.rstrip(',')



    thesis_reasearch = ""

    for i in range(7,9):
        for j in range(1,6):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                thesis_reasearch = thesis_reasearch + 'None' + ','
            else:
                thesis_reasearch = thesis_reasearch + request.POST.get(key_is) + ','
    
    data['thesis_reasearch'] = thesis_reasearch.rstrip(',')



    sponsored_research = ""

    for i in range(9,10):
        for j in range(1,8):
            key_is = f'info_{i}_{j}'
            print(key_is)
            
            print(request.POST.get(key_is))
            if(request.POST.get(key_is) == ""):
                sponsored_research = sponsored_research + 'None' + ','
            else:
                sponsored_research = sponsored_research + request.POST.get(key_is) + ','
    
    data['sponsored_research'] = sponsored_research.rstrip(',')


    return data




def reverse_appraisal_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'name', 'designation', 'discipline', 'field_knowledge', 'designation', 'current_res_int',
        'instructional_tasks', 'research_element', 'publication', 'referred_conf',
        'conf_organised', 'memberships', 'honours', 'edt_of_rep_pub', 
        'expert_lec_del', 'mem_of_bos', 'extention_tasks',
        'add_assign', 'service_inst_community', 'other_contri', 'your_comments',
        'date', 'sign_faculty', 'remarks', 'sign_hod', 'sign_director'
    ]

  
    for key in simple_keys:
        value = getattr(data, key)
        reversed_data[key] = value if value != 'None' else ''

    # Reversing array-like values
    # reversed_data['details_of_family_members_already_done'] = getattr(data,'details_of_family_members_already_done').split(',')
    
    courses_taught = getattr(data,'courses_taught').split(',')
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
    new_courses_introduced = getattr(data,'new_courses_introduced').split(',')
    for i in range(3, 5):
        for j in range(1, 4):
            key = f'info_{i}_{j}'
            value = new_courses_introduced.pop(0)
            reversed_data[key] = value if value != 'None' else ''
        

        
    new_courses_developed = getattr(data,'new_courses_developed').split(',')
    for i in range(5, 7):
        for j in range(1, 5):
            key = f'info_{i}_{j}'
            value = new_courses_developed.pop(0)
            reversed_data[key] = value if value != 'None' else ''



    thesis_reasearch = getattr(data,'thesis_reasearch').split(',')
    for i in range(7, 9):
        for j in range(1, 6):
            key = f'info_{i}_{j}'
            value = thesis_reasearch.pop(0)
            reversed_data[key] = value if value != 'None' else ''



    sponsored_research = getattr(data,'sponsored_research').split(',')
    for i in range(9, 10):
        for j in range(1, 8):
            key = f'info_{i}_{j}'
            value = sponsored_research.pop(0)
            reversed_data[key] = value if value != 'None' else ''

    return reversed_data
