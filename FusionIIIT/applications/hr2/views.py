from django.shortcuts import render
from .models import *
from applications.globals.models import ExtraInfo
from applications.globals.models import *
from django.db.models import Q
from django.http import Http404
from .forms import EditDetailsForm, EditConfidentialDetailsForm, EditServiceBookForm, NewUserForm, AddExtraInfo, CPDAForm
from django.contrib import messages
from applications.eis.models import *
from django.http import HttpResponse, HttpResponseRedirect
from applications.establishment.models import *
from applications.establishment.views import *
from applications.eis.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo
from html import escape
from io import BytesIO
import re
from applications.filetracking.sdk.methods import *
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import (get_object_or_404, redirect, render,
                              render)


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


def dashboard(request):
    template = 'hr2Module/new_dashboard.html'
    return render(request, template)

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


# def cpda_form(request, id):
#     """ Views for edit details"""
#     template = 'hr2Module/cpda_form.html'

#     try:
#         employee = ExtraInfo.objects.get(user__id=id)
#     except ExtraInfo.DoesNotExist:
#         raise Http404("Employee does not exist")

#     if(employee.user_type == 'faculty'):
#         if request.method == "POST":
#             form = CPDAForm(request.POST)
#             if form.is_valid():
#                 cpda_instance = form.save(commit=False)
#                 cpda_instance.extra_info = employee
#                 cpda_instance.save()

#                 print("Created Cpda Object!")


#                 uploader = "21BCS183"
#                 uploader_designation = "student"
#                 receiver = "21BCS185"
#                 receiver_designation = "hradmin"
#                 src_module = "HR"
#                 src_object_id = str(cpda_instance.id)
#                 file_extra_JSON = {"key": "value"}

#                 # Create a file representing the LTC form and send it to HR admin
#                 file_id = create_file(
#                     uploader=uploader,
#                     uploader_designation=uploader_designation,
#                     receiver=receiver,
#                     receiver_designation=receiver_designation,
#                     src_module=src_module,
#                     src_object_id=src_object_id,
#                     file_extra_JSON=file_extra_JSON,
#                     attached_file=None  # Attach any file if necessary
#                 )

#                 print("Sent the file to Hradmin!")

#                 messages.success(request, "CPDA Form submitted successfully")

#             else:
#                 messages.warning(request, "Error in submitting form")
#         else:
#             form = CPDAForm()

#         context = {'form': form, 'employee': employee}
#         return render(request, template, context)

# def view_cpda_form(request, id):
   
#     cpda_request = get_object_or_404(CPDAform, id=id)
#     context = {
#         'cpda_form': [cpda_request]
#     }
#     # print("cpda object: ", cpda_request)
#     return render(request, 'hr2Module/view_cpda_form.html', context)


# def faculty_cpda_form_view(request, id):
   
#     cpda_request = get_object_or_404(CPDAform, name = id)
#     context = {
#         'cpda_request': cpda_request
#     }
#     print("cpda object: ", cpda_request)
#     return render(request, 'hr2Module/view_cpda_form.html', context)

# def view_cpda_hr_admin(request):
#     if request.method == "GET":
#         # Replace the following line with your logic to retrieve the list of submitted forms
#         cpda_requests = CPDAform.objects.all()  # Query all CPDAform objects
        
#         context = {
#             'cpda_requests': cpda_requests
#         }
#         return render(request, 'hr2Module/view_cpda_form_hrAdmin.html', context)




# 
# 
# 
# 
# def reverse_cpda_pre_processing(cpda_form_data):
#     reversed_data = {}

#     # Reverse general information
#     reversed_data['name'] = [cpda_form_data['name']]
#     reversed_data['block_year'] = [str(cpda_form_data['block_year'])]
#     reversed_data['pf_no'] = [str(ltc_form_data['pf_no'])]
#     reversed_data['basic_pay_salary'] = [str(ltc_form_data['basic_pay_salary'])]
#     reversed_data['designation'] = [ltc_form_data['designation']]
#     reversed_data['department_info'] = [ltc_form_data['department_info']]
#     reversed_data['leave_availability'] = ['True'] if ltc_form_data['leave_availability'] else ['False']
#     reversed_data['leave_start_date'] = [ltc_form_data['leave_start_date']]
#     reversed_data['leave_end_date'] = [ltc_form_data['leave_end_date']]
#     reversed_data['date_of_leave_for_family'] = [ltc_form_data['date_of_leave_for_family']]
#     reversed_data['nature_of_leave'] = [ltc_form_data['nature_of_leave']]
#     reversed_data['purpose_of_leave'] = [ltc_form_data['purpose_of_leave']]
#     reversed_data['hometown_or_not'] = ['True'] if ltc_form_data['hometown_or_not'] else ['False']
#     reversed_data['place_of_visit'] = [ltc_form_data['place_of_visit']]
#     reversed_data['address_during_leave'] = [ltc_form_data['address_during_leave']]

#     # Reverse details of family members
#     print("no")
#     family_members = ltc_form_data['[details_of_family_members_already_done]'].split(',')
#     print("ywa",family_members)
#     for i, member in enumerate(family_members, start=1):
#         reversed_data[f'info_{i}_1'] = [member.split(',')[0]]
#         reversed_data[f'info_{i}_2'] = [member.split(',')[1]]
#         reversed_data[f'info_{i}_3'] = [member.split(',')[2]]

