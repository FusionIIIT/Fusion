from notifications.signals import notify
from django.views import View
from django.views.generic import View
from django.http import HttpResponse
import csv
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
from applications.academic_information.models import Spi, Student, Curriculum
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from applications.academic_information.models import Course
from applications.academic_procedures.models import course_registration, Register
from applications.programme_curriculum.filters import CourseFilter
from notification.views import examination_notif
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
from .models import hidden_grades, authentication
from rest_framework.permissions import AllowAny
from applications.online_cms.models import (Student_grades)

from applications.programme_curriculum.models import Course as Courses, CourseInstructor


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
    user_details = ExtraInfo.objects.get(user=request.user)
    des = HoldsDesignation.objects.all().filter(user=request.user).first() 
    if str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor":
        return HttpResponseRedirect('/examination/updateGrades/')
    elif request.session.get("currentDesignationSelected") == "acadadmin":
        return HttpResponseRedirect('/examination/updateGrades/')

    return HttpResponseRedirect('/dashboard/')


@login_required(login_url='/accounts/login')
def submit(request):

    unique_course_ids = course_registration.objects.values(
        'course_id').distinct()

    # Cast the course IDs to integers
    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs
    courses_info = Course.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))

    return render(request, '../templates/examination/submit.html', {'courses_info': courses_info})


@login_required(login_url='/accounts/login')
def verify(request):
    unique_course_ids = hidden_grades.objects.values('course_id').distinct()

    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    courses_info = Course.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))

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

    registrations = course_registration.objects.filter(
        course_id__id=course_id, semester_id=semester_id)

    context = {
        'registrations': registrations
    }

    return render(request, 'examination/entergrades.html', context)


def verifygrades(request):
    course_id = request.GET.get('course')
    semester_id = request.GET.get('semester')

    registrations = hidden_grades.objects.filter(
        course_id=course_id, semester_id=semester_id)

    context = {
        'registrations': registrations
    }

    return render(request, 'examination/verifygrades.html', context)


def authenticate(request):  # new
    # Retrieve unique course IDs from hidden_grades
    unique_course_ids = Student_grades.objects.values('course_id').distinct()

    # Cast the course IDs to integers
    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs
    courses_info = Courses.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))
    working_years = Student_grades.objects.values(
        'year').distinct()
    context = {
        'courses_info': courses_info,
        'working_years':working_years

    }
    print(working_years)
    return render(request, '../templates/examination/authenticate.html', context)


@login_required(login_url='/accounts/login')
def authenticategrades(request):  # new
    course_id = request.GET.get('course')
    year = request.GET.get('year')

    print(course_id)
    print(year)

    course_instance = Courses.objects.get(id=course_id)
    registrations = authentication.objects.filter(
        course_id=course_instance, course_year=year)

    if registrations:
        # Registrations exist, pass them to the template context
        context = {
            'registrations': registrations,
            'year': year
        }
    else:
        course_instance = Courses.objects.get(id=course_id)
        course_present = Student_grades.objects.filter(
            course_id=course_id, year=year)
        if (course_present):
            authentication_object = authentication.objects.create(
                course_id=course_instance, course_year=year)
            registrations = authentication.objects.filter(
                course_id=course_instance, course_year=year)

            context = {
                'registrations': registrations,
                'course_year': year,
            }

    context = {
        'registrations': registrations,
        'year': year
    }

    return render(request, 'examination/authenticategrades.html', context)


# def examination_notif(sender, recipient, type):
#     try:
#         url = 'examination:examination'
#         module = 'examination'
#         verb = type
#         flag = "examination"

#         notify.send(sender=sender,
#                     recipient=recipient,
#                     url=url,
#                     module=module,
#                     verb=verb,
#                     flag=flag)

