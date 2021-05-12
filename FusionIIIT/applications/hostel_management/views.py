from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, DepartmentInfo)
from applications.academic_information.models import Student
from applications.academic_information.models import *
from django.db.models import Q
import datetime
from datetime import time, datetime
from time import mktime, time,localtime
from .models import *
import xlrd
from .forms import HostelNoticeBoardForm
import re
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.generic import View


@login_required
def hostel_view(request, context={}):
    """
    This is a general function which is used for all the views functions.
    This function renders all the contexts required in templates.
    @variables:
            hall_1_student - stores all hall 1 students
            hall_3_student - stores all hall 3 students
            hall_4_student - stores all hall 4 students
            all_hall - stores all the hall of residence
            all_notice - stores all notices of hostels (latest first)
    """
    hall_1_student = Student.objects.filter(hall_no=1)[:10]
    hall_3_student = Student.objects.filter(hall_no=3)[:10]
    hall_4_student = Student.objects.filter(hall_no=4)[:10]
    all_hall = Hall.objects.all()
    # halls_student = {}
    # for hall in all_hall:
    #     halls_student[hall.hall_id] = Student.objects.filter(hall_no=int(hall.hall_id[4]))[:10]

    all_notice = HostelNoticeBoard.objects.all().order_by("-id")

    Staff_obj = Staff.objects.all()
    hall1 = Hall.objects.get(hall_id='hall1')
    hall3=Hall.objects.get(hall_id='hall3')
    hall4=Hall.objects.get(hall_id='hall4')
    hall1_staff = StaffSchedule.objects.filter(hall=hall1)
    hall3_staff = StaffSchedule.objects.filter(hall=hall3)
    hall4_staff = StaffSchedule.objects.filter(hall=hall4)
    hall_caretaker = HallCaretaker.objects.all()

    hall_student=""
    get_hall=""
    current_hall=""
    get_avail_room=[]
    for i in hall_caretaker:
        if i.staff.id.user==request.user:
            get_hall=i.hall
            break
        
    if get_hall:
        total_rooms=HallRoom.objects.filter(hall=get_hall)
        for i in total_rooms:
            if(i.room_cap>i.room_occupied):
                get_avail_room.append(i)

        get_hall_num=re.findall('[0-9]+',str(get_hall.hall_id))
        hall_student=Student.objects.filter(hall_no=int(str(get_hall_num[0])))
        current_hall='hall'+str(get_hall_num[0])


    hall_caretaker_user=[]
    for h_c in hall_caretaker:
        hall_caretaker_user.append(h_c.staff.id.user)      

    worker_report = WorkerReport.objects.all()

    context = {
        'hall_1_student': hall_1_student,
        'hall_3_student': hall_3_student,
        'hall_4_student': hall_4_student,
        'all_hall': all_hall,
        'all_notice': all_notice,
        'staff':Staff_obj,
        'hall1_staff' : hall1_staff,
        'hall3_staff' : hall3_staff,
        'hall4_staff' : hall4_staff,
        'hall_caretaker' : hall_caretaker_user,
        'room_avail' : get_avail_room,
        'hall_student':hall_student,
        'worker_report': worker_report,
        # 'halls_student': halls_student,
        'current_hall' : current_hall,
        **context
    }

    return render(request, 'hostelmanagement/hostel.html', context)



def staff_edit_schedule(request):
    if request.method == 'POST':
        start_time= datetime.datetime.strptime(request.POST["start_time"],'%H:%M').time()
        end_time= datetime.datetime.strptime(request.POST["end_time"],'%H:%M').time()
        # hall_no = request.POST["hall_no"]
        staff_name=request.POST["Staff_name"]
        staff_type=request.POST["staff_type"]
        day=request.POST["day"]

        staff=Staff.objects.get(pk=staff_name)
        try:
            hall_staff=StaffSchedule.objects.get(staff_id=staff)
            hall_staff.day=day
            hall_staff.start_time=start_time
            hall_staff.end_time=end_time
            hall_staff.staff_type=staff_type
            hall_staff.save()
        except:
            # hall=Hall.objects.get(hall_id=hall_no)
            hall_caretaker = HallCaretaker.objects.all()
            get_hall=""
            for i in hall_caretaker:
                if i.staff.id.user==request.user:
                    get_hall=i.hall
                    break

            StaffSchedule(hall=get_hall,staff_id=staff,day=day,staff_type=staff_type,start_time=start_time,end_time=end_time).save()

    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))



def staff_delete_schedule(request):
    if request.method == 'POST':
        staff_name=request.POST["dlt_schedule"]
        staff=Staff.objects.get(pk=staff_name)
        staff_schedule=StaffSchedule.objects.get(staff_id=staff)
        staff_schedule.delete()
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


@login_required
def notice_board(request):
    """
    This function is used to create a form to show the notice on the Notice Board.
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
                
        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def edit_student_room(request):
    if request.method == "POST":
        roll_no = request.POST["roll_no"]
        room_no = request.POST["room_no"]
        batch=str(roll_no[0])+str(roll_no[1])+str(roll_no[2])+str(roll_no[3])
        students = Student.objects.filter(batch=int(batch))
        for i in students:
            if str(i.id.user)==str(roll_no):
                room = re.findall('[0-9]+',str(i.room_no))
                room_num=str(room[0])
                block = str(i.room_no[0])
                hall=Hall.objects.get(hall_id="hall"+str(i.hall_no))
                Room=HallRoom.objects.get(hall=hall,block_no=block,room_no=room_num)
                Room.room_occupied=Room.room_occupied-1
                Room.save()
               
                block=str(room_no[0])
                room = re.findall('[0-9]+',str(room_no))
                Room=HallRoom.objects.get(hall=hall,block_no=block,room_no=str(room[0]))
                i.room_no=str(block)+"-"+str(room[0])
                i.save()
                Room.room_occupied=Room.room_occupied+1
                Room.save()

        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


@login_required
def generate_worker_report(request):
    if request.method == "POST":
        files = request.FILES['upload_report']
        excel = xlrd.open_workbook(file_contents=files.read())
        user_id = request.user.extrainfo.id
        if str(excel.sheets()[0].cell(0,0).value)[:5].lower() == str(HallCaretaker.objects.get(staff__id=user_id).hall):
            hall_3_workers = []
            for sheet in excel.sheets():
                month = excel.sheet_names()[0][:2]
                year = excel.sheet_names()[0][3:]
                for row in range(1, sheet.nrows):
                    worker_id = str(sheet.cell(row,0).value)
                    worker_name = str(sheet.cell(row,1).value)
                    present = 0
                    for col in range(2, sheet.ncols):
                        if int(sheet.cell(row,col).value) == 1:
                            present += 1
                    working_days = sheet.ncols - 2
                    absent = sheet.ncols - present - 2
                    hall_no = HallCaretaker.objects.get(staff__id=user_id).hall
                    new_report = WorkerReport.objects.create(worker_id=worker_id, hall=hall_no, worker_name=worker_name, month=month, year=year, absent=absent, total_day=working_days, remark="none")
                    new_report.save()
                    hall_3_workers.append([worker_id, worker_name, present, absent])

                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

        return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        template = get_template('hostelmanagement/view_report.html')
        worker_report = WorkerReport.objects.all()
        worker = {
            'worker_report' : worker_report
        }
        html = template.render(worker)
        pdf = render_to_pdf('hostelmanagement/view_report.html', worker)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Invoice_%s.pdf" %("12341231")
            content = "inline; filename='%s'" %(filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" %(filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")

