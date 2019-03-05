from datetime import date
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from datetime import date, datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.generic import View
from django.db.models import Q
from applications.central_mess.utils import render_to_pdf
from django.contrib.auth.models import User
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation
from .forms import MinuteForm
from .models import (Feedback, Menu, Menu_change_request, Mess_meeting,
                     Mess_minutes, Mess_reg, Messinfo, Monthly_bill,
                     Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food)


def mess(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    print(desig)
    form = MinuteForm()
    current_date = date.today()
    mess_reg = Mess_reg.objects.last()
    count1 = 0
    count2 = 0
    count3 = 0
    count4 = 0
    count5 = 0
    count6 = 0
    count7 = 0
    count8 = 0
    nonveg_total_bill = 0
    rebate_count = 0
    #
    # @periodic_task(run_every=(crontab(hour="*", minute="*", day_of_week="*")))
    #     print("Start")
    #     now = datetime.now()
    #     print(now)

    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        vaca_obj = Vacation_food.objects.filter(student_id=student)
        feedback_obj = Feedback.objects.filter(student_id=student)
        data = Nonveg_data.objects.filter(student_id=student)
        monthly_bill = Monthly_bill.objects.filter(student_id=student)
        payments = Payments.objects.filter(student_id=student)
        rebates = Rebate.objects.filter(student_id=student)
        meeting = Mess_meeting.objects.all()
        minutes = Mess_minutes.objects.all()
        sprequest = Special_request.objects.filter(status='1')
        splrequest = Special_request.objects.filter(student_id=student).order_by('-app_date')
        feed = Feedback.objects.all()
        messinfo = Messinfo.objects.get(student_id=student)
        count = 0
        #variable y stores the menu items
        y = Menu.objects.all()
        x = Nonveg_menu.objects.all()

        for item in rebates:
            d1 = item.start_date
            d2 = item.end_date
            item.duration = abs((d2 - d1).days)+1
            item.save()

        for items in rebates:
            if items.leave_type == 'casual':
                count += item.duration

        for f in feed:
            mess_opt = Messinfo.objects.get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess1':
                count1 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess1':
                count2 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess1':
                count3 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess1':
                count4 += 1

        for f in feed:
            mess_opt = Messinfo.objects.get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess2':
                count5 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess2':
                count6 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess2':
                count7 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess2':
                count8 += 1

        for bill in monthly_bill:

            for z in data:
                if z.order_date.strftime("%B") == bill.month:
                    nonveg_total_bill = nonveg_total_bill + z.dish.price
                    bill.nonveg_total_bill = nonveg_total_bill

                else:
                    bill.nonveg_total_bill = 0

            for r in rebates:
                if r.status == '2':
                    print(bill.month)
                    print(r.start_date.strftime("%B"))
                    if r.start_date.strftime("%B") == bill.month:
                        rebate_count = rebate_count + abs((r.end_date - r.start_date).days) + 1
                        bill.rebate_count = rebate_count

                    else:
                        bill.rebate_count = 0

            bill.rebate_amount = bill.rebate_count*79
            bill.total_bill = bill.amount - bill.rebate_amount + bill.nonveg_total_bill
            bill.save()

        context = {
                   'menu': y,
                   'messinfo': messinfo,
                   'monthly_bill': monthly_bill,
                   'payments': payments,
                   'nonveg': x,
                   'vaca': vaca_obj,
                   'info': extrainfo,
                   'feedback': feedback_obj,
                   'feed': feed,
                   'student': student,
                   'data': data,
                   'mess_reg': mess_reg,
                   'current_date': current_date,
                   'count': count,
                   'rebates': rebates,
                   'meeting': meeting,
                   'minutes': minutes,
                   'sprequest': sprequest,
                   'splrequest': splrequest,
                   'count1': count1,
                   'count2': count2,
                   'count3': count3,
                   'count4': count4,
                   'count5': count5,
                   'count6': count6,
                   'count7': count7,
                   'count8': count8,
                   'form': form,
                   'desig': desig
            }

        return render(request, "messModule/mess.html", context)

    elif extrainfo.user_type == 'staff':
        # make info with diff name and then pass context
        newmenu = Menu_change_request.objects.all()
        vaca_all = Vacation_food.objects.all()
        y = Menu.objects.all()
        x = Nonveg_menu.objects.all()
        leave = Rebate.objects.filter(status='1')
        context = {
                   'menu': y,
                   'newmenu': newmenu,
                   'vaca_all': vaca_all,
                   'info': extrainfo,
                   'leave': leave,
                   'current_date': current_date,
                   'mess_reg': mess_reg,
                   'desig': desig,
        }

        return render(request, "messModule/mess.html", context)

    elif extrainfo.user_type == 'faculty':
        meeting = Mess_meeting.objects.all()
        minutes = Mess_minutes.objects.all()
        feed = Feedback.objects.all()
        y = Menu.objects.all()

        for f in feed:
            mess_opt = Messinfo.objects.get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess1':
                count1 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess1':
                count2 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess1':
                count3 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess1':
                count4 += 1

        for f in feed:
            mess_opt = Messinfo.objects.get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess2':
                count5 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess2':
                count6 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess2':
                count7 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess2':
                count8 += 1

        return render(request, 'messModule/mess.html',
                      {'info': extrainfo, 'menu': y, 'meeting': meeting,
                       'minutes': minutes, 'count1': count1,
                       'count2': count2, 'count3': count3, 'feed': feed,
                       'count4': count4, 'form': form, 'count5': count5,
                       'count6': count6, 'count7': count7, 'count8': count8, 'desig': desig})


@login_required
@transaction.atomic
@csrf_exempt
def place_order(request):
    """
    This function is to place non-veg food orders
    :param request:
        user: Current user
        order_interval: Time of the day for which order is placed eg breakfast/lunch/dinner
    :variables:
        extra_info: Extra information about the current user. From model ExtraInfo
        student: Student information about the current user
        student_mess: Mess choices of the student
        dish_request: Predefined dish available
    :return:
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)

    if extra_info.user_type == 'student':
        student = Student.objects.get(id=extra_info)
        student_mess = Messinfo.objects.get(student_id=student)

        if student_mess.mess_option == 'mess1':
            try:
                dish_request = Nonveg_menu.objects.get(dish=request.POST.get("dish"))
                order_interval = request.POST.get("interval")
                order_date = datetime.now().date()
                nonveg_object = Nonveg_data(student_id=student, order_date=order_date,
                                            order_interval=order_interval, dish=dish_request)
                nonveg_object.save()
                messages.success(request, 'Your request is forwarded !!', extra_tags='successmsg')
                return HttpResponseRedirect('/mess')
            except ObjectDoesNotExist:
                return HttpResponse("seems like object error")

        else:
            return HttpResponse("you can't apply for this application")


@csrf_exempt
@login_required
@transaction.atomic
def submit_mess_feedback(request):
    """
    This function is to record the feeback submitted
    :param request:
        description: Description of feedback
        feedback_type: Type of feedback
        user: Current logged in user
    :variable:
         extra_info: Extra information of the user
         date_today: Today's date
         feedback_object: Object of Feedback to store current variables
    :return:
        data: to record success or any errors
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)

    if extra_info.user_type == 'student':
        student = Student.objects.get(id=extra_info)
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
        return JsonResponse(data)