#     except Exception as e:
#         print("Error sending notification:", e)


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
    try:
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = usrnm.extrainfo
        ann_maker_id = user_info.id
        requests_received = get_to_request(usrnm)

        if request.method == 'POST':
            batch = request.POST.get('batch', '')
            programme = request.POST.get('programme', '')
            message = request.POST.get('announcement', '')
            upload_announcement = request.FILES.get('upload_announcement')
            department = request.POST.get('department')
            ann_date = date.today()

            obj1, created = Announcements.objects.get_or_create(
                maker_id=user_info,
                batch=batch,
                programme=programme,
                message=message,
                upload_announcement=upload_announcement,
                department=department,
                ann_date=ann_date
            )

            recipients = User.objects.all()  # Modify this query as per your requirements
            examination_notif(sender=usrnm, recipient=recipients, type=message)

        context = browse_announcements()
        return render(request, 'examination/announcement_req.html', {
            "user_designation": user_info.user_type,
            "announcements": context,
            "request_to": requests_received
        })
    except Exception as e:

        return render(request, 'examination/announcement_req.html', {"error_message": "An error occurred. Please try again later."})


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

            hidden_grade.save()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grades.csv"'

        # Write data to CSV
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Semester ID', 'Course ID', 'Grade'])
        for student_id, semester_id, course_id, grade in zip(student_ids, semester_ids, course_ids, grades):
            writer.writerow([student_id, semester_id, course_id, grade])

        return response
        return render(request, '../templates/examination/grades_updated.html', {})


class Submithidden_gradesMultipleView(APIView):
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

            hidden_grade.save()

        return render(request, '../templates/examination/grades_updated.html', {})


class update_authentication(View):
    def post(self, request, *args, **kwargs):
        # Extract data from the POST request
        course = request.POST.get('course')
        course_year = request.POST.get('course_year')
        authenticator1 = request.POST.get('authenticator1')
        authenticator2 = request.POST.get('authenticator2')
        authenticator3 = request.POST.get('authenticator3')

        # Retrieve the registration object
        try:

            course_instance = Courses.objects.get(id=course)
            registration = authentication.objects.get(
                course_id=course_instance, course_year=course_year)
        except authentication.DoesNotExist:
            # Redirect if registration does not exist
            return redirect('examination:submitGrades')

        # Update authenticators if the values have changed
        if authenticator1 is not None:
            registration.authenticator_1 = (authenticator1 == '1')
        else:
            registration.authenticator_1 = 0
        if authenticator2 is not None:
            registration.authenticator_2 = (authenticator2 == '1')
        else:
            registration.authenticator_2 = 0
        if authenticator3 is not None:
            registration.authenticator_3 = (authenticator3 == '1')
        else:
            registration.authenticator_3 = 0

        # Save the changes
        registration.save()

        # Redirect to the appropriate page
        return redirect('examination:authenticate')


class DownloadExcelView(View):
    def post(self, request, *args, **kwargs):
        # Retrieve form data
        student_ids = request.POST.getlist('student_ids[]')
        semester_ids = request.POST.getlist('semester_ids[]')
        course_ids = request.POST.getlist('course_ids[]')
        grades = request.POST.getlist('grades[]')

        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grades.csv"'

        # Write data to CSV
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Semester ID', 'Course ID', 'Grade'])
        for student_id, semester_id, course_id, grade in zip(student_ids, semester_ids, course_ids, grades):
            writer.writerow([student_id, semester_id, course_id, grade])

        return response


