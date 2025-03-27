from django.core.serializers import serialize
from django.http import HttpResponseBadRequest
from .models import HostelLeave, HallCaretaker
from applications.hostel_management.models import HallCaretaker, HallWarden
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
from rest_framework.exceptions import NotFound
from django.shortcuts import redirect
from django.template import loader
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from .models import HallCaretaker, HallWarden
from django.urls import reverse
from .models import StudentDetails
from rest_framework.exceptions import APIException



from django.shortcuts import render, redirect

from .models import HostelLeave
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status



from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
# from .models import HostelStudentAttendance
from django.http import JsonResponse
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, DepartmentInfo)
from applications.academic_information.models import Student
from applications.academic_information.models import *
from django.db.models import Q
import datetime
from datetime import time, datetime, date
from time import mktime, time, localtime
from .models import *
import xlrd
from .forms import GuestRoomBookingForm, HostelNoticeBoardForm
import re
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import View
from django.db.models import Q
from django.contrib import messages
from .utils import render_to_pdf, save_worker_report_sheet, get_caretaker_hall
from .utils import add_to_room, remove_from_room
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
import json

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from Fusion.settings.common import LOGIN_URL
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from .forms import HallForm
from notification.views import hostel_notifications
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


# //! My change


@login_required
def hostel_view(request, context={}):
    """
    This is a general function which is used for all the views functions.
    This function renders all the contexts required in templates.
    @param:
        request - HttpRequest object containing metadata about the user request.
        context - stores any data passed during request,by default is empty.

    @variables:
        hall_1_student - stores all hall 1 students
        hall_3_student - stores all hall 3 students
        hall_4_student - stores all hall 4 students
        all_hall - stores all the hall of residence
        all_notice - stores all notices of hostels (latest first)
    """
    # Check if the user is a superuser
    is_superuser = request.user.is_superuser

    all_hall = Hall.objects.all()
    halls_student = {}
    for hall in all_hall:
        halls_student[hall.hall_id] = Student.objects.filter(
            hall_no=int(hall.hall_id[4])).select_related('id__user')

    hall_staffs = {}
    for hall in all_hall:
        hall_staffs[hall.hall_id] = StaffSchedule.objects.filter(
            hall=hall).select_related('staff_id__id__user')

    all_notice = HostelNoticeBoard.objects.all().order_by("-id")
    hall_notices = {}
    for hall in all_hall:
        hall_notices[hall.hall_id] = HostelNoticeBoard.objects.filter(
            hall=hall).select_related('hall', 'posted_by__user')

    pending_guest_room_requests = {}
    for hall in all_hall:
        pending_guest_room_requests[hall.hall_id] = GuestRoomBooking.objects.filter(
            hall=hall, status='Pending').select_related('hall', 'intender')
        
       
    guest_rooms = {}
    for hall in all_hall:
        guest_rooms[hall.hall_id] = GuestRoom.objects.filter(
            hall=hall,vacant=True).select_related('hall')
    user_guest_room_requests = GuestRoomBooking.objects.filter(
        intender=request.user).order_by("-arrival_date")

    halls = Hall.objects.all()
    # Create a list to store additional details
    hostel_details = []

    # Loop through each hall and fetch assignedCaretaker and assignedWarden
    for hall in halls:
        try:
            caretaker = HallCaretaker.objects.filter(hall=hall).first()
            warden = HallWarden.objects.filter(hall=hall).first()
        except HostelAllotment.DoesNotExist:
            assigned_caretaker = None
            assigned_warden = None

        vacant_seat=(hall.max_accomodation-hall.number_students)
        hostel_detail = {
            'hall_id': hall.hall_id,
            'hall_name': hall.hall_name,
            'seater_type':hall.type_of_seater,
            'max_accomodation': hall.max_accomodation,
            'number_students': hall.number_students,
            'vacant_seat':vacant_seat,
            'assigned_batch': hall.assigned_batch,
            'assigned_caretaker': caretaker.staff.id.user.username if caretaker else None,
            'assigned_warden': warden.faculty.id.user.username if warden else None,
        }

        hostel_details.append(hostel_detail)

    Staff_obj = Staff.objects.all().select_related('id__user')
    hall1 = Hall.objects.get(hall_id='hall1')
    hall3 = Hall.objects.get(hall_id='hall3')
    hall4 = Hall.objects.get(hall_id='hall4')
    hall1_staff = StaffSchedule.objects.filter(hall=hall1)
    hall3_staff = StaffSchedule.objects.filter(hall=hall3)
    hall4_staff = StaffSchedule.objects.filter(hall=hall4)
    hall_caretakers = HallCaretaker.objects.all().select_related()
    hall_wardens = HallWarden.objects.all().select_related()
    all_students = Student.objects.all().select_related('id__user')
    all_students_id = []
    for student in all_students:
        all_students_id.append(student.id_id)
    # print(all_students)
    hall_student = ""
    current_hall = ""
    get_avail_room = []
    get_hall = get_caretaker_hall(hall_caretakers, request.user)
    if get_hall:
        get_hall_num = re.findall('[0-9]+', str(get_hall.hall_id))
        hall_student = Student.objects.filter(hall_no=int(
            str(get_hall_num[0]))).select_related('id__user')
        current_hall = 'hall'+str(get_hall_num[0])

    for hall in all_hall:
        total_rooms = HallRoom.objects.filter(hall=hall)
        for room in total_rooms:
            if (room.room_cap > room.room_occupied):
                get_avail_room.append(room)

    hall_caretaker_user = []
    for caretaker in hall_caretakers:
        hall_caretaker_user.append(caretaker.staff.id.user)

    hall_warden_user = []
    for warden in hall_wardens:
        hall_warden_user.append(warden.faculty.id.user)

    all_students = Student.objects.all().select_related('id__user')
    all_students_id = []
    for student in all_students:
        all_students_id.append(student.id_id)

    todays_date = date.today()
    current_year = todays_date.year
    current_month = todays_date.month

    if current_month != 1:
        worker_report = WorkerReport.objects.filter(Q(hall__hall_id=current_hall, year=current_year, month=current_month) | Q(
            hall__hall_id=current_hall, year=current_year, month=current_month-1))
    else:
        worker_report = WorkerReport.objects.filter(
            hall__hall_id=current_hall, year=current_year-1, month=12)

    attendance = HostelStudentAttendence.objects.all().select_related()
    halls_attendance = {}
    for hall in all_hall:
        halls_attendance[hall.hall_id] = HostelStudentAttendence.objects.filter(
            hall=hall).select_related()

    user_complaints = HostelComplaint.objects.filter(
        roll_number=request.user.username)
    user_leaves = HostelLeave.objects.filter(roll_num=request.user.username)
    my_leaves = []
    for leave in user_leaves:
        my_leaves.append(leave)
    my_complaints = []
    for complaint in user_complaints:
        my_complaints.append(complaint)

    all_leaves = HostelLeave.objects.all()
    all_complaints = HostelComplaint.objects.all()

    add_hostel_form = HallForm()
    warden_ids = Faculty.objects.all().select_related('id__user')

    # //! My change for imposing fines
    user_id = request.user
    staff_fine_caretaker = user_id.extrainfo.id
    students = Student.objects.all()

    fine_user = request.user

    if request.user.id in Staff.objects.values_list('id__user', flat=True):
        staff_fine_caretaker = request.user.extrainfo.id

        caretaker_fine_id = HallCaretaker.objects.filter(
            staff_id=staff_fine_caretaker).first()
        if caretaker_fine_id:
            hall_fine_id = caretaker_fine_id.hall_id
            hostel_fines = HostelFine.objects.filter(
                hall_id=hall_fine_id).order_by('fine_id')
            context['hostel_fines'] = hostel_fines

    # caretaker_fine_id = HallCaretaker.objects.get(staff_id=staff_fine_caretaker)
    # hall_fine_id = caretaker_fine_id.hall_id
    # hostel_fines = HostelFine.objects.filter(hall_id=hall_fine_id).order_by('fine_id')

    if request.user.id in Staff.objects.values_list('id__user', flat=True):
        staff_inventory_caretaker = request.user.extrainfo.id

        caretaker_inventory_id = HallCaretaker.objects.filter(
            staff_id=staff_inventory_caretaker).first()

        if caretaker_inventory_id:
            hall_inventory_id = caretaker_inventory_id.hall_id
            inventories = HostelInventory.objects.filter(
                hall_id=hall_inventory_id).order_by('inventory_id')

            # Serialize inventory data
            inventory_data = []
            for inventory in inventories:
                inventory_data.append({
                    'inventory_id': inventory.inventory_id,
                    'hall_id': inventory.hall_id,
                    'inventory_name': inventory.inventory_name,
                    # Convert DecimalField to string
                    'cost': str(inventory.cost),
                    'quantity': inventory.quantity,
                })

            inventory_data.sort(key=lambda x: x['inventory_id'])
            context['inventories'] = inventory_data

    # all students details for caretaker and warden
    if request.user.id in Staff.objects.values_list('id__user', flat=True):
        staff_student_info = request.user.extrainfo.id

        if HallCaretaker.objects.filter(staff_id=staff_student_info).exists():
            hall_caretaker_id = HallCaretaker.objects.get(
                staff_id=staff_student_info).hall_id

            hall_num = Hall.objects.get(id=hall_caretaker_id)
            hall_number = int(''.join(filter(str.isdigit,hall_num.hall_id)))

            
            # hostel_students_details = Student.objects.filter(hall_no=hall_number)
            # context['hostel_students_details']= hostel_students_details

            hostel_students_details = []
            students = Student.objects.filter(hall_no=hall_number)

            a_room=[]
            t_rooms = HallRoom.objects.filter(hall=hall_num)
            for room in t_rooms:
                if (room.room_cap > room.room_occupied):
                    a_room.append(room)

            # print(a_room)
            # Retrieve additional information for each student
            for student in students:
                student_info = {}
                student_info['student_id'] = student.id.id
                student_info['first_name'] = student.id.user.first_name
                student_info['programme'] = student.programme
                student_info['batch'] = student.batch
                student_info['hall_number'] = student.hall_no
                student_info['room_number'] = student.room_no
                student_info['specialization'] = student.specialization
                # student_info['parent_contact'] = student.parent_contact
                
                # Fetch address and phone number from ExtraInfo model
                extra_info = ExtraInfo.objects.get(user=student.id.user)
                student_info['address'] = extra_info.address
                student_info['phone_number'] = extra_info.phone_no
                
                hostel_students_details.append(student_info)

            # Sort the hostel_students_details list by roll number
            hostel_students_details = sorted(hostel_students_details, key=lambda x: x['student_id'])
            
            
            context['hostel_students_details'] = hostel_students_details
            context['av_room'] = a_room

    if request.user.id in Faculty.objects.values_list('id__user', flat=True):
        staff_student_info = request.user.extrainfo.id    
        if HallWarden.objects.filter(faculty_id=staff_student_info).exists():
            hall_warden_id = HallWarden.objects.get(
                faculty_id=staff_student_info).hall_id

            hall_num = Hall.objects.get(id=hall_warden_id)

            hall_number = int(''.join(filter(str.isdigit,hall_num.hall_id)))
            
            # hostel_students_details = Student.objects.filter(hall_no=hall_number)
            # context['hostel_students_details']= hostel_students_details

            hostel_students_details = []
            students = Student.objects.filter(hall_no=hall_number)

            # Retrieve additional information for each student
            for student in students:
                student_info = {}
                student_info['student_id'] = student.id.id
                student_info['first_name'] = student.id.user.first_name
                student_info['programme'] = student.programme
                student_info['batch'] = student.batch
                student_info['hall_number'] = student.hall_no
                student_info['room_number'] = student.room_no
                student_info['specialization'] = student.specialization
                # student_info['parent_contact'] = student.parent_contact
                
                # Fetch address and phone number from ExtraInfo model
                extra_info = ExtraInfo.objects.get(user=student.id.user)
                student_info['address'] = extra_info.address
                student_info['phone_number'] = extra_info.phone_no
                
                hostel_students_details.append(student_info)
                hostel_students_details = sorted(hostel_students_details, key=lambda x: x['student_id'])


            context['hostel_students_details'] = hostel_students_details

            


    # print(request.user.username);
    if Student.objects.filter(id_id=request.user.username).exists():
        user_id = request.user.username
        student_fines = HostelFine.objects.filter(student_id=user_id)
        # print(student_fines)
        context['student_fines'] = student_fines

    hostel_transactions = HostelTransactionHistory.objects.order_by('-timestamp')

    # Retrieve all hostel history entries
    hostel_history = HostelHistory.objects.order_by('-timestamp')
    context = {

        'all_hall': all_hall,
        'all_notice': all_notice,
        'staff': Staff_obj,
        'hall1_staff': hall1_staff,
        'hall3_staff': hall3_staff,
        'hall4_staff': hall4_staff,
        'hall_caretaker': hall_caretaker_user,
        'hall_warden': hall_warden_user,
        'room_avail': get_avail_room,
        'hall_student': hall_student,
        'worker_report': worker_report,
        'halls_student': halls_student,
        'current_hall': current_hall,
        'hall_staffs': hall_staffs,
        'hall_notices': hall_notices,
        'attendance': halls_attendance,
        'guest_rooms': guest_rooms,
        'pending_guest_room_requests': pending_guest_room_requests,
        'user_guest_room_requests': user_guest_room_requests,
        'all_students_id': all_students_id,
        'is_superuser': is_superuser,
        'warden_ids': warden_ids,
        'add_hostel_form': add_hostel_form,
        'hostel_details': hostel_details,
        'all_students_id': all_students_id,
        'my_complaints': my_complaints,
        'my_leaves': my_leaves,
        'all_leaves': all_leaves,
        'all_complaints': all_complaints,
        'staff_fine_caretaker': staff_fine_caretaker,
        'students': students,
        'hostel_transactions':hostel_transactions,
        'hostel_history':hostel_history,
        **context
    }

    return render(request, 'hostelmanagement/hostel.html', context)
    
