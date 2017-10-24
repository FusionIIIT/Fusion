import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
# from applications.academic_procedures.models import Register
from applications.academic_information.models import Course, Student
from applications.globals.models import ExtraInfo
from .models import Register, FinalRegistrations
from django.db.models import Max
from django.contrib import messages

# from . forms import AddDropCourseForm

# Create your views here.


@login_required(login_url='/accounts/login')
def academic_procedures(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    student = Student.objects.all().filter(id=user_details.id).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)

    registered_or_not = Register.objects.all().filter(student_id=student).first()
    # Fucntio call to get the current user's branch
    user_branch = get_user_branch(user_details)
    user_sem = 2

    get_courses = Course.objects.all().filter(sem=(user_sem+1))
    # Fucntion Call to get the courses related to the branch
    branch_courses = get_branch_courses(get_courses, user_branch)
    details = {
            'current_user': current_user,
            'user_sem': user_sem,
            'check_pre_register': registered_or_not
            }
    final_register = Register.objects.all().filter(student_id=user_details.id)
    final_register_count = FinalRegistrations.objects.all().filter(student_id=user_details.id)

    print(final_register_count)

    return render(
        request, '../templates/academic_procedures/academic.html', {
                                                                'details': details,
                                                                'courses_list': branch_courses,
                                                                'final_register': final_register,
                                                                'final_count': final_register_count
                                                                }
        )


# function to get user semester
def get_user_semester(roll_no):
    roll = str(roll_no)
    roll = int(roll[:4])
    now = datetime.datetime.now()
    year, month = now.year, int(now.month)
    user_year = int(year) - roll
    sem = 'odd'
    if month >= 7 and month <= 12:
        sem = 'odd'
    else:
        sem = 'even'
    if sem == 'odd':
        return user_year * 2 + 1
    else:
        return user_year * 2


def get_branch_courses(courses, branch):
    course_list = []
    for course in courses:
        if branch[:2] == course.course_id[:2].lower() or len(course.course_id) > 5:
            course_list.append(course)
    return course_list


def get_user_branch(user_details):
    return user_details.department.name


@login_required(login_url='/accounts/login')
def add_course(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)
    user_sem = 3
    get_courses = Course.objects.all().filter(sem=user_sem)
    print(get_courses, user_sem)
    details = {'current_user': current_user, 'user_sem': user_sem}
    return render(
        request,
        '../templates/academic_procedures/addCourse.html',
        {'details': details, 'courses_list': get_courses})


def register(request):
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.POST.get('user'))
        current_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id=current_user.id).first()
        # current_user = get_object_or_404(ExtraInfo, user=current_user.username)
        values_length = 0
        for key, values in request.POST.lists():
            values_length = len(values)
            break
        # Get the semester for the registration
        sem = request.POST.get('semester')
        for x in range(values_length):
            for key, values in request.POST.lists():
                if (key == 'choice'):
                    last_id = Register.objects.all().aggregate(Max('r_id'))
                    print(last_id)
                    try:
                        last_id = last_id['r_id__max']+1
                    except:
                        last_id = 1
                    course_id = get_object_or_404(Course, course_id=values[x])
                    p = Register(
                        r_id=last_id,
                        course_id=course_id,
                        student_id=current_user,
                        semester=sem
                        )
                    p.save()
                else:
                    continue
        messages.info(request, 'Pre-Registration Successful')
        return HttpResponseRedirect('/academic-procedures/main')
    else:
        print('not okay')
        return HttpResponseRedirect('/academic-procedures/main')


def final_register(request):
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id=extraInfo_user.id).first()
        # Fuction Call to get the current semster of the Student
        user_sem = get_user_semester(extraInfo_user.id)
        p = FinalRegistrations(
            reg_id=extraInfo_user,
            semester=user_sem+1,
            student_id=current_user,
            registration=True
            )
        p.save()
        messages.info(request, 'Registration Successful')
    return HttpResponseRedirect('/academic-procedures/main')


@login_required(login_url='/accounts/login')
def drop_course(request):
    pass
