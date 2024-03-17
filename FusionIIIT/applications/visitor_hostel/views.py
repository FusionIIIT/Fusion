import datetime
from datetime import date
import xlrd
import os
import sys

from django.core.files.storage import FileSystemStorage

from Fusion import settings
from applications.visitor_hostel.models import RoomDetail
from django.contrib.auth.models import User

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render

from applications.globals.models import *
from applications.visitor_hostel.forms import *
from applications.visitor_hostel.models import *
from applications.complaint_system.models import Caretaker
# from notification.views import visitor_hostel_caretaker_notif
import numpy as np
from django.contrib.auth.models import User

# from .forms import InventoryForm

# for notifications
from notification.views import visitors_hostel_notif


# main page showing dashboard of user

@login_required(login_url='/accounts/login/')
def visitorhostel(request):

    # intenders
    intenders = User.objects.all()
    user = request.user
    # intender = request.user.holds_designations.filter(designation__name = 'Intender').exists()
    vhcaretaker = request.user.holds_designations.filter(
        designation__name='VhCaretaker').exists()
    vhincharge = request.user.holds_designations.filter(
        designation__name='VhIncharge').exists()

    # finding designation of user

    user_designation = "student"
    if vhincharge:
        user_designation = "VhIncharge"
    elif vhcaretaker:
        user_designation = "VhCaretaker"
    else:
        user_designation = "Intender"

    available_rooms = {}
    forwarded_rooms = {}
    cancel_booking_request = []

    # bookings for intender view
    if (user_designation == "Intender"):
        all_bookings = BookingDetail.objects.select_related(
            'intender', 'caretaker').all().order_by('booking_from')
        pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(status="Pending") | Q(
            status="Forward"),  booking_to__gte=datetime.datetime.today(), intender=user).order_by('booking_from')
        active_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status="CheckedIn", booking_to__gte=datetime.datetime.today(), intender=user).order_by('booking_from')
        dashboard_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(status="Pending") | Q(status="Forward") | Q(
            status="Confirmed") | Q(status='Rejected'), booking_to__gte=datetime.datetime.today(), intender=user).order_by('booking_from')
        # print(dashboard_bookings.booking_from)

        visitors = {}
        rooms = {}
        for booking in active_bookings:
            temp = range(2, booking.person_count + 1)
            visitors[booking.id] = temp

        for booking in active_bookings:
            for room_no in booking.rooms.all():
                temp2 = range(1, booking.number_of_rooms_alloted)
                rooms[booking.id] = temp2

        complete_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            check_out__lt=datetime.datetime.today(), intender=user).order_by('booking_from').reverse()
        canceled_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status="Canceled", intender=user).order_by('booking_from')
        rejected_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status='Rejected', intender=user).order_by('booking_from')
        cancel_booking_requested = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status='CancelRequested', intender=user).order_by('booking_from')

    else:  # booking for caretaker and incharge view
        all_bookings = BookingDetail.objects.select_related(
            'intender', 'caretaker').all().order_by('booking_from')
        pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            Q(status="Pending") | Q(status="Forward"), booking_to__gte=datetime.datetime.today()).order_by('booking_from')
        active_bookings = BookingDetail.objects.filter(Q(status="Confirmed") | Q(
            status="CheckedIn"), booking_to__gte=datetime.datetime.today()).select_related('intender', 'caretaker').order_by('booking_from')
        cancel_booking_request = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status="CancelRequested", booking_to__gte=datetime.datetime.today()).order_by('booking_from')
        dashboard_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(status="Pending") | Q(
            status="Forward") | Q(status="Confirmed"), booking_to__gte=datetime.datetime.today()).order_by('booking_from')
        print(dashboard_bookings)
        visitors = {}
        rooms = {}

        # x = BookingDetail.objects.all().annotate(rooms_count=Count('rooms'))

        c_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            Q(status="Forward"),  booking_to__gte=datetime.datetime.today()).order_by('booking_from')

        # number of visitors
        for booking in active_bookings:
            temp = range(2, booking.person_count + 1)
            visitors[booking.id] = temp

        # rooms alloted to booking
        for booking in active_bookings:
            for room_no in booking.rooms.all():
                temp2 = range(2, booking.number_of_rooms_alloted + 1)
                rooms[booking.id] = temp2
                # print(booking.rooms.all())

        complete_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(status="Canceled") | Q(
            status="Complete"), check_out__lt=datetime.datetime.today()).select_related().order_by('booking_from').reverse()
        canceled_bookings = BookingDetail.objects.filter(status="Canceled").select_related(
            'intender', 'caretaker').order_by('booking_from')
        cancel_booking_requested = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            status='CancelRequested', booking_to__gte=datetime.datetime.today(), intender=user).order_by('booking_from')
        rejected_bookings = BookingDetail.objects.select_related(
            'intender', 'caretaker').filter(status='Rejected').order_by('booking_from')

        # finding available room list for alloting rooms
        for booking in pending_bookings:
            booking_from = booking.booking_from
            booking_to = booking.booking_to
            temp1 = booking_details(booking_from, booking_to)
            available_rooms[booking.id] = temp1

        # forwarded rooms details
        for booking in c_bookings:
            booking_from = booking.booking_from
            booking_to = booking.booking_to
            temp2 = forwarded_booking_details(booking_from, booking_to)
            forwarded_rooms[booking.id] = temp2
        # print(available_rooms)
        # print(forwarded_rooms)
    # inventory data
    inventory = Inventory.objects.all()
    inventory_bill = InventoryBill.objects.select_related('item_name').all()
    # completed booking bills

    completed_booking_bills = {}
    all_bills = Bill.objects.select_related()

    current_balance = 0
    for bill in all_bills:
        completed_booking_bills[bill.id] = {'intender': str(bill.booking.intender), 'booking_from': str(
            bill.booking.booking_from), 'booking_to': str(bill.booking.booking_to), 'total_bill': str(bill.meal_bill + bill.room_bill), 'bill_date': str(bill.bill_date)}
        current_balance = current_balance+bill.meal_bill + bill.room_bill

    for inv_bill in inventory_bill:
        current_balance = current_balance - inv_bill.cost

    active_visitors = {}
    for booking in active_bookings:
        if booking.status == 'CheckedIn':
            for visitor in booking.visitor.all():
                active_visitors[booking.id] = visitor

    # edit_room_statusForm=RoomStatus.objects.filter(Q(status="UnderMaintenance") | Q(status="Available"))

    previous_visitors = VisitorDetail.objects.all()

    # ------------------------------------------------------------------------------------------------------------------------------
    bills = {}

    for booking in active_bookings:
        if booking.status == 'CheckedIn':
            rooms = booking.rooms.all()
            days = (datetime.date.today() - booking.check_in).days
            category = booking.visitor_category
            person = booking.person_count

            room_bill = 100
            if days == 0:
                days = 1

            if category == 'A':
                room_bill = 0
            elif category == 'B':
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill+days*400
                    else:
                        room_bill = room_bill+days*500
            elif category == 'C':
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill+days*800
                    else:
                        room_bill = room_bill+days*1000
            else:
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill+days*1400
                    else:
                        room_bill = room_bill+days*1600

            mess_bill = 0
            for visitor in booking.visitor.all():
                meal = MealRecord.objects.select_related(
                    'booking__intender', 'booking__caretaker', 'visitor').filter(booking_id=booking.id)

                mess_bill1 = 0
                for m in meal:
                    if m.morning_tea != 0:
                        mess_bill1 = mess_bill1+m.morning_tea*10
                    if m.eve_tea != 0:
                        mess_bill1 = mess_bill1+m.eve_tea*10
                    if m.breakfast != 0:
                        mess_bill1 = mess_bill1+m.breakfast*50
                    if m.lunch != 0:
                        mess_bill1 = mess_bill1+m.lunch*100
                    if m.dinner != 0:
                        mess_bill1 = mess_bill1+m.dinner*100

                    mess_bill = mess_bill + mess_bill1

            total_bill = mess_bill + room_bill

            bills[booking.id] = {'mess_bill': mess_bill,
                                 'room_bill': room_bill, 'total_bill': total_bill}

   # print(available_rooms)
    # -------------------------------------------------------------------------------------------------------------------------------

    visitor_list = []
    for b in dashboard_bookings:
        count = 1
        b_visitor_list = b.visitor.all()
        for v in b_visitor_list:
            if count == 1:
                visitor_list.append(v)
                count = count+1

    return render(request, "vhModule/visitorhostel.html",
                  {'all_bookings': all_bookings,
                   'complete_bookings': complete_bookings,
                   'pending_bookings': pending_bookings,
                   'active_bookings': active_bookings,
                   'canceled_bookings': canceled_bookings,
                   'dashboard_bookings': dashboard_bookings,

                   'bills': bills,
                   # 'all_rooms_status' : all_rooms_status,
                   'available_rooms': available_rooms,
                   'forwarded_rooms': forwarded_rooms,
                   # 'booked_rooms' : booked_rooms,
                   # 'under_maintainence_rooms' : under_maintainence_rooms,
                   # 'occupied_rooms' : occupied_rooms,
                   'inventory': inventory,
                   'inventory_bill': inventory_bill,
                   'active_visitors': active_visitors,
                   'intenders': intenders,
                   'user': user,
                   'visitors': visitors,
                   'rooms': rooms,
                   # 'num_rooms' : list(range(1, booking.number_of_rooms_alloted+1)),
                   # 'num_rooms' :list(range(1, booking.number_of_rooms_alloted+1)),
                   'previous_visitors': previous_visitors,
                   'completed_booking_bills': completed_booking_bills,
                   'current_balance': current_balance,
                   'rejected_bookings': rejected_bookings,
                   'cancel_booking_request': cancel_booking_request,
                   'cancel_booking_requested': cancel_booking_requested,
                   'user_designation': user_designation})

