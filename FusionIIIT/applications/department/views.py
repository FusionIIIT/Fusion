from cgitb import html
from datetime import date
import json
from multiprocessing import Process

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
# Create your views here.
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty,DepartmentInfo)
from applications.eis.models import (faculty_about, emp_research_projects)
from .models import Information
from notification.views import department_notif
from .models import SpecialRequest, Announcements , Information
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def department_information(request):

    cse_info = Information.objects.filter(department_id=51).first()
    ece_info = Information.objects.filter(department_id=30).first()
    me_info = Information.objects.filter(department_id=37).first()
    sm_info = Information.objects.filter(department_id=28).first()
    department_context = {
        "cse_info" : cse_info,
        "ece_info" : ece_info,
        "me_info" : me_info,
        "sm_info" : sm_info
    }
    # print(department_context)
    # print(me_info.phone_number,me_info.email,me_info.department_id)
    return department_context

def browse_announcements():
    """
    This function is used to browse Announcements Department-Wise
    made by different faculties and admin.

    @variables:
        cse_ann - Stores CSE Department Announcements
        ece_ann - Stores ECE Department Announcements
        me_ann - Stores ME Department Announcements
        sm_ann - Stores SM Department Announcements
        all_ann - Stores Announcements intended for all Departments
        context - Dictionary for storing all above data

    """
    cse_ann = Announcements.objects.filter(department="CSE")
    ece_ann = Announcements.objects.filter(department="ECE")
    me_ann = Announcements.objects.filter(department="ME")
    sm_ann = Announcements.objects.filter(department="SM")
    all_ann = Announcements.objects.filter(department="ALL")

    context = {
        "cse" : cse_ann,
        "ece" : ece_ann,
        "me" : me_ann,
        "sm" : sm_ann,
        "all" : all_ann
    }
    # print(context)
    return context

def get_make_request(user_id):
    """
    This function is used to get requests for maker

    @variables:
        req - Contains request queryset

    """
    req = SpecialRequest.objects.filter(request_maker=user_id)
    return req

def get_to_request(username):
    """
    This function is used to get requests for the receiver

    @variables:
        req - Contains request queryset

    """
    req = SpecialRequest.objects.filter(request_receiver=username)
    return req

@login_required(login_url='/accounts/login')
def dep_main(request):
    """
    This function is used to differentiate between Different users
    and redirect them to different urls.

    @param:
        request - contains metadata about the requested page

    @variables:
        fac_view - Check if user is Faculty
        student - Check if user is student
        context - Stores data returned by browse_announcement()
        context_f - Stores data returned by faculty()

    """
    user = request.user
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    ann_maker_id = user_info.id
    user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id)
    user_departmentid = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id).department_id
    
    requests_made = get_make_request(user_info)
    
    fac_view = request.user.holds_designations.filter(designation__name='faculty').exists()
    student = request.user.holds_designations.filter(designation__name='student').exists()
    staff = request.user.holds_designations.filter(designation__name='staff').exists()
    
    context = browse_announcements()
    context_f = faculty()
    user_designation = ""


    department_context = department_information(request)

    if fac_view:
        user_designation = "faculty"
    elif student:
        user_designation = "student"
    else:
        user_designation = "staff"

    if request.method == 'POST':
        request_type = request.POST.get('request_type', '')
        request_to = request.POST.get('request_to', '')
        request_details = request.POST.get('request_details', '')
        request_date = date.today()

        obj_sprequest, created_object = SpecialRequest.objects.get_or_create(request_maker=user_info,
                                                    request_date=request_date,
                                                    brief=request_type,
                                                    request_details=request_details,
                                                    status="Pending",
                                                    remarks="--",
                                                    request_receiver=request_to
                                                    )
    
    if user_designation == "student":
        department_templates = {
            51: 'department/cse_index.html',
            30: 'department/ece_index.html',
            37: 'department/me_index.html',
            53: 'department/sm_index.html'
        }
        default_template = 'department/cse_index.html'
        template_name = department_templates.get(user_departmentid, default_template)

        return render(request, template_name, {
            "announcements": context,
            "fac_list": context_f,
            "requests_made": requests_made,
            "department_info": department_context

        })
       
    elif user_designation=="faculty":
        return HttpResponseRedirect("facView")
    
    elif user_designation=="staff":
        return HttpResponseRedirect("staffView")

