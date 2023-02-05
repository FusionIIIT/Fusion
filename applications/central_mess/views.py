from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db import transaction
from threading import Thread
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.generic import View
from django.db.models import Count
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth.models import User
from .utils import render_to_pdf
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from .forms import MinuteForm, MessInfoForm
from .models import (Feedback, Menu, Menu_change_request, Mess_meeting,
                     Mess_minutes, Mess_reg, Messinfo, Monthly_bill,
                     Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food, MessBillBase)
from .handlers import (add_nonveg_order, add_mess_feedback, add_vacation_food_request,
                       add_menu_change_request, handle_menu_change_response, handle_vacation_food_request,
                       add_mess_registration_time, add_leave_request, add_mess_meeting_invitation,
                       handle_rebate_response, add_special_food_request,
                       handle_special_request, add_bill_base_amount, add_mess_committee, generate_bill)
from notification.views import central_mess_notif


today_g = datetime.today()
month_g = today_g.month
month_g_l = today_g.strftime('%B')
year_g = today_g.year
tomorrow_g = today_g + timedelta(days=1)
first_day_of_this_month = date.today().replace(day=1)
first_day_of_next_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1)
last_day_of_this_month = first_day_of_next_month - timedelta(days=1)
next_month = first_day_of_next_month.month
last_day_prev_month = first_day_of_this_month - timedelta(days=1)
month_last_g = last_day_prev_month.month
year_last_g = last_day_prev_month.year
previous_month = last_day_prev_month.strftime('%B')


