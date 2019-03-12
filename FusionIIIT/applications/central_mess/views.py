from datetime import date, datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.generic import View
from django.core import serializers
from django.forms.models import model_to_dict
from applications.central_mess.utils import render_to_pdf
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation
from .forms import MinuteForm
from .models import (Feedback, Menu, Menu_change_request, Mess_meeting,
                     Mess_minutes, Mess_reg, Messinfo, Monthly_bill,
                     Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food)
from .handlers import (add_nonveg_order, add_mess_feedback, add_vacation_food_request,
                       add_menu_change_request, handle_menu_change_response, handle_vacation_food_request,
                       add_mess_registration_time, add_leave_request, add_mess_meeting_invitation,
                       handle_rebate_response, add_special_food_request,
                       handle_special_request, add_bill_base_amount)


def mess(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    current_date = date.today()
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    print(desig)
    form = MinuteForm()
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
        mess_optn = Messinfo.objects.get(student_id=student)
        y = Menu.objects.filter(mess_option=mess_optn.mess_option)
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
        # context = {
        #            'menu': y,
        #            'vaca_all': vaca_all,
        #            'info': extrainfo,
        #            'leave': leave,
        #            'current_date': current_date,
        #            'mess_reg': mess_reg,
        #            'desig': desig,
        # }
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
            add_nonveg_order(request, student)
            return HttpResponseRedirect('/mess')
        elif student_mess.mess_option == 'mess2':
            messages.info(request,"You cannot apply for non veg food")
        else:
            return HttpResponse("you can't apply for this application sorry for the inconvenience")


@csrf_exempt
@login_required
@transaction.atomic
def submit_mess_feedback(request):
    """
    This function is to record the feedback submitted
    :param request:
        user: Current logged in user
    :variable:
         extra_info: Extra information of the user
    :return:
        data: to record success or any errors
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extra_info)
    if extra_info.user_type == 'student':
        data = add_mess_feedback(request, student)
        return JsonResponse(data)


@csrf_exempt
@login_required
@transaction.atomic
def mess_vacation_submit(request):
    """
    This function is to record vacation food requests
    :param request:
        user: Current user information
    :variables:
    :return:
        data: JsonResponse
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extra_info)
    if extra_info.user_type == 'student':
        data = add_vacation_food_request(request, student)
        return JsonResponse(data)


@login_required
@transaction.atomic
def submit_mess_menu(request):
    """
    This function is to record mess menu change requests
    :param request:
        user:Current user
    :return:
    """
    # TODO add ajax for this
    user = request.user
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations
    context = {}
    # A user may hold multiple designations
    for d in designation:
        if d.designation.name == 'mess_convener':
            data = add_menu_change_request(request)
            if data['status'] == 1:
                return HttpResponseRedirect("/mess")

    return render(request, 'mess.html', context)


@login_required
def menu_change_response(request):
    """
    This function is to respond to mess menu requests
    :param request:
        user: Current user
    :return:
    """
    user = request.user
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations
    for d in designation:
        if d.designation.name == 'mess_manager':
           data = handle_menu_change_response(request)
        return JsonResponse(data)


@login_required
def response_vacation_food(request, ap_id):
    """
    This function records the response to vacation food requests
    :param request:
        user: Current user
    :param ap_id:
    :variables:
        holds_designations: Designation of the current user
    :return:
    """
    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    designation = holds_designations

    for d in designation:
        if d.designation.name == 'mess_manager':
            data = handle_vacation_food_request(request, ap_id)
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
           designation: designation of current user to validate proper platform
    """
    #   TODO ajax convert add a section to see previous sessions as well as close a session
    user = request.user
    designation = HoldsDesignation.objects.filter(user=user)
    for d in designation:
        if d.designation.name == 'mess_manager':
            data = add_mess_registration_time(request)
            return HttpResponseRedirect("/mess")


@transaction.atomic
@csrf_exempt
def mess_leave_request(request):
    """
        This function is to record and validate leave requests
        @request:
            user: Current user
        @variables:
            student: Information od student submitting the request
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extra_info)
    data = add_leave_request(request, student)
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
       @variables:
    """
    # todo add ajax to this page as well
    data = add_mess_meeting_invitation(request)
    return HttpResponseRedirect("/mess")


@login_required
@transaction.atomic
@csrf_exempt
def rebate_response(request):
    """
       This function is to respond to rebate requests
       :param request: user: Current user
       @variables: designation : designation of the user
       @return:
            data: returns the status of the application
    """
    user = request.user
    designation = HoldsDesignation.objects.filter(user=user)
    for d in designation:
        if d.designation.name == 'mess_manager':
            data = handle_rebate_response(request)
    return JsonResponse(data)


@login_required
@transaction.atomic
@csrf_exempt
def place_request(request):
    # This is for placing special food request
    """
        This function is to place special food requests ( used by students )
        @variables:
        user: Current user
        @return:
        data['status']: returns status of the application
    """
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    if extra_info.user_type == 'student':
        extra_info = ExtraInfo.objects.get(user=user)
        student = Student.objects.get(id=extra_info)
        data = add_special_food_request(request, student)
        return JsonResponse(data)


@login_required
@transaction.atomic
@csrf_exempt
def special_request_response(request):
    """
       This function is to respond to special request for food submitted by students
       data: message regarding the request
    """
    data = handle_special_request(request)
    return JsonResponse(data)


@login_required
@transaction.atomic
@csrf_exempt
def update_cost(request):
    """
    This function is to update the base cost of the monthly central mess bill
    :param request:
    :return:
    """
    user = request.user
    # extrainfo = ExtraInfo.objects.get(user=user)
    data = add_bill_base_amount(request)
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
    # todo generate proper logic for generate_mess_bill
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
                print("ok")
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
    else:
        monthly_bill_obj.save()
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


def menu_change_request(request):
    user = request.user
    # holds_designations = HoldsDesignation.objects.filter(user=user)
    newmenu = Menu_change_request.objects.filter(status=2)
    # extrainfo = ExtraInfo.objects.get(user=user)
    # current_date = date.today()
    data = model_to_dict(newmenu)
    # json_models = serializers.serialize("json", newmenu)
    # data = {
    #     'newmenu': model_data,
    # }
    return JsonResponse(data)
    # return HttpResponse("hi")
    # return HttpResponse(model_data,
    #                     mimetype='application/json')
    # return HttpResponse(simplejson.dumps(data),
    #                     mimetype='application/json')
    # return JsonResponse(data)
    # return render(request, "messModule/respondmenu.html", context)