def staff_edit_schedule(request):
    """
    This function is responsible for creating a new or updating an existing staff schedule.
    @param:
       request - HttpRequest object containing metadata about the user request.

    @variables:
       start_time - stores start time of the schedule.
       end_time - stores endtime of the schedule.
       staff_name - stores name of staff.
       staff_type - stores type of staff.
       day - stores assigned day of the schedule.
       staff - stores Staff instance related to staff_name.
       staff_schedule - stores StaffSchedule instance related to 'staff'.
       hall_caretakers - stores all hall caretakers.
    """
    if request.method == 'POST':
        start_time = datetime.datetime.strptime(
            request.POST["start_time"], '%H:%M').time()
        end_time = datetime.datetime.strptime(
            request.POST["end_time"], '%H:%M').time()
        staff_name = request.POST["Staff_name"]
        staff_type = request.POST["staff_type"]
        day = request.POST["day"]

        staff = Staff.objects.get(pk=staff_name)
        try:
            staff_schedule = StaffSchedule.objects.get(staff_id=staff)
            staff_schedule.day = day
            staff_schedule.start_time = start_time
            staff_schedule.end_time = end_time
            staff_schedule.staff_type = staff_type
            staff_schedule.save()
            messages.success(request, 'Staff schedule updated successfully.')
        except:
            hall_caretakers = HallCaretaker.objects.all()
            get_hall = ""
            get_hall = get_caretaker_hall(hall_caretakers, request.user)
            StaffSchedule(hall=get_hall, staff_id=staff, day=day,
                          staff_type=staff_type, start_time=start_time, end_time=end_time).save()
            messages.success(request, 'Staff schedule created successfully.')
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def staff_delete_schedule(request):
    """
    This function is responsible for deleting an existing staff schedule.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      staff_dlt_id - stores id of the staff whose schedule is to be deleted.
      staff - stores Staff object related to 'staff_name'
      staff_schedule - stores staff schedule related to 'staff'
    """
    if request.method == 'POST':
        staff_dlt_id = request.POST["dlt_schedule"]
        staff = Staff.objects.get(pk=staff_dlt_id)
        staff_schedule = StaffSchedule.objects.get(staff_id=staff)
        staff_schedule.delete()
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