#     # Reverse details of dependents
#     dependents = ltc_form_data['details_of_dependents'].split(',')
#     for i, dependent in enumerate(dependents, start=1):
#         reversed_data[f'd_info_{i}_1'] = [dependent.split(',')[0]]
#         reversed_data[f'd_info_{i}_2'] = [dependent.split(',')[1]]
#         reversed_data[f'd_info_{i}_3'] = [dependent.split(',')[2]]
#         reversed_data[f'd_info_{i}_4'] = [dependent.split(',')[3]]

#     # Reverse remaining fields
#     reversed_data['amount_of_advance_required'] = [str(ltc_form_data['amount_of_advance_required'])]
#     reversed_data['certified_family_dependents'] = [ltc_form_data['certified_family_dependents']]
#     reversed_data['certified_advance'] = [str(ltc_form_data['certified_advance'])]
#     reversed_data['adjusted_month'] = [ltc_form_data['adjusted_month']]
#     reversed_data['date'] = [ltc_form_data['date']]
#     reversed_data['phone_number_for_contact'] = [str(ltc_form_data['phone_number_for_contact'])]

#     return reversed_data




# def cpda_pre_processing(request):
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



def cpda_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    print(employee.user_type)

    
    if(employee.user_type == 'faculty'):
        template = 'hr2Module/cpda_form.html'

        if request.method == "POST":
            try:
                print("Creating cpda object!")

                # print(ltc_pre_processing(request))
                sanction_status_str = request.POST.get('sanction_status')
                if sanction_status_str.lower() == 'true':
                    sanction_status = True
                elif sanction_status_str.lower() == 'false':
                    sanction_status = False
                else:
                    # Handle invalid value here, maybe raise an error or set a default value
                    sanction_status = False  # Setting a default value of False


                # ltc_form_data = ltc_pre_processing(request)
                name = request.POST.get('name')
                designation = request.POST.get('designation')
                pf_no = request.POST.get('pf_no')
                purpose = request.POST.get('purpose')
                amount_required = request.POST.get('amount_required')
                adjusted_pda = request.POST.get('adjusted_pda')
                achievements_uploaded_date = request.POST.get('achievements_uploaded_date')
                submission_date = request.POST.get('submission_date')
                recomm_hod_confirm = request.POST.get('recomm_hod_confirm')
                date_rspc_confirm = request.POST.get('date_rspc_confirm')
                balance_available = request.POST.get('balance_available')
                advance_amount_pda = request.POST.get('advance_amount_pda')
                dealing_asstt_name = request.POST.get('dealing_asstt_name')
                ar_dr_name = request.POST.get('ar_dr_name')
                check_amount = request.POST.get('check_amount')
                dealing_asstt_ia_name = request.POST.get('dealing_asstt_ia_name')
                ar_dr_ia_name = request.POST.get('ar_dr_ia_name')
                # sanction_status = request.POST.get('sanction_status')
                copy_to = request.POST.get('copy_to')

                cpda_form = CPDAform.objects.create(
                    # id=id,
                    name=name,
                    designation=designation,
                    pf_no=pf_no,
                    purpose=purpose,
                    amount_required=amount_required,
                    adjusted_pda=adjusted_pda,
                    achievements_uploaded_date=achievements_uploaded_date,
                    submission_date=submission_date,
                    recomm_hod_confirm=recomm_hod_confirm,
                    date_rspc_confirm=date_rspc_confirm,
                    balance_available=balance_available,
                    advance_amount_pda=advance_amount_pda,
                    dealing_asstt_name=dealing_asstt_name,
                    ar_dr_name=ar_dr_name,
                    check_amount=check_amount,
                    dealing_asstt_ia_name=dealing_asstt_ia_name,
                    ar_dr_ia_name=ar_dr_ia_name,
                    sanction_status=sanction_status,
                    copy_to=copy_to
                )

                print("Created Cpda Object!")


                uploader = "21BCS183"
                uploader_designation = "student"
                receiver = "21BCS185"
                receiver_designation = "hradmin"
                src_module = "HR"
                src_object_id = str(cpda_form.id)
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
                print("Sent the file to Hradmin!")

                messages.success(request, "CPDA form filled successfully")

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

         # Query all CPDA requests
        name = "aojha"
        cpda_requests = CPDAform.objects.filter(name=name)

        context = {'employee': employee, 'cpda_requests': cpda_requests}

        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')