# Get methods for bookings


@login_required(login_url='/accounts/login/')
def get_booking_requests(request):
    if request.method == 'POST':
        pending_bookings = BookingDetail.objects.select_related(
            'intender', 'caretaker').filter(status="Pending")

        return render(request, "vhModule/visitorhostel.html", {'pending_bookings': pending_bookings})
    else:
        return HttpResponseRedirect('/visitorhostel/')

# getting active bookings


@login_required(login_url='/accounts/login/')
def get_active_bookings(request):
    if request.method == 'POST':
        active_bookings = BookingDetail.objects.select_related(
            'intender', 'caretaker').filter(status="Confirmed")

        return render(request, "vhModule/visitorhostel.html", {'active_bookings': active_bookings})
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def get_inactive_bookings(request):
    if request.method == 'POST':
        inactive_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            Q(status="Cancelled") | Q(status="Rejected") | Q(status="Complete"))

        return render(request, "vhModule/visitorhostel.html", {'inactive_bookings': inactive_bookings})
    else:
        return HttpResponseRedirect('/visitorhostel/')

# Method for making booking request


@login_required(login_url='/accounts/login/')
def get_booking_form(request):
    if request.method == 'POST':
        intenders = User.objects.all()
        return render(request, "vhModule/visitorhostel.html", {'intenders': intenders})
    else:
        return HttpResponseRedirect('/visitorhostel/')

