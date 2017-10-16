from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def complaint(request):
    context = {}

    return render(request, "complaintModule/complaint.html", context)