def mess(request):
    """
    This view get the access to the central mess dashboard. View all details and apply for any changes.
    It also shows the previous feedback submitted by the user.
    """
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    current_date = date.today()
    holds_designations = HoldsDesignation.objects.select_related().filter(user=user)
    desig = holds_designations
    form = MinuteForm()
    mess_reg = Mess_reg.objects.select_related().last()
    count1 = 0
    count2 = 0
    count3 = 0
    count4 = 0
    count5 = 0
    count6 = 0
    count7 = 0
    count8 = 0

    if extrainfo.user_type == 'student':
        student = Student.objects.select_related('id','id__user','id__department').get(id=extrainfo)
        vaca_obj = Vacation_food.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student)
        feedback_obj = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student).order_by('-fdate')
        data = Nonveg_data.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(student_id=student).order_by('-app_date')
        monthly_bill = Monthly_bill.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student)
        payments = Payments.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student)
        rebates = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student).order_by('-app_date')
        splrequest = Special_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student).order_by('-app_date') 
        try:
            mess_optn = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
        except:
            return HttpResponseRedirect("/mess/info-form")
        
        if student.programme == 'B.Tech' or student.programme == 'B.Des':
            programme = 1
        else:
            programme = 0
        # newmenu = Menu_change_request.objects.all()
        # meeting = Mess_meeting.objects.all()
        # minutes = Mess_minutes.objects.all()
        # feed = Feedback.objects.all()
        # sprequest = Special_request.objects.filter(status='1')
        count = 0
        #variable y stores the menu items

        y = Menu.objects.filter(mess_option=mess_optn.mess_option)
        x = Nonveg_menu.objects.all()

        # for item in rebates:
        #     d1 = item.start_date
        #     d2 = item.end_date
        #     item.duration = abs((d2 - d1).days)+1
        #     item.save()

        # for items in rebates:
        #     if items.leave_type == 'casual' and (items.status == '1' or items.status == '2'):
        #         count += item.duration

        bill = Monthly_bill.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(Q(student_id=student) & Q(month=month_g_l) & Q(year=year_g))
        amount_c = MessBillBase.objects.latest('timestamp')
        rebate_count = 0
        nonveg_total_bill = 0
        for z in data:
            if z.order_date.month == month_g:
                nonveg_total_bill = nonveg_total_bill + z.dish.price

            else:
                bill.nonveg_total_bill = 0

        for r in rebates:
            if r.status == '2':
                if r.start_date.month == month_g:
                    if r.end_date.month == next_month:
                        rebate_count = rebate_count + abs((last_day_of_this_month - r.start_date).days) + 1
                    else:
                        rebate_count = rebate_count + abs((r.end_date - r.start_date).days) + 1
                elif r.end_date.month == month_g:
                    rebate_count = rebate_count + abs((r.end_date - first_day_of_this_month).days) + 1
                else:
                    rebate_count = 0
        rebate_amount = rebate_count * amount_c.bill_amount / 30
        total_bill = amount_c.bill_amount - rebate_amount + nonveg_total_bill
        if bill:
            bill.update(student_id = student,
                        month = month_g_l,
                        year = year_g,
                        amount = amount_c.bill_amount,
                        rebate_count = rebate_count,
                        rebate_amount = rebate_amount,
                        nonveg_total_bill=nonveg_total_bill,
                        total_bill = total_bill)

        else:
            bill_object = Monthly_bill(student_id=student,
                                       amount=amount_c.bill_amount,
                                       rebate_count=rebate_count,
                                       rebate_amount=rebate_amount,
                                       nonveg_total_bill=nonveg_total_bill,
                                       total_bill=total_bill,
                                       month=month_g_l,
                                       year=year_g)
            bill_object.save()

        for d in desig:
            if d.designation.name == 'mess_committee_mess1' or d.designation.name == 'mess_convener_mess1':
                newmenu = Menu_change_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(dish__mess_option='mess1').order_by('-app_date')
                # newmenu = Menu_change_request.objects.all()
                meeting = Mess_meeting.objects.all()
                minutes = Mess_minutes.objects.select_related().all()
                feed = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(mess='mess1').order_by('-fdate')
                feed2 = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(mess='mess2').order_by('-fdate')
                sprequest = Special_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='1').order_by('-app_date')
                sprequest_past = Special_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='2').order_by('-app_date')
                # count1 = feed.filter(Q(feedback_type='Maintenance') & Q(mess='mess1')).count()
                for f in feed:
                    if f.feedback_type == 'Maintenance' and mess_optn.mess_option == 'mess1':
                        count1 += 1

                    elif f.feedback_type == 'Food' and mess_optn.mess_option == 'mess1':
                        count2 += 1

                    elif f.feedback_type == 'Cleanliness' and mess_optn.mess_option == 'mess1':
                        count3 += 1

                    elif f.feedback_type == 'Others' and mess_optn.mess_option == 'mess1':
                        count4 += 1
                for f in feed2:
                    if f.feedback_type == 'Maintenance' and mess_optn.mess_option == 'mess2':
                        count5 += 1

                    elif f.feedback_type == 'Food' and mess_optn.mess_option == 'mess2':
                        count6 += 1

                    elif f.feedback_type == 'Cleanliness' and mess_optn.mess_option == 'mess2':
                        count7 += 1

                    elif f.feedback_type == 'Others' and mess_optn.mess_option == 'mess2':
                        count8 += 1

                context = {
                    'menu': y,
                    'messinfo': mess_optn,
                    'newmenu': newmenu,
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
                    'sprequest_past': sprequest_past,
                    'programme':programme,
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

            if d.designation.name == 'mess_committee_mess2' or d.designation.name == 'mess_convener_mess2':
                # newmenu = Menu_change_request.objects.all()
                newmenu = Menu_change_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(dish__mess_option='mess2').order_by('-app_date')
                meeting = Mess_meeting.objects.all()
                minutes = Mess_minutes.objects.select_related().all()
                feed = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(mess='mess2').order_by('-fdate')
                feed2 = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(mess='mess1').order_by('-fdate')
                sprequest = Special_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='1').order_by('-app_date')
                sprequest_past = Special_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='2').order_by('-app_date')
                # count5 = feed.filter(Q(feedback_type='Maintenance') & Q(mess='mess2')).count()
                for f in feed2:
                    if f.feedback_type == 'Maintenance' and mess_optn.mess_option == 'mess1':
                        count1 += 1

                    elif f.feedback_type == 'Food' and mess_optn.mess_option == 'mess1':
                        count2 += 1

                    elif f.feedback_type == 'Cleanliness' and mess_optn.mess_option == 'mess1':
                        count3 += 1

                    elif f.feedback_type == 'Others' and mess_optn.mess_option == 'mess1':
                        count4 += 1
                for f in feed:
                    if f.feedback_type == 'Maintenance' and mess_optn.mess_option == 'mess2':
                        count5 += 1

                    elif f.feedback_type == 'Food' and mess_optn.mess_option == 'mess2':
                        count6 += 1

                    elif f.feedback_type == 'Cleanliness' and mess_optn.mess_option == 'mess2':
                        count7 += 1

                    elif f.feedback_type == 'Others' and mess_optn.mess_option == 'mess2':
                        count8 += 1

                context = {
                    'menu': y,
                    'messinfo': mess_optn,
                    'newmenu': newmenu,
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
                    'programme': programme,
                    'meeting': meeting,
                    'minutes': minutes,
                    'sprequest': sprequest,
                    'splrequest': splrequest,
                    'sprequest_past': sprequest_past,
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

        context = {
                   'menu': y,
                   'messinfo': mess_optn,
                   'monthly_bill': monthly_bill,
                   'payments': payments,
                   'nonveg': x,
                   'vaca': vaca_obj,
                   'info': extrainfo,
                   'feedback': feedback_obj,
                   'student': student,
                   'data': data,
                   'mess_reg': mess_reg,
                   'current_date': current_date,
                   'count': count,
                   'rebates': rebates,
                   'splrequest': splrequest,
                   'form': form,
                   'programme': programme,
                   'desig': desig
            }

        return render(request, "messModule/mess.html", context)

    elif extrainfo.user_type == 'staff':
        current_bill = MessBillBase.objects.latest('timestamp')
        nonveg_orders_today = Nonveg_data.objects.filter(order_date=today_g)\
            .values('dish__dish','order_interval').annotate(total=Count('dish'))
        nonveg_orders_tomorrow = Nonveg_data.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(order_date=tomorrow_g)\
            .values('dish__dish','order_interval').annotate(total=Count('dish'))
        # make info with diff name and then pass context
        newmenu = Menu_change_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').all().order_by('-app_date')
        vaca_all = Vacation_food.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').all().order_by('-app_date')
        # members_mess = HoldsDesignation.objects.filter(designation__name='mess_convener')
        members_mess = HoldsDesignation.objects.select_related().filter(Q(designation__name__contains='mess_convener')
                                                       | Q(designation__name__contains='mess_committee'))
        y = Menu.objects.all()
        x = Nonveg_menu.objects.all()
        leave = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='1').order_by('-app_date')
        leave_past = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(status='2').order_by('-app_date')

        context = {
                   'bill_base': current_bill,
                   'today': today_g.date(),
                   'tomorrow': tomorrow_g.date(),
                   'nonveg_orders_t':nonveg_orders_tomorrow,
                   'nonveg_orders': nonveg_orders_today,
                   'members': members_mess,
                   'menu': y,
                   'newmenu': newmenu,
                   'vaca_all': vaca_all,
                   'info': extrainfo,
                   'leave': leave,
                   'leave_past': leave_past,
                   'current_date': current_date,
                   'mess_reg': mess_reg,
                   'desig': desig,
        }

        return render(request, "messModule/mess.html", context)

    elif extrainfo.user_type == 'faculty':
        meeting = Mess_meeting.objects.all()
        minutes = Mess_minutes.objects.select_related().all()
        feed = Feedback.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').all().order_by('-fdate')
        y = Menu.objects.all()

        for f in feed:
            mess_opt = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess1':
                count1 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess1':
                count2 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess1':
                count3 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess1':
                count4 += 1

        for f in feed:
            mess_opt = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=f.student_id)
            if f.feedback_type == 'Maintenance' and mess_opt.mess_option == 'mess2':
                count5 += 1

            elif f.feedback_type == 'Food' and mess_opt.mess_option == 'mess2':
                count6 += 1

            elif f.feedback_type == 'Cleanliness' and mess_opt.mess_option == 'mess2':
                count7 += 1

            elif f.feedback_type == 'Others' and mess_opt.mess_option == 'mess2':
                count8 += 1
        context = {
             'info': extrainfo,
             'menu': y,
             'meeting': meeting,
             'minutes': minutes,
             'count1': count1,
             'count2': count2, 'count3': count3, 'feed': feed,
             'count4': count4, 'form': form, 'count5': count5,
             'count6': count6, 'count7': count7, 'count8': count8, 'desig': desig
        }
        return render(request, 'messModule/mess.html', context)