# request booking form action view starts here


@login_required(login_url='/accounts/login/')
def request_booking(request):

    if request.method == 'POST':
        flag = 0

        # getting details from request form
        intender = request.POST.get('intender')
        user = User.objects.get(id=intender)
        print("jiihuhhih")
        print(user)
        booking_id = request.POST.get('booking-id')
        category = request.POST.get('category')
        person_count = request.POST.get('number-of-people')
        bookingObject = []
        # if person_count and (int(person_count)<20):
        #   person_count = person_count

        # else:
        #  flag = 1    # for error

        #     person_count = 1
        purpose_of_visit = request.POST.get('purpose-of-visit')
        booking_from = request.POST.get('booking_from')
        booking_to = request.POST.get('booking_to')
        booking_from_time = request.POST.get('booking_from_time')
        booking_to_time = request.POST.get('booking_to_time')
        remarks_during_booking_request = request.POST.get(
            'remarks_during_booking_request')
        bill_to_be_settled_by = request.POST.get('bill_settlement')
        number_of_rooms = request.POST.get('number-of-rooms')
        caretaker = 'shailesh'

     #   if (int(person_count)<int(number_of_rooms)):
      #      flag=1

      #  if flag ==0:
        # print(sys.getsizeof(booking_from_time))
        # print(sys.getsizeof(booking_from))
        # print(sys.getsizeof(purpose_of_visit))
        # print(sys.getsizeof(bill_to_be_settled_by))
        # print("gfcfhcghv")
        care_taker = HoldsDesignation.objects.select_related('user','working','designation').filter(designation__name = "VhCaretaker")
        care_taker = care_taker[0]
        # print(care_taker,"care_taker")
        care_taker = care_taker.user
        bookingObject = BookingDetail.objects.create(
            caretaker=care_taker,
            purpose=purpose_of_visit,
            intender=user,
            booking_from=booking_from,
            booking_to=booking_to,
            visitor_category=category,
            person_count=person_count,
            arrival_time=booking_from_time,
            departure_time=booking_to_time,
            # remark=remarks_during_booking_request,
            number_of_rooms=number_of_rooms,
            bill_to_be_settled_by=bill_to_be_settled_by)
        # visitor_hostel_caretaker_notif(request.user,care_taker,"Submitted")
        # print (bookingObject)
        # print("Hello")
