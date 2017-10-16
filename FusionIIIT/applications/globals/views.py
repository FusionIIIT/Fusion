from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def index(request):
    context = {}

    return render(request, "globals/index1.html", context)


def login(request):
    context = {}

    return render(request, "globals/login.html", context)


def dashboard(request):
    context = {}

    return render(request, "dashboard/dashboard.html", context)