# def view_ltc_form(request, id):
#     ltc_request = get_object_or_404(LTCform, id=id)

    # # Preprocessing data
    # family_mem_a = ltc_form.family_members_about_to_avail.split(',')[0].strip() if ltc_form.family_members_about_to_avail else ''
    # family_mem_b = ltc_form.family_members_about_to_avail.split(',')[1].strip() if ltc_form.family_members_about_to_avail else ''
    # family_mem_c = ltc_form.family_members_about_to_avail.split(',')[2].strip() if ltc_form.family_members_about_to_avail else ''
    # ltc_form.details_of_family_members_already_done = ', '.join(filter(None, [family_mem_a, family_mem_b, family_mem_c]))

    # family_members = []
    # for i in range(1, 7):  
    #     name = getattr(ltc_form, f'info_{i}_2', '')  
    #     age = getattr(ltc_form, f'info_{i}_3', '')   
    #     if name and age:
    #         family_members.append(f"{name} ({age} years)")
    # ltc_form.family_members_about_to_avail = ', '.join(family_members)

    # dependents = []
    # for i in range(1, 7): 
    #     name = getattr(ltc_form, f'd_info_{i}_2', '')  
    #     age = getattr(ltc_form, f'd_info_{i}_3', '')   
    #     why_dependent = getattr(ltc_form, f'd_info_{i}_4', '')  
    #     if name and age:
    #         dependents.append(f"{name} ({age} years), {why_dependent}")
    # ltc_form.details_of_dependents = ', '.join(dependents)


    # context = {
    #     'ltc_form': [ltc_request]
    # }
    

# def view_ltc_form(request, id):
   
#     ltc_request = get_object_or_404(LTCform, id=id)
#     context = {
#         'ltc_form': [ltc_request]
#     }
        
#     return render(request, 'hr2Module/view_ltc_form.html', context)
    

def view_cpda_form(request, id):
   
    cpda_request = get_object_or_404(CPDAform, id=id)
    
    # print("cpda object: ", cpda_request)
    # print(cpda_request['details_of_family_members_already_done'])
    # print("cpda object: ", reverse_cpda_pre_processing(cpda_request))
    # cpda_request = reverse_cpda_pre_processing(cpda_request)

    # print(cpda_request)

    context = {

        # 'name' : cpda_request.name,
        # 'pf_no': cpda_request.pf_no,
        # 'designation': cpda_request.designation,
        # 'purpose': cpda_request.purpose,
        # 'amount_required': cpda_request.amount_required,
        # 'adjusted_pda': cpda_request.adjusted_pda,
        # 'achievements_uploaded_date': cpda_request.achievements_uploaded_date,
        # 'submission_date': cpda_request.submission_date,
        # 'recomm_hod_confirm': cpda_request.recomm_hod_confirm,
        # 'date_rspc_confirm': cpda_request.date_rspc_confirm,
        # 'balance_available': cpda_request.balance_available,
        # 'advance_amount_pda': cpda_request.advance_amount_pda,
        # 'dealing_asstt_name': cpda_request.dealing_asstt_name,
        # 'ar_dr_name': cpda_request.ar_dr_name,
        # 'check_amount': cpda_request.check_amount,
        # 'dealing_asstt_ia_name': cpda_request.dealing_asstt_ia_name,
        # 'ar_dr_ia_name': cpda_request.ar_dr_ia_name,
        # 'sanction_status': cpda_request.sanction_status,
        # 'copy_to': cpda_request.copy_to,
        # 'id': cpda_request.id,

        'cpda_form' : [cpda_request]
    }

    return render(request, 'hr2Module/view_cpda_form.html',context)

# def reverse_cpda_pre_processing(cpda_form_data):
#     reversed_data = {}

#     # Reverse general information
#     reversed_data['name'] = [cpda_form_data.name]
#     reversed_data['block_year'] = [str(cpda_form_data.block_year)]
#     reversed_data['pf_no'] = [str(cpda_form_data.pf_no)]
#     reversed_data['basic_pay_salary'] = [str(cpda_form_data.basic_pay_salary)]
#     reversed_data['designation'] = [cpda_form_data.designation]
#     reversed_data['department_info'] = [cpda_form_data.department_info]
#     reversed_data['leave_availability'] = ['True'] if cpda_form_data.leave_availability else ['False']
#     reversed_data['leave_start_date'] = [cpda_form_data.leave_start_date]
#     reversed_data['leave_end_date'] = [cpda_form_data.leave_end_date]
#     reversed_data['date_of_leave_for_family'] = [cpda_form_data.date_of_leave_for_family]
#     reversed_data['nature_of_leave'] = [cpda_form_data.nature_of_leave]
#     reversed_data['purpose_of_leave'] = [cpda_form_data.purpose_of_leave]
#     reversed_data['hometown_or_not'] = ['True'] if cpda_form_data.hometown_or_not else ['False']
#     reversed_data['place_of_visit'] = [cpda_form_data.place_of_visit]
#     reversed_data['address_during_leave'] = [cpda_form_data.address_during_leave]

#     # Reverse details of family members
#     family_members = cpda_form_data.details_of_family_members_already_done.split(',')
    
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
#     dependents = cpda_form_data.details_of_dependents.split(',')

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
#     reversed_data['amount_of_advance_required'] = [str(cpda_form_data.amount_of_advance_required)]
#     reversed_data['certified_family_dependents'] = [cpda_form_data.certified_family_dependents]
#     reversed_data['certified_advance'] = [str(cpda_form_data.certified_advance)]
#     reversed_data['adjusted_month'] = [cpda_form_data.adjusted_month]
#     reversed_data['date'] = [cpda_form_data.date]
#     reversed_data['phone_number_for_contact'] = [str(cpda_form_data.phone_number_for_contact)]

