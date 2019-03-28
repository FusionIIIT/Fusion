from django.core.exceptions import ObjectDoesNotExist
from datetime import date, datetime
from datetime import timedelta
from threading import Thread
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.generic import View
from django.db.models import Q
from django.contrib.auth.models import User
from .forms import MinuteForm
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from .models import (Feedback, Menu, Menu_change_request, Mess_meeting,
                     Mess_minutes, Mess_reg, Messinfo, Monthly_bill,
                     Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food, MessBillBase)


today_g = datetime.today()
year_g = today_g.year
tomorrow_g = today_g + timedelta(days=1)


def add_nonveg_order(request, student):
    """
    This function is to place non veg orders
    :param request:
        user: Current user
        order_interval: Time of the day for which order is placed eg breakfast/lunch/dinner
    :param student: student placing the order
    :variables:
        extra_info: Extra information about the current user. From model ExtraInfo
        student: Student information about the current user
        student_mess: Mess choices of the student
        dish_request: Predefined dish available
        nonveg_object: Object of Nonveg_data
    :return:
    """
    try:
        dish_request = Nonveg_menu.objects.get(dish=request.POST.get("dish"))
        order_interval = request.POST.get("interval")
        order_date = tomorrow_g
        nonveg_object = Nonveg_data(student_id=student, order_date=order_date,
                                    order_interval=order_interval, dish=dish_request)
        nonveg_object.save()
        # messages.success(request, 'Your request is forwarded !!', extra_tags='successmsg')

    except ObjectDoesNotExist:
        return HttpResponse("Seems like object does not exist")


def add_mess_feedback(request, student):
    """
    This function is to record the feedback submitted
    :param request:
        description: Description of feedback
        feedback_type: Type of feedback
    :param student: Student placing the request
    :variable:
         extra_info: Extra information of the user
         date_today: Today's date
         feedback_object: Object of Feedback to store current variables
    :return:
        data: to record success or any errors
    """
    date_today = datetime.now().date()
    description = request.POST.get('description')
    feedback_type = request.POST.get('feedback_type')
    feedback_object = Feedback(student_id=student, fdate=date_today,
                               description=description,
                               feedback_type=feedback_type)

    feedback_object.save()
    data = {
        'status': 1
    }
    return data


def add_vacation_food_request(request, student):
    """
        This function is to record vacation food requests
        :param request:
            start_date: Starting date of food request
            end_date: Last date of food request
            purpose: purpose for vacation food
        :param student: Student placing the order
        :variables:
            date_today: to record the date of the application
            vacation_object: to store current values for object of 'Vacation_food'
        :return:
            data: status = 1 or 2
    """
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    purpose = request.POST.get('purpose')
    date_today = str(datetime.now().date())
    # TODO add helper to validate the dates on order to replace the if thing from repeating
    if (start_date < date_today) or (end_date < start_date):
        data = {
            'status': 2
        }
        return data
    vacation_object = Vacation_food(student_id=student, start_date=start_date,
                                    end_date=end_date, purpose=purpose)
    vacation_object.save()
    data = {
        'status': 1
    }
    return data


def add_menu_change_request(request):
    # TODO logic here is flawed if the same dish is use more than once then it will give an error !!!
    #  or if there are two requests on the same dish
    """
    This function is to record mess menu change requests
    :param request:
        dish: Current dish
        new_dish: Dish to be replaced
    :return:
    """
    try:
        print("inside add_menu")
        dish = Menu.objects.get(dish=request.POST.get("dish"))
        print("dish")
        new_dish = request.POST.get("newdish")
        print("newdish")
        reason = request.POST.get("reason")
        menu_object = Menu_change_request(dish=dish, request=new_dish, reason=reason)
        menu_object.save()
        data = {
            'status': 1
        }
        return data
    except ObjectDoesNotExist:
        data = {
            'status': 0
        }
        return data


def handle_menu_change_response(request):
    # TODO logic here is flawed if the same dish is use more than once then it will give an error !!!
    #  or if there are two requests on the same dish
    """
        This function is to respond to mess menu requests
        :param request:
            stat: Accept or reject a request
            ap_id: id of the application being accepted or rejected
        :variable application: Object of Menu_change_request

        :return: data with status of the application
            5 for error
    """
    ap_id = request.POST.get('idm')
    stat = request.POST['status']
    application = Menu_change_request.objects.get(pk=ap_id)
    print(stat)
    if stat == '2':
        application.status = 2
        meal = application.dish
        obj = Menu.objects.get(dish=meal.dish)
        obj.dish = application.request
        obj.save()
        data = {
            'status': '2'
        }

    elif stat == '0':
        application.status = 0
        data = {
            'status': '1'
        }

    else:
        application.status = 1
        data = {
            'status': '0'
        }

    application.save()
    # data = {
    #     'status': 1
    # }
    return data


