from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

from .models import Course, Education, Experience, Has, StudentPlacement


@login_required
def placement(request):
    context = {}

    return render(request, "placementModule/placement.html", context)


@login_required
def profile(request, username):
    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    student = get_object_or_404(Student, Q(id=profile.id))
    studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
    skills = Has.objects.filter(Q(unique_id=student))
    education = Education.objects.filter(Q(unique_id=student))
    course = Course.objects.filter(Q(unique_id=student))
    experience = Experience.objects.filter(Q(unique_id=student))
    context = {'user': user, 'profile': profile, 'student': studentplacement, 'skills': skills,
               'educations': education, 'courses': course, 'experiences': experience}
    return render(request, "placementModule/placement.html", context)
