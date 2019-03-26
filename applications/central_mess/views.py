import datetime
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

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
        splrequest = Special_request.objects.all()
        feed = Feedback.objects.all()
        messinfo = Messinfo.objects.get(student_id=student)
        count = 0
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
def placeorder(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)

        stu = Messinfo.objects.get(student_id=student)
        if stu.mess_option == 'mess1':
            dish = Nonveg_menu.objects.get(
                                           dish=request.POST.get("dish"),
                                           order_interval=request.POST['interval'])
            order_interval = dish.order_interval
            order_date = datetime.now().date()
            nonveg_obj = Nonveg_data(student_id=student, order_date=order_date,
                                     order_interval=order_interval, dish=dish)
            nonveg_obj.save()
            return HttpResponseRedirect("/mess")

        else:
            return HttpResponse("you can't apply for this application")


@csrf_exempt
@login_required
@transaction.atomic
def submit(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        fdate = datetime.datetime.now().date()
        description = request.POST.get('description')
        feedback_type = request.POST.get('feedback_type')
        feedback_obj = Feedback(student_id=student, fdate=fdate,
                                description=description,
                                feedback_type=feedback_type)

        feedback_obj.save()
        data = {
            'status': 1
        }
        return JsonResponse(data)


@csrf_exempt
@login_required
@transaction.atomic
def vacasubmit(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        purpose = request.POST.get('purpose')
        vaca_obj = Vacation_food(student_id=student, start_date=start_date,
                                 end_date=end_date, purpose=purpose)

        vaca_obj.save()
        #return HttpResponseRedirect("/mess")
        data = {
             'status':1
         }

        return JsonResponse(data)


@login_required
@transaction.atomic
def menusubmit(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    for d in desig:

        if d.designation.name == 'mess_convener':

            dish = Menu.objects.get(dish=request.POST.get("dish"))
            newdish = request.POST.get("newdish")
            reason = request.POST.get("reason")
            app_obj = Menu_change_request(dish=dish, request=newdish, reason=reason)
            app_obj.save()
            return HttpResponseRedirect("/mess")

    return render(request, 'mess.html', context)


@login_required
def response(request, ap_id):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations

    for d in desig:
        if d.designation.name == 'mess_manager':
            application = Menu_change_request.objects.get(pk=ap_id)

            if(request.POST.get('submit') == 'approve'):
                application.status = 2
                meal = application.dish
                obj = Menu.objects.get(dish=meal.dish)
                obj.dish = application.request
                obj.save()

            elif(request.POST.get('submit') == 'reject'):
                application.status = 0

            else:
                application.status = 1

        application.save()

    return HttpResponseRedirect("/mess")


@login_required
def processvacafood(request, ap_id):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations

    for d in desig:
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
def regadd(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations

    for d in desig:
        if d.designation.name == 'mess_manager':

            sem = request.POST.get('sem')
            start_reg = request.POST.get('start_date')
            end_reg = request.POST.get('end_date')
            mess_reg_obj = Mess_reg(sem=sem, start_reg=start_reg, end_reg=end_reg)
            mess_reg_obj.save()

            return HttpResponseRedirect("/mess")


@transaction.atomic
@csrf_exempt
def leaverequest(request):
    flag = 1
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extrainfo)
    leave_type = request.POST.get('leave_type')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    purpose = request.POST.get('purpose')

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
            print((b <= a and (d >= a and d <= c)) or (b >= a and (d >= a and d <= c)) or (b <= a and (d >= c)) or ((b >= a and b<=c) and (d >= c)))
            print((b >= a and b<=c) and (d >= c))
            if ((b <= a and (d >= a and d <= c)) or (b >= a and (d >= a and d <= c)) or (b <= a and (d >= c)) or ((b >= a and b<=c) and (d >= c))):
                flag = 0
                break

    if flag == 1:
        rebate_obj = Rebate(student_id=student, leave_type=leave_type, start_date=start_date,
                                end_date=end_date, purpose=purpose)
        rebate_obj.save()

    data = {
            'status': flag,
    }


    return JsonResponse(data)


@login_required
@transaction.atomic
def minutes(request):
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


def responserebate(request, ap_id):
    leaves = Rebate.objects.get(pk=ap_id)

    if(request.POST.get('submit') == 'approve'):
        leaves.status = '2'

    else:
        leaves.status = '0'
    leaves.save()
    return HttpResponseRedirect("/mess")


def placerequest(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        print (request.POST)
        extrainfo = ExtraInfo.objects.get(user=user)
        student = Student.objects.get(id=extrainfo)
        fr = request.POST.get("start_date")
        to = request.POST.get("end_date")
        print (fr, to, "dates")
        food1 = request.POST.get("food1")
        food2 = request.POST.get("food2")
        purpose = request.POST.get("purpose")

        print ("Hello")
        spfood_obj = Special_request(student_id=student, start_date=fr, end_date=to,
                                     item1=food1, item2=food2, request=purpose)
        spfood_obj.save()
        data = {
             'status': 1,
        }
        return JsonResponse(data)


def responsespl(request, ap_id):
    sprequest = Special_request.objects.get(pk=ap_id)
    if(request.POST.get('submit') == 'approve'):
        sprequest.status = '2'
    else:
        sprequest.status = '0'

    sprequest.save()
    return HttpResponseRedirect("/mess")

def updatecost(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    cost = request.POST.get("newcost")

    monthlybill = Monthly_bill.objects.all()

    for temp in monthlybill:
        temp.amount = cost
        temp.save()

    return HttpResponseRedirect("/mess")
