from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def leave(request):
    context = {}

    return render(request, "leaveModule/leave.html", context)
