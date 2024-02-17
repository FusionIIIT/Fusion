from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
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
from .forms import HostelNoticeBoardForm
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

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

from django.core.serializers import serialize

# //! My change
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db import IntegrityError


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

    Staff_obj = Staff.objects.all().select_related('id__user')
    hall1 = Hall.objects.get(hall_id='hall1')
    hall3 = Hall.objects.get(hall_id='hall3')
    hall4 = Hall.objects.get(hall_id='hall4')
    hall1_staff = StaffSchedule.objects.filter(hall=hall1)
    hall3_staff = StaffSchedule.objects.filter(hall=hall3)
    hall4_staff = StaffSchedule.objects.filter(hall=hall4)
    hall_caretakers = HallCaretaker.objects.all().select_related()
    hall_wardens = HallWarden.objects.all().select_related()

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
                    print('Room  unavailable!')
                    messages.error(request, 'Room  unavailable!')
                    break
            else:
                is_valid = False
                print("Wrong Credentials entered!")
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


@login_required
def generate_worker_report(request):
    """
    This function is used to read uploaded worker report spreadsheet(.xls) and generate WorkerReport instance and save it in the database.
    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      files - stores uploaded worker report file 
      excel - stores the opened spreadsheet file raedy for data extraction.
      user_id - stores user id of the current user.
      sheet - stores a sheet from the uploaded spreadsheet.
    """
    if request.method == "POST":
        try:
            files = request.FILES['upload_report']
            excel = xlrd.open_workbook(file_contents=files.read())
            user_id = request.user.extrainfo.id
            if str(excel.sheets()[0].cell(0, 0).value)[:5].lower() == str(HallCaretaker.objects.get(staff__id=user_id).hall):
                for sheet in excel.sheets():
                    save_worker_report_sheet(excel, sheet, user_id)
                    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

            return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))
        except:
            messages.error(
                request, "Please upload a file in valid format before submitting")
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
        todays_date = date.today()
        current_year = todays_date.year
        current_month = todays_date.month

        template = get_template('hostelmanagement/view_report.html')

        hall_caretakers = HallCaretaker.objects.all()
        get_hall = ""
        get_hall = get_caretaker_hall(hall_caretakers, request.user)
        print(get_hall)
        if months < current_month:
            worker_report = WorkerReport.objects.filter(
                hall=get_hall, month__gte=current_month-months, year=current_year)
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
    notices =  all().values('id', 'hall', 'posted_by', 'head_line', 'content', 'description')
    data = list(notices)
    return JsonResponse(data, safe=False)




def all_leave_data(request):
    all_leave = HostelLeave.objects.all()
    return render(request, 'hostelmanagement/all_leave_data.html', {'all_leave': all_leave})


class create_hostel_leave(APIView):
    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def get(self, request):
        return render(request, 'hostelmanagement/create_leave.html')
    
    def post(self, request):
    
        data = request.data
        student_name = data.get('student_name')
        roll_num = data.get('roll_num')
        reason = data.get('reason')
        start_date = data.get('start_date', timezone.now())
        end_date = data.get('end_date')

        # Create HostelLeave object and save to the database
        leave = HostelLeave.objects.create(
            student_name=student_name,
            roll_num=roll_num,
            reason=reason,
            start_date=start_date,
            end_date=end_date
        )

        return JsonResponse({'message': 'HostelLeave created successfully'}, status=status.HTTP_201_CREATED)

def create_leave(request):
    return render(request, 'hostelmanagement/create_leave.html')

# hostel complaints


def hostel_complaint_list(request):
    complaints = HostelComplaint.objects.all()
    return render(request, 'hostelmanagement/hostel_complaint.html', {'complaints': complaints})


class PostComplaint(APIView):
    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def get(self, request):
        return render(request, 'hostelmanagement/post_complaint_form.html')

    def post(self, request):
        hall_name = request.data.get('hall_name')
        student_name = request.data.get('student_name')
        roll_number = request.data.get('roll_number')
        description = request.data.get('description')
        contact_number = request.data.get('contact_number')

        complaint = HostelComplaint.objects.create(
            hall_name=hall_name,
            student_name=student_name,
            roll_number=roll_number,
            description=description,
            contact_number=contact_number
        )
        
        # Use JavaScript to display a pop-up message after submission
        return HttpResponse('<script>alert("Complaint submitted successfully"); window.location.href = "/hostelmanagement";</script>')


# userComplaint user can see complaints registered by him



class UserComplaints(APIView):
    authentication_classes = []  # Allow public access for testing
    permission_classes = []  # Allow any user to access the view

    def get(self, request, roll_number):
        # Filter complaints by the roll number, case-insensitive
        user_complaints = HostelComplaint.objects.filter(Q(roll_number__iexact=roll_number))
        
        # Render a template displaying the user's complaints
        return render(request, 'hostelmanagement/user_complaints.html', {'complaints': user_complaints})


# /// login  required



# @login_required
# def hostel_complaint_list(request):
#     complaints = HostelComplaint.objects.all()
#     return render(request, 'hostelmanagement/hostel_complaint.html', {'complaints': complaints})


# @login_required
# def hostel_complaint_list(request):
   
#     # Get the currently logged-in student
#     student = request.user
    

