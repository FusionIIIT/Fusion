from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def placement(request):
    context = {}

    return render(request, "placementModule/placement.html", context)