def handle_vacation_food_request(request, ap_id):
    """
       This function records the response to vacation food requests
       :param request:
           user: Current user

       :param ap_id:

       :variables:
           holds_designations: Designation of the current user
           applications: Object of application with the given id
       :return:
    """

    applications = Vacation_food.objects.get(pk=ap_id)
    if request.POST.get('submit') == 'approve':
        applications.status = '2'

    elif request.POST.get('submit') == 'reject':
        applications.status = '0'

    else:
        applications.status = '1'
    applications.save()
    data = {
        'status': 1
    }
    return data


def add_mess_registration_time(request):
    """
           This function is to start mess registration
           @request:
               user: Current user
               sem: Semester for which registration is started
               start_reg: Start Date
               end_reg: End Date
               holds_designations: designation of current user to validate proper platform
               mess_reg_obj: Object of Mess_reg to store current values
           @variables:
           :return data: Status of the application
    """
    sem = request.POST.get('sem')
    start_reg = request.POST.get('start_date')
    end_reg = request.POST.get('end_date')
    mess_reg_obj = Mess_reg(sem=sem, start_reg=start_reg, end_reg=end_reg)
    mess_reg_obj.save()
    data = {
        'status': 1
    }
    return data


def add_leave_request(request, student):
    """
        This function is to record and validate leave requests
        :param student: Information of student submitting the request
        @request:
            leave_type: Type of leave
            start_date: Starting date of the leave
            end_date: Date of return
            purpose: Purpose of the leave
        @variables:
            today: Date today in string format
            rebates: Record of past leave requests of the student
            rebate_object:  Rebate object that stores current information
    """
    flag = 1
    today = str(datetime.now().date())
    # leave_doc = request.FILES['myfile']
    leave_type = request.POST.get('leave_type')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    purpose = request.POST.get('purpose')
    #  TODO VALIDATE DATE
    if (start_date < today) or (end_date < start_date):
        data = {
            'status': 3
        }
        return data

    rebates = Rebate.objects.filter(student_id=student)
    rebate_check = rebates.filter(Q(status='1')|Q(status='2'))

    for r in rebate_check:
        if(start_date >= r.start_date) or (end_date <= r.end_date):
            data = {
                'status': 3
            }
            return data

    rebate_object = Rebate(student_id=student, leave_type=leave_type, start_date=start_date,
                           end_date=end_date, purpose=purpose)
    rebate_object.save()
    data = {
        'status': 1
    }
    return data


def add_mess_meeting_invitation(request):
    """
       This function is to schedule a mess committee meeting
       @request:
           date: Date of the meeting
           venue: Venue of the meeting
           time: Time of the meeting
           agenda: Agenda of the meeting
       @variables:
           invitation_obj: Object of Mess_meeting with current values of date, venue, agenda, meeting time
    """
    date = request.POST.get('date')
    venue = request.POST.get('venue')
    agenda = request.POST.get('agenda')
    time = request.POST.get('time')
    invitation_obj = Mess_meeting(meet_date=date, agenda=agenda, venue=venue, meeting_time=time)
    invitation_obj.save()
    data = {
            'status': 1,
    }
    return data


def handle_rebate_response(request):
    """
       This function is to respond to rebate requests
       @variables:
       id: id of the rebate request
       leaves: Object corresponding to the id of the rebate request
       @return:
       data: returns the status of the application
    """
    id = request.POST.get('id_rebate')
    leaves = Rebate.objects.get(pk=id)
    leaves.status = request.POST["status"]
    leaves.save()
    data = {
        'message': 'You responded to request !'
    }
    return data


def add_special_food_request(request, student):
    """
        This function is to place special food requests ( used by students )
        @variables:
        user: Current user
        student: Information regarding the student placing the request
        purpose: The purpose for the special food request *taken from "purpose" POST method
        date_today: String of today's date allows checking dates to avoid reduntant values
        spfood_obj: Special Request object to store values to be updated
        @request:
        fr: Start Date of the food request *taken from form "start_date" POST method
        to: End Date of the food request *taken from form "end_date" POST method
        food1: Food option 1 *taken from form "food1" POST method
        food2: Food option 2 *taken from form "food2" POST method
        @return:
        data['status']: returns status of the application
    """
    fr = request.POST.get("start_date")
    to = request.POST.get("end_date")
    food1 = request.POST.get("food1")
    food2 = request.POST.get("food2")
    purpose = request.POST.get('purpose')
    # date_format = "%Y-%m-%d"
    date_today = datetime.now().date()
    date_today = str(date_today)
    print(date_today)
    #   TODO ADD DATE VALIDATION
    if (date_today > to) or (to < fr):
        data = {
            'status': 3
            # case when the to date has passed
        }
        messages.error(request, "Invalid dates")
        return JsonResponse(data)
    spfood_obj = Special_request(student_id=student, start_date=fr, end_date=to,
                                 item1=food1, item2=food2, request=purpose)
    if Special_request.objects.filter(student_id=student, start_date=fr, end_date=to,
                                      item1=food1, item2=food2, request=purpose).exists():
        data = {
            'status': 2,
        }
        return data
    else:
        spfood_obj.save()
        data = {
            'status': 1,
        }
        return data