#        {% if messages %}
#   {% for message in messages %}
#     <div class="alert alert-dismissible alert-success">
#       <button type="button" class="close" data-dismiss="alert">
#       ×
#       </button>
#       <strong>{{message}}<strong>
#     </div>
#  {% endfor %}
# {% endif %}

        # in case of any attachment

        doc = request.FILES.get('files-during-booking-request')
        remark = remarks_during_booking_request,
        if doc:
            print("hello")
            filename, file_extenstion = os.path.splitext(
                request.FILES.get('files-during-booking-request').booking_id)
            filename = booking_id
            full_path = settings.MEDIA_ROOT + "/VhImage/"
            url = settings.MEDIA_URL + filename + file_extenstion
            if not os.path.isdir(full_path):
                cmd = "mkdir " + full_path
                os.subprocess.call(cmd, shell=True)
            fs = FileSystemStorage(full_path, url)
            fs.save(filename + file_extenstion, doc)
            uploaded_file_url = "/media/online_cms/" + filename
            uploaded_file_url = uploaded_file_url + file_extenstion
            bookingObject.image = uploaded_file_url
            bookingObject.save()

        # visitor datails from place request form

        visitor_name = request.POST.get('name')
        visitor_phone = request.POST.get('phone')
        visitor_email = request.POST.get('email')
        visitor_address = request.POST.get('address')
        visitor_organization = request.POST.get('organization')
        visitor_nationality = request.POST.get('nationality')
        # visitor_nationality="jk"
        if visitor_organization == '':
            visitor_organization = ' '

        visitor = VisitorDetail.objects.create(
            visitor_phone=visitor_phone, visitor_name=visitor_name, visitor_email=visitor_email, visitor_address=visitor_address, visitor_organization=visitor_organization, nationality=visitor_nationality
        )

        # try:
        # bd = BookingDetail.objects.get(id=booking_id)

        bookingObject.visitor.add(visitor)
        bookingObject.save()

        # except:
        # print("exception occured")
        # return HttpResponse('/visitorhostel/')

        # for sending notification of booking request to caretaker

        # caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = "VhCaretaker")
        # visitors_hostel_notif(request.user, care_taker.user, 'booking_request')

        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


# updating a booking request

@login_required(login_url='/accounts/login/')
def update_booking(request):
    if request.method == 'POST':
        user = request.user
        print(request.POST)

        booking_id = request.POST.get('booking-id')

        category = request.POST.get('category')
        person_count = request.POST.get('number-of-people')
        bookingObject = []
        if person_count:
            person_count = person_count
        else:
            person_count = 1
        purpose_of_visit = request.POST.get('purpose-of-visit')
        booking_from = request.POST.get('booking_from')
        booking_to = request.POST.get('booking_to')
        number_of_rooms = request.POST.get('number-of-rooms')

        # remark = request.POST.get('remark')
        booking = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        booking.person_count = person_count
        booking.number_of_rooms = number_of_rooms
        booking.booking_from = booking_from
        booking.booking_to = booking_to
        booking.purpose = purpose_of_visit
        booking.save()
        forwarded_rooms = {}
        # BookingDetail.objects.filter(id=booking_id).update(person_count=person_count,
        #                                                     purpose=purpose_of_visit,
        #                                                     booking_from=booking_from,
        #                                                     booking_to=booking_to,
        #                                                     number_of_rooms=number_of_rooms)
        booking = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        c_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
            Q(status="Forward"),  booking_to__gte=datetime.datetime.today()).order_by('booking_from')
        for booking in c_bookings:
            booking_from = booking.booking_from
            booking_to = booking.booking_to
            temp2 = forwarded_booking_details(booking_from, booking_to)
            forwarded_rooms[booking.id] = temp2
        return render(request, "visitorhostel/",
                      {
                          'forwarded_rooms': forwarded_rooms})

    else:
        return HttpResponseRedirect('/visitorhostel/')


# confirm booking by VhIncharge

