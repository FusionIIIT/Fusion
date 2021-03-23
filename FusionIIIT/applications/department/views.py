import datetime
import json
from operator import or_
from functools import reduce

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from applications.eis.models import (faculty_about, emp_research_projects)

#from .models import ()
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Create your views here.
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
    fac_view = request.user.holds_designations.filter(designation__name='faculty').exists() ## main part
    student = request.user.holds_designations.filter(designation__name='student').exists()

    # finding designation of user
    user_designation = ""
    # if cse_hod:
    #     user_designation = "hod"
    # elif fac_view:
    #     user_designation = "faculty"
    # elif student:
    #     user_designation = "student"
    
    print(fac_view, student) #### Both false for Faculties... maybe error in database need to confirm
    if fac_view:
        user_designation = "faculty"
    else:
        user_designation = "student"
    
    if user_designation == "student":
        return render(request,"department/index.html")
    elif(str(user.extrainfo.user_type)=='faculty'):
        return render(request, 'department/dep_complaint.html')

def file_complaint(request):
    #return render(request, "department/dep_complaint.html")
    return render(request, 'department/dep_complaint.html')

def BtechFirstYear_Students(request):
    student_list1=Student.objects.filter(batch=2019)
    id_dict={'student_list':student_list1,'batch':"First"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def BtechSecondYear_Students(request):
    student_list2=Student.objects.filter(batch=2018)
    id_dict={'student_list':student_list2,'batch':"Second"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def BtechThirdYear_Students(request):
    student_list3=Student.objects.filter(batch=2017)
    id_dict={'student_list':student_list3,'batch':"Third"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def BtechFinalYear_Students(request):
    student_list4=Student.objects.filter(batch=2016)[:11]
    id_dict={'student_list':student_list4,'batch':"Final"}
    return render(request, 'department/BTechStudents.html',context=id_dict)

def cse_faculty(request):
    cse_f=ExtraInfo.objects.filter(department__name='CSE').filter(user_type='faculty')
    id_dict={'fac_list':cse_f,'department':'CSE'}
    return render(request,'department/faculty.html',context=id_dict)

def ece_faculty(request):
    ece_f=ExtraInfo.objects.filter(department__name='ECE').filter(user_type='faculty')
    id_dict={'fac_list':ece_f,'department':'ECE'}
    return render(request,'department/faculty.html',context=id_dict)

def me_faculty(request):
    me_f=ExtraInfo.objects.filter(department__name='ME').filter(user_type='faculty')
    id_dict={'fac_list':me_f,'department':'ME'}
    return render(request,'department/faculty.html',context=id_dict)
