import os
from django.shortcuts import render, HttpResponseRedirect
from django.http import HttpResponse
from . models import Resgister
from applications.academic_information.models import (Calendar, Course, Exam_timetable, Grades, Holiday,
                                                        Instructor, Meeting, Student_attendance, Timetable)
from . forms import AddDropCourseForm 
# Create your views here.


@login_required(login_url='/login')
def add_course(request):

    if request.method == 'POST':
        return HttpResponse('congratzzzzz')
    else:
        CourseForm = AddDropCourseForm(user=request.user)

    return render(request, 'test.html', {'CourseForm': CourseForm})