@login_required(login_url='/accounts/login/')
def confirm_booking(request):
    if request.method == 'POST':
        booking_id = request.POST.get('booking-id')
        intender = request.POST.get('intender'),
        category = request.POST.get('category')
        purpose = request.POST.get('purpose-of-visit')
        booking_from = request.POST.get('booking_from')
        booking_to = request.POST.get('booking_to')
        person_count = request.POST.get('number-of-people')

        # rooms list
        rooms = request.POST.getlist('rooms[]')
        # print(rooms)
        booking = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        bd = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        bd.status = 'Confirmed'
        bd.category = category

        for room in rooms:
            room_object = RoomDetail.objects.get(room_number=room)
            bd.rooms.add(room_object)
        bd.save()

        # notification of booking confirmation
        visitors_hostel_notif(request.user, bd.intender,
                              'booking_confirmation')
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def cancel_booking(request):
    if request.method == 'POST':
        user = request.user
        print(request.POST)
        booking_id = request.POST.get('booking-id')
        remark = request.POST.get('remark')
        charges = request.POST.get('charges')
        BookingDetail.objects.select_related('intender', 'caretaker').filter(id=booking_id).update(
            status='Canceled', remark=remark)
        booking = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)

        # if no applicable charges then set charges to zero
        x = 0
        if charges:
            Bill.objects.create(booking=booking, meal_bill=x, room_bill=int(
                charges), caretaker=user, payment_status=True)
        else:
            Bill.objects.create(booking=booking, meal_bill=x,
                                room_bill=x, caretaker=user, payment_status=True)

        complete_bookings = BookingDetail.objects.filter(Q(status="Canceled") | Q(
            status="Complete"), booking_to__lt=datetime.datetime.today()).select_related('intender', 'caretaker').order_by('booking_from')

        # to notify the intender that his cancellation request has been confirmed

        visitors_hostel_notif(request.user, booking.intender,
                              'booking_cancellation_request_accepted')
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')

# cancel confirmed booing by intender


@login_required(login_url='/accounts/login/')
def cancel_booking_request(request):
    if request.method == 'POST':
        intender = request.user.holds_designations.filter(
            designation__name='VhIncharge')
        booking_id = request.POST.get('booking-id')
        remark = request.POST.get('remark')
        BookingDetail.objects.select_related('intender', 'caretaker').filter(
            id=booking_id).update(status='CancelRequested', remark=remark)

        incharge_name = HoldsDesignation.objects.select_related(
            'user', 'working', 'designation').filter(designation__name="VhIncharge")[1]

        # to notify the VhIncharge about a new cancelltaion request

        visitors_hostel_notif(
            request.user, incharge_name.user, 'cancellation_request_placed')
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


# rehject a booking request

@login_required(login_url='/accounts/login/')
def reject_booking(request):
    if request.method == 'POST':
        booking_id = request.POST.get('booking-id')
        remark = request.POST.get('remark')
        BookingDetail.objects.select_related('intender', 'caretaker').filter(id=booking_id).update(
            status="Rejected", remark=remark)

        # to notify the intender that his request has been rejected

        # visitors_hostel_notif(request.user, booking.intender, 'booking_rejected')
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')

# Guest check in view


@login_required(login_url='/accounts/login/')
def check_in(request):
    if request.method == 'POST':
        booking_id = request.POST.get('booking-id')
        visitor_name = request.POST.get('name')
        visitor_phone = request.POST.get('phone')
        visitor_email = request.POST.get('email')
        visitor_address = request.POST.get('address')
        check_in_date = datetime.date.today()

        # save visitors details
        visitor = VisitorDetail.objects.create(
            visitor_phone=visitor_phone, visitor_name=visitor_name, visitor_email=visitor_email, visitor_address=visitor_address)
        try:
            bd = BookingDetail.objects.select_related(
                'intender', 'caretaker').get(id=booking_id)
            bd.status = "CheckedIn"
            bd.check_in = check_in_date
            bd.visitor.add(visitor)
            bd.save()

        except:
            return HttpResponse('/visitorhostel/')
        return HttpResponse('/visitorhostel/')
    else:
        return HttpResponse('/visitorhostel/')

# guest check out view


