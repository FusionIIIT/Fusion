from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def mess(request):
    context = {}

    return render(request, "messModule/mess.html", context)