def handle_special_request(request):
    """
       This function is to respond to special request for food submitted by students
       @variables:
       special_request: data corresponding to id of the special request being accepted or rejected
    """
    special_request = Special_request.objects.get(pk=request.POST["id"])
    special_request.status = request.POST["status"]
    special_request.save()
    data = {
        'message': 'You responded to the request !'
    }
    return data


def add_bill_base_amount(request):
    """
    This function is to update the base cost of the monthly central mess bill
    :param request:
    :return:
    """
    # month_now = today.strftime('%B')
    cost = request.POST.get("amount")
    if cost < 0:
        data = {
            'status' : '2',
            'message': "Negative Values not allowed"
        }
        return data
    data = {
        'status': 1,
        'message': "Successfully updated"
    }
    amount_object = MessBillBase(bill_amount=cost)
    amount_object.save()

    return data


def add_mess_committee(request, roll_number):
    mess = Messinfo.objects.get(student_id__id=roll_number)
    if mess.mess_option == 'mess1':
        designation = Designation.objects.get(name='mess_committee_mess1')
    else:
        designation = Designation.objects.get(name='mess_committee_mess2')
    # designation = Designation.objects.get(name='mess_committee')
    add_obj = HoldsDesignation.objects.filter(Q(user__username=roll_number) & Q(designation=designation))
    if add_obj:
        data = {
            'status': 2,
            'message': roll_number + " is already a part of mess committee"
        }
        return data
    else:
        add_user = User.objects.get(username=roll_number)
        designation_object = HoldsDesignation(user=add_user, working=add_user, designation=designation)
        designation_object.save()
        data = {
            'status': 1,
            'message': roll_number + " is added to Mess Committee"
        }
        return data


def generate_bill():
    student_all = Student.objects.all()
    month_t = datetime.now().month - 1
    first_day_of_this_month = date.today().replace(day=1)
    last_day_prev_month = first_day_of_this_month - timedelta(days=1)
    previous_month = last_day_prev_month.strftime('%B')
    # previous_month = month_t.strftime("%B")
    print(previous_month)
    amount_c = MessBillBase.objects.latest('timestamp')
    for student in student_all:
        nonveg_total_bill=0
        rebate_count = 0
        total = 0
        nonveg_data = Nonveg_data.objects.filter(student_id=student)
        rebates = Rebate.objects.filter(student_id=student)
        for order in nonveg_data:
            if order.order_date.strftime("%B") == previous_month:
                nonveg_total_bill = nonveg_total_bill + order.dish.price
        for r in rebates:
            if r.status == '2':
                if r.start_date.strftime("%B") == previous_month:
                    rebate_count = rebate_count + abs((r.end_date - r.start_date).days) + 1
        rebate_amount = rebate_count*amount_c.bill_amount/30
        total = amount_c.bill_amount + nonveg_total_bill + rebate_amount
        bill_object = Monthly_bill(student_id=student,
                                   month=previous_month,
                                   amount=amount_c.bill_amount,
                                   rebate_count=rebate_count,
                                   rebate_amount=rebate_amount,
                                   nonveg_total_bill=nonveg_total_bill,
                                   total_bill=total)
        if Monthly_bill.objects.filter(student_id=student,
                                       month=previous_month,
                                       year = year_g,
                                       total_bill=total):
            print("exists")
        elif Monthly_bill.objects.filter(student_id=student,
                                       month=previous_month,
                                       year = year_g):
            Monthly_bill.objects.filter(student_id=student,
                                        month=previous_month,
                                        year=year_g).update(student_id=student,
                                                            month=previous_month,
                                                            amount=amount_c.bill_amount,
                                                            rebate_count=rebate_count,
                                                            rebate_amount=rebate_amount,
                                                            nonveg_total_bill=nonveg_total_bill,
                                                            total_bill=total)
            # bill_object.update()
            print(student)
        else:
            bill_object.save()
            print(student)

