from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def visitorhostel(request):
    context = {}

    return render(request, "vhModule/visitorhostel.html", context)
