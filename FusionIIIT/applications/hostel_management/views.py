from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, DepartmentInfo)
from applications.academic_information.models import Student
from applications.academic_information.models import *
from django.http import HttpResponseRedirect
from .models import *
import xlrd
from .forms import HostelNoticeBoardForm


@login_required
def hostel_view(request):
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
    all_notice = HostelNoticeBoard.objects.all().order_by("-id")                    

    context = {
        'hall_1_student': hall_1_student,
        'hall_3_student': hall_3_student,
        'hall_4_student': hall_4_student,
        'all_hall': all_hall,
        'all_notice': all_notice
    }

    return render(request, 'hostelmanagement/hostel.html', context)


@login_required
def add_hall_room(request):
    """
    This function is used to upload the alloted hall room excel sheets by the respective hall caretakers.
    This function will update the hall_no and room_no of Student table.
    """
    if request.method == "POST":
        files = request.FILES['hallroom']
        excel = xlrd.open_workbook(file_contents=files.read())
        user_id = request.user.extrainfo.id
    
        if str(excel.sheets()[0].cell(2,9).value) == 'Hall-4':
            if str(HallCaretaker.objects.get(staff__id=user_id).hall) == 'hall4':
                hall_4_allotment = []
                for sheet in excel.sheets():
                    for row in range(1, sheet.nrows):
                        roll_no = int(sheet.cell(row,1).value)
                        name = str(sheet.cell(row,2).value)
                        program = str(sheet.cell(row,4).value)
                        room_no = str(sheet.cell(row,7).value)
                        block = str(sheet.cell(row,8).value)
                        hall_4_allotment.append([roll_no, name, program, room_no, block])

                for st in hall_4_allotment:
                    Student.objects.filter(id__id=st[0]).update(hall_no=4, room_no=st[3])

                # hall_4_student = Student.objects.filter(hall_no=4)

                # context = {
                #     'hall_4_student': hall_4_student
                # }

                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


        if str(excel.sheets()[0].cell(2,9).value) == 'Hall-3':
            if str(HallCaretaker.objects.get(staff__id=user_id).hall) == 'hall3':
                hall_3_allotment = []
                for sheet in excel.sheets():
                    for row in range(1, sheet.nrows):
                        roll_no = int(sheet.cell(row,1).value)
                        name = str(sheet.cell(row,2).value)
                        program = str(sheet.cell(row,4).value)
                        room_no = str(sheet.cell(row,7).value)
                        block = str(sheet.cell(row,8).value)
                        hall_3_allotment.append([roll_no, name, program, room_no, block])
                

                for st in hall_3_allotment:
                    Student.objects.filter(id__id=st[0]).update(hall_no=3, room_no=st[3])


                # hall_3_student = Student.objects.filter(hall_no=3)

                # context = {
                #     'hall_3_student': hall_3_student
                # }

                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))


        if str(excel.sheets()[0].cell(2,9).value)[:6] == 'Hall-1':
            if str(HallCaretaker.objects.get(staff__id=user_id).hall) == 'hall1':
                hall_1_allotment = []
                for sheet in excel.sheets():
                    for row in range(1, sheet.nrows):
                        roll_no = int(sheet.cell(row,1).value)
                        name = str(sheet.cell(row,2).value)
                        program = str(sheet.cell(row,4).value)
                        room_no = str(sheet.cell(row,7).value)
                        block = str(sheet.cell(row,8).value)
                        hall_1_allotment.append([roll_no, name, program, room_no, block])

                for st in hall_1_allotment:
                    Student.objects.filter(id__id=st[0]).update(hall_no=1, room_no=st[3])


                # hall_1_student = Student.objects.filter(hall_no=1)

                # context = {
                #     'hall_1_student': hall_1_student
                # }

                return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))

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