#     return reversed_data

# hr admin get
def form_mangement_cpda(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15,19]
                                        
        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context= {
            'cpda_requests' : cpda_requests,
            'hr' : "1",
            'dire': "1",
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

    # Create a file representing the cpda form and send it to HR admin
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

    messages.success(request, "cpda form filled successfully")

    return HttpResponse("Sucess")
# hod ne get kiya
def form_mangement_cpda_get_hod(request):
    if request.method == "GET":
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username=username, designation=designation, src_module="HR")

        # Extract src_object_id values
        # src_object_ids = [(item['src_object_id']) for item in inbox]
        
        src_object_ids = []
        for item in inbox:
            src_object_ids.append(int(item['src_object_id'][2:3]))
        
        print(src_object_ids)

        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context = {
            'cpda_requests': cpda_requests,
            'hr': "1",
            'user_designation': designation,
            'dire': "1",
        }

        print(cpda_requests[0].name)

        return render(request, 'hr2Module/cpda_form.html', context)

    
def form_mangement_cpda_hod(request,id):
    print("Request of forward!")
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS017"
    # isko sahi krna h
    receiver_designation = "Director"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the cpda form and send it to HR admin
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

    print("Sent the file to Director!")

    messages.success(request, "cpda form filled successfully")

    return HttpResponse("Success")

# def form_mangement_cpda_get_ar(request):
#     if request.method == "GET":
#         username = "21BCS187"
#         # isko bhi sahi krna h
#         designation = "Dealing Assistant"
#         inbox = view_inbox(username=username, designation=designation, src_module="HR")

#         # Extract src_object_id values
#         # src_object_ids = [(item['src_object_id']) for item in inbox]
        
#         src_object_ids = []
#         for item in inbox:
#             src_object_ids.append(int(item['src_object_id'][2:4]))
        
#         print(src_object_ids)

#         ltc_requests = []

#         for src_object_id in src_object_ids:
#             ltc_request = get_object_or_404(LTCform, id=src_object_id)
#             ltc_requests.append(ltc_request)

#         context = {
#             'ltc_requests': ltc_requests,
#             'hr': "1",
#         }

#         print(ltc_requests[0].name)

#         return render(request, 'hr2Module/ltc_form.html', context)
    
def form_mangement_cpda_director(request,id):
    print("Request of forward!")
    uploader = "21BCS187"
    uploader_designation = "student"
    receiver = "21BCS017"
    # isko sahi krna h
    receiver_designation = "AR/DR"
    src_module = "HR"
    src_object_id = id,
    file_extra_JSON = {"key": "value"}

    # Create a file representing the cpda form and send it to HR admin
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

    print("Sent the file to AR/DR!")

    messages.success(request, "cpda form filled successfully")

    return HttpResponse("Sucess")
    
def form_mangement_cpda_get_director(request):
    if request.method == "GET":
        username = "21BCS017"
        # isko bhi sahi krna h
        designation = "Director"
        inbox = view_inbox(username=username, designation=designation, src_module="HR")

        # Extract src_object_id values
        # src_object_ids = [(item['src_object_id']) for item in inbox]

        # src_object_ids = [19]
        
        src_object_ids = []
        for item in inbox:
            src_object_ids.append(int(item['src_object_id'][2:3]))
        
        print(src_object_ids)

        cpda_requests = []

        for src_object_id in src_object_ids:
            cpda_request = get_object_or_404(CPDAform, id=src_object_id)
            cpda_requests.append(cpda_request)

        context = {
            'cpda_requests': cpda_requests,
            'hr': "1",
            'dire': "2"
        }

        print(cpda_requests[0].name)

        return render(request, 'hr2Module/cpda_form.html', context)