@login_required
@transaction.atomic
def mess_info(request):
    """
    Register someone in mess 1 or mess 2

    @params:
        request: contains metadata about the requested page

    @variables:
        user_id: user id of the current user
        student_id: Student Object of given user_id
        mess_option: requested mess : {"mess1" || "mess2"}
    """
    if (request.method == "POST"):
        user_id = request.user
        student_id = Student.objects.select_related('id').only('id__id').get(id__id=user_id)
        form = MessInfoForm(request.POST)
        if form.is_valid():
            mess_option =  form.cleaned_data['mess_option']
            Messinfo.objects.create(student_id=student_id, mess_option=mess_option)
        return HttpResponseRedirect("/mess")

    form = MessInfoForm()
    context = {
        "form": form
    }
    return render(request, "messModule/messInfoForm.html", context)

@login_required
@transaction.atomic
@csrf_exempt
def place_order(request):
    """
    This function is to place non-veg food orders

    @param:
        request: contains metadata about the requested page
    
    @variables:
        user: Current user
        order_interval: Time of the day for which order is placed eg breakfast/lunch/dinner
        extra_info: Extra information about the current user. From model ExtraInfo
        student: Student information about the current user
        student_mess: Mess choices of the student
        dish_request: Predefined dish available
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    if extra_info.user_type == 'student':
        student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)
        student_mess = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
        add_nonveg_order(request, student)
        return HttpResponseRedirect('/mess')


@csrf_exempt
@login_required
@transaction.atomic
def submit_mess_feedback(request):
    """
    This function is to record the feedback submitted

    @param:
        request: contains metadata about the requested page

    @variable:
        user: Current logged in user
        extra_info: Extra information of the user

    @return:
        data: to record success or any errors
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)
    if extra_info.user_type == 'student':
        data = add_mess_feedback(request, student)
        central_mess_notif(request.user, request.user, 'feedback_submitted')
        return JsonResponse(data)