def faculty_view(request):
    """
    This function is contains data for Requests and Announcement Related methods.
    Data is added to Announcement Table using this function.

    @param:
        request - contains metadata about the requested page

    @variables:
        usrnm, user_info, ann_maker_id - Stores data needed for maker
        batch, programme, message, upload_announcement,
        department, ann_date, user_info - Gets and store data from FORM used for Announcements.

    """
    context_f = faculty()
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    ann_maker_id = user_info.id
    requests_received = get_to_request(usrnm)
    user_departmentid = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id).department_id
    department_context = department_information(request)
    
    if request.method == 'POST':
        batch = request.POST.get('batch', '')
        programme = request.POST.get('programme', '')
        message = request.POST.get('announcement', '')
        upload_announcement = request.FILES.get('upload_announcement')
        department = request.POST.get('department')
        ann_date = date.today()
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id)
        getstudents = ExtraInfo.objects.select_related('user')
        recipients = User.objects.filter(extrainfo__in=getstudents)

        obj1, created = Announcements.objects.get_or_create(maker_id=user_info,
                                    batch=batch,
                                    programme=programme,
                                    message=message,
                                    upload_announcement=upload_announcement,
                                    department = department,
                                    ann_date=ann_date)
        
        department_notif(usrnm, recipients , message)
        
    context = browse_announcements()
    
    department_templates = {
        51: 'department/csedep_request.html',
        30: 'department/ecedep_request.html',
        37: 'department/medep_request.html',
        53: 'department/smdep_request.html'
    }
    default_template = 'department/dep_request.html'
    
    template_name = department_templates.get(user_departmentid, default_template)
    
    return render(request, template_name, {
        "user_designation": user_info.user_type,
        "announcements": context,
        "request_to": requests_received,
        "fac_list": context_f,
        "department_info": department_context
    })
    