@login_required
def notice_board(request):
    """
    This function is used to create a form to show the notice on the Notice Board.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      hall - stores hall of residence related to the notice.
      head_line - stores headline of the notice. 
      content - stores content of the notice uploaded as file.
      description - stores description of the notice.
    """
    if request.method == "POST":
        form = HostelNoticeBoardForm(request.POST, request.FILES)

        if form.is_valid():
            hall = form.cleaned_data['hall']
            head_line = form.cleaned_data['head_line']
            content = form.cleaned_data['content']
            description = form.cleaned_data['description']

            new_notice = HostelNoticeBoard.objects.create(hall=hall, posted_by=request.user.extrainfo, head_line=head_line, content=content,
                                                          description=description)

            new_notice.save()
            messages.success(request, 'Notice created successfully.')
        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


@login_required
def delete_notice(request):
    """
    This function is responsible for deleting ana existing notice from the notice board.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      notice_id - stores id of the notice.
      notice - stores HostelNoticeBoard object related to 'notice_id'
    """
    if request.method == 'POST':
        notice_id = request.POST["dlt_notice"]
        notice = HostelNoticeBoard.objects.get(pk=notice_id)
        notice.delete()
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def edit_student_rooms_sheet(request):
    """
    This function is used to edit the room and hall of a multiple students.
    The user uploads a .xls file with Roll No, Hall No, and Room No to be updated.
    @param:
        request - HttpRequest object containing metadata about the user request.
    """
    if request.method == "POST":
        sheet = request.FILES["upload_rooms"]
        excel = xlrd.open_workbook(file_contents=sheet.read())
        all_rows = excel.sheets()[0]
        for row in all_rows:
            if row[0].value == "Roll No":
                continue
            roll_no = row[0].value
            hall_no = row[1].value
            if row[0].ctype == 2:
                roll_no = str(int(roll_no))
            if row[1].ctype == 2:
                hall_no = str(int(hall_no))

            room_no = row[2].value
            block = str(room_no[0])
            room = re.findall('[0-9]+', room_no)
            is_valid = True
            student = Student.objects.filter(id=roll_no.strip())
            hall = Hall.objects.filter(hall_id="hall"+hall_no[0])
            if student and hall.exists():
                Room = HallRoom.objects.filter(
                    hall=hall[0], block_no=block, room_no=str(room[0]))
                if Room.exists() and Room[0].room_occupied < Room[0].room_cap:
                    continue
                else:
                    is_valid = False
                    # print('Room  unavailable!')
                    messages.error(request, 'Room  unavailable!')
                    break
            else:
                is_valid = False
                # print("Wrong Credentials entered!")
                messages.error(request, 'Wrong credentials entered!')
                break

        if not is_valid:
            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

        for row in all_rows:
            if row[0].value == "Roll No":
                continue
            roll_no = row[0].value
            if row[0].ctype == 2:
                roll_no = str(int(roll_no))

            hall_no = str(int(row[1].value))
            room_no = row[2].value
            block = str(room_no[0])
            room = re.findall('[0-9]+', room_no)
            is_valid = True
            student = Student.objects.filter(id=roll_no.strip())
            remove_from_room(student[0])
            add_to_room(student[0], room_no, hall_no)
        messages.success(request, 'Hall Room change successfull !')

        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def edit_student_room(request):
    """
    This function is used to edit the room number of a student.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @varibles:
      roll_no - stores roll number of the student.
      room_no - stores new room number. 
      batch - stores batch number of the student generated from 'roll_no'
      students - stores students related to 'batch'.
    """
    if request.method == "POST":
        roll_no = request.POST["roll_no"]
        hall_room_no = request.POST["hall_room_no"]
        index = hall_room_no.find('-')
        room_no = hall_room_no[index+1:]
        hall_no = hall_room_no[:index]
        student = Student.objects.get(id=roll_no)
        remove_from_room(student)
        add_to_room(student, new_room=room_no, new_hall=hall_no)
        messages.success(request, 'Student room changed successfully.')
        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def edit_attendance(request):
    """
    This function is used to edit the attendance of a student.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      student_id = The student whose attendance has to be updated.
      hall = The hall of the concerned student.
      date = The date on which attendance has to be marked.
    """
    if request.method == "POST":
        roll_no = request.POST["roll_no"]

        student = Student.objects.get(id=roll_no)
        hall = Hall.objects.get(hall_id='hall'+str(student.hall_no))
        date = datetime.datetime.today().strftime('%Y-%m-%d')

        if HostelStudentAttendence.objects.filter(student_id=student, date=date).exists() == True:
            messages.error(
                request, f'{student.id.id} is already marked present on {date}')
            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

        record = HostelStudentAttendence.objects.create(student_id=student,
                                                        hall=hall, date=date, present=True)
        record.save()

        messages.success(request, f'Attendance of {student.id.id} recorded.')

        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


# @login_required
# def generate_worker_report(request):
#     """
#     This function is used to read uploaded worker report spreadsheet(.xls) and generate WorkerReport instance and save it in the database.
#     @param:
#       request - HttpRequest object containing metadata about the user request.

#     @variables:
#       files - stores uploaded worker report file 
#       excel - stores the opened spreadsheet file raedy for data extraction.
#       user_id - stores user id of the current user.
#       sheet - stores a sheet from the uploaded spreadsheet.
#     """
#     if request.method == "POST":
#         try:
#             files = request.FILES['upload_report']
#             excel = xlrd.open_workbook(file_contents=files.read())
#             user_id = request.user.extrainfo.id
#             if str(excel.sheets()[0].cell(0, 0).value)[:5].lower() == str(HallCaretaker.objects.get(staff__id=user_id).hall):
#                 for sheet in excel.sheets():
#                     save_worker_report_sheet(excel, sheet, user_id)
#                     return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

#             return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
#         except:
#             messages.error(
#                 request, "Please upload a file in valid format before submitting")
#             return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


# class GeneratePDF(View):
#     def get(self, request, *args, **kwargs):
#         """
#         This function is used to generate worker report in pdf format available for download.
#         @param:
#           request - HttpRequest object containing metadata about the user request.

#         @variables:
#           months - stores number of months for which the authorized user wants to generate worker report.
#           toadys_date - stores current date.
#           current_year - stores current year retrieved from 'todays_date'.
#           current_month - stores current month retrieved from 'todays_date'.
#           template - stores template returned by 'get_template' method.
#           hall_caretakers - stores all hall caretakers.
#           worker_report - stores 'WorkerReport' instances according to 'months'.

#         """
#         months = int(request.GET.get('months'))
#         todays_date = date.today()
#         current_year = todays_date.year
#         current_month = todays_date.month

#         template = get_template('hostelmanagement/view_report.html')

#         hall_caretakers = HallCaretaker.objects.all()
#         get_hall = ""
#         get_hall = get_caretaker_hall(hall_caretakers, request.user)
        
#         if months < current_month:
#             worker_report = WorkerReport.objects.filter(
#                 hall=get_hall, month__gte=current_month-months, year=current_year)
#         else:
#             worker_report = WorkerReport.objects.filter(Q(hall=get_hall, year=current_year, month__lte=current_month) | Q(
#                 hall=get_hall, year=current_year-1, month__gte=12-months+current_month))

#         worker = {
#             'worker_report': worker_report
#         }
#         html = template.render(worker)
#         pdf = render_to_pdf('hostelmanagement/view_report.html', worker)
#         if pdf:
#             response = HttpResponse(pdf, content_type='application/pdf')
#             filename = "Invoice_%s.pdf" % ("12341231")
#             content = "inline; filename='%s'" % (filename)
#             download = request.GET.get("download")
#             if download:
#                 content = "attachment; filename='%s'" % (filename)
#             response['Content-Disposition'] = content
#             return response
#         return HttpResponse("Not found")