@csrf_exempt
@login_required
@transaction.atomic
def mess_vacation_submit(request):
    """
    This function is to record vacation food requests

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        extra_info: Extra information of the user
        student: Student information about the current user

    @return:
        data: JsonResponse
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)

    if extra_info.user_type == 'student':
        data = add_vacation_food_request(request, student)
        return JsonResponse(data)


@login_required
@transaction.atomic
def submit_mess_menu(request):
    """
    This function is to record mess menu change requests by the  mess_committee

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        holds_designations: designation of current user
        extrainfo: Extra information of the user
        student: Student information about the current user
    """
    # TODO add ajax for this
    user = request.user
    holds_designations = HoldsDesignation.objects.select_related().filter(user=user)
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    designation = holds_designations
    student = Student.objects.select_related('id','id__user','id__department').get(id=extrainfo)
    # globallyChange()
    context = {}
    # A user may hold multiple designations

    data = add_menu_change_request(request,student)
    if data['status'] == 1:
        return HttpResponseRedirect("/mess")

    return render(request, 'messModule/mess.html', context)


@login_required
def menu_change_response(request):
    """
    This function is to respond to mess menu requests

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        holds_designations: designation of current user
    """
    user = request.user
    holds_designations = HoldsDesignation.objects.select_related().filter(user=user)

    designation = holds_designations
    data = handle_menu_change_response(request)
    return JsonResponse(data)


@login_required
def response_vacation_food(request, ap_id):
    """
    This function records the response to vacation food requests

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        holds_designations: designation of current user
    """
    user = request.user
    # extra_info = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.select_related().filter(user=user)
    designation = holds_designations

    for d in designation:
        if d.designation.name == 'mess_manager':
            data = handle_vacation_food_request(request, ap_id)
    return HttpResponseRedirect("/mess")


@login_required
@transaction.atomic
def regsubmit(request):
    """
    This function ise used to change mess option

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        extrainfo: Extra information of the user
        student: Student information about the current user
        mess_info_inst: MessInfo Object of the current user
        monthly_bill_obj: Monthly_bill Object of the current user
        mess_monthly_bill: monthly bill of each month of a semester
    """
    i = 0
    j = 0
    month_1 = ['January', 'February', 'March', 'April', 'May', 'June']
    month_2 = ['July', 'August', 'September', 'October', 'November', 'December']
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)

    if extrainfo.user_type == 'student':
        student = Student.objects.select_related('id','id__user','id__department').get(id=extrainfo)
        mess = request.POST.get('mess_type')
        mess_info_inst = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
        mess_info_inst.mess_option = mess
        mess_info_inst.save()
        mess_reg = Mess_reg.objects.last()

        if Monthly_bill.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student):
            return HttpResponseRedirect("/mess")

        else:

            if mess_reg.end_reg.strftime("%B") in month_1:
                mess_monthly_bill = []
                while i<=5:
                    monthly_bill_obj = Monthly_bill(student_id=student, month=month_1[i], year=year_last_g)
                    mess_monthly_bill.append(monthly_bill_obj)
                    i = i+1
                Monthly_bill.objects.bulk_create(mess_monthly_bill)

            else:
                mess_monthly_bill = []
                while j<=5:
                    monthly_bill_obj = Monthly_bill(student_id=student, month=month_2[j], year=year_last_g)
                    mess_monthly_bill.append(monthly_bill_obj)
                    j = j+1
                Monthly_bill.objects.bulk_create(mess_monthly_bill)

        return HttpResponseRedirect("/mess")

    else:
        return redirect('mess')


@login_required
@transaction.atomic
def start_mess_registration(request):
    """
    This function is to start mess registration

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        designation: designation of current user to validate proper platform
    """
    #   TODO ajax convert add a section to see previous sessions as well as close a session
    user = request.user
    designation = HoldsDesignation.objects.select_related().filter(user=user)
    for d in designation:
        if d.designation.name == 'mess_manager':
            data = add_mess_registration_time(request)
            return JsonResponse(data)


@transaction.atomic
@csrf_exempt
def mess_leave_request(request):
    """
    This function is to record and validate leave requests

    @param
        request: contains metadata about the requested page

    @variables:
        user: Current user information
        extra_info: Extra information of the user
        student: Student information about the current user
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)
    data = add_leave_request(request, student)
    return JsonResponse(data)


