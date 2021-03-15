from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from django.contrib.auth.models import User
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, DepartmentInfo)
from applications.academic_information.models import *
# from .models import AllotedHostelRoom


# Create your views here.

# @login_required
# def alloted_room(request):
#     hall_1_boys_student = AllotedHostelRoom.objects.filter(id__hall_no="HALL-1-BOYS")
#     hall_1_girls_student = AllotedHostelRoom.objects.filter(id__hall_no="HALL-1-GIRLS")
#     hall_3_student = AllotedHostelRoom.objects.filter(id__hall_no="HALL-3")
#     hall_4_student = AllotedHostelRoom.objects.filter(id__hall_no="Hall-4")
#     context = {
#         'hall_1_boys_student': hall_1_boys_student,
#         'hall_1_girls_student': hall_1_girls_student,
#         'hall_3_student': hall_3_student,
#         'hall_4_student': hall_4_student
#     }
    
#     return render(request, 'hostel_management/alloted_hostel_room.html', context)

def view_alloted_room(request):
    hall_1_student = Student.objects.filter(hall_no=1)
    hall_3_student = Student.objects.filter(hall_no=3)
    hall_4_student = Student.objects.filter(hall_no=4)[:10]

    paginator = Paginator(hall_4_student, 5) # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)               

    context = {
        'hall_1_student': hall_1_student,
        'hall_3_student': hall_3_student,
        'hall_4_student': hall_4_student,
        'page_obj': page_obj
    }

    return render(request, 'hostelmanagement/hostel.html', context)