@login_required
def generate_worker_report(request):
    if request.method == "POST":
        try:
            files = request.FILES.get('upload_report')
            if files:
                # Check if the file has a valid extension
                file_extension = files.name.split('.')[-1].lower()
                if file_extension not in ['xls', 'xlsx']:
                    messages.error(request, "Invalid file format. Please upload a .xls or .xlsx file.")
                    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
                
                excel = xlrd.open_workbook(file_contents=files.read())
                user_id = request.user.extrainfo.id
                for sheet in excel.sheets():
                    # print('111111111111111111111111111111111111',sheet[0])
                    save_worker_report_sheet(excel, sheet, user_id)
                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
            else:
                messages.error(request, "No file uploaded")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        """
        This function is used to generate worker report in pdf format available for download.
        @param:
          request - HttpRequest object containing metadata about the user request.

        @variables:
          months - stores number of months for which the authorized user wants to generate worker report.
          toadys_date - stores current date.
          current_year - stores current year retrieved from 'todays_date'.
          current_month - stores current month retrieved from 'todays_date'.
          template - stores template returned by 'get_template' method.
          hall_caretakers - stores all hall caretakers.
          worker_report - stores 'WorkerReport' instances according to 'months'.

        """
        months = int(request.GET.get('months'))
        # print('~~~~month',months)
        todays_date = date.today()
        current_year = todays_date.year
        current_month = todays_date.month

        template = get_template('hostelmanagement/view_report.html')

        hall_caretakers = HallCaretaker.objects.all()
        get_hall = ""
        get_hall = get_caretaker_hall(hall_caretakers, request.user)
        # print('~~~~~ get_hall' , get_hall)
        # print('month<curr_mn~~~~~~~',months,current_month)
        
        if months < current_month:
            worker_report = WorkerReport.objects.filter(
                hall=get_hall,)
        else:
            worker_report = WorkerReport.objects.filter(Q(hall=get_hall, year=current_year, month__lte=current_month) | Q(
                hall=get_hall, year=current_year-1, month__gte=12-months+current_month))

        worker = {
            'worker_report': worker_report
        }
        html = template.render(worker)
        pdf = render_to_pdf('hostelmanagement/view_report.html', worker)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Invoice_%s.pdf" % ("12341231")
            content = "inline; filename='%s'" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


def hostel_notice_board(request):
    notices = all().values('id', 'hall', 'posted_by',
                           'head_line', 'content', 'description')
    data = list(notices)
    return JsonResponse(data, safe=False)


@login_required
def all_leave_data(request):
    user_id = request.user.id  # Using request.user to get the user ID
    try:
        # Assuming the user's profile is stored in extrainfo
        staff = request.user.extrainfo.id
    except AttributeError:
        staff = None

    if staff is not None and HallCaretaker.objects.filter(staff_id=staff).exists():
        all_leave = HostelLeave.objects.all()
        return render(request, 'hostelmanagement/all_leave_data.html', {'all_leave': all_leave})
    else:
        return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


@login_required
def create_hostel_leave(request):
    
    if request.method == 'GET':
        return render(request, 'hostelmanagement/create_leave.html')
    elif request.method == 'POST':
        data = request.POST  # Assuming you are sending form data via POST request
        student_name = data.get('student_name')
        roll_num = data.get('roll_num')
        phone_number = data.get('phone_number')  # Retrieve phone number from form data
        reason = data.get('reason')
        start_date = data.get('start_date', timezone.now())
        end_date = data.get('end_date')
        

        # Create HostelLeave object and save to the database
        leave = HostelLeave.objects.create(
            student_name=student_name,
            roll_num=roll_num,
            phone_number=phone_number,  # Include phone number in the object creation
            reason=reason,
            start_date=start_date,
            end_date=end_date,
            
        )
        caretakers = HallCaretaker.objects.all()
        sender = request.user
        type = "leave_request"
        for caretaker in caretakers:
            try:
                # Send notification
                hostel_notifications(sender, caretaker.staff.id.user, type)
            except Exception as e:
                # Handle notification sending error
                print(f"Error sending notification to caretaker {caretaker.staff.user.username}: {e}")

        return JsonResponse({'message': 'HostelLeave created successfully'}, status=status.HTTP_201_CREATED)

# hostel_complaints_list caretaker can see all hostel complaints

@login_required
def hostel_complaint_list(request):
    user_id = request.user.id

    try:
        # Assuming the user's profile is stored in extrainfo
        staff = request.user.extrainfo.id
    except AttributeError:
        staff = None

    if staff is not None and HallCaretaker.objects.filter(staff_id=staff).exists():
        complaints = HostelComplaint.objects.all()
        return render(request, 'hostelmanagement/hostel_complaint.html', {'complaints': complaints})
    else:
        return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


@login_required
def get_students(request):
    try:
        staff = request.user.extrainfo.id
        print(staff)
    except AttributeError:
        staff = None

    if HallCaretaker.objects.filter(staff_id=staff).exists():
        hall_id = HallCaretaker.objects.get(staff_id=staff).hall_id
        print(hall_id)
        hall_no = Hall.objects.get(id=hall_id)
        print(hall_no)
        student_details = StudentDetails.objects.filter(hall_id=hall_no)

        return render(request, 'hostelmanagement/student_details.html', {'students': student_details})

    elif HallWarden.objects.filter(faculty_id=staff).exists():
        hall_id = HallWarden.objects.get(faculty_id=staff).hall_id
        student_details = StudentDetails.objects.filter(hall_id=hall_no)

        return render(request, 'hostelmanagement/student_details.html', {'students': student_details})
    else:
        return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')

# Student can post complaints


class PostComplaint(APIView):
    # Assuming you are using session authentication
    authentication_classes = [SessionAuthentication]
    # Allow only authenticated users to access the view
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        # print(request.user.username)
        if not request.user.is_authenticated:
            # Redirect to the login page if user is not authenticated
            return redirect('/hostelmanagement')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'hostelmanagement/post_complaint_form.html')

    def post(self, request):
        hall_name = request.data.get('hall_name')
        student_name = request.data.get('student_name')
        roll_number = request.data.get('roll_number')
        description = request.data.get('description')
        contact_number = request.data.get('contact_number')

        # Assuming the student's name is stored in the user object
        student_name = request.user.username

        complaint = HostelComplaint.objects.create(
            hall_name=hall_name,
            student_name=student_name,
            roll_number=roll_number,
            description=description,
            contact_number=contact_number
        )

        # Use JavaScript to display a pop-up message after submission
        return HttpResponse('<script>alert("Complaint submitted successfully"); window.location.href = "/hostelmanagement";</script>')


# // student can see his leave status

class my_leaves(View):
    @method_decorator(login_required, name='dispatch')
    def get(self, request, *args, **kwargs):
        try:
            # Get the user ID from the request's user
            user_id = str(request.user)

            # Retrieve leaves registered by the current student based on their roll number
            my_leaves = HostelLeave.objects.filter(roll_num__iexact=user_id)
            # Construct the context to pass to the template
            context = {
                'leaves': my_leaves
            }

            # Render the template with the context data
            return render(request, 'hostelmanagement/my_leaves.html', context)

        except User.DoesNotExist:
            # Handle the case where the user with the given ID doesn't exist
            return HttpResponse(f"User with ID {user_id} does not exist.")


class HallIdView(APIView):
    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def get(self, request, *args, **kwargs):
        hall_id = HostelAllotment.objects.values('hall_id')
        return Response(hall_id, status=status.HTTP_200_OK)