@login_required
@transaction.atomic
def minutes(request):
    """
    This function is used to upload the minutes of the meeting

    @param
        request: contains metadata about the requested page

    @variables:
        form: MinuteForm Object to create minutes of the meeting
    """
    if request.method == 'POST' and request.FILES:
        form = MinuteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/mess')
        else:
            return HttpResponseRedirect('/mess')


@csrf_exempt
@transaction.atomic
def invitation(request):
    """
    This function is to schedule a mess committee meeting

    @param
        request: contains metadata about the requested page
    """
    # todo add ajax to this page as well
    data = add_mess_meeting_invitation(request)
    # return HttpResponseRedirect("/mess")
    return JsonResponse(data)


@login_required
@transaction.atomic
@csrf_exempt
def rebate_response(request):
    """
    This function is to respond to rebate requests

    @param request: 
        request - contains metadata about the requested page 

    @variables: 
        user: Current user details
        designation : designation of the user

    @return:
        data: returns the status of the application
    """
    data = {
        'status': 1
    }
    user = request.user
    designation = HoldsDesignation.objects.select_related().filter(user=user)

    for d in designation:
        if d.designation.name == 'mess_manager':
            data = handle_rebate_response(request)
    return JsonResponse(data)


@login_required
@transaction.atomic
@csrf_exempt
def place_request(request):
    """
        This function is to place special food requests ( used by students )
        
        @params:
            request - contains metadata about the requested page 

        @variables:
            user: Current user details
        
        @return:
            data['status']: returns status of the application
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    if extra_info.user_type == 'student':
        extra_info = ExtraInfo.objects.select_related().get(user=user)
        student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)
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
    
    @param:
        request - contains metadata about the requested page 

    @variables:  
        user - contains user details
    """
    user = request.user
    # extrainfo = ExtraInfo.objects.get(user=user)
    data = add_bill_base_amount(request)
    return JsonResponse(data)


def generate_mess_bill(request):
    """
    This function is to generate the bill of the students

    @param:
        request - contains metadata about the requested page 

    @variables:
        user: stores current user information
        nonveg_data : stores records of non-veg ordered by a student
        year_now: current year
        month_now: current month
        amount_m: monhly base amount
        students: information of all students
        mess_info: Mess Information, mainly choice of mess
        rebates: Rebate records of students
    """
    # todo generate proper logic for generate_mess_bill
    user = request.user
    t1 = Thread(target=generate_bill, args=())
    t1.setDaemon(True)
    t1.start()
    # int = generate_bill()
    data ={
        'status': 1
    }
    return JsonResponse(data)

    
class MenuPDF(View):

    def post(self, request, *args, **kwargs):
        user = request.user
        extra_info = ExtraInfo.objects.select_related().get(user=user)
        y = Menu.objects.all()

        if extra_info.user_type=='student':
            student = Student.objects.select_related('id','id__user','id__department').get(id=extra_info)
            mess_info = Messinfo.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
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
    """
    This function is to generate the menu in pdf format (downloadable) for mess 1

    @param:
        request - contains metadata about the requested page 

    @variables:
        current_user - get user from request
        user_details - extract details of the user from the database
    """
    def post(self, request, *args, **kwargs):
        user = request.user
        # extrainfo = ExtraInfo.objects.get(user=user)
        y = Menu.objects.all()
        context = {
            'menu': y,
            'mess_option': 'mess1'
        }
        return render_to_pdf('messModule/menudownloadable1.html', context)


