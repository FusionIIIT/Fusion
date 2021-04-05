from datetime import date
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from notification.views import  complaint_system_notif

from .models import Announcements
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
    
    fac_view = request.user.holds_designations.filter(designation__name='faculty').exists()
    student = request.user.holds_designations.filter(designation__name='student').exists()
    context = browse_announcements()
    context_f = faculty()
    user_designation = ""
    if fac_view:
        user_designation = "faculty"
    elif student:
        user_designation = "student"
    if user_designation == "student":
        return render(request,"department/index.html", {"announcements":context,
                                                        "fac_list" : context_f})
    elif(str(user.extrainfo.user_type)=='faculty'):
        return file_request(request)

def file_request(request):
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
    if request.method == 'POST':
        batch = request.POST.get('batch', '')
        programme = request.POST.get('programme', '')
        message = request.POST.get('announcement', '')
        upload_announcement = request.FILES.get('upload_announcement')
        department = request.POST.get('department')
        ann_date = date.today()
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_maker_id)

        obj1, created = Announcements.objects.get_or_create(maker_id=user_info,
                                    batch=batch,
                                    programme=programme,
                                    message=message,
                                    upload_announcement=upload_announcement,
                                    department = department,
                                    ann_date=ann_date)

    context = browse_announcements()
    return render(request, 'department/dep_request.html', {"user_designation":user_info.user_type,
                                                            "announcements":context
                                                        })


@login_required(login_url='/accounts/login')
def All_Students(request,bid):
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
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==11:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2017,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==1111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2016,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==11111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='CSE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==111111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2018,
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
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==21:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2018,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==211:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2017,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id') 
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==2111:
        student_list1=Student.objects.order_by('id').filter(programme='B.Tech',
                                                            batch=2016,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==21111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2019,
                                                            id__user_type='student',
                                                            id__department__name='ECE').select_related('id')
        paginator=Paginator(student_list1,25,orphans=5)
        page_number=request.GET.get('page')
        student_list=paginator.get_page(page_number)
        id_dict={'student_list':student_list,}
        return render(request, 'department/AllStudents.html',context=id_dict)
    elif int(bid)==211111:
        student_list1=Student.objects.order_by('id').filter(programme='M.Tech',
                                                            batch=2018,
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

def faculty():
    """
    This function is used to Return data of Faculties Department-Wise.

    @variables:
        cse_f - Stores data of faculties from CSE Department
        ece_f - Stores data of faculties from ECE Department
        me_f - Stores data of faculties from ME Department
        context_f - Stores all above variables in Dictionary

    """
    cse_f=ExtraInfo.objects.filter(department__name='CSE',user_type='faculty')
    ece_f=ExtraInfo.objects.filter(department__name='ECE',user_type='faculty')
    me_f=ExtraInfo.objects.filter(department__name='ME',user_type='faculty')
    context_f = {
        "cse_f" : cse_f,
        "ece_f" : ece_f,
        "me_f" : me_f,
    }
    return context_f
