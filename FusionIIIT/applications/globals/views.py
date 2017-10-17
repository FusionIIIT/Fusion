from django.shortcuts import render


def index(request):
    context = {}

    return render(request, "globals/index1.html", context)


def login(request):
    context = {}

    return render(request, "globals/login.html", context)


def dashboard(request):
    context = {}

    return render(request, "dashboard/dashboard.html", context)
