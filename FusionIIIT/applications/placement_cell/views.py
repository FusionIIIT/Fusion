from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

from .models import Has, StudentPlacement


@login_required
def placement(request):
    context = {}

    return render(request, "placementModule/placement.html", context)


def profile(request, username):
    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    student = get_object_or_404(Student, Q(id=profile.id))
    studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
    skills = Has.objects.filter(Q(unique_id=student))
    context = {'user': user, 'profile': profile, 'student': studentplacement, 'skills': skills}
    return render(request, "placementModule/placement.html", context)