@csrf_exempt
@login_required
@transaction.atomic
def mess_vacation_submit(request):
    """
    This function is to record vacation food requests
    :param request:
        user: Current user information
        start_date: Starting date of food request
        end_date: Last date of food request
        purpose: purpose for vacation food
    :variables:
        date_today: to record the date of the application
        vacation_object: to store current values for object of 'Vacation_food'
    :return:
        data: JsonResponse
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)

    if extra_info.user_type == 'student':
        student = Student.objects.get(id=extra_info)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        purpose = request.POST.get('purpose')
        date_today = str(datetime.now().date())
        if(start_date < date_today)or(end_date < start_date):
            data = {
                'status': 2
            }
            return JsonResponse(data)

        vacation_object = Vacation_food(student_id=student, start_date=start_date,
                                 end_date=end_date, purpose=purpose)

        vacation_object.save()
        data = {
             'status': 1
         }

        return JsonResponse(data)


@login_required
@transaction.atomic
def submit_mess_menu(request):
    """
    This function is to record mess menu change requests
    :param request:
        dish: Current dish
        new_dish: Dish to be replaced
    :return:
    """
    # TODO logic here is flawed if the same dish is use more than once then it will give an error !!!
    #  or if there are two requests on the same dish

    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations
    context = {}
    for d in designation:
        if d.designation.name == 'mess_convener':
            dish = Menu.objects.get(dish=request.POST.get("dish"))
            new_dish = request.POST.get("newdish")
            reason = request.POST.get("reason")
            menu_object = Menu_change_request(dish=dish, request=new_dish, reason=reason)
            menu_object.save()
            return HttpResponseRedirect("/mess")

    return render(request, 'mess.html', context)


@login_required
def menu_change_response(request):
    """
    This function is to respond to mess menu requests
    :param request:
        stat: Accept or reject a request
    :variables:

    :return:
    """
    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations
    ap_id = request.POST.get('idm')
    stat = request.POST['status']
    for d in designation:
        if d.designation.name == 'mess_manager':
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

    return JsonResponse(data)


# @login_required
# def response(request, ap_id):
#     user = request.user
#     extrainfo = ExtraInfo.objects.get(user=user)
#     holds_designations = HoldsDesignation.objects.filter(user=user)
#     desig = holds_designations
#
#     for d in desig:
#         if d.designation.name == 'mess_manager':
#             application = Menu_change_request.objects.get(pk=ap_id)
#
#             if(request.POST.get('submit') == 'approve'):
#                 application.status = 2
#                 meal = application.dish
#                 obj = Menu.objects.get(dish=meal.dish)
#                 obj.dish = application.request
#                 obj.save()
#
#             elif(request.POST.get('submit') == 'reject'):
#                 application.status = 0
#
#             else:
#                 application.status = 1
#
#         application.save()
#
#     return HttpResponseRedirect("/mess")


@login_required
def response_vacation_food(request, ap_id):
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
    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations

    for d in designation:
        if d.designation.name == 'mess_manager':
            applications = Vacation_food.objects.get(pk=ap_id)

            if(request.POST.get('submit') == 'approve'):
                applications.status = '2'

            elif(request.POST.get('submit') == 'reject'):
                applications.status = '0'

            else:
                applications.status = '1'

            applications.save()
    return HttpResponseRedirect("/mess")


@login_required
@transaction.atomic
def regsubmit(request):

    i = 0
    j = 0
    month_1 = ['January', 'February', 'March', 'April', 'May', 'June']
    month_2 = ['July', 'August', 'September', 'October', 'November', 'December']
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        mess = request.POST.get('mess_type')
        mess_info_inst = Messinfo.objects.get(student_id=student)
        mess_info_inst.mess_option = mess
        mess_info_inst.save()
        mess_reg = Mess_reg.objects.last()

        if Monthly_bill.objects.filter(student_id=student):
            return HttpResponseRedirect("/mess")

        else:

            if mess_reg.end_reg.strftime("%B") in month_1:
                while i<=5:
                    monthly_bill_obj = Monthly_bill(student_id=student, month=month_1[i])
                    monthly_bill_obj.save()
                    i = i+1

            else:
                while j<=5:
                    monthly_bill_obj = Monthly_bill(student_id=student, month=month_2[j])
                    monthly_bill_obj.save()
                    j = j+1

        return HttpResponseRedirect("/mess")

    else:
        return redirect('mess')


@login_required
@transaction.atomic
def start_mess_registration(request):
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
    """
    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations

    for d in designation:
        if d.designation.name == 'mess_manager':
            sem = request.POST.get('sem')
            start_reg = request.POST.get('start_date')
            end_reg = request.POST.get('end_date')
            mess_reg_obj = Mess_reg(sem=sem, start_reg=start_reg, end_reg=end_reg)
            mess_reg_obj.save()

            return HttpResponseRedirect("/mess")