def generate_transcript(request):

    student_id = request.GET.get('student')
    semester = request.GET.get('semester')
    courses_registered = Student_grades.objects.filter(
        roll_no=student_id, semester=semester)

    # Initialize a dictionary to store course grades
    course_grades = {}

    total_course_registered = Student_grades.objects.filter(
        roll_no=student_id, semester__lte=semester)
    # for each_course in total_course_registered:
    #     course_name = Curriculum.objects.filter(
    #         curriculum_id=each_course.curr_id_id)
    
    

    for course in courses_registered:
        try:
            # Attempt to fetch the grade for the course from Student_grades
            grade = Student_grades.objects.get(
                roll_no=student_id, course_id=course.course_id)

            # course_detail = Curriculum.objects.get(
            #     course_id=course.course_id, batch=grade.batch)
            course_instance = Courses.objects.get(id=course.course_id_id)
            check_authentication_object = authentication.objects.filter(
                course_id=course_instance, course_year=grade.year)
            all_authenticators_true = True

            if check_authentication_object:
                # Iterate over each authentication object
                for auth_obj in check_authentication_object:
                    # Check if all authenticators are true
                    if not (auth_obj.authenticator_1 and auth_obj.authenticator_2 and auth_obj.authenticator_3):
                        all_authenticators_true = False
                        break  # No need to check further if any authenticator is False
            else:
                # Create authentication object if it doesn't exist
                authentication_object = authentication.objects.create(
                    course_id=course_instance, course_year=grade.year)
                # Get all registrations for the course and year
                registrations = authentication.objects.filter(
                    course_id=course_instance, course_year=grade.year)
                all_authenticators_true = False

            course_grades[course_instance] = {
                'grade': grade,
                'all_authenticators_true': all_authenticators_true
            }  # Store the grade
        except Student_grades.DoesNotExist:
            # Grade not available
            course_grades[course] = "Grading not done yet"

    context = {
        'courses_grades': course_grades,
        'total_course_registered':total_course_registered
    }
    #   print(context)

    return render(request, 'examination/generate_transcript.html', context)

# new


def generate_transcript_form(request):
    if request.method == 'POST':
        programme = request.POST.get('programme')
        batch = request.POST.get('batch')
        specialization = request.POST.get('specialization')
        semester = request.POST.get('semester')

        if specialization == None:
            students = Student.objects.filter(
                programme=programme, batch=batch)
        else:
            students = Student.objects.filter(
                programme=programme, batch=batch, specialization=specialization)

        # Pass the filtered students to the template
        context = {
            'students': students,
            'semester': semester
        }
        return render(request, 'examination/generate_transcript_students.html', context)
    else:
        programmes = Student.objects.values_list(
            'programme', flat=True).distinct()
        specializations = Student.objects.exclude(
            specialization__isnull=True).values_list('specialization', flat=True).distinct()
        batches = Student.objects.values_list('batch', flat=True).distinct()
        context = {
            'programmes': programmes,
            'batches': batches,
            'specializations': specializations,
        }

        return render(request, 'examination/generate_transcript_form.html', context)


@login_required(login_url='/accounts/login')
def updateGrades(request):
    unique_course_ids = Student_grades.objects.values(
        'course_id').distinct()

    # Cast the course IDs to integers
    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs

    print(unique_course_ids)
    courses_info = Courses.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))

    unique_batch_ids = Student_grades.objects.values(
        'batch').distinct()

    context = {
        'courses_info': courses_info,
        'unique_batch_ids': unique_batch_ids,
    }

    return render(request, '../templates/examination/submitGrade.html', context)


def updateEntergrades(request):
    course_id = request.GET.get('course')
    semester_id = request.GET.get('semester')
    batch = request.GET.get('batch')

    course_present = Student_grades.objects.filter(
        course_id=course_id, semester=semester_id, batch=batch)

    context = {
        'registrations': course_present
    }

    return render(request, '../templates/examination/updateEntergrades.html', context)


