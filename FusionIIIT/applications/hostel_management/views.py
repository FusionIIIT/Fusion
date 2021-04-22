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
    all_notice = HostelNoticeBoard.objects.all().order_by("-id")

    Staff_obj = Staff.objects.all()
    hall1 = Hall.objects.get(hall_id='hall1')
    hall3=Hall.objects.get(hall_id='hall3')
    hall4=Hall.objects.get(hall_id='hall4')
    hall1_staff = StaffSchedule.objects.filter(hall=hall1)
    hall3_staff = StaffSchedule.objects.filter(hall=hall3)
    hall4_staff = StaffSchedule.objects.filter(hall=hall4)
    hall_caretaker = HallCaretaker.objects.all()
    hall_caretaker_user=[]
    for h_c in hall_caretaker:
        hall_caretaker_user.append(h_c.staff.id.user)                    

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
        **context
    }

    return render(request, 'hostelmanagement/hostel.html', context)



def staff_edit_schedule(request):
    if request.method == 'POST':
        start_time= datetime.datetime.strptime(request.POST["start_time"],'%H:%M').time()
        end_time= datetime.datetime.strptime(request.POST["end_time"],'%H:%M').time()
        hall_no = request.POST["hall_no"]
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
            hall=Hall.objects.get(hall_id=hall_no)
            StaffSchedule(hall=hall,staff_id=staff,day=day,staff_type=staff_type,start_time=start_time,end_time=end_time).save()

    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))



def staff_delete_schedule(request):
    if request.method == 'POST':
        staff_name=request.POST["dlt_schedule"]
        staff=Staff.objects.get(pk=staff_name)
        staff_schedule=StaffSchedule.objects.get(staff_id=staff)
        staff_schedule.delete()
    return HttpResponseRedirect(reverse("hostelmanagement:hostel_view"))



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







#--------------------Booking Guest Room-----------------------#



def guest_room_book(request):
    return render(request, "hostelmanagement/guestroom_booking.html")


@login_required(login_url='/accounts/login/')
def hostel_guest_room(request):

    # intenders
    intenders = User.objects.all()
    user = request.user
    # intender = request.user.holds_designations.filter(designation__name = 'Intender').exists()
    # vhcaretaker = request.user.holds_designations.filter(
    #     designation__name='VhCaretaker').exists()
    # vhincharge = request.user.holds_designations.filter(
    #     designation__name='VhIncharge').exists()

    hall_caretaker = HallCaretaker.objects.all()
    hall_caretaker_user=[]
    for h_c in hall_caretaker:
        hall_caretaker_user.append(h_c.staff.id.user)

    hall_warden = HallWarden.objects.all()
    hall_warden_user=[]
    for h_w in hall_warden:
        hall_warden_user.append(h_w.faculty.id.user)

    # finding designation of user

    user_designation = "student"
    if user in hall_caretaker_user:
        user_designation = "Caretaker"
    elif user in hall_warden_user:
        user_designation = "Warden"
    else:
        user_designation = "Intender"

    available_rooms = {}
    forwarded_rooms = {}
    cancel_booking_request = []

    # bookings for intender view
    if (user_designation == "Intender"):
        all_bookings = GuestRoomBooking.objects.select_related('intender').all().order_by('arrival_date')
        pending_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status="Pending") | Q(status="Forward"),  departure_date__gte=datetime.datetime.today(), intender=user).order_by('arrival_date')
        active_bookings = GuestRoomBooking.objects.select_related('intender').filter(status="CheckedIn", departure_date__gte=datetime.datetime.today(), intender=user).order_by('arrival_date')
        dashboard_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status = "Pending") | Q(status="Forward") | Q(status = "Confirmed") | Q(status = 'Rejected'), departure_date__gte=datetime.datetime.today(), intender=user).order_by('arrival_date')
        # print(dashboard_bookings.arrival_date)

        visitors = {}
        rooms = {}
        for booking in active_bookings:
            temp = range(2, booking.total_guest + 1)
            visitors[booking.id] = temp

        for booking in active_bookings:
            for room_no in booking.rooms.all():
                temp2 = range(1, booking.rooms_required)
                rooms[booking.id] = temp2

        complete_bookings = GuestRoomBooking.objects.select_related('intender').filter(departure_date__lt=datetime.datetime.today(), intender=user).order_by('arrival_date')
        canceled_bookings = GuestRoomBooking.objects.select_related('intender').filter(status="Canceled", intender=user).order_by('arrival_date')
        rejected_bookings = GuestRoomBooking.objects.select_related('intender').filter(status='Rejected', intender=user).order_by('arrival_date')
        cancel_booking_requested = GuestRoomBooking.objects.select_related('intender').filter(status='CancelRequested', intender=user).order_by('arrival_date')


    else:  # booking for caretaker and incharge view
        all_bookings = GuestRoomBooking.objects.select_related('intender').all().order_by('arrival_date')
        pending_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status="Pending") | Q(status="Forward"), departure_date__gte=datetime.datetime.today()).order_by('arrival_date')
        active_bookings = GuestRoomBooking.objects.filter(Q(status="Confirmed") | Q(status="CheckedIn"), departure_date__gte=datetime.datetime.today()).select_related('intender').order_by('arrival_date')
        cancel_booking_request = GuestRoomBooking.objects.select_related('intender').filter(status="CancelRequested", departure_date__gte=datetime.datetime.today()).order_by('arrival_date')
        dashboard_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status = "Pending") | Q(status="Forward") | Q(status = "Confirmed"), departure_date__gte=datetime.datetime.today()).order_by('arrival_date')
        visitors = {}
        rooms = {}

        # x = GuestRoomBooking.objects.all().annotate(rooms_count=Count('rooms'))

        c_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status="Forward"),  departure_date__gte=datetime.datetime.today()).order_by('arrival_date')
        
        # number of visitors
        for booking in active_bookings:
            temp = range(2, booking.total_guest + 1)
            visitors[booking.id] = temp


        # rooms alloted to booking
        for booking in active_bookings:
            for room_no in booking.rooms.all():
                temp2 = range(2, booking.rooms_required + 1)
                rooms[booking.id] = temp2
                #print(booking.rooms.all())


        complete_bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(status="Canceled") | Q(status="Complete"), departure_date__lt=datetime.datetime.today()).select_related().order_by('arrival_date')
        canceled_bookings = GuestRoomBooking.objects.filter(status="Canceled").select_related('intender').order_by('arrival_date')
        cancel_booking_requested = GuestRoomBooking.objects.select_related('intender').filter(status='CancelRequested', departure_date__gte=datetime.datetime.today(), intender=user).order_by('arrival_date')
        rejected_bookings = GuestRoomBooking.objects.select_related('intender').filter(status='Rejected').order_by('arrival_date')

        # finding available room list for alloting rooms
        for booking in pending_bookings:
            arrival_date = booking.arrival_date
            departure_date = booking.departure_date
            temp1 = booking_details(arrival_date, departure_date)
            available_rooms[booking.id] = temp1
            
        # forwarded rooms details
        for booking in c_bookings:
            arrival_date = booking.arrival_date
            departure_date = booking.departure_date
            temp2 = forwarded_booking_details(arrival_date, departure_date)
            forwarded_rooms[booking.id] = temp2

    all_hall = Hall.objects.all()
    context = {'all_bookings': all_bookings,
                   'complete_bookings': complete_bookings,
                   'pending_bookings': pending_bookings,
                   'active_bookings': active_bookings,
                   'canceled_bookings': canceled_bookings,
                   'dashboard_bookings' : dashboard_bookings,
                   'available_rooms': available_rooms,
                   'forwarded_rooms': forwarded_rooms,
                   'intenders': intenders,
                   'user': user,
                   'visitors': visitors,
                   'rooms' : rooms,
                   'rejected_bookings': rejected_bookings,
                   'cancel_booking_request': cancel_booking_request,
                   'cancel_booking_requested' : cancel_booking_requested,
                   'user_designation': user_designation,
                   'all_hall': all_hall
                   }

    return render(request, "hostelmanagement/guestroom_booking.html", context)