def reverse_ltc_pre_processing(ltc_form_data):
    reversed_data = {}

    # Reverse general information
    reversed_data['name'] = [ltc_form_data['name']]
    reversed_data['block_year'] = [str(ltc_form_data['block_year'])]
    reversed_data['pf_no'] = [str(ltc_form_data['pf_no'])]
    reversed_data['basic_pay_salary'] = [str(ltc_form_data['basic_pay_salary'])]
    reversed_data['designation'] = [ltc_form_data['designation']]
    reversed_data['department_info'] = [ltc_form_data['department_info']]
    reversed_data['leave_availability'] = ['True'] if ltc_form_data['leave_availability'] else ['False']
    reversed_data['leave_start_date'] = [ltc_form_data['leave_start_date']]
    reversed_data['leave_end_date'] = [ltc_form_data['leave_end_date']]
    reversed_data['date_of_leave_for_family'] = [ltc_form_data['date_of_leave_for_family']]
    reversed_data['nature_of_leave'] = [ltc_form_data['nature_of_leave']]
    reversed_data['purpose_of_leave'] = [ltc_form_data['purpose_of_leave']]
    reversed_data['hometown_or_not'] = ['True'] if ltc_form_data['hometown_or_not'] else ['False']
    reversed_data['place_of_visit'] = [ltc_form_data['place_of_visit']]
    reversed_data['address_during_leave'] = [ltc_form_data['address_during_leave']]
    # reversed_data['serialNumber'] = [ltc_form_data['serialNumber']]
    # reversed_data['fullName'] = [ltc_form_data['fullName']]
    # reversed_data['age'] = [ltc_form_data['age']]

    # Reverse details of family members
    print("no")
    family_members = ltc_form_data['[details_of_family_members_already_done]'].split(',')
    print("ywa",family_members)
    for i, member in enumerate(family_members, start=1):
        reversed_data[f'info_{i}_1'] = [member.split(',')[0]]
        reversed_data[f'info_{i}_2'] = [member.split(',')[1]]
        reversed_data[f'info_{i}_3'] = [member.split(',')[2]]

    # Reverse details of dependents
    dependents = ltc_form_data['details_of_dependents'].split(',')
    for i, dependent in enumerate(dependents, start=1):
        reversed_data[f'd_info_{i}_1'] = [dependent.split(',')[0]]
        reversed_data[f'd_info_{i}_2'] = [dependent.split(',')[1]]
        reversed_data[f'd_info_{i}_3'] = [dependent.split(',')[2]]
        reversed_data[f'd_info_{i}_4'] = [dependent.split(',')[3]]

    # Reverse remaining fields
    reversed_data['amount_of_advance_required'] = [str(ltc_form_data['amount_of_advance_required'])]
    reversed_data['certified_family_dependents'] = [ltc_form_data['certified_family_dependents']]
    reversed_data['certified_advance'] = [str(ltc_form_data['certified_advance'])]
    reversed_data['adjusted_month'] = [ltc_form_data['adjusted_month']]
    reversed_data['date'] = [ltc_form_data['date']]
    reversed_data['phone_number_for_contact'] = [str(ltc_form_data['phone_number_for_contact'])]

    return reversed_data




def ltc_pre_processing(request):
    ltc_form_data = {}

    # Extract general information
    ltc_form_data['name'] = request.POST.get('name')
    ltc_form_data['block_year'] = int(request.POST.get('block_year'))
    ltc_form_data['pf_no'] = int(request.POST.get('pf_no'))
    ltc_form_data['basic_pay_salary'] = int(request.POST.get('basic_pay_salary'))
    ltc_form_data['designation'] = request.POST.get('designation')
    ltc_form_data['department_info'] = request.POST.get('department_info')
    ltc_form_data['leave_availability'] = request.POST.getlist('leave_availability') == ['True', 'True']
    ltc_form_data['leave_start_date'] = request.POST.get('leave_start_date')
    ltc_form_data['leave_end_date'] = request.POST.get('leave_end_date')
    ltc_form_data['date_of_leave_for_family'] = request.POST.get('date_of_leave_for_family')
    ltc_form_data['nature_of_leave'] = request.POST.get('nature_of_leave')
    ltc_form_data['purpose_of_leave'] = request.POST.get('purpose_of_leave')
    ltc_form_data['hometown_or_not'] = request.POST.get('hometown_or_not') == 'True'
    ltc_form_data['place_of_visit'] = request.POST.get('place_of_visit')
    ltc_form_data['address_during_leave'] = request.POST.get('address_during_leave')
    # ltc_form_data['serialNumber'] = request.POST.get('serialNumber')
    # ltc_form_data['fullName'] = request.POST.get('fullName')
    # ltc_form_data['age'] = request.POST.get('age')

    # Extract details of family members
    family_members = []
    for i in range(1, 7):
        if request.POST.get(f'info_{i}_1'):
            family_member = ','.join(request.POST.getlist(f'info_{i}_{j}')[0] for j in range(1, 4))
            family_members.append(family_member)
    ltc_form_data['details_of_family_members_already_done'] = ','.join(family_members)

    # Extract details of dependents
    dependents = []
    for i in range(1, 7):
        if request.POST.get(f'd_info_{i}_1'):
            dependent = ','.join(request.POST.getlist(f'd_info_{i}_{j}')[0] for j in range(1, 5))
            dependents.append(dependent)
    ltc_form_data['details_of_dependents'] = ','.join(dependents)

    # Extract remaining fields
    ltc_form_data['amount_of_advance_required'] = int(request.POST.get('amount_of_advance_required'))
    ltc_form_data['certified_family_dependents'] = request.POST.get('certified_family_dependents')
    ltc_form_data['certified_advance'] = int(request.POST.get('certified_advance'))
    ltc_form_data['adjusted_month'] = request.POST.get('adjusted_month')
    ltc_form_data['date'] = request.POST.get('date')
    ltc_form_data['phone_number_for_contact'] = int(request.POST.get('phone_number_for_contact'))

    return ltc_form_data

@csrf_exempt
def ltc_form(request):
    if request.method == "POST":
        data = json.loads(request.body)
        for item in data:
            LTCform.objects.create(
                serial_number=item['serialNumber'], 
                full_name=item['fullName'], 
                age=item['age']
            )
        return JsonResponse({'message': 'Data saved successfully'})
    else:
        return JsonResponse({'error': 'Invalid request method'})