@login_required(login_url='/accounts/login/')
def check_out(request):
    user = get_object_or_404(User, username=request.user.username)
    c = ExtraInfo.objects.select_related('department').all().filter(user=user)

    if user:
        if request.method == 'POST':
            id = request.POST.get('id')
            meal_bill = request.POST.get('mess_bill')
            room_bill = request.POST.get('room_bill')
            checkout_date = datetime.date.today()
            total_bill = int(meal_bill)+int(room_bill)
            BookingDetail.objects.select_related('intender', 'caretaker').filter(id=id).update(
                check_out=datetime.datetime.today(), status="Complete")
            booking = BookingDetail.objects.select_related(
                'intender', 'caretaker').get(id=id)
            Bill.objects.create(booking=booking, meal_bill=int(meal_bill), room_bill=int(
                room_bill), caretaker=user, payment_status=True, bill_date=checkout_date)

            # for visitors in visitor_info:

            # meal=Meal.objects.all().filter(visitor=v_id).distinct()
            # print(meal)
            # for m in meal:
            # mess_bill1=0
            # if m.morning_tea==True:
            #     mess_bill1=mess_bill1+ m.persons*10
            #     print(mess_bill1)
            # if m.eve_tea==True:
            #     mess_bill1=mess_bill1+m.persons*10
            # if m.breakfast==True:
            #     mess_bill1=mess_bill1+m.persons*50
            # if m.lunch==True:
            #     mess_bill1=mess_bill1+m.persons*100
            # if m.dinner==True:
            #     mess_bill1=mess_bill1+m.persons*100
            #
            # if mess_bill1==m.persons*270:
            #     mess_bill=mess_bill+225*m.persons
            # else:
            #         mess_bill=mess_bill + mess_bill1

            # RoomStatus.objects.filter(book_room=book_room[0]).update(status="Available",book_room='')

            return HttpResponseRedirect('/visitorhostel/')
        else:
            return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def record_meal(request):
    user = get_object_or_404(User, username=request.user.username)
    c = ExtraInfo.objects.select_related('department').all().filter(user=user)

    if user:
        if request.method == "POST":

            id = request.POST.get('pk')
            booking_id = request.POST.get('booking')
            booking = BookingDetail.objects.select_related(
                'intender', 'caretaker').get(id=booking_id)
            visitor = VisitorDetail.objects.get(id=id)
            date_1 = datetime.datetime.today()
            print(id, booking_id, booking, visitor, date_1)
            m_tea = request.POST.get("m_tea")
            breakfast = request.POST.get("breakfast")
            lunch = request.POST.get("lunch")
            eve_tea = request.POST.get("eve_tea")
            dinner = request.POST.get("dinner")

            person = 1
            print("bid: ", id)
            
            try:
                meal = MealRecord.objects.select_related('booking__intender', 'booking__caretaker', 'visitor').get(
                    visitor=visitor, booking=booking, meal_date=date_1)
            except:
                meal = False

            if meal:
                meal.morning_tea += int(m_tea)
                meal.eve_tea += int(eve_tea)
                meal.breakfast += int(breakfast)
                meal.lunch += int(lunch)
                meal.dinner += int(dinner)
                meal.save()
                return HttpResponseRedirect('/visitorhostel/')

            else:
                MealRecord.objects.create(visitor=visitor,
                                          booking=booking,
                                          morning_tea=m_tea,
                                          eve_tea=eve_tea,
                                          meal_date=date_1,
                                          breakfast=breakfast,
                                          lunch=lunch,
                                          dinner=dinner,
                                          persons=person)

            return HttpResponseRedirect('/visitorhostel/')
        else:
            return HttpResponseRedirect('/visitorhostel/')

# generate bill records between date range


@login_required(login_url='/accounts/login/')
def bill_generation(request):
    user = get_object_or_404(User, username=request.user.username)
    c = ExtraInfo.objects.all().filter(user=user)

    if user:
        if request.method == 'POST':
            v_id = request.POST.getlist('visitor')[0]

            meal_bill = request.POST.getlist('mess_bill')[0]
            room_bill = request.POST.getlist('room_bill')[0]
            status = request.POST.getlist('status')[0]
            if status == "True":
                st = True
            else:
                st = False

            user = get_object_or_404(User, username=request.user.username)
            c = ExtraInfo.objects.select_related(
                'department').filter(user=user)
            visitor = Visitor.objects.filter(visitor_phone=v_id)
            visitor = visitor[0]
            visitor_bill = Visitor_bill.objects.create(
                visitor=visitor, caretaker=user, meal_bill=meal_bill, room_bill=room_bill, payment_status=st)
            messages.success(request, 'guest check out successfully')
            return HttpResponseRedirect('/visitorhostel/')

        else:
            return HttpResponseRedirect('/visitorhostel/')