@transaction.atomic
@csrf_exempt
def mess_leave_request(request):
    """
        This function is to record and validate leave requests
        @request:
            user: Current user
            leave_type: Type of leave
            start_date: Starting date of the leave
            end_date: Date of return
            purpose: Purpose of the leave
        @variables:
            today: Date today in string format
            student: Information od student submitting the request
            rebates: Record of past leave requests of the student
            rebate_object:  Rebate object that stores current infromation
    """
    flag = 1
    user = request.user
    today = str(datetime.now().date())
    extra_info = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extra_info)
    leave_type = request.POST.get('leave_type')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    purpose = request.POST.get('purpose')
    if(start_date < today)or(end_date<start_date):
        data = {
            'status': 3
        }
        return JsonResponse(data)

    rebates = Rebate.objects.filter(student_id=student)

    for r in rebates:
        if r.status == '1' or r.status == '2':
            print(r.start_date)
            print("compare")
            print(start_date)
            date_format = "%Y-%m-%d"
            a = datetime.strptime(str(r.start_date), date_format)
            b = datetime.strptime(str(start_date), date_format)
            c = datetime.strptime(str(r.end_date), date_format)
            d = datetime.strptime(str(end_date), date_format)
            print((b <= a and (d >= a and d <= c)) or (b >= a and (d >= a and d <= c))
                  or (b <= a and (d >= c)) or ((b >= a and b<=c) and (d >= c)))
            print((b >= a and b <= c) and (d >= c))
            if ((b <= a and (d >= a and d <= c)) or (b >= a and (d >= a and d <= c))
                    or (b <= a and (d >= c)) or ((b >= a and b<=c) and (d >= c))):
                flag = 0
                break

    if flag == 1:
        rebate_object = Rebate(student_id=student, leave_type=leave_type, start_date=start_date,
                               end_date=end_date, purpose=purpose)
        rebate_object.save()

    data = {
            'status': flag,
    }

    return JsonResponse(data)


