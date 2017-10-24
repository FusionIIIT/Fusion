import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render

# from applications.academic_procedures.models import Register
from applications.academic_information.models import Course
from applications.globals.models import ExtraInfo

# from . forms import AddDropCourseForm

# Create your views here.


@login_required(login_url='/accounts/login')
def academic_procedures(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)
    user_sem = 3
    get_courses = Course.objects.all().filter(sem=user_sem)
    print(get_courses, user_sem)
    details = {'current_user': current_user, 'user_sem': user_sem}
    return render(
        request, '../templates/academic_procedures/academic.html',
        {'details': details, 'courses_list': get_courses})


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


@login_required(login_url='/accounts/login')
def drop_course(request):
    pass