# get available rooms list between date range


@login_required(login_url='/accounts/login/')
def room_availabity(request):
    if request.method == 'POST':
        date_1 = request.POST.get('start_date')
        date_2 = request.POST.get('end_date')
        available_rooms_list = []
        available_rooms_bw_dates = booking_details(date_1, date_2)
        # print("Available rooms are ")
        for room in available_rooms_bw_dates:
            available_rooms_list.append(room.room_number)

        available_rooms_array = np.asarray(available_rooms_list)
        print(available_rooms_array)
        return render(request, "vhModule/room-availability.html", {'available_rooms': available_rooms_array})
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def add_to_inventory(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        bill_number = request.POST.get('bill_number')
        quantity = int((request.POST.get('quantity')))
        cost = int(request.POST.get('cost'))
        consumable = request.POST.get('consumable')
        if consumable == 'false':
            isConsumable = False
        else:
            isConsumable = True
        print(isConsumable)
        x = Inventory.objects.create(
            item_name=item_name, quantity=quantity, consumable=isConsumable)
        print(x.pk)
        item = Inventory.objects.get(pk=x.pk)
        item_id = item.pk
        InventoryBill.objects.create(
            bill_number=bill_number, cost=cost, item_name_id=item_id)
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def update_inventory(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        quantity = int(request.POST.get('quantity'))
        if quantity < 0:
            quantity = 1
        if quantity == 0:
            Inventory.objects.filter(id=id).delete()
        else:
            Inventory.objects.filter(id=id).update(quantity=quantity)
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def edit_room_status(request):
    if request.method == 'POST':
        room_number = request.POST.get('room_number')
        room_status = request.POST.get('room_status')
        room = RoomDetail.objects.get(room_number=room_number)
        RoomDetail.objects.filter(room_id=room).update(status=room_status)
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')


@login_required(login_url='/accounts/login/')
def bill_between_dates(request):
    if request.method == 'POST':
        date_1 = request.POST.get('start_date')
        date_2 = request.POST.get('end_date')
        bill_range_bw_dates = bill_range(date_1, date_2)
        meal_total = 0
        room_total = 0
        individual_total = []

        # calculating room and mess bill booking wise
        for i in bill_range_bw_dates:
            meal_total = meal_total + i.meal_bill
            room_total = room_total + i.room_bill
            individual_total.append(i.meal_bill + i.room_bill)
        total_bill = meal_total + room_total
        # zip(bill_range_bw_dates, individual_total)
        return render(request, "vhModule/booking_bw_dates.html", {
            # 'booking_bw_dates': bill_range_bw_dates,
            'booking_bw_dates_length': bill_range_bw_dates,
            'meal_total': meal_total,
            'room_total': room_total,
            'total_bill': total_bill,
            'individual_total': individual_total,
            'booking_bw_dates': zip(bill_range_bw_dates, individual_total)
        })
    else:
        return HttpResponseRedirect('/visitorhostel/')


def bill_range(date1, date2):

    bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(booking_from__lte=date1, booking_to__gte=date1) | Q(booking_from__gte=date1,
                                                                                                                                          booking_to__lte=date2) | Q(booking_from__lte=date2, booking_to__gte=date2) | Q(booking_from__lte=date1, booking_to__gte=date1) | Q(booking_from__gte=date1, booking_to__lte=date2) | Q(booking_from__lte=date2, booking_to__gte=date2))
    # bill_details = Bill.objects.filter(Q(booking__booking_from__lte=date1, booking__booking_to__gte=date1, booking__status="Confirmed") | Q(booking__booking_from__gte=date1,
    #                                                                                                                   booking__booking_to__lte=date2, booking__status="Confirmed") | Q(booking__booking_from__lte=date2, booking__booking_to__gte=date2, status="Confirmed") | Q(booking_from__lte=date1, booking__booking_to__gte=date1, status="CheckedIn") | Q(booking__booking_from__gte=date1, booking__booking_to__lte=date2, booking__status="CheckedIn") | Q(booking__booking_from__lte=date2, booking__booking_to__gte=date2, booking__status="CheckedIn"))
    bookings_bw_dates = []
    booking_ids = []
    for booking_id in bookings:
        booking_ids.append(booking_id.id)

    all_bill = Bill.objects.select_related('caretaker').all().order_by('-id')

    for b_id in booking_ids:
        if Bill.objects.select_related('caretaker').filter(booking__pk=b_id).exists():
            bill_id = Bill.objects.select_related(
                'caretaker').get(booking__pk=b_id)
            bookings_bw_dates.append(bill_id)

    return bookings_bw_dates


def booking_details(date1, date2):

    bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(booking_from__lte=date1, booking_to__gte=date1, status="Confirmed") | Q(booking_from__gte=date1,
                                                                                                                                                              booking_to__lte=date2, status="Confirmed") | Q(booking_from__lte=date2, booking_to__gte=date2, status="Confirmed") | Q(booking_from__lte=date1, booking_to__gte=date1, status="Forward") | Q(booking_from__gte=date1,
                                                                                                                                                                                                                                                                                                                                                           booking_to__lte=date2, status="Forward") | Q(booking_from__lte=date2, booking_to__gte=date2, status="Forward") | Q(booking_from__lte=date1, booking_to__gte=date1, status="CheckedIn") | Q(booking_from__gte=date1, booking_to__lte=date2, status="CheckedIn") | Q(booking_from__lte=date2, booking_to__gte=date2, status="CheckedIn"))

    booked_rooms = []
    for booking in bookings:
        for room in booking.rooms.all():
            booked_rooms.append(room)

    available_rooms = []
    all_rooms = RoomDetail.objects.all()
    for room in all_rooms:
        if room not in booked_rooms:
            available_rooms.append(room)

    return available_rooms