def ltc_form(request, id):
    """ Views for edit details"""
    try:
        employee = ExtraInfo.objects.get(user__id=id)
    except:
        raise Http404("Employee does not exist! id doesnt exist")

    print(employee.user_type)

    
    if(employee.user_type == 'faculty'):
        template = 'hr2Module/ltc_form.html'

        if request.method == "POST":
            try:
                print("Creating ltc object!")

                print(ltc_pre_processing(request))


                ltc_form_data = ltc_pre_processing(request)

                ltc_form = LTCform.objects.create(
                    employee_id=id,
                    name=ltc_form_data['name'],
                    block_year=ltc_form_data['block_year'],
                    pf_no=ltc_form_data['pf_no'],
                    basic_pay_salary=ltc_form_data['basic_pay_salary'],
                    designation=ltc_form_data['designation'],
                    department_info=ltc_form_data['department_info'],
                    leave_availability=ltc_form_data['leave_availability'],
                    leave_start_date=ltc_form_data['leave_start_date'],
                    leave_end_date=ltc_form_data['leave_end_date'],
                    date_of_leave_for_family=ltc_form_data['date_of_leave_for_family'],
                    nature_of_leave=ltc_form_data['nature_of_leave'],
                    purpose_of_leave=ltc_form_data['purpose_of_leave'],
                    hometown_or_not=ltc_form_data['hometown_or_not'],
                    place_of_visit=ltc_form_data['place_of_visit'],
                    address_during_leave=ltc_form_data['address_during_leave'],
                    details_of_family_members_already_done=ltc_form_data['details_of_family_members_already_done'],
                    details_of_dependents=ltc_form_data['details_of_dependents'],
                    amount_of_advance_required=ltc_form_data['amount_of_advance_required'],
                    certified_family_dependents=ltc_form_data['certified_family_dependents'],
                    certified_advance=ltc_form_data['certified_advance'],
                    adjusted_month=ltc_form_data['adjusted_month'],
                    date=ltc_form_data['date'],
                    phone_number_for_contact=ltc_form_data['phone_number_for_contact'],
                    # serialNumber=ltc_form_data['serialNumber'],
                    # fullName=ltc_form_data['fullName'],
                    # age=ltc_form_data['age']
                )

                print("Created Ltc Object!")


                uploader = "21BCS183"
                uploader_designation = "student"
                receiver = "21BCS185"
                receiver_designation = "hradmin"
                src_module = "HR_ltc"
                src_object_id = str(ltc_form.id)
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

                print("Sent the file to Hradmin!")

                messages.success(request, "Ltc form filled successfully")

            except Exception as e:
                print("error" , e)
                messages.warning(request, "Fill not correctly")
                context = {'employee': employee}
                return render(request, template, context)

    

         # Query all LTC requests
        ltc_requests = LTCform.objects.filter(employee_id=id)

        context = {'employee': employee, 'ltc_requests': ltc_requests}

        return render(request, template, context)
    else:
        return render(request, 'hr2Module/edit.html')

# def view_ltc_form(request, id):
#     ltc_request = get_object_or_404(LTCform, id=id)

    # # Preprocessing data
    # family_mem_a = ltc_form.family_members_about_to_avail.split(',')[0].strip() if ltc_form.family_members_about_to_avail else ''
    # family_mem_b = ltc_form.family_members_about_to_avail.split(',')[1].strip() if ltc_form.family_members_about_to_avail else ''
    # family_mem_c = ltc_form.family_members_about_to_avail.split(',')[2].strip() if ltc_form.family_members_about_to_avail else ''
    # ltc_form.details_of_family_members_already_done = ', '.join(filter(None, [family_mem_a, family_mem_b, family_mem_c]))

    # family_members = []
    # for i in range(1, 7):  
    #     name = getattr(ltc_form, f'info_{i}_2', '')  
    #     age = getattr(ltc_form, f'info_{i}_3', '')   
    #     if name and age:
    #         family_members.append(f"{name} ({age} years)")
    # ltc_form.family_members_about_to_avail = ', '.join(family_members)

    # dependents = []
    # for i in range(1, 7): 
    #     name = getattr(ltc_form, f'd_info_{i}_2', '')  
    #     age = getattr(ltc_form, f'd_info_{i}_3', '')   
    #     why_dependent = getattr(ltc_form, f'd_info_{i}_4', '')  
    #     if name and age:
    #         dependents.append(f"{name} ({age} years), {why_dependent}")
    # ltc_form.details_of_dependents = ', '.join(dependents)


    # context = {
    #     'ltc_form': [ltc_request]
    # }
    

# def view_ltc_form(request, id):
   
#     ltc_request = get_object_or_404(LTCform, id=id)
#     context = {
#         'ltc_form': [ltc_request]
#     }
        
#     return render(request, 'hr2Module/view_ltc_form.html', context)
    