def staff_view(request):
    """
    This function is contains data for Requests and Announcement Related methods.
    Data is added to Announcement Table using this function.

    @param:
        request - contains metadata about the requested page

    @variables:
        usrnm, user_info, ann_maker_id - Stores data needed for maker
        batch, programme, message, upload_announcement,
        department, ann_date, user_info - Gets and store data from FORM used for Announcements for Students.

    """
    context_f = faculty()
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    ann_maker_id = user_info.id
    user_departmentid = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id).department_id

    department_context = department_information(request)
    
    requests_received = get_to_request(usrnm)
    if request.method == 'POST':
        form_type =   request.POST.get('form_type', '')
        if form_type == 'form1' :
            
            batch = request.POST.get('batch', '')
            programme = request.POST.get('programme', '')
            message = request.POST.get('announcement', '')
            upload_announcement = request.FILES.get('upload_announcement')
            department = request.POST.get('department')
            ann_date = date.today()
            user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id)
            getstudents = ExtraInfo.objects.select_related('user')
            recipients = User.objects.filter(extrainfo__in=getstudents)

            obj1, created = Announcements.objects.get_or_create(maker_id=user_info,
                                        batch=batch,
                                        programme=programme,
                                        message=message,
                                        upload_announcement=upload_announcement,
                                        department = department,
                                        ann_date=ann_date)
            department_notif(usrnm, recipients , message)
            
        elif form_type == 'form2' :
            
            email = request.POST.get('email', '')
            phone_number = request.POST.get('contact_number', '')
            facilites = request.POST.get('facilities', '')
            labs = request.POST.get('labs', '')
            department_id = user_departmentid

            # Check if a row with the specified department_id already exists
            try:
                department_info = Information.objects.get(department_id=department_id)
                # If row exists, update the values
                department_info.email = email
                department_info.phone_number_number = phone_number
                department_info.facilites = facilites
                department_info.labs = labs
                department_info.save()
            except Information.DoesNotExist:
                # If row does not exist, create a new one
                department_info = Information.objects.create(
                    department_id=department_id,
                    email=email,
                    phone_number=phone_number,
                    facilites=facilites,
                    labs=labs
                )
            
        
    context = browse_announcements()
    
    
    department_templates = {
        51: 'department/csedep_request.html',
        30: 'department/ecedep_request.html',
        37: 'department/medep_request.html',
        53: 'department/smdep_request.html',

    } 
    default_template = 'department/dep_request.html'
    
    desig=request.session.get('currentDesignationSelected', 'default_value')
    if desig=='deptadmin_cse':
        template_name = 'department/admin_cse.html'
    
        return render(request, template_name, {
            "user_designation": user_info.user_type,
            "announcements": context,
            "request_to": requests_received,
            "fac_list": context_f,
            "department_info": department_context
        }) 
    elif desig=='deptadmin_ece':
        template_name = 'department/admin_ece.html'
        return render(request, template_name, {
            "user_designation": user_info.user_type,
            "announcements": context,
            "request_to": requests_received,
            "fac_list": context_f,
            "department_info": department_context
        }) 
    elif desig=='deptadmin_me':
        template_name = 'department/admin_me.html'
        return render(request, template_name, {
            "user_designation": user_info.user_type,
            "announcements": context,
            "request_to": requests_received,
            "fac_list": context_f,
            "department_info": department_context
        }) 
    elif desig=='deptadmin_sm':
        template_name = 'department/admin_sm.html'
        return render(request, template_name, {
            "user_designation": user_info.user_type,
            "announcements": context,
            "request_to": requests_received,
            "fac_list": context_f,
            "department_info": department_context
        }) 
         
    # if  desig == 'deptadmin_cse':
    #     return render(request, 'admin_cse.html')
    # elif desig == 'deptadmin_ece':
    #     return render(request, 'admin_ece.html')
    # elif desig == 'deptadmin_sm':
    #     return render(request, 'admin_sm.html')
    # elif desig == 'deptadmin_me':
    #     return render(request, 'admin_me.html')
    # else:
    #     return render(request, 'default.html')

    template_name = department_templates.get(user_departmentid, default_template)
    return render(request, template_name, {
        "user_designation": user_info.user_type,
        "announcements": context,
        "request_to": requests_received,
        "fac_list": context_f,
        "department_info": department_context
    })
    
   

@login_required(login_url='/accounts/login')

def all_students(request, bid):
    """
    This function is used to Return data of Faculties Department-Wise.

    @param:
        request - contains metadata about the requested page
        bid - stores key for different batches

    @variables:
        student_list1 - Stores student data department, batch and programme-wise
        student_list - Stores data pagewise

    """

    def decode_bid(bid):
        """Decodes the bid structure into programme, batch, and department (if applicable)."""

        try:
            department_code = bid[0]
            programme = {
                '1': 'B.Tech',
                '2': 'M.Tech',
                '3': 'PhD',

            }[department_code]
            batch = 2021 - len(bid) + 1
            return {'programme': programme, 'batch': batch}
        except (IndexError, KeyError):
            return None  # Handle malformed bid values
    # Get sort parameter from the request
    sort_by = request.GET.get('sort_by', None)  # No default sort
    last_sort = request.session.get('last_sort', None)

    # Decode bid into filter criteria
    filter_criteria = decode_bid(bid)
    if not filter_criteria:
        return HttpResponseBadRequest("Invalid bid value")

    # Apply additional department filter since it seems fixed 
    filter_criteria['id__department__name'] = 'CSE'

    # Apply sort parameter to the queryset
    if sort_by:
        if last_sort == sort_by:
            sort_by = '-' + sort_by  # Reverse the order
        try:
            student_list1 = Student.objects.order_by(sort_by).filter(
                id__user_type='student',
                **filter_criteria
            ).select_related('id')
        except:
            # If the sort field doesn't exist or isn't sortable, ignore the sort parameter
            student_list1 = Student.objects.filter(
                id__user_type='student',
                **filter_criteria
            ).select_related('id')
        request.session['last_sort'] = sort_by  # Save the sort parameter for the next request
    else:
        student_list1 = Student.objects.filter(
            id__user_type='student',
            **filter_criteria
        ).select_related('id')

    paginator = Paginator(student_list1, 25, orphans=5)
    page_number = request.GET.get('page')
    student_list = paginator.get_page(page_number)
    id_dict = {'student_list': student_list}
    return render(request, 'department/AllStudents.html', context=id_dict)


