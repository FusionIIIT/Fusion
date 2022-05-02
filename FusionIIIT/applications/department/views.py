from cgitb import html
from datetime import date
import json
from multiprocessing import Process

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)

from notification.views import department_notif
from .models import SpecialRequest, Announcements
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Create your views here.


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

    requests_made = get_make_request(user_info)
    
    fac_view = request.user.holds_designations.filter(designation__name='faculty').exists()
    student = request.user.holds_designations.filter(designation__name='student').exists()
    staff = request.user.holds_designations.filter(designation__name='staff').exists()
    
    context = browse_announcements()
    context_f = faculty()
    user_designation = ""
    
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
        return render(request,"department/index.html", {"announcements":context,
                                                        "fac_list" : context_f,
                                                        "requests_made" : requests_made
                                                    })
    # elif(str(user.extrainfo.user_type)=="faculty"):
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
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    ann_maker_id = user_info.id
    requests_received = get_to_request(usrnm)
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
        # department_notif(usrnm, recipients , message)
        
    context = browse_announcements()
    return render(request, 'department/dep_request.html', {"user_designation":user_info.user_type,
                                                            "announcements":context,
                                                            "request_to":requests_received
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
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    ann_maker_id = user_info.id
    requests_received = get_to_request(usrnm)
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
        # department_notif(usrnm, recipients , message)
        
    context = browse_announcements()
    return render(request, 'department/dep_request.html', {"user_designation":user_info.user_type,
                                                            "announcements":context,
                                                            "request_to":requests_received
                                                        })

@login_required(login_url='/accounts/login')
def all_students(request,bid):
    """
    This function is used to Return data of Faculties Department-Wise.

    @param:
        request - contains metadata about the requested page
        bid - stores key for different batches

    @variables:
        student_list1 - Stores student data department, batch and programme-wise
        student_list - Stores data pagewise

    """
    if int(bid)==1:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==11:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==1111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==11111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==111111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==1111111:
        student_list1=Student.objects.order_by('id').filter(programme='PhD',
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==2:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==21:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==211:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==2111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==21111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==211111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==2111111:
        student_list1=Student.objects.order_by('id').filter(programme='PhD',
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==3:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==31:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==311:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==3111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==31111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==311111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==3111111:
        student_list1=Student.objects.order_by('id').filter(programme='PhD',
                                                            id__user_type='student',
                                                            id__department__name='ME').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==4:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==41:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==411:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==4111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==41111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2021,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==411111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2020,
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==4111111:
        student_list1=Student.objects.order_by('id').filter(programme='PhD',
                                                            id__user_type='student',
                                                            id__department__name='SM').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)

    

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
    return context_f

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