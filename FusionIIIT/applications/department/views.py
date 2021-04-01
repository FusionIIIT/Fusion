from applications.department.models import Announcements
import datetime
import json
from operator import or_
from functools import reduce

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
                                         HoldsDesignation)
from applications.eis.models import (faculty_about, emp_research_projects)
from notification.views import  complaint_system_notif

#from .models import ()
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Create your views here.

def index(request):
    context = {}
    print(request.user)
    if(str(request.user)!="AnonymousUser"):
        return HttpResponseRedirect('/dashboard/')
    else:
        return render(request, "globals/index1.html", context)

@login_required(login_url='/accounts/login')
def admin(request):
    admin = Designation.objects.get(name='admin')
    hod = Designation.objects.get(name='hod')
    hd_admin = HoldsDesignation.objects.filter(
        user=request.user, designation=admin)
    hd_hod = HoldsDesignation.objects.filter(
        user=request.user, designation=hod)


def hod(request):
    ###### not working need to find another way to implement
    user = request.user
    
    #cse_hod = request.user.holds_designations.filter(designation__name='hod').exists()
    fac_view = request.user.holds_designations.filter(designation__name='faculty').exists() 
    print(request.user.holds_designations.filter(designation__name='faculty'))
    student = request.user.holds_designations.filter(designation__name='student').exists()

    # finding designation of user
    user_designation = ""
    # if cse_hod:
    #     user_designation = "hod"
    # elif fac_view:
    #     user_designation = "faculty"
    # elif student:
    #     user_designation = "student"
    
    print(fac_view, student) 
    if fac_view:
        user_designation = "faculty"
    elif student:
        user_designation = "student"
    if user_designation == "student":
        return render(request,"department/index.html")
    elif(str(user.extrainfo.user_type)=='faculty'):
        return render(request, 'department/dep_request.html', {"user_designation":'faculty'})

def file_request(request):
    #return render(request, "department/dep_complaint.html")
    return render(request, 'department/dep_request.html')

def BtechFirstYear_Students(request):
    # student_list1=Student.objects.filter(batch=2019)
    # print(request.user)
    # print(User.objects.all()[:5])
    student_list1=Student.objects.order_by('id').filter(programme='B.Tech',batch=2019,id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list1,'batch':"B.Tech First"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def BtechSecondYear_Students(request):
    student_list2=Student.objects.order_by('id').filter(programme='B.Tech',batch=2018,id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list2,'batch':"B.Tech Second"}
    return render(request, 'department/BTechStudents.html',context=id_dict)
    # return render(request, 'globals/index1.html',context=id_dict)


def BtechThirdYear_Students(request):
    student_list3=Student.objects.order_by('id').filter(programme='B.Tech',batch=2017,id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list3,'batch':"B.Tech Third"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def BtechFinalYear_Students(request):
    student_list4=Student.objects.order_by('id').filter(programme='B.Tech',batch=2016,id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list4,'batch':"B.Tech Final"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def MtechFirstYear_Students(request):
    student_list5=Student.objects.order_by('id').filter(programme='M.Tech',id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list5,'batch':"M.Tech First"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def MtechSecondYear_Students(request):
    student_list6=Student.objects.order_by('id').filter(programme='M.Tech',id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list6,'batch':"M.Tech Second"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def PhD_Students(request):
    student_list7=Student.objects.order_by('id').filter(programme='PhD',id__user_type='student',id__department__name='CSE').select_related('id')[:10]
    id_dict={'student_list':student_list7,'batch':"PhD All"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def cse_faculty(request):
    cse_f=ExtraInfo.objects.filter(department__name='CSE',user_type='faculty')
    id_dict={'fac_list':cse_f,'department':'CSE'}
    return render(request,'department/faculty.html',context=id_dict)

def ece_faculty(request):
    ece_f=ExtraInfo.objects.filter(department__name='ECE',user_type='faculty')
    id_dict={'fac_list':ece_f,'department':'ECE'}
    return render(request,'department/faculty.html',context=id_dict)

def me_faculty(request):
    me_f=ExtraInfo.objects.filter(department__name='ME',user_type='faculty')
    id_dict={'fac_list':me_f,'department':'ME'}
    return render(request,'department/faculty.html',context=id_dict)

@login_required
def make_announcements(request,maker_id):
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').get(id=id)

    if request.method == 'POST':
        maker_id = request.POST.get('maker_id', '')
        programme = request.POST.get('programme', '')
        batch = request.POST.get('batch', '')
        announcement = request.POST.get('announcement')

    obj1, created = Announcements.objects.get_or_create(maker_id=y,
        
                                programme=programme,
                                batch=batch,
                                announcement=announcement)
                               
    # message = "A New Announcement has been published"
    #     complaint_system_notif(request.user, caretaker_name.user,'make_announcement_alert',obj1.id,user,message)

    return HttpResponseRedirect('/dep/browse_announcements/')

def browse_announcements(request):
    """
    function that shows detail about complaint
    """
    # browse_announcements = Announcements.objects.select_related('maker_id','date','announcement','batch','programme').get(id=maker_id)
    # if(browse_announcements.maker_id is None):
    #     maker_id = browse_announcements.maker_id  
    # else:
    #     maker_id = browse_announcements.maker_id.id
    #     Announcements.objects.select_related('maker_id','date','announcement','batch','programme').get(id=maker_id)        
    # a=User.objects.get(username=browse_announcements.maker_id.user.username)           
    # y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    # num=0
    
   
    # return render(request, "dep/browse_announcements.html", {"browse_announcements": browse_announcements, "maker_id":maker_id,"batch":batch,"programme":programme})
    return render(request, 'department/browse_announcements.html')



# def BtechFirstYear_Students_Announcements(request):
#    announcements_list1 = Announcements.objects.all()[:11]
#    id_dict={'announcements_list':announcements_list1 }
#    return render(request, 'department/browse_announcements.html',context=id_dict)

# def BtechSecondYear_Students_Announcements(request):
#     announcements_list2 = Announcements.objects.all()[:11]
#     id_dict={'announcements_list':announcements_list2 }
#     return render(request, 'department/browse_announcements.html',context=id_dict)

# def BtechThirdYear_Students_Announcements(request):
#     announcements_list3 = Announcements.objects.all()[:11]
#     id_dict={'announcements_list':announcements_list3 }
#     return render(request, 'department/browse_announcements.html',context=id_dict)

# def BtechFinalYear_Students_Announcements(request):
#     announcements_list4 = Announcements.objects.all()[:11]
#     id_dict={'announcements_list':announcements_list4 }
#     return render(request, 'department/browse_announcements.html',context=id_dict)