@login_required
@transaction.atomic
def minutes(request):
    """
    To upload the minutes of the meeting
    :param request:
    :return:
    """
    if request.method == 'POST' and request.FILES:
        form = MinuteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('success')
        else:
            return HttpResponse("not uploaded")


@csrf_exempt
@transaction.atomic
def invitation(request):
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
    # data = {
    #         'status': 1,
    # }
    return HttpResponseRedirect("/mess")


# def rebate_response(request, ap_id):
#     leaves = Rebate.objects.get(pk=ap_id)

#     if(request.POST.get('submit') == 'approve'):
#         leaves.status = '2'

#     else:
#         leaves.status = '0'
#     leaves.save()
#     return HttpResponseRedirect("/mess")


def rebate_response(request):
    """
       This function is to respond to rebate requests
       @variables:
       id: id of the rebate request
       leaves: Object corresponding to the id of the rebate request
       @return:
       data: returns the status of the application
    """
    print("in \n\n\n\n\\n\n\n\n\\n\n\n\n\\n\n\n\n")
    id = request.POST.get('id_rebate')
    leaves = Rebate.objects.get(pk=id)
    leaves.status = request.POST["status"]
    leaves.save()
    data = {
        'message':'You responded to request !'
    }
    return JsonResponse(data)


def place_request(request):
    # This is for placing special food request
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
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    if extra_info.user_type == 'student':
        print(request.POST)
        extra_info = ExtraInfo.objects.get(user=user)
        student = Student.objects.get(id=extra_info)
        fr = request.POST.get("start_date")
        to = request.POST.get("end_date")
        print (fr, to, "dates")
        food1 = request.POST.get("food1")
        food2 = request.POST.get("food2")
        purpose = request.POST.get('purpose')
        print(purpose)
        # date_format = "%Y-%m-%d"
        date_today = datetime.now().date()
        date_today = str(date_today)
        print(date_today)
        if (date_today > to)or(to < fr):
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
            return JsonResponse(data)
        else:
            spfood_obj.save()
            data = {
                 'status': 1,
            }
            return JsonResponse(data)


# def special_request_response(request, ap_id):
#     sprequest = Special_request.objects.get(pk=ap_id)
#     if(request.POST.get('submit') == 'approve'):
#         sprequest.status = '2'
#     else:
#         sprequest.status = '0'
#
#     sprequest.save()
#     return HttpResponseRedirect("/mess")

def special_request_response(request):
    """
       This function is to respond to special request for food submitted by students
       @variables:
       special_request: data corresponding to id of the special request being accepted or rejected
    """
    special_request = Special_request.objects.get(pk=request.POST["id"])
    special_request.status = request.POST["status"]
    special_request.save()
    data = {
        'message':'You responded to the request !'
    }
    return JsonResponse(data)