def faculty():
    """
    This function is used to Return data of Faculties Department-Wise.

    @variables:
        cse_f - Stores data of faculties from CSE Department
        ece_f - Stores data of faculties from ECE Department
        me_f - Stores data of faculties from ME Department
        sm_f - Stores data of faculties from ME Department
        context_f - Stores all above variables in Dictionary

    """
    cse_f=ExtraInfo.objects.filter(department__name='CSE',user_type='faculty')
    ece_f=ExtraInfo.objects.filter(department__name='ECE',user_type='faculty')
    me_f=ExtraInfo.objects.filter(department__name='ME',user_type='faculty')
    sm_f=ExtraInfo.objects.filter(department__name='SM',user_type='faculty')
    staff=ExtraInfo.objects.filter(user_type='staff')

    context_f = {
        "cse_f" : cse_f,
        "ece_f" : ece_f,
        "me_f" : me_f,
        "sm_f" : sm_f,
        "staffNcse" : list(staff)+list(cse_f),
        "staffNece" : list(staff)+list(ece_f),
        "staffNme" : list(staff)+list(me_f),
        "staffNsm" : list(staff)+list(sm_f)


    }
    # print(cse_f)
    return context_f


def alumni(request):
    """
    This function is used to Return data of Alumni Department-Wise.

    @variables:
        cse_a - Stores data of alumni from CSE Department
        ece_a - Stores data of alumni from ECE Department
        me_a - Stores data of alumni from ME Department
        sm_a - Stores data of alumni from ME Department
        context_a - Stores all above variables in Dictionary

    """
    cse_a=ExtraInfo.objects.filter(department__name='CSE',user_type='alumni')
    ece_a=ExtraInfo.objects.filter(department__name='ECE',user_type='alumni')
    me_a=ExtraInfo.objects.filter(department__name='ME',user_type='alumni')
    sm_a=ExtraInfo.objects.filter(department__name='SM',user_type='alumni')

    context_a = {
        "cse_a" : cse_a,
        "ece_a" : ece_a,
        "me_a" : me_a,
        "sm_a" : sm_a
    }
    return render(request, 'department/alumni.html', context_a)

def approved(request):
    """
    This function is used to approve requests.

    @variables:
        request_id - Contains ID of the request to be updated
        remark - Contains Remarks added by the user while Approving the status

    """
    if request.method == 'POST':
        request_id = request.POST.get('id')
        remark = request.POST.get('remark')
        SpecialRequest.objects.filter(id=request_id).update(status="Approved", remarks=remark)
    request.method = ''
    return redirect('/dep/facView/')


def deny(request):
    """
    This function is used to deny requests.

    @variables:
        request_id - Contains ID of the request to be updated
        remark - Contains Remarks added by the user while Denying the status

    """
    if request.method == 'POST':
        request_id = request.POST.get('id')
        remark = request.POST.get('remark')
        SpecialRequest.objects.filter(id=request_id).update(status="Denied", remarks=remark)
    request.method = ''
    return redirect('/dep/facView/')