#     # Filter complaints to show only those posted by the student
#     complaints = HostelComplaint.objects.filter(roll_number=request.data.get("roll_number"))
    

#     return render(request, 'hostelmanagement/hostel_complaint.html', {'complaints': complaints})
    


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class AssignCaretakerView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    template_name = 'hostelmanagement/assign_caretaker.html' 


    def get(self, request, *args, **kwargs):
        hall = Hall.objects.all()
        caretaker_usernames=Staff.objects.all()
        return render(request, self.template_name , {'halls': hall,'caretaker_usernames':caretaker_usernames})

    def post(self, request, *args, **kwargs):
        hall_id = request.data.get('hall_id')
        caretaker_username = request.data.get('caretaker_username')

        try:
            hall = Hall.objects.get(hall_id=hall_id)
            caretaker_staff = Staff.objects.get(id__user__username=caretaker_username)

            # Delete any previous assignments of the caretaker in HallCaretaker table
            HallCaretaker.objects.filter(staff=caretaker_staff).delete()

            # Delete any previous assignments of the caretaker in RoomAllotment table
            HostelAllotment.objects.filter(assignedCaretaker=caretaker_staff).delete()

            # Delete any previously assigned caretaker to the same hall
            HallCaretaker.objects.filter(hall=hall).delete()

            # Assign the new caretaker to the hall in HallCaretaker table
            hall_caretaker = HallCaretaker.objects.create(hall=hall, staff=caretaker_staff)

            # Update the assigned caretaker in Hostelallottment table
            hostel_allotments = HostelAllotment.objects.filter(hall=hall)
            for hostel_allotment in hostel_allotments:
                hostel_allotment.assignedCaretaker = caretaker_staff
                hostel_allotment.save()

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
    template_name = 'hostelmanagement/assign_batch.html'  # Assuming the HTML file is directly in the 'templates' folder
    
    def get(self, request, *args, **kwargs):
        hall = Hall.objects.all()
        return render(request, self.template_name , {'halls': hall})

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            hall_id = data.get('hall_id')

            hall = Hall.objects.get(hall_id=hall_id)
            hall.assigned_batch = data.get('batch')
            hall.save()

            # Update the assignedBatch field in HostelAllotment table for the corresponding hall
            room_allotments = HostelAllotment.objects.filter(hall=hall)
            for room_allotment in room_allotments:
                room_allotment.assignedBatch = hall.assigned_batch
                room_allotment.save()

            return JsonResponse({'status': 'success', 'message': 'Batch assigned successfully'}, status=200)
            
        except Hall.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': f'Hall with ID {hall_id} not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    def test_func(self):
        # Check if the user is a superuser
        return self.request.user.is_superuser
    
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
        caretaker_usernames=Staff.objects.all()
        return render(request, self.template_name , {'halls': hall,'caretaker_usernames':caretaker_usernames})

    def post(self, request, *args, **kwargs):
        hall_id = request.data.get('hall_id')
        caretaker_username = request.data.get('caretaker_username')

        try:
            hall = Hall.objects.get(hall_id=hall_id)
            caretaker_staff = Staff.objects.get(id__user__username=caretaker_username)

            # Delete any previous assignments of the caretaker in HallCaretaker table
            HallCaretaker.objects.filter(staff=caretaker_staff).delete()

            # Delete any previous assignments of the caretaker in RoomAllotment table
            HostelAllotment.objects.filter(assignedCaretaker=caretaker_staff).delete()

            # Delete any previously assigned caretaker to the same hall
            HallCaretaker.objects.filter(hall=hall).delete()

            # Assign the new caretaker to the hall in HallCaretaker table
            hall_caretaker = HallCaretaker.objects.create(hall=hall, staff=caretaker_staff)

            # Update the assigned caretaker in Hostelallottment table
            hostel_allotments = HostelAllotment.objects.filter(hall=hall)
            for hostel_allotment in hostel_allotments:
                hostel_allotment.assignedCaretaker = caretaker_staff
                hostel_allotment.save()

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
    template_name = 'hostelmanagement/assign_batch.html'  # Assuming the HTML file is directly in the 'templates' folder
    
    def get(self, request, *args, **kwargs):
        hall = Hall.objects.all()
        return render(request, self.template_name , {'halls': hall})

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            hall_id = data.get('hall_id')

            hall = Hall.objects.get(hall_id=hall_id)
            hall.assigned_batch = data.get('batch')
            hall.save()

            # Update the assignedBatch field in HostelAllotment table for the corresponding hall
            room_allotments = HostelAllotment.objects.filter(hall=hall)
            for room_allotment in room_allotments:
                room_allotment.assignedBatch = hall.assigned_batch
                room_allotment.save()

            return JsonResponse({'status': 'success', 'message': 'Batch assigned successfully'}, status=200)
            
        except Hall.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': f'Hall with ID {hall_id} not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    def test_func(self):
        # Check if the user is a superuser
        return self.request.user.is_superuser
    
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
def all_staff(request):
    """
    This function returns all staff information.

    @param:
      request - HttpRequest object containing metadata about the user request.

    @variables:
      all_staff - stores all staff information.
    """
    # Query all staff information
    all_staff = StaffSchedule.objects.all()

    print(all_staff)

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

