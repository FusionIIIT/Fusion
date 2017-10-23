from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User
from applications.academic_procedures.models import Register
from applications.academic_information.models import Course
from django.shortcuts import get_object_or_404
import datetime
# from . forms import AddDropCourseForm

# Create your views here.


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
    get_courses = Course.objects.all().filter(sem = user_sem).first()
    print(get_courses)
    return HttpResponse('fucked')

@login_required(login_url='/accounts/login')
def drop_course(request):
    pass