def view_ltc_form(request, id):
   
    ltc_request = get_object_or_404(LTCform, id=id)
    
    # print("ltc object: ", ltc_request)
    # print(ltc_request['details_of_family_members_already_done'])
    # print("ltc object: ", reverse_ltc_pre_processing(ltc_request))
    ltc_request = reverse_ltc_pre_processing(ltc_request)

    print(ltc_request)

    context = {
        'block_year' : ltc_request["block_year"][0],
        'pf_no': ltc_request["pf_no"][0],
        'designation': ltc_request["designation"][0],
        'name': ltc_request["name"][0],
        'basic_pay_salary': ltc_request["basic_pay_salary"][0],
        'department_info': ltc_request["department_info"][0],
        'date_of_leave_for_family': ltc_request["date_of_leave_for_family"][0],
        'leave_end_date': ltc_request["leave_end_date"][0],
        'leave_start_date': ltc_request["leave_start_date"][0],
        'nature_of_leave': ltc_request["nature_of_leave"][0],
        'purpose_of_leave': ltc_request["purpose_of_leave"][0],
        'place_of_visit': ltc_request["place_of_visit"][0],
        'address_during_leave': ltc_request["address_during_leave"][0],


        'details_of_family_members_already_done': ltc_request["name"][0],

        'info_1_2': ltc_request["info_1_2"][0],

        'info_1_1': ltc_request["info_1_1"][0],

        'amount_of_advance_required': ltc_request["amount_of_advance_required"][0],
        'certified_family_dependents': ltc_request["certified_family_dependents"][0],
        'certified_advance': ltc_request["certified_advance"][0],
        'date': ltc_request["date"][0],
        'adjusted_month': ltc_request["adjusted_month"][0],
        'phone_number_for_contact': ltc_request["phone_number_for_contact"][0],

        
        'ltc_form' : ltc_request
    }

    return render(request, 'hr2Module/view_ltc_form.html',context)

def reverse_ltc_pre_processing(ltc_form_data):
    reversed_data = {}

    # Reverse general information
    reversed_data['name'] = [ltc_form_data.name]
    reversed_data['block_year'] = [str(ltc_form_data.block_year)]
    reversed_data['pf_no'] = [str(ltc_form_data.pf_no)]
    reversed_data['basic_pay_salary'] = [str(ltc_form_data.basic_pay_salary)]
    reversed_data['designation'] = [ltc_form_data.designation]
    reversed_data['department_info'] = [ltc_form_data.department_info]
    reversed_data['leave_availability'] = ['True'] if ltc_form_data.leave_availability else ['False']
    reversed_data['leave_start_date'] = [ltc_form_data.leave_start_date]
    reversed_data['leave_end_date'] = [ltc_form_data.leave_end_date]
    reversed_data['date_of_leave_for_family'] = [ltc_form_data.date_of_leave_for_family]
    reversed_data['nature_of_leave'] = [ltc_form_data.nature_of_leave]
    reversed_data['purpose_of_leave'] = [ltc_form_data.purpose_of_leave]
    reversed_data['hometown_or_not'] = ['True'] if ltc_form_data.hometown_or_not else ['False']
    reversed_data['place_of_visit'] = [ltc_form_data.place_of_visit]
    reversed_data['address_during_leave'] = [ltc_form_data.address_during_leave]

    # Reverse details of family members
    family_members = ltc_form_data.details_of_family_members_already_done.split(',')
    
    count = 0

    for i in range(1, 7):
        if(len(family_members) > count+3):
            reversed_data[f'info_{i}_1'] = [family_members[count]]
            reversed_data[f'info_{i}_2'] = [family_members[count+1]]
            reversed_data[f'info_{i}_3'] = [family_members[count+2]]
            count+=3
        else:
            reversed_data[f'info_{i}_1'] = ['']
            reversed_data[f'info_{i}_2'] = ['']
            reversed_data[f'info_{i}_3'] = ['']
            count+=3

    # for i, member in enumerate(family_members, start=1):
    #     if member:
    #         reversed_data[f'info_{i}_1'] = [member.split(',')[0]]
    #         reversed_data[f'info_{i}_2'] = [member.split(',')[1]]
    #         reversed_data[f'info_{i}_3'] = [member.split(',')[2]]
    #     else:
    #         # If family member information is not provided, use empty strings
    #         reversed_data[f'info_{i}_1'] = ['']
    #         reversed_data[f'info_{i}_2'] = ['']
    #         reversed_data[f'info_{i}_3'] = ['']

    # Reverse details of dependents
    dependents = ltc_form_data.details_of_dependents.split(',')

    count=0

    for i in range(1, 7):
        if(len(dependents) > count+4):
            reversed_data[f'd_info_{i}_1'] = [dependents[count]]
            reversed_data[f'd_info_{i}_2'] = [dependents[count+1]]
            reversed_data[f'd_info_{i}_3'] = [dependents[count+2]]
            reversed_data[f'd_info_{i}_4'] = [dependents[count+3]]
            count+=4
        else:
            reversed_data[f'd_info_{i}_1'] = ['']
            reversed_data[f'd_info_{i}_2'] = ['']
            reversed_data[f'd_info_{i}_3'] = ['']
            reversed_data[f'd_info_{i}_4'] = ['']
            count+=4


    # for i, dependent in enumerate(dependents, start=1):
    #     if dependent:
    #         reversed_data[f'd_info_{i}_1'] = [dependent.split(',')[0]]
    #         reversed_data[f'd_info_{i}_2'] = [dependent.split(',')[1]]
    #         reversed_data[f'd_info_{i}_3'] = [dependent.split(',')[2]]
    #         reversed_data[f'd_info_{i}_4'] = [dependent.split(',')[3]]
    #     else:
    #         # If dependent information is not provided, use empty strings
    #         reversed_data[f'd_info_{i}_1'] = ['']
    #         reversed_data[f'd_info_{i}_2'] = ['']
    #         reversed_data[f'd_info_{i}_3'] = ['']
    #         reversed_data[f'd_info_{i}_4'] = ['']

    # Reverse remaining fields
    reversed_data['amount_of_advance_required'] = [str(ltc_form_data.amount_of_advance_required)]
    reversed_data['certified_family_dependents'] = [ltc_form_data.certified_family_dependents]
    reversed_data['certified_advance'] = [str(ltc_form_data.certified_advance)]
    reversed_data['adjusted_month'] = [ltc_form_data.adjusted_month]
    reversed_data['date'] = [ltc_form_data.date]
    reversed_data['phone_number_for_contact'] = [str(ltc_form_data.phone_number_for_contact)]

    return reversed_data