# function for finding forwarded booking rooms


def forwarded_booking_details(date1, date2):

    bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(booking_from__lte=date1, booking_to__gte=date1, status="Confirmed") | Q(booking_from__gte=date1,
                                                                                                                                                              booking_to__lte=date2, status="Confirmed") | Q(booking_from__lte=date2, booking_to__gte=date2, status="Confirmed") | Q(booking_from__lte=date1, booking_to__gte=date1, status="CheckedIn") | Q(booking_from__gte=date1, booking_to__lte=date2, status="CheckedIn") | Q(booking_from__lte=date2, booking_to__gte=date2, status="CheckedIn"))
    forwarded_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(booking_from__lte=date1, booking_to__gte=date1, status="Forward") | Q(booking_from__gte=date1,
                                                                                                                                                                      booking_to__lte=date2, status="Forward") | Q(booking_from__lte=date2, booking_to__gte=date2, status="Forward"))
    booked_rooms = []

    # Bookings for rooms which are forwarded but not yet approved

    forwarded_booking_rooms = []
    for booking in forwarded_bookings:
        for room in booking.rooms.all():
            forwarded_booking_rooms.append(room)

    return forwarded_booking_rooms


# View for forwarding booking - from VhCaretaker to VhIncharge

@login_required(login_url='/accounts/login/')
def forward_booking(request):
    if request.method == 'POST':
        user = request.user
        booking_id = request.POST.get('id')
        previous_category = request.POST.get('previous_category')
        modified_category = request.POST.get('modified_category')
        rooms = request.POST.getlist('rooms[]')
        remark = request.POST.get('remark')
        print(rooms)
        BookingDetail.objects.select_related('intender', 'caretaker').filter(
            id=booking_id).update(status="Forward", remark=remark)
        booking = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        bd = BookingDetail.objects.select_related(
            'intender', 'caretaker').get(id=booking_id)
        bd.modified_visitor_category = modified_category

        count_rooms = 0
        for room in rooms:
            count_rooms = count_rooms + 1
            room_object = RoomDetail.objects.get(room_number=room)
            bd.rooms.add(room_object)
        bd.number_of_rooms_alloted = count_rooms
        bd.save()

        dashboard_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(Q(status="Pending") | Q(status="Forward") | Q(
            status="Confirmed") | Q(status='Rejected'), booking_to__gte=datetime.datetime.today(), intender=user).order_by('booking_from')

        # return render(request, "vhModule/visitorhostel.html",
        #           {'dashboard_bookings' : dashboard_bookings})
        incharge_name = HoldsDesignation.objects.select_related(
            'user', 'working', 'designation').filter(designation__name="VhIncharge")[1]

        # notify incharge about forwarded booking
        visitors_hostel_notif(
            request.user, incharge_name.user, 'booking_forwarded')
        return HttpResponseRedirect('/visitorhostel/')
    else:
        return HttpResponseRedirect('/visitorhostel/')
