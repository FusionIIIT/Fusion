# # import datetime
# from celery.task.schedules import crontab
# from celery.schedules import crontab
# from celery import Celery
# from django_celery_beat.models import CrontabSchedule, PeriodicTask
# # from celery.decorators import task
# # from celery.utils.log import get_task_logger
# # from datetime import datetime
# from celery.task.schedules import crontab
# from celery.decorators import periodic_task
#
#
# app = Celery('tasks', broker='pyamqp://guest@localhost//')
# # disable coordinated universal time. Runs on local time
# app.conf.enable_utc = False
#
#
# @periodic_task(run_every=(crontab(minute='*/1')), name="some_task", ignore_result=True)
# def some_task():
#     print("5")

from datetime import date, datetime, timedelta
from django.db import transaction
from threading import Thread
from .models import *
from notification.views import central_mess_notif

today_g = date.today()
year_g = today_g.year
tomorrow_g = today_g + timedelta(days=1)
first_day_of_this_month = date.today().replace(day=1)
this_month = first_day_of_this_month.strftime('%B')
this_year = first_day_of_this_month.year
last_day_prev_month = first_day_of_this_month - timedelta(days=1)
previous_month = last_day_prev_month.strftime('%B')
previous_month_year = last_day_prev_month.year
first_day_of_next_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1)
last_day_of_this_month = first_day_of_next_month - timedelta(days=1)
next_month = first_day_of_next_month.month
first_day_prev_month = last_day_prev_month.replace(day=1)


def generate_bill():
    print(today_g)
    print(this_month)
    print(previous_month)
    
    t1 = Thread(target=generate_per_day_bill(), args=())
    t1.setDaemon(True)
    t1.start()
    
    
    
    
def check_registration(student):
    try:
        reg_date = Reg_records.objects.filter(student_id = student).latest('start_date')
        if(reg_date.start_date == today_g):
            try:
                reg_object = Reg_main.objects.get(student_id = student)
                reg_object.current_mess_status = "Registered"
            except:
                pass
    except: 
        pass 
    
    
    

def check_deregistration(student):
    try:
        reg_end_date = Reg_records.objects.filter(student_id = student).latest('start_date')
        if(reg_end_date.end_date == today_g):
            try:
                reg_object = Reg_main.objects.get(student_id = student)
                reg_object.current_mess_status = "Deregistered"
                reg_object.save()
            except:
                pass
    except:
        pass 



def check_next_month_status(per_day_cost, current_balance, amount):
    rem_days = abs(int(last_day_of_this_month.day) -25)
    amount_for_remain_days = int(rem_days)*int(per_day_cost)
    if(current_balance - amount_for_remain_days < amount):
        # TODO send notification to student for paying the fees
        central_mess_notif()


def check_daily(student, per_day_cost):
    two_day_amount = int(2)*int(per_day_cost)
    reg_main_obj = Reg_main.objects.get(student_id=student)
    balance = reg_main_obj.balance
    if(balance <= two_day_amount):
        #TODO add the notification for the student
        central_mess_notif()

        reg_end_date_obj = Reg_records.objects.filter(student_id = student).latest('start_date')
        reg_end_date = tomorrow_g + timedelta(days=1)
        reg_end_date_obj.end_date = reg_end_date
        reg_end_date_obj.save()


def generate_per_day_bill():
    per_day_cost_obj = MessBillBase.objects.latest('timestamp')
    per_day_cost = per_day_cost_obj.bill_amount
    amount = int(30) * int(per_day_cost)
    # print(per_day_cost)
    deregistered_students = Reg_main.objects.filter(current_mess_status = "Deregistered")
    for student in deregistered_students:
        student_id = student.student_id
        check_registration(student_id)    
    
    registered_students = Reg_main.objects.filter(current_mess_status = "Registered")
    for student in registered_students:
        student_id = student.student_id
        check_deregistration(student_id)
    
    registered_students = Reg_main.objects.filter(current_mess_status = "Registered")
    for student in registered_students:
        student_id = student.student_id
        current_balance = student.balance
        check_daily(student_id, per_day_cost)
        if(int(today_g.day) == 25):
            check_next_month_status(per_day_cost, current_balance, amount)
        try:
            rebate_obj = Rebate.objects.get(student_id = student_id, start_date__lte = today_g, end_date__gte= today_g, status = 2) # TODO check for the correct value of accepting status
            try:
                monthly_bill_object = Monthly_bill.objects.get(student_id=student_id, month= this_month, year=this_year)
                monthly_bill_object.rebate_count = monthly_bill_object.rebate_count + 1
                monthly_bill_object.rebate_amount = monthly_bill_object.rebate_amount + per_day_cost
                monthly_bill_object.save()                    
            except:
                    new_monthly_bill_object = Monthly_bill(student_id=student_id, month = this_month, year=this_year, amount= amount, total_bill = 0, rebate_count = 1, rebate_amount= per_day_cost)
                    new_monthly_bill_object.save()
        except:
                try:
                    monthly_bill_object = Monthly_bill.objects.get(student_id=student_id, month= this_month, year=this_year) 
                    print(monthly_bill_object.total_bill)                   
                    monthly_bill_object.total_bill = monthly_bill_object.total_bill + per_day_cost
                    print(monthly_bill_object.total_bill)                   
                    
                    current_balance = current_balance - per_day_cost
                    student.balance = current_balance
                    monthly_bill_object.save()
                except: 
                    new_monthly_bill_object = Monthly_bill(student_id=student_id, month = this_month, year=this_year, amount= amount, total_bill = per_day_cost, rebate_count = 0, rebate_amount= 0)
                    current_balance = current_balance - per_day_cost
                    student.balance = current_balance
                    new_monthly_bill_object.save()
        if(today_g == last_day_of_this_month and current_balance < amount):
            student.current_mess_status = "Deregistered"
            try:
                reg_record_end_date = Reg_records.objects.filter(student_id = student_id).order_by('start_date')[0]                
                reg_record_end_date.end_date = first_day_of_next_month
                print(reg_record_end_date)
                reg_record_end_date.save()
            except:
                pass
        student.save()
        
        
        


# def my_scheduled_task():
    # Your task code goes here
    # Monthly_bill.objects.all().delete()