@login_required(login_url=LOGIN_URL)
def logout_view(request):
    logout(request)
    return redirect("/")


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AssignCaretakerView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    template_name = 'hostelmanagement/assign_caretaker.html'

    def get(self, request, *args, **kwargs):
        hall = Hall.objects.all()
        caretaker_usernames = Staff.objects.all()
        return render(request, self.template_name, {'halls': hall, 'caretaker_usernames': caretaker_usernames})

    def post(self, request, *args, **kwargs):
        hall_id = request.data.get('hall_id')
        caretaker_username = request.data.get('caretaker_username')

        try:
            hall = Hall.objects.get(hall_id=hall_id)
            caretaker_staff = Staff.objects.get(
                id__user__username=caretaker_username)

            # Retrieve the previous caretaker for the hall, if any
            prev_hall_caretaker = HallCaretaker.objects.filter(hall=hall).first()
            # print(prev_hall_caretaker.staff.id)
            # Delete any previous assignments of the caretaker in HallCaretaker table
            HallCaretaker.objects.filter(staff=caretaker_staff).delete()

            # Delete any previous assignments of the caretaker in HostelAllotment table
            HostelAllotment.objects.filter(
                assignedCaretaker=caretaker_staff).delete()

            # Delete any previously assigned caretaker to the same hall
            HallCaretaker.objects.filter(hall=hall).delete()

            # Assign the new caretaker to the hall in HallCaretaker table
            hall_caretaker = HallCaretaker.objects.create(
                hall=hall, staff=caretaker_staff)

            # # Update the assigned caretaker in Hostelallottment table
            hostel_allotments = HostelAllotment.objects.filter(hall=hall)
            for hostel_allotment in hostel_allotments:
                hostel_allotment.assignedCaretaker = caretaker_staff
                hostel_allotment.save()

            # Retrieve the current warden for the hall
            current_warden = HallWarden.objects.filter(hall=hall).first()

            try:
                history_entry = HostelTransactionHistory.objects.create(
                    hall=hall,
                    change_type='Caretaker',
                    previous_value= prev_hall_caretaker.staff.id if (prev_hall_caretaker and prev_hall_caretaker.staff) else 'None',
                    new_value=caretaker_username
                )
            except Exception as e:
                print("Error creating HostelTransactionHistory:", e)

            
            # Create hostel history
            try:
                HostelHistory.objects.create(
                    hall=hall,
                    caretaker=caretaker_staff,
                    batch=hall.assigned_batch,
                    warden=current_warden.faculty if( current_warden and current_warden.faculty) else None
                )
            except Exception as e:
                print ("Error creating history",e)
            return Response({'message': f'Caretaker {caretaker_username} assigned to Hall {hall_id} successfully'}, status=status.HTTP_201_CREATED)

        except Hall.DoesNotExist:
            return Response({'error': f'Hall with ID {hall_id} not found'}, status=status.HTTP_404_NOT_FOUND)
        except Staff.DoesNotExist:
            return Response({'error': f'Caretaker with username {caretaker_username} not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)



@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AssignBatchView(View):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    # Assuming the HTML file is directly in the 'templates' folder
    template_name = 'hostelmanagement/assign_batch.html'

    def get(self, request, *args, **kwargs):
        hall = Hall.objects.all()
        return render(request, self.template_name, {'halls': hall})

    def update_student_hall_allotment(self, hall, assigned_batch):
        hall_number = int(''.join(filter(str.isdigit, hall.hall_id)))
        students = Student.objects.filter(batch=int(assigned_batch))
       
        
        for student in students:
            student.hall_no = hall_number
            student.save()
            

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():  # Start a database transaction

                data = json.loads(request.body.decode('utf-8'))
                hall_id = data.get('hall_id')

                hall = Hall.objects.get(hall_id=hall_id)
                # previous_batch = hall.assigned_batch  # Get the previous batch
                previous_batch = hall.assigned_batch if hall.assigned_batch is not None else 0  # Get the previous batch
                hall.assigned_batch = data.get('batch')
                hall.save()

                

                
            
                # Update the assignedBatch field in HostelAllotment table for the corresponding hall
                room_allotments = HostelAllotment.objects.filter(hall=hall)
                for room_allotment in room_allotments:
                    room_allotment.assignedBatch = hall.assigned_batch
                    room_allotment.save()
                
                # retrieve the current caretaker and current warden for the hall
                current_caretaker =HallCaretaker.objects.filter(hall=hall).first()
                current_warden = HallWarden.objects.filter(hall=hall).first()

                # Record the transaction history
                HostelTransactionHistory.objects.create(
                    hall=hall,
                    change_type='Batch',
                    previous_value=previous_batch,
                    new_value=hall.assigned_batch
                )

                # Create hostel history
                try:
                    HostelHistory.objects.create(
                        hall=hall,
                        caretaker=current_caretaker.staff if (current_caretaker and current_caretaker.staff) else None,
                        
                        batch=hall.assigned_batch,
                        warden=current_warden.faculty if( current_warden and current_warden.faculty) else None

                    )
                except Exception as e:
                    print ("Error creating history",e)

                self.update_student_hall_allotment(hall, hall.assigned_batch)
                print("batch assigned successssssssssssssssssss")
                messages.success(request, 'batch assigned succesfully')
                
                return JsonResponse({'status': 'success', 'message': 'Batch assigned successfully'}, status=200)

        except Hall.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': f'Hall with ID {hall_id} not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    def test_func(self):
        # Check if the user is a superuser
        return self.request.user.is_superuser


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AssignWardenView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    template_name = 'hostelmanagement/assign_warden.html'

    def post(self, request, *args, **kwargs):
        hall_id = request.data.get('hall_id')
        warden_id = request.data.get('warden_id')
        try:
            hall = Hall.objects.get(hall_id=hall_id)
            warden = Faculty.objects.get(id__user__username=warden_id)

            # Retrieve the previous caretaker for the hall, if any
            prev_hall_warden = HallWarden.objects.filter(hall=hall).first()
           
            # Delete any previous assignments of the warden in Hallwarden table
            HallWarden.objects.filter(faculty=warden).delete()

            # Delete any previous assignments of the warden in HostelAllotment table
            HostelAllotment.objects.filter(assignedWarden=warden).delete()

            # Delete any previously assigned warden to the same hall
            HallWarden.objects.filter(hall=hall).delete()

            # Assign the new warden to the hall in Hallwarden table
            hall_warden = HallWarden.objects.create(hall=hall, faculty=warden)

            #current caretker
            current_caretaker =HallCaretaker.objects.filter(hall=hall).first()
            print(current_caretaker)
            
            # Update the assigned warden in Hostelallottment table
            hostel_allotments = HostelAllotment.objects.filter(hall=hall)
            for hostel_allotment in hostel_allotments:
                hostel_allotment.assignedWarden = warden
                hostel_allotment.save()

            try:
                history_entry = HostelTransactionHistory.objects.create(
                    hall=hall,
                    change_type='Warden',
                    previous_value= prev_hall_warden.faculty.id if (prev_hall_warden and prev_hall_warden.faculty) else 'None',
                    new_value=warden
                )
            except Exception as e:
                print("Error creating HostelTransactionHistory:", e)


            # Create hostel history
            try:
                HostelHistory.objects.create(
                    hall=hall,
                    caretaker=current_caretaker.staff if (current_caretaker and current_caretaker.staff) else None,
                    
                    batch=hall.assigned_batch,
                    warden=warden
                )
            except Exception as e:
                print ("Error creating history",e)


            return Response({'message': f'Warden {warden_id} assigned to Hall {hall_id} successfully'}, status=status.HTTP_201_CREATED)

        except Hall.DoesNotExist:
            return Response({'error': f'Hall with ID {hall_id} not found'}, status=status.HTTP_404_NOT_FOUND)
        except Faculty.DoesNotExist:
            return Response({'error': f'Warden with username {warden_id} not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AddHostelView(View):
    template_name = 'hostelmanagement/add_hostel.html'

    def get(self, request, *args, **kwargs):
        form = HallForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = HallForm(request.POST)
        if form.is_valid():
            hall_id = form.cleaned_data['hall_id']

            # # Check if a hall with the given hall_id already exists
            # if Hall.objects.filter(hall_id=hall_id).exists():
            #     messages.error(request, f'Hall with ID {hall_id} already exists.')
            #     return redirect('hostelmanagement:add_hostel')

            # Check if a hall with the given hall_id already exists
            if Hall.objects.filter(hall_id=hall_id).exists():
                error_message = f'Hall with ID {hall_id} already exists.'

                return HttpResponse(error_message, status=400)

            # If not, create a new hall
            form.save()
            messages.success(request, 'Hall added successfully!')
            # Redirect to the view showing all hostels
            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
            # return render(request, 'hostelmanagement/admin_hostel_list.html')

        # If form is not valid, render the form with errors
        return render(request, self.template_name, {'form': form})


class CheckHallExistsView(View):

    def get(self, request, *args, **kwargs):

        hall_id = request.GET.get('hall_id')
        try:
            hall = Hall.objects.get(hall_id=hall_id)
            exists = True
        except Hall.DoesNotExist:
            exists = False
        messages.MessageFailure(request, f'Hall {hall_id} already exist.')
        return JsonResponse({'exists': exists})


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AdminHostelListView(View):
    template_name = 'hostelmanagement/admin_hostel_list.html'

    def get(self, request, *args, **kwargs):
        halls = Hall.objects.all()
        # Create a list to store additional details
        hostel_details = []

        # Loop through each hall and fetch assignedCaretaker and assignedWarden
        for hall in halls:
            try:
                caretaker = HallCaretaker.objects.filter(hall=hall).first()
                warden = HallWarden.objects.filter(hall=hall).first()
            except HostelAllotment.DoesNotExist:
                assigned_caretaker = None
                assigned_warden = None

            hostel_detail = {
                'hall_id': hall.hall_id,
                'hall_name': hall.hall_name,
                'max_accomodation': hall.max_accomodation,
                'number_students': hall.number_students,
                'assigned_batch': hall.assigned_batch,
                'assigned_caretaker': caretaker.staff.id.user.username if caretaker else None,
                'assigned_warden': warden.faculty.id.user.username if warden else None,
            }

            hostel_details.append(hostel_detail)

        return render(request, self.template_name, {'hostel_details': hostel_details})


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class DeleteHostelView(View):
    def get(self, request, hall_id, *args, **kwargs):
        # Get the hall instance
        hall = get_object_or_404(Hall, hall_id=hall_id)

        # Delete related entries in other tables
        hostelallotments = HostelAllotment.objects.filter(hall=hall)
        hostelallotments.delete()

        # Delete the hall
        hall.delete()
        messages.success(request, f'Hall {hall_id} deleted successfully.')

        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


class HallIdView(APIView):
    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def get(self, request, *args, **kwargs):
        hall_id = HostelAllotment.objects.values('hall_id')
        return Response(hall_id, status=status.HTTP_200_OK)


@login_required(login_url=LOGIN_URL)
def logout_view(request):
    logout(request)
    return redirect("/")


# //! alloted_rooms
def alloted_rooms(request, hall_id):
    """
    This function returns the allotted rooms in a particular hall.

    @param:
      request - HttpRequest object containing metadata about the user request.
      hall_id - Hall ID for which the allotted rooms need to be retrieved.

    @variables:
      allotted_rooms - stores all the rooms allotted in the given hall.
    """
    # Query the hall by hall_id
    hall = Hall.objects.get(hall_id=hall_id)
    # Query all rooms allotted in the given hall
    allotted_rooms = HallRoom.objects.filter(hall=hall, room_occupied__gt=0)
    # Prepare a list of room details to be returned
    room_details = []
    for room in allotted_rooms:
        room_details.append({
            'hall': room.hall.hall_id,
            'room_no': room.room_no,
            'block_no': room.block_no,
            'room_cap': room.room_cap,
            'room_occupied': room.room_occupied
        })
    return JsonResponse(room_details, safe=False)


def alloted_rooms_main(request):
    """
    This function returns the allotted rooms in all halls.

    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      all_halls - stores all the halls.
      all_rooms - stores all the rooms allotted in all halls.
    """
    # Query all halls
    all_halls = Hall.objects.all()

    # Query all rooms allotted in all halls
    all_rooms = []
    for hall in all_halls:
        all_rooms.append(HallRoom.objects.filter(
            hall=hall, room_occupied__gt=0))

    # Prepare a list of room details to be returned
    room_details = []
    for rooms in all_rooms:
        for room in rooms:
            room_details.append({
                'hall': room.hall.hall_name,
                'room_no': room.room_no,
                'block_no': room.block_no,
                'room_cap': room.room_cap,
                'room_occupied': room.room_occupied
            })

    # Return the room_details as JSON response
    return render(request, 'hostelmanagement/alloted_rooms_main.html', {'allotted_rooms': room_details, 'halls': all_halls})


# //! all_staff
def all_staff(request, hall_id):
    """
    This function returns all staff information for a specific hall.

    @param:
      request - HttpRequest object containing metadata about the user request.
      hall_id - The ID of the hall for which staff information is requested.


    @variables:
      all_staff - stores all staff information for the specified hall.
    """

    # Query all staff information for the specified hall
    all_staff = StaffSchedule.objects.filter(hall_id=hall_id)

    # Prepare a list of staff details to be returned
    staff_details = []
    for staff in all_staff:
        staff_details.append({
            'type': staff.staff_type,
            'staff_id': staff.staff_id_id,
            'hall_id': staff.hall_id,
            'day': staff.day,
            'start_time': staff.start_time,
            'end_time': staff.end_time
        })

    # Return the staff_details as JSON response
    return JsonResponse(staff_details, safe=False)


# //! Edit Stuff schedule
class StaffScheduleView(APIView):
    """
    API endpoint for creating or editing staff schedules.
    """

    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def patch(self, request, staff_id):
        staff = get_object_or_404(Staff, pk=staff_id)
        staff_type = request.data.get('staff_type')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        day = request.data.get('day')


        if start_time and end_time and day and staff_type:
            # Check if staff schedule exists for the given day
            existing_schedule = StaffSchedule.objects.filter(
                staff_id=staff_id).first()
            if existing_schedule:
                existing_schedule.start_time = start_time
                existing_schedule.end_time = end_time
                existing_schedule.day = day
                existing_schedule.staff_type = staff_type
                existing_schedule.save()
                return Response({"message": "Staff schedule updated successfully."}, status=status.HTTP_200_OK)
            else:
                # If staff schedule doesn't exist for the given day, return 404
                return Response({"error": "Staff schedule does not exist for the given day."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"error": "Please provide start_time, end_time, and day."}, status=status.HTTP_400_BAD_REQUEST)


# //! Hostel Inventory

@login_required
def get_inventory_form(request):
    user_id = request.user
    # print("user_id",user_id)
    staff = user_id.extrainfo.id
    # print("staff",staff)

    # Check if the user is present in the HallCaretaker table
    if HallCaretaker.objects.filter(staff_id=staff).exists():
        # If the user is a caretaker, allow access
        halls = Hall.objects.all()
        return render(request, 'hostelmanagement/inventory_form.html', {'halls': halls})
    else:
        # If the user is not a caretaker, redirect to the login page
        # return redirect('login')  # Adjust 'login' to your login URL name
        return HttpResponse(f'<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


@login_required
def edit_inventory(request, inventory_id):
    # Retrieve hostel inventory object
    inventory = get_object_or_404(HostelInventory, pk=inventory_id)

    # Check if the user is a caretaker
    user_id = request.user
    staff_id = user_id.extrainfo.id

    if HallCaretaker.objects.filter(staff_id=staff_id).exists():
        halls = Hall.objects.all()

        # Prepare inventory data for rendering
        inventory_data = {
            'inventory_id': inventory.inventory_id,
            'hall_id': inventory.hall_id,
            'inventory_name': inventory.inventory_name,
            'cost': str(inventory.cost),  # Convert DecimalField to string
            'quantity': inventory.quantity,
        }

        # Render the inventory update form with inventory data
        return render(request, 'hostelmanagement/inventory_update_form.html', {'inventory': inventory_data, 'halls': halls})
    else:
        # If the user is not a caretaker, show a message and redirect
        return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


class HostelInventoryUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, inventory_id):
        user_id = request.user
        staff_id = user_id.extrainfo.id

        if not HallCaretaker.objects.filter(staff_id=staff_id).exists():
            return Response({'error': 'You are not authorized to update this hostel inventory'}, status=status.HTTP_401_UNAUTHORIZED)

        hall_id = request.data.get('hall_id')
        inventory_name = request.data.get('inventory_name')
        cost = request.data.get('cost')
        quantity = request.data.get('quantity')

        # Validate required fields
        if not all([hall_id, inventory_name, cost, quantity]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve hostel inventory object
        hostel_inventory = get_object_or_404(HostelInventory, pk=inventory_id)

        # Update hostel inventory object
        hostel_inventory.hall_id = hall_id
        hostel_inventory.inventory_name = inventory_name
        hostel_inventory.cost = cost
        hostel_inventory.quantity = quantity
        hostel_inventory.save()

        # Return success response
        return Response({'message': 'Hostel inventory updated successfully'}, status=status.HTTP_200_OK)


class HostelInventoryView(APIView):
    """
    API endpoint for CRUD operations on hostel inventory.
    """
    # permission_classes = [IsAuthenticated]

    # authentication_classes = []  # Allow public access for testing
    # permission_classes = []  # Allow any user to access the view

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, hall_id):
        user_id = request.user
        staff_id = user_id.extrainfo.id

        if not HallCaretaker.objects.filter(staff_id=staff_id).exists():
            return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')

        # Retrieve hostel inventory objects for the given hall ID
        inventories = HostelInventory.objects.filter(hall_id=hall_id)

        # Get all hall IDs
        halls = Hall.objects.all()

        # Serialize inventory data
        inventory_data = []
        for inventory in inventories:
            inventory_data.append({
                'inventory_id': inventory.inventory_id,
                'hall_id': inventory.hall_id,
                'inventory_name': inventory.inventory_name,
                'cost': str(inventory.cost),  # Convert DecimalField to string
                'quantity': inventory.quantity,
            })

        inventory_data.sort(key=lambda x: x['inventory_id'])

        # Return inventory data as JSON response
        return render(request, 'hostelmanagement/inventory_list.html', {'halls': halls, 'inventories': inventory_data})

    def post(self, request):
        user_id = request.user
        staff_id = user_id.extrainfo.id

        if not HallCaretaker.objects.filter(staff_id=staff_id).exists():
            return Response({'error': 'You are not authorized to create a new hostel inventory'}, status=status.HTTP_401_UNAUTHORIZED)

        # Extract data from request
        hall_id = request.data.get('hall_id')
        inventory_name = request.data.get('inventory_name')
        cost = request.data.get('cost')
        quantity = request.data.get('quantity')

        # Validate required fields
        if not all([hall_id, inventory_name, cost, quantity]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create hostel inventory object
        try:
            hostel_inventory = HostelInventory.objects.create(
                hall_id=hall_id,
                inventory_name=inventory_name,
                cost=cost,
                quantity=quantity
            )
            return Response({'message': 'Hostel inventory created successfully', 'hall_id': hall_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, inventory_id):
        user_id = request.user
        staff_id = user_id.extrainfo.id

        if not HallCaretaker.objects.filter(staff_id=staff_id).exists():
            return Response({'error': 'You are not authorized to delete this hostel inventory'}, status=status.HTTP_401_UNAUTHORIZED)

        inventory = get_object_or_404(HostelInventory, pk=inventory_id)
        inventory.delete()
        return Response({'message': 'Hostel inventory deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


def update_allotment(request, pk):
    if request.method == 'POST':
        try:
            allotment = HostelAllottment.objects.get(pk=pk)
        except HostelAllottment.DoesNotExist:
            return JsonResponse({'error': 'HostelAllottment not found'}, status=404)

        try:
            allotment.assignedWarden = Faculty.objects.get(
                id=request.POST['warden_id'])
            allotment.assignedCaretaker = Staff.objects.get(
                id=request.POST['caretaker_id'])
            allotment.assignedBatch = request.POST.get(
                'student_batch', allotment.assignedBatch)
            allotment.save()
            return JsonResponse({'success': 'HostelAllottment updated successfully'})
        except (Faculty.DoesNotExist, Staff.DoesNotExist, IntegrityError):
            return JsonResponse({'error': 'Invalid data or integrity error'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def request_guest_room(request):
    """
    This function is used by the student to book a guest room.
    @param:
      request - HttpRequest object containing metadata about the user request.
    """
    if request.method == "POST":
        form = GuestRoomBookingForm(request.POST)

        if form.is_valid():
            # print("Inside valid")
            hall = form.cleaned_data['hall']
            guest_name = form.cleaned_data['guest_name']
            guest_phone = form.cleaned_data['guest_phone']
            guest_email = form.cleaned_data['guest_email']
            guest_address = form.cleaned_data['guest_address']
            rooms_required = form.cleaned_data['rooms_required']
            total_guest = form.cleaned_data['total_guest']
            purpose = form.cleaned_data['purpose']
            arrival_date = form.cleaned_data['arrival_date']
            arrival_time = form.cleaned_data['arrival_time']
            departure_date = form.cleaned_data['departure_date']
            departure_time = form.cleaned_data['departure_time']
            nationality = form.cleaned_data['nationality']
            room_type = form.cleaned_data['room_type']  # Add room type


            max_guests = {
                'single': 1,
                'double': 2,
                'triple': 3,
            }
            # Fetch available room count based on room type and hall
            available_rooms_count = GuestRoom.objects.filter(
                hall=hall, room_type=room_type, vacant=True
            ).count()
            
             # Check if there are enough available rooms
            if available_rooms_count < rooms_required:
                messages.error(request, "Not enough available rooms.")
                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
            
            # Check if the number of guests exceeds the capacity of selected rooms
            if total_guest > rooms_required * max_guests.get(room_type, 1):
                messages.error(request, "Number of guests exceeds the capacity of selected rooms.")
                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
            

            newBooking = GuestRoomBooking.objects.create(hall=hall, intender=request.user, guest_name=guest_name, guest_address=guest_address,
                                                         guest_phone=guest_phone, guest_email=guest_email, rooms_required=rooms_required, total_guest=total_guest, purpose=purpose,
                                                         arrival_date=arrival_date, arrival_time=arrival_time, departure_date=departure_date, departure_time=departure_time, nationality=nationality,room_type=room_type)
            newBooking.save()
            messages.success(request, "Room request submitted successfully!")

            
            # Get the caretaker for the selected hall
            hall_caretaker = HallCaretaker.objects.get(hall=hall)
            caretaker = hall_caretaker.staff.id.user
            # Send notification to caretaker
            hostel_notifications(sender=request.user, recipient=caretaker, type='guestRoom_request')

            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
        else:
            messages.error(request, "Something went wrong")
            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


@login_required
def update_guest_room(request):
    if request.method == "POST":
        if 'accept_request' in request.POST:
            status = request.POST['status']
            guest_room_request = GuestRoomBooking.objects.get(
                pk=request.POST['accept_request'])
            guest_room_instance = GuestRoom.objects.get(
                hall=guest_room_request.hall, room=request.POST['guest_room_id'])

            # Assign the guest room ID to guest_room_id field
            guest_room_request.guest_room_id = str(guest_room_instance.id)

            # Update the assigned guest room's occupancy details
            guest_room_instance.occupied_till = guest_room_request.departure_date
            guest_room_instance.vacant = False  # Mark the room as occupied
            guest_room_instance.save()

            # Update the occupied_till field of the room_booked
            room_booked = GuestRoom.objects.get(
                hall=guest_room_request.hall, room=request.POST['guest_room_id'])
            room_booked.occupied_till = guest_room_request.departure_date
            room_booked.save()

            # Save the guest room request after updating the fields
            guest_room_request.status = status
            guest_room_request.save()
            messages.success(request, "Request accepted successfully!")

            hostel_notifications(sender=request.user,recipient=guest_room_request.intender,type='guestRoom_accept')


        elif 'reject_request' in request.POST:
            guest_room_request = GuestRoomBooking.objects.get(
                pk=request.POST['reject_request'])
            guest_room_request.status = 'Rejected'
            guest_room_request.save()

            messages.success(request, "Request rejected successfully!")

            hostel_notifications(sender=request.user,recipient=guest_room_request.intender,type='guestRoom_reject')

        else:
            messages.error(request, "Invalid request!")
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def available_guestrooms_api(request):
    if request.method == 'GET':
        
        hall_id = request.GET.get('hall_id')
        room_type = request.GET.get('room_type')

        if hall_id and room_type:
            available_rooms_count = GuestRoom.objects.filter(hall_id=hall_id, room_type=room_type, vacant=True).count()
            return JsonResponse({'available_rooms_count': available_rooms_count})

    return JsonResponse({'error': 'Invalid request'}, status=400)


# //Caretaker can approve or reject leave applied by the student
@csrf_exempt
def update_leave_status(request):
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        status = request.POST.get('status')
        try:
            leave = HostelLeave.objects.get(id=leave_id)
            leave.status = status
            leave.remark = request.POST.get('remark')
            leave.save()

            # Send notification to the student
            sender = request.user  # Assuming request.user is the caretaker
            
            student_id = leave.roll_num  # Assuming student is a foreign key field in HostelLeave model
            recipient = User.objects.get(username=student_id)
            type = "leave_accept" if status == "Approved" else "leave_reject"
            hostel_notifications(sender, recipient, type)

            return JsonResponse({'status': status,'remarks':leave.remark,'message': 'Leave status updated successfully.'})
        except HostelLeave.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Leave not found.'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)


# //! Manage Fine
# //! Add Fine Functionality


@login_required
def show_fine_edit_form(request,fine_id):
    user_id = request.user
    staff = user_id.extrainfo.id
    caretaker = HallCaretaker.objects.get(staff_id=staff)
    hall_id = caretaker.hall_id

    fine = HostelFine.objects.filter(fine_id=fine_id)



    return render(request, 'hostelmanagement/impose_fine_edit.html', {'fines': fine[0]})

@login_required
def update_student_fine(request,fine_id):
    if request.method == 'POST':
        fine = HostelFine.objects.get(fine_id=fine_id)
        print("------------------------------------------------")
        print(request.POST)
        fine.amount = request.POST.get('amount')
        fine.status = request.POST.get('status')
        fine.reason = request.POST.get('reason')
        fine.save()
        
        return HttpResponse({'message': 'Fine has edited successfully'}, status=status.HTTP_200_OK)


@login_required
def impose_fine_view(request):
    user_id = request.user
    staff = user_id.extrainfo.id
    students = Student.objects.all()

    if HallCaretaker.objects.filter(staff_id=staff).exists():
        return render(request, 'hostelmanagement/impose_fine.html', {'students': students})

    return HttpResponse(f'<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


class HostelFineView(APIView):
    """
    API endpoint for imposing fines on students.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        # Check if the user is a caretaker
        user_id = request.user
        staff = user_id.extrainfo.id

        try:
            caretaker = HallCaretaker.objects.get(staff_id=staff)
        except HallCaretaker.DoesNotExist:
            return HttpResponse(f'<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')

        hall_id = caretaker.hall_id

        # Extract data from the request
        student_id = request.data.get('student_id')
        student_name = request.data.get('student_fine_name')
        amount = request.data.get('amount')
        reason = request.data.get('reason')

        # Validate the data
        if not all([student_id, student_name, amount, reason]):
            return HttpResponse({'error': 'Incomplete data provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the HostelFine object
        try:
            fine = HostelFine.objects.create(
                student_id=student_id,
                student_name=student_name,
                amount=amount,
                reason=reason,
                hall_id=hall_id
            )
            # Sending notification to the student about the imposed fine
           
            
            
            recipient = User.objects.get(username=student_id)
            
            sender = request.user
            
            type = "fine_imposed"
            hostel_notifications(sender, recipient, type)

            return HttpResponse({'message': 'Fine imposed successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def get_student_name(request, username):
    try:
        user = User.objects.get(username=username)
        full_name = f"{user.first_name} {user.last_name}" if user.first_name or user.last_name else ""
        return JsonResponse({"name": full_name})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


@login_required
def hostel_fine_list(request):
    user_id = request.user
    staff = user_id.extrainfo.id
    caretaker = HallCaretaker.objects.get(staff_id=staff)
    hall_id = caretaker.hall_id
    hostel_fines = HostelFine.objects.filter(
        hall_id=hall_id).order_by('fine_id')

    if HallCaretaker.objects.filter(staff_id=staff).exists():
        return render(request, 'hostelmanagement/hostel_fine_list.html', {'hostel_fines': hostel_fines})

    return HttpResponse(f'<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/"</script>')


@login_required
def student_fine_details(request):
    user_id = request.user.username
    # print(user_id)
    # staff=user_id.extrainfo.id

    # Check if the user_id exists in the Student table
    # if HallCaretaker.objects.filter(staff_id=staff).exists():
    #     return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/";</script>')

    if not Student.objects.filter(id_id=user_id).exists():
        return HttpResponse('<script>alert("You are not authorized to access this page"); window.location.href = "/hostelmanagement/";</script>')

    # # Check if the user_id exists in the HostelFine table
    if not HostelFine.objects.filter(student_id=user_id).exists():
        return HttpResponse('<script>alert("You have no fines recorded"); window.location.href = "/hostelmanagement/";</script>')

    # # Retrieve the fines associated with the current student
    student_fines = HostelFine.objects.filter(student_id=user_id)

    return render(request, 'hostelmanagement/student_fine_details.html', {'student_fines': student_fines})

    # return JsonResponse({'message': 'Nice'}, status=status.HTTP_200_OK)


class HostelFineUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, fine_id):
        user_id = request.user
        staff = user_id.extrainfo.id

        data = request.data
        fine_idd = data.get('fine_id')
        status_ = data.get('status')
        # print("fine_idd",fine_idd)
        # print("status_",status_)

        try:
            caretaker = HallCaretaker.objects.get(staff_id=staff)
        except HallCaretaker.DoesNotExist:
            return Response({'error': 'You are not authorized to access this page'}, status=status.HTTP_403_FORBIDDEN)

        hall_id = caretaker.hall_id

        # Convert fine_id to integer
        fine_id = int(fine_id)

        # Get hostel fine object
        try:
            hostel_fine = HostelFine.objects.get(
                hall_id=hall_id, fine_id=fine_id)
        except HostelFine.DoesNotExist:
            raise NotFound(detail="Hostel fine not found")

        # Validate required fields
        if status_ not in ['Pending', 'Paid']:
            return Response({'error': 'Invalid status value'}, status=status.HTTP_400_BAD_REQUEST)

        # # Update status of the hostel fine
        hostel_fine.status = status_
        hostel_fine.save()

        # Return success response
        return Response({'message': 'Hostel fine status updated successfully!'}, status=status.HTTP_200_OK)

    def delete(self, request, fine_id):
        user_id = request.user
        staff = user_id.extrainfo.id

        try:
            caretaker = HallCaretaker.objects.get(staff_id=staff)
        except HallCaretaker.DoesNotExist:
            return Response({'error': 'You are not authorized to access this page'}, status=status.HTTP_403_FORBIDDEN)

        hall_id = caretaker.hall_id

        # Convert fine_id to integer
        fine_id = int(fine_id)

        # Get hostel fine object
        try:
            hostel_fine = HostelFine.objects.get(
                hall_id=hall_id, fine_id=fine_id)
            hostel_fine.delete()
        except HostelFine.DoesNotExist:
            raise NotFound(detail="Hostel fine not found")

        return Response({'message': 'Fine deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)




class EditStudentView(View):
    template_name = 'hostelmanagement/edit_student.html'
    
    def get(self, request, student_id):
        student = Student.objects.get(id=student_id)
        
        context = {'student': student}
        return render(request, self.template_name, context)

    def post(self, request, student_id):
        student = Student.objects.get(id=student_id)
       
        # Update student details
        student.id.user.first_name = request.POST.get('first_name')
        student.id.user.last_name = request.POST.get('last_name')
        student.programme = request.POST.get('programme')
        student.batch = request.POST.get('batch')
        student.hall_no = request.POST.get('hall_number')
        student.room_no = request.POST.get('room_number')
        student.specialization = request.POST.get('specialization')
        
        student.save()

        # Update phone number and address from ExtraInfo model
        student.id.phone_no = request.POST.get('phone_number')
        student.id.address = request.POST.get('address')
        student.id.save()
        student.save()
        messages.success(request, 'Student details updated successfully.')
        return redirect("hostelmanagement:hostel_view")
    
class RemoveStudentView(View):
    def post(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            student.hall_no = 0
            student.save()
            messages.success(request, 'Student removed successfully.')
            return redirect("hostelmanagement:hostel_view")
            return JsonResponse({'status': 'success', 'message': 'Student removed successfully'})
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def dispatch(self, request, *args, **kwargs):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Method Not Allowed'}, status=405)
        return super().dispatch(request, *args, **kwargs)
    

