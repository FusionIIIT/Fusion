from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render

# from . models import Register
from .forms import AddDropCourseForm

# Create your views here.


@login_required(login_url='/login')
def add_course(request):

    if request.method == 'POST':
        return HttpResponse('congratzzzzz')
    else:
        CourseForm = AddDropCourseForm(user=request.user)

    return render(request, 'test.html', {'CourseForm': CourseForm})


def drop_course(request):
    pass
