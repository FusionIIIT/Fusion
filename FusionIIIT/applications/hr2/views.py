from django.shortcuts import render
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
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo
from html import escape
from io import BytesIO
import re

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
