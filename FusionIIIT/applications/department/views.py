import datetime
import json
from operator import or_
from functools import reduce

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

#from .models import ()
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Create your views here.
@login_required(login_url='/accounts/login')
def admin(request):
    admin = Designation.objects.get(name='admin')
    hod = Designation.objects.get(name='hod')
    hd_admin = HoldsDesignation.objects.filter(
        user=request.user, designation=admin)
    hd_hod = HoldsDesignation.objects.filter(
        user=request.user, designation=hod)


def hod(request):
    return render(request,"department/index.html")