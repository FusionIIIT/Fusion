from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def profile(request):
    context = {}

    return render(request, "eisModule/profile.html", context)