# request booking form action view starts here

@login_required(login_url='/accounts/login/')
def request_booking(request):

    if request.method == 'POST':
        flag=0

        # getting details from request form
        hall_no = request.POST.get('hall_no')
        print("hall_no", hall_no)
        hall = Hall.objects.get(hall_id=hall_no)
        intender = request.POST.get('intender')
        user = request.user
        booking_id =  request.POST.get('booking-id')
        total_guest = request.POST.get('number-of-people')
        bookingObject = []
      
        purpose_of_visit = request.POST.get('purpose-of-visit')
        arrival_date = request.POST.get('booking_from')
        departure_date = request.POST.get('booking_to')
        arrival_time = request.POST.get('booking_from_time')
        departure_time = request.POST.get('booking_to_time')
        number_of_rooms = request.POST.get('number-of-rooms')

        # visitor datails from place request form 

        visitor_name = request.POST.get('name')
        visitor_phone = request.POST.get('phone')
        visitor_email = request.POST.get('email')
        visitor_address = request.POST.get('address')
        visitor_nationality = request.POST.get('nationality')
       

        bookingObject = GuestRoomBooking.objects.create(
                                                    hall=hall,
                                                     purpose=purpose_of_visit,
                                                     intender=user,
                                                     arrival_date=arrival_date,
                                                     departure_date=departure_date,
                                                     total_guest=total_guest,
                                                     arrival_time=arrival_time,
                                                     departure_time=departure_time,
                                                     rooms_required=number_of_rooms,
                                                    guest_name=visitor_name,
                                                    guest_phone=visitor_phone,
                                                    guest_email=visitor_email,
                                                    guest_address=visitor_address,
                                                    nationality=visitor_nationality
                                                     )

        bookingObject.save()


        return HttpResponseRedirect(reverse("hostelmanagement:guest_room"))
    else:
        return HttpResponseRedirect(reverse("hostelmanagement:guest_room"))



def booking_details(date1, date2):

    bookings = GuestRoomBooking.objects.select_related('intender').filter(Q(arrival_date__lte=date1, departure_date__gte=date1, status="Confirmed") | Q(arrival_date__gte=date1,
                                                                                                                      departure_date__lte=date2, status="Confirmed") | Q(arrival_date__lte=date2, departure_date__gte=date2, status="Confirmed") | Q(arrival_date__lte=date1, departure_date__gte=date1, status="Forward") | Q(arrival_date__gte=date1,
                                                                                                                      departure_date__lte=date2, status="Forward") | Q(arrival_date__lte=date2, departure_date__gte=date2, status="Forward") | Q(arrival_date__lte=date1, departure_date__gte=date1, status="CheckedIn") | Q(arrival_date__gte=date1, departure_date__lte=date2, status="CheckedIn") | Q(arrival_date__lte=date2, departure_date__gte=date2, status="CheckedIn"))

    booked_rooms = []
    for booking in bookings:
        for room in booking.rooms.all():
            booked_rooms.append(room)

    available_rooms = []
    all_rooms = GuestRoomDetail.objects.all()
    for room in all_rooms:
        if room not in booked_rooms:
            available_rooms.append(room)

    return available_rooms