# hr admin get
def form_mangement_ltc(request):
    if(request.method == "GET"):
        username = "21BCS185"
        designation = "hradmin"
        inbox = view_inbox(username = username, designation = designation, src_module = "HR_ltc")

        # print(inbox)

        # Extract src_object_id values
        src_object_ids = [item['src_object_id'] for item in inbox]
        print(src_object_ids)

        # src_object_ids = [14,15,19]
                                        
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
    src_module = "HR_ltc"
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
# hod ne get kiya
def form_mangement_ltc_get_hod(request):
    if request.method == "GET":
        username = "21BCS181"
        designation = "HOD"
        inbox = view_inbox(username=username, designation=designation, src_module="HR_ltc")

        # Extract src_object_id values
        # src_object_ids = [(item['src_object_id']) for item in inbox]
        
        src_object_ids = []
        for item in inbox:
            src_object_ids.append(int(item['src_object_id'][2:3]))
        
        print(src_object_ids)

        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context = {
            'ltc_requests': ltc_requests,
            'hr': "1",
            'user_designation': designation,
        }

        print(ltc_requests[0].name)

        return render(request, 'hr2Module/ltc_form.html', context)

    
def form_mangement_ltc_hod(request,id):
    print("Request of forward!")
    uploader = "21BCS183"
    uploader_designation = "student"
    receiver = "21BCS017"
    # isko sahi krna h
    receiver_designation = "Director"
    src_module = "HR_ltc"
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

    print("Sent the file to Director!")

    messages.success(request, "Ltc form filled successfully")

    return HttpResponse("Sucess")

# def form_mangement_ltc_get_ar(request):
#     if request.method == "GET":
#         username = "21BCS187"
#         # isko bhi sahi krna h
#         designation = "Dealing Assistant"
#         inbox = view_inbox(username=username, designation=designation, src_module="HR_ltc")

#         # Extract src_object_id values
#         # src_object_ids = [(item['src_object_id']) for item in inbox]
        
#         src_object_ids = []
#         for item in inbox:
#             src_object_ids.append(int(item['src_object_id'][2:4]))
        
#         print(src_object_ids)

#         ltc_requests = []

#         for src_object_id in src_object_ids:
#             ltc_request = get_object_or_404(LTCform, id=src_object_id)
#             ltc_requests.append(ltc_request)

#         context = {
#             'ltc_requests': ltc_requests,
#             'hr': "1",
#         }

#         print(ltc_requests[0].name)

#         return render(request, 'hr2Module/ltc_form.html', context)
    
def form_mangement_ltc_director(request,id):
    print("Request of forward!")
    uploader = "21BCS187"
    uploader_designation = "student"
    receiver = "21BCS017"
    # isko sahi krna h
    receiver_designation = "AR/DR"
    src_module = "HR_ltc"
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

    print("Sent the file to AR/DR!")

    messages.success(request, "Ltc form filled successfully")

    return HttpResponse("Sucess")
    
def form_mangement_ltc_get_director(request):
    if request.method == "GET":
        username = "21BCS017"
        # isko bhi sahi krna h
        designation = "Director"
        inbox = view_inbox(username=username, designation=designation, src_module="HR_ltc")

        # Extract src_object_id values
        # src_object_ids = [(item['src_object_id']) for item in inbox]

        # src_object_ids = [19]
        
        src_object_ids = []
        for item in inbox:
            src_object_ids.append(int(item['src_object_id'][2:3]))
        
        print(src_object_ids)

        ltc_requests = []

        for src_object_id in src_object_ids:
            ltc_request = get_object_or_404(LTCform, id=src_object_id)
            ltc_requests.append(ltc_request)

        context = {
            'ltc_requests': ltc_requests,
            'hr': "1",
        }

        print(ltc_requests[0].name)

        return render(request, 'hr2Module/ltc_form.html', context)      


@login_required(login_url='/accounts/login')
def dashboard(request):
    user = request.user
    print(request.user)

    user_id = ExtraInfo.objects.get(user=user).user_id
    print(user_id)
    context = {'user_id': user_id}
    print("context",user_id)
    return render(request, 'hr2Module/dashboard.html',context)         