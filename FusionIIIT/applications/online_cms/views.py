from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from applications.globals.models import *
from applications.academic_procedures.models import *
from applications.academic_information.models import *
from datetime import datetime

@login_required
def viewcourses(request):
    user=request.user
    extrainfo=ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        student=Student.objects.get(id=extrainfo)
        month=datetime.now().month
        sem=0
        if month>=8 and month <=12:
            sem=1
        roll=student.id.id[:4]
        print(roll," ",student.id.user.username)
        semester=(datetime.now().year-int(roll))*2+sem
        print(semester,"sem")
        register=Register.objects.filter(student_id=student,semester=semester)
        return render(request,'online_cms/viewcourses.html',{'register':register})
    else:
        instructor=Instructor.objects.filter(instructor_id=extrainfo)
        return render(request,'online_cms/viewcourses.html',{'instructor':instructor})


@login_required
def courses(request,course_code):
    return HttpResponse(course_name)
