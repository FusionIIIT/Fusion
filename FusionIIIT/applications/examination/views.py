from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models.query_utils import Q
from django.http import request, HttpResponse
from django.shortcuts import get_object_or_404, render, HttpResponse, redirect
from django.http import HttpResponse, HttpResponseRedirect
import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import date
import requests
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from applications.programme_curriculum.models import Course
from applications.academic_procedures.models import course_registration
from applications.programme_curriculum.filters import CourseFilter
from notification.views import  examination_notif
from applications.department.models import SpecialRequest, Announcements
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from django.shortcuts import render, redirect, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import hidden_grades
from .forms import StudentGradeForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import hidden_grades
from rest_framework.permissions import AllowAny


@login_required(login_url='/accounts/login')
def exam(request):
    """
    This function is used to Differenciate acadadmin and all other user.

    @param:
        request - contains metadata about the requested page

    @variables:
        user_details - Gets the information about the logged in user.
        des - Gets the designation about the looged in user.
    # """
    # user_details = ExtraInfo.objects.get(user = request.user)
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
    #     return HttpResponseRedirect('/examination/submit/')
    # elif str(request.user) == "acadadmin" :
    #     return HttpResponseRedirect('/examination/submit/')

    return HttpResponseRedirect('/examination/submit/')


@login_required(login_url='/accounts/login')
def submit(request):
    # courses = Course.objects.all()

    # coursefilter = CourseFilter(request.GET, queryset=courses)

    # courses = coursefilter.qs
     unique_course_ids = course_registration.objects.values('course_id').distinct()

    # Cast the course IDs to integers
     unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs
     courses_info = Course.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))
    
     return render(request, '../templates/examination/submit.html',{'courses_info': courses_info})
    # return render(request,'../templates/examination/submit.html' , {})


@login_required(login_url='/accounts/login')
def verify(request):
    # Retrieve unique course IDs from hidden_grades
    unique_course_ids = hidden_grades.objects.values('course_id').distinct()

    # Cast the course IDs to integers
    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs
    courses_info = Course.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))

    # Pass the unique course IDs and corresponding course names and codes to the template
    return render(request, '../templates/examination/verify.html', {'courses_info': courses_info})


@login_required(login_url='/accounts/login')
def publish(request):
    return render(request, '../templates/examination/publish.html', {})


@login_required(login_url='/accounts/login')
def notReady_publish(request):
    return render(request, '../templates/examination/notReady_publish.html', {})


@login_required(login_url='/accounts/login')
def timetable(request):
    return render(request, '../templates/examination/timetable.html', {})


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
        "cse": cse_ann,
        "ece": ece_ann,
        "me": me_ann,
        "sm": sm_ann,
        "all": all_ann
    }

    return context


def get_to_request(username):
    """
    This function is used to get requests for the receiver

    @variables:
        req - Contains request queryset

    """
    req = SpecialRequest.objects.filter(request_receiver=username)
    return req


def entergrades(request):
    course_id = request.GET.get('course')
    semester_id = request.GET.get('semester')

    course_present = hidden_grades.objects.filter(
        course_id=course_id, semester_id=semester_id)

    if (course_present):
        return render(request, 'examination/all_course_grade_filled.html', {})

    # Retrieve course registrations based on course and semester
    registrations = course_registration.objects.filter(
        course_id__id=course_id, semester_id=semester_id)

    # Pass the registrations queryset to the template context
    context = {
        'registrations': registrations
    }

    return render(request, 'examination/entergrades.html', context)

def verifygrades(request):
    course_id = request.GET.get('course')
    semester_id = request.GET.get('semester')

    registrations = hidden_grades.objects.filter(
        course_id=course_id, semester_id=semester_id)

    # Pass the registrations queryset to the template context
    context = {
        'registrations': registrations
    }

    return render(request, 'examination/verifygrades.html', context)


@login_required(login_url='/accounts/login')
def announcement(request):
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
    user_info = ExtraInfo.objects.all().select_related(
        'user', 'department').filter(user=usrnm).first()
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
        user_info = ExtraInfo.objects.all().select_related(
            'user', 'department').get(id=ann_maker_id)
        getstudents = ExtraInfo.objects.select_related('user')
        recipients = User.objects.filter(extrainfo__in=getstudents)

        obj1, created = Announcements.objects.get_or_create(maker_id=user_info,
                                                            batch=batch,
                                                            programme=programme,
                                                            message=message,
                                                            upload_announcement=upload_announcement,
                                                            department=department,
                                                            ann_date=ann_date)
        examination_notif(usrnm, recipients , message)

    context = browse_announcements()
    return render(request, 'examination/announcement_req.html', {"user_designation": user_info.user_type,
                                                                 "announcements": context,
                                                                 "request_to": requests_received
                                                                 })


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status


class Updatehidden_gradesMultipleView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        student_ids = request.POST.getlist('student_ids[]')
        semester_ids = request.POST.getlist('semester_ids[]')
        course_ids = request.POST.getlist('course_ids[]')
        grades = request.POST.getlist('grades[]')

        if len(student_ids) != len(semester_ids) != len(course_ids) != len(grades):
            return Response({'error': 'Invalid grade data provided'}, status=status.HTTP_400_BAD_REQUEST)

        for student_id, semester_id, course_id, grade in zip(student_ids, semester_ids, course_ids, grades):
            # Create an instance of hidden_grades model and save the data

            try:
                hidden_grade = hidden_grades.objects.get(
                    course_id=course_id, student_id=student_id, semester_id=semester_id)
                hidden_grade.grade = grade
                hidden_grade.save()
            except hidden_grades.DoesNotExist:
                # If the grade doesn't exist, create a new one
                hidden_grade = hidden_grades.objects.create(
                    course_id=course_id, student_id=student_id, semester_id=semester_id, grade=grade)
                hidden_grade.save()
            # hidden_grade = hidden_grades.objects.create(
            #     student_id=student_id,
            #     course_id=course_id,
            #     semester_id=semester_id,
            #     grade=grade
            # )
            print(
                f"Student ID: {student_id}, Semester ID: {semester_id}, Course ID: {course_id}, Grade: {grade}")
            hidden_grade.save()

        return Response({'message': 'Grades updated successfully'}, status=status.HTTP_200_OK)