def menu_change_request(request):
    """
    This function is to request a change in menu

    @param:
        request - contains metadata about the requested page 

    @variables:
        current_user - get user from request
        user_details - extract details and designation of the user from the database
        new_menu - the new menu to replace the previous menu
    """
    newmenu = Menu_change_request.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(status=2)
    data = model_to_dict(newmenu)
    return JsonResponse(data)


def submit_mess_committee(request):
    """
    This function is to add the new mess committee

    @param:
        request - contains metadata about the requested page 

    @variables:
        current_user - get user from request
        user_details - extract details and designation of the user from the database
    """
    roll_number = request.POST['rollnumber']

    data = add_mess_committee(request, roll_number)
    return JsonResponse(data)


def remove_mess_committee(request):
    """
    This function is to remove the current mess committee

    @param:
        request - contains metadata about the requested page 

    @variables:
        current_user - get user from request
        user_details - extract details and designation of the user from the database

    """
    member_id = request.POST['member_id']
    data_m = member_id.split("-")
    roll_number = data_m[1]
    if data_m[0] == 'mess_committee_mess1':
        designation = Designation.objects.get(name='mess_committee_mess1')
    elif data_m[0] == 'mess_convener_mess1':
        designation = Designation.objects.get(name='mess_convener_mess1')
    elif data_m[0] == 'mess_committee_mess2':
        designation = Designation.objects.get(name='mess_committee_mess2')
    else:
        designation = Designation.objects.get(name='mess_convener_mess2')
    remove_object = HoldsDesignation.objects.select_related().get(Q(user__username=roll_number) & Q(designation=designation))
    remove_object.delete()
    data = {
        'status': 1,
        'message': 'Successfully removed '
    }
    return JsonResponse(data)


def get_leave_data(request):
    leave_data = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(Q(start_date__lte=today_g)&Q(end_date__gte=today_g)).count()
    leave_data_t = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(Q(start_date__lte=tomorrow_g)&Q(end_date__gte=tomorrow_g)).count()
    data = {
        'status': 1,
        'message': 'HI I AM WORKING',
        'today': today_g.date(),
        'tomorrow': tomorrow_g.date(),
        'counttoday': leave_data,
        'counttomorrow':leave_data_t
    }
    return JsonResponse(data)


def accept_vacation_leaves(request):
    """
    This function is to accept vacation leave request

    @param:
        request - contains metadata about the requested page 
        request - details about leave

    @variables:
        current_user - get user from request
        user_details - extract details and designation of the user from the database
        start_date_leave - Starting date of leave
        end_date_leave - Ending date of leave
    """
    start_date_leave = request.GET['start_date']
    end_date_leave = request.GET['end_date']
    leave_data = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(Q(start_date__gte=start_date_leave)
                                       &Q(end_date__lte=end_date_leave)
                                       &Q(leave_type="vacation")
                                       &Q(status='1'))

    if leave_data:
        for item in leave_data:
            item.status = '2'
            item.save()

    data = {
        'status': 1,
        'display': 'Vacation Leaves Successfully Accepted'
    }
    return JsonResponse(data)