class moderate_student_grades(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        student_ids = request.POST.getlist('student_ids[]')
        semester_ids = request.POST.getlist('semester_ids[]')
        course_ids = request.POST.getlist('course_ids[]')
        grades = request.POST.getlist('grades[]')

        if len(student_ids) != len(semester_ids) != len(course_ids) != len(grades):
            return Response({'error': 'Invalid grade data provided'}, status=status.HTTP_400_BAD_REQUEST)

        for student_id, semester_id, course_id, grade in zip(student_ids, semester_ids, course_ids, grades):

            try:
                grade_of_student = Student_grades.objects.get(
                    course_id=course_id, roll_no=student_id, semester=semester_id)
                grade_of_student.grade = grade
                grade_of_student.save()
            except Student_grades.DoesNotExist:
                # If the grade doesn't exist, create a new one
                hidden_grade = hidden_grades.objects.create(
                    course_id=course_id, student_id=student_id, semester_id=semester_id, grade=grade)
                hidden_grade.save()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grades.csv"'

        # Write data to CSV
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Semester ID', 'Course ID', 'Grade'])
        for student_id, semester_id, course_id, grade in zip(student_ids, semester_ids, course_ids, grades):
            writer.writerow([student_id, semester_id, course_id, grade])

        return response
        return render(request, '../templates/examination/grades_updated.html', {})


@login_required(login_url='/accounts/login')
def submitGrades(request):

    unique_course_ids = course_registration.objects.values(
        'course_id').distinct()
    working_years = course_registration.objects.values(
        'working_year').distinct()



    # Cast the course IDs to integers
    unique_course_ids = unique_course_ids.annotate(
        course_id_int=Cast('course_id', IntegerField()))

    # Retrieve course names and course codes based on unique course IDs

    print(unique_course_ids)
    courses_info = Courses.objects.filter(
        id__in=unique_course_ids.values_list('course_id_int', flat=True))

    context = {
        'courses_info': courses_info,
        'working_years': working_years
    }

    print(working_years)

    return render(request, '../templates/examination/gradeSubmission.html', context)


def submitEntergrades(request):
    course_id = request.GET.get('course')
    year = request.GET.get('year')
    if year is None or not year.isdigit():
        message = "YEAR SHOULD NOT BE NONE"
        context = {
            'message': message
        }

        return render(request, '../templates/examination/message.html', context)
        return HttpResponse("Invalid year parameter")
        # Handle invalid year parameter
        # You can return an error response or redirect the user to an error page
    courses_info = Courses.objects.get(id=course_id)

    courses = Student_grades.objects.filter(
        course_id=courses_info.id, year=year)

    if courses:
        message = "THIS Course was Already Submitted"
        context = {
            'message': message
        }

        return render(request, '../templates/examination/message.html', context)

    students = course_registration.objects.filter(
        course_id_id=course_id, working_year=year)

    # print(students)

    context = {
        'registrations': students,
        'curr_id': course_id,
        'year': year
    }

    return render(request, '../templates/examination/gradeSubmissionForm.html', context)


class submitEntergradesStoring(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        student_ids = request.POST.getlist('student_ids[]')
        batch_ids = request.POST.getlist('batch_ids[]')
        course_ids = request.POST.getlist('course_ids[]')
        semester_ids = request.POST.getlist('semester_ids[]')
        year_ids = request.POST.getlist('year_ids[]')
        marks = request.POST.getlist('marks[]')
        grades = request.POST.getlist('grades[]')

        if len(student_ids) != len(batch_ids) != len(course_ids) != len(semester_ids) != len(year_ids) != len(marks) != len(grades):
            return Response({'error': 'Invalid grade data provided'}, status=status.HTTP_400_BAD_REQUEST)

        for student_id, batch_id, course_id, semester_id, year_id, mark, grade in zip(student_ids, batch_ids, course_ids, semester_ids, year_ids, marks, grades):
            # Create an instance of hidden_grades model and save the data

            try:
                grade_of_student = Student_grades.objects.get(
                    course_id=course_id, roll_no=student_id, semester=semester_id)
            except Student_grades.DoesNotExist:
                # If the grade doesn't exist, create a new one
                course_instance = Courses.objects.get(id=course_id)
                student_grade = Student_grades.objects.create(
                    course_id=course_instance, roll_no=student_id, semester=semester_id, grade=grade, batch=batch_id, year=year_id, total_marks=mark)
                student_grade.save()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grades.csv"'

        # Write data to CSV
        writer = csv.writer(response)
        writer.writerow(['student_id', 'batch_ids', 'course_id',
                        'semester_id', 'year_ids', 'marks', 'grade'])
        for student_id, batch_id, course_id, semester_id, year_id, mark, grade in zip(student_ids, batch_ids, course_ids, semester_ids, year_ids, marks, grades):
            writer.writerow([student_id, batch_id, course_id,
                            semester_id, year_id, mark, grade])

        return response
        return render(request, '../templates/examination/grades_updated.html', {})