def update_cost(request):
    """
    This function is to update the base cost of the monthly central mess bill
    :param request:
    :return:
    """
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    today = datetime.today()
    year_now = today.year
    month_now = today.strftime('%B')
    print(month_now)
    print(year_now)
    cost = request.POST.get("amount")
    data = {
        'status': 1,
    }
    monthly_bill = Monthly_bill.objects.filter(Q(month=month_now) & Q(year=year_now))
    for temp in monthly_bill:
        print(temp)
        print(temp.year)
        temp.amount = cost
        temp.save()
    print(temp)
    return JsonResponse(data)


def generate_mess_bill(request):
    """
        This function is to generate the bill of the students
        @variables:
        user: stores current user infromatiob
        nonveg_data : stores records of nonveg ordered by a student
        year_now: current year
        month_now: current month
        amount_m: monhly base amount
        students: information of all students
        mess_info: Mess Information, mainly choice of mess
        rebates: Rebate records of students
        """
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    nonveg_data = Nonveg_data.objects.all()
    today = datetime.today()
    year_now = today.year
    month_now = today.strftime('%B')
    amount_m = int(request.POST["amount"])
    print(amount_m)
    # amount_m = 2400
    data = {
        'status': 1,
    }
    mess_info = Messinfo.objects.all()
    students = Student.objects.all()
    for temp in mess_info:
        print(temp)
        count = 0
        rebate_amount = 0
        nonveg_total_bill = 0
        rebates = Rebate.objects.filter(student_id=temp.student_id)
        for item in rebates:
            d1 = item.start_date
            d2 = item.end_date
            item.duration = abs((d2 - d1).days)+1
            item.save()

        for items in rebates:
            if items.leave_type == 'casual':
                count += item.duration
        rebate_count = count
        rebate_amount = rebate_count*80
        total_bill = rebate_amount + nonveg_total_bill + amount_m
        monthly_bill_obj = Monthly_bill(student_id=temp.student_id,
                                        month=month_now,
                                        year=year_now,
                                        amount=amount_m,
                                        rebate_count=rebate_count,
                                        rebate_amount=rebate_amount,
                                        nonveg_total_bill=nonveg_total_bill,
                                        total_bill=total_bill)
        if Monthly_bill.objects.filter(student_id=temp.student_id, month=month_now, year=year_now):
            if Monthly_bill.objects.filter(student_id=temp.student_id, month=month_now, year=year_now,
                                           total_bill=total_bill):
                print("exists")
            else:
                Monthly_bill.objects.filter(student_id=temp.student_id, month=month_now, year=year_now). \
                    update(student_id=temp.student_id,
                           month=month_now,
                           year=year_now,
                           amount=amount_m,
                           rebate_amount=rebate_amount,
                           rebate_count=rebate_count,
                           nonveg_total_bill=nonveg_total_bill,
                           total_bill=total_bill
                           )
                # print("updated")
    else:
        monthly_bill_obj.save()
        # print("generate")
    # for temp in students:
    #     monthly_bill_obj = Monthly_bill(student_id=temp, month=month_now, year=year_now, amount=amount_m)
    #     if Monthly_bill.objects.filter(student_id=temp, month=month_now, year=year_now):
    #         print('exists')
    #     else:
    #         monthly_bill_obj.save()
    return JsonResponse(data)

    
class MenuPDF(View):

    def post(self, request, *args, **kwargs):
        user = request.user
        extra_info = ExtraInfo.objects.get(user=user)
        y = Menu.objects.all()

        if extra_info.user_type=='student':
            student = Student.objects.get(id=extra_info)
            mess_info = Messinfo.objects.get(student_id=student)
            mess_option = mess_info.mess_option
            context = {
                'menu': y,
                'mess_option': mess_option
            }
            if mess_option=='mess2':
                return render_to_pdf('messModule/menudownloadable2.html', context)
            else:
                return render_to_pdf('messModule/menudownloadable1.html', context)
        else:
            context = {
                'menu': y,
                'mess_option': 'mess2'
            }
            return render_to_pdf('messModule/menudownloadable2.html', context)
        # return HttpResponse(pdf, content_type='application/pdf')


class MenuPDF1(View):
    # This function is to generate the menu in pdf format (downloadable) for mess 1
    def post(self, request, *args, **kwargs):
        user = request.user
        extrainfo = ExtraInfo.objects.get(user=user)
        y = Menu.objects.all()
        context = {
            'menu': y,
            'mess_option': 'mess1'
        }
        return render_to_pdf('messModule/menudownloadable1.html', context)