def select_mess_convener(request):
    """
    This function is to select a new convenor for mess

    @param:
        request - contains metadata about the requested page 
        
    @variables:
        current_user - get user from request
        user_details - extract details and designation of the user from the database
        designation - to get the designation of the user
        first_day_of_the_month - first day of the month
        last_day_of_the_month - last day of the month
        previous_month - last month
        bill_object - accessing the bill from Monthly bills
    """
    member_id = request.POST['member_id_add']
    data_m = member_id.split("-")
    roll_number = data_m[1]

    if data_m[0] == 'mess_committee_mess1':
        designation = Designation.objects.get(name='mess_committee_mess1')
        new_designation = Designation.objects.get(name='mess_convener_mess1')
        # One mess can have only one mess convener
        existing_check = HoldsDesignation.objects.select_related().filter(designation=new_designation)
        if existing_check.count():
            data = {
                'status': 1,
                'message': 'Mess Convener already exists for Mess 1 ! \nRemove the existing convener to add new one'
            }
            return JsonResponse(data)
        else:
            modify_object = HoldsDesignation.objects.select_related().get(Q(user__username=roll_number) & Q(designation=designation))
            modify_object.designation = new_designation
            modify_object.save()
    else:
        designation = Designation.objects.get(name='mess_committee_mess2')
        new_designation = Designation.objects.get(name='mess_convener_mess2')
        existing_check = HoldsDesignation.objects.select_related().filter(designation=new_designation)
        if existing_check.count():
            data = {
                'status': 1,
                'message': 'Mess Convener already exists for Mess 2 ! \n Remove the existing convener to add new one'
            }
            return JsonResponse(data)
        else:
            modify_object = HoldsDesignation.objects.select_related().get(Q(user__username=roll_number) & Q(designation=designation))
            modify_object.designation = new_designation
            modify_object.save()

    data = {
        'status': 1,
        'message': 'Successfully added as mess convener ! '
    }
    return JsonResponse(data)


def download_bill_mess(request):
    """
    This function is to get the mess bill for current month

    @param:
        request - contains metadata about the requested page 
        request - first day of the month and last day of the previous month

    @variables:
        current_user - get user from request
        user_details - extract details of the user from the database
        first_day_of_the_month - first day of the month
        last_day_of_the_month - last day of the month
        previous_month - last month
        bill_object - accessing the bill from Monthly bills
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)
    first_day_of_this_month = date.today().replace(day=1)
    last_day_prev_month = first_day_of_this_month - timedelta(days=1)
    previous_month = last_day_prev_month.strftime('%B')
    bill_object = Monthly_bill.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(Q(month=previous_month)&Q(year=year_last_g))
    # bill_object = Monthly_bill.objects.all()

    context = {
        'bill': bill_object,
    }
    return render_to_pdf('messModule/billpdfexport.html', context)


def get_nonveg_order(request):
    """
    This function is to apply for non-veg order

    @param:
        request - contains metadata about the requested page 

    @variables:
        current_user - get user from request
        user_details - extract details of the user from the database
    """
    date_o = request.POST['order_date']
    nonveg_orders_tomorrow = Nonveg_data.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','dish').filter(order_date=date_o) \
        .values('dish__dish', 'order_interval').annotate(total=Count('dish'))
    data = {
        'status': 1,
    }
    return JsonResponse(data)


def add_leave_manager(request):
    """
    This function is to apply for leave

    @param:
        request - contains metadata about the requested page 
        request - start date, end date and type of leave

    @variables:
        current_user - get user from request
        user_details - extract details of the user from the database
        start_date - starting date of the leave
        end_data - ending date of leave
        type - type of leave
    """
    flag = 1
    start_date = request.POST.get('l_startd')
    end_date = request.POST.get('l_endd')
    roll_number = request.POST.get('l_rollno')
    type = request.POST.get('l_type')
    purpose = request.POST.get('l_purpose')
    student = Student.objects.select_related('id','id__user','id__department').get(id__id=roll_number)
    add_obj = Rebate(student_id = student,
                     start_date = start_date,
                     end_date = end_date,
                     purpose = purpose,
                     status='2',
                     leave_type=type)

    if (end_date < start_date):
        data = {
            'status': 3,
            'message': "Please check the dates"
        }
        flag = 0
        return HttpResponse('Check the dates')

    date_format = "%Y-%m-%d"
    b = datetime.strptime(str(start_date), date_format)
    d = datetime.strptime(str(end_date), date_format)

    rebates = Rebate.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=student)
    rebate_check = rebates.filter(status='2')

    for r in rebate_check:
        a = datetime.strptime(str(r.start_date), date_format)
        c = datetime.strptime(str(r.end_date), date_format)
        if ((b <= a and (d >= a and d <= c)) or (b >= a and (d >= a and d <= c))
                or (b <= a and (d >= c)) or ((b >= a and b <= c) and (d >= c))):
            flag = 0
            data = {
                'status': 3,
                'message': "Already applied for these dates",
            }
            return HttpResponse('You are seeing this page : As the leave has been applied for these days already')
    if flag == 1:
        message = 'Your leave request has been accepted between dates ' + str(b.date()) + ' and ' + str(d.date())
        central_mess_notif(request.user, student.id.user, 'leave_request', message)
        add_obj.save()
    return HttpResponseRedirect('/